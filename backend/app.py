import sys
import asyncio

if sys.platform.startswith("win"):
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

import re
import json
import pydantic
import uvicorn
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from multiprocessing import freeze_support
from concurrent.futures import ThreadPoolExecutor
from graph import app as graph_app
from agents.common_state import AgentState
import nest_asyncio
nest_asyncio.apply() 

thread_pool = ThreadPoolExecutor()

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def make_json_serializable(obj):
    # Handle SearchResultItem objects
    if hasattr(obj, "__class__") and obj.__class__.__name__ == "SearchResultItem":
        try:
            return {
                "title": obj.title,
                "link": str(obj.link) if hasattr(obj.link, "url") else str(obj.link),
                "snippet": obj.snippet,
                "source_api": obj.source_api,
                "content": obj.content
            }
        except Exception as e:
            print(f"Warning: Error serializing SearchResultItem: {str(e)}")
            return str(obj)

    # Handle Pydantic models
    if isinstance(obj, pydantic.BaseModel):
        try:
            return obj.model_dump()
        except AttributeError: 
            return obj.dict()
        except Exception as e:
            print(f"Warning: Error serializing pydantic model: {str(e)}")
            return str(obj)
            
    # Handle pydantic-core types (HttpUrl, etc.)
    if hasattr(obj, "__str__") and (
        obj.__class__.__module__.startswith("pydantic") or 
        obj.__class__.__module__.startswith("pydantic_core") or
        "HttpUrl" in obj.__class__.__name__  # Explicit HttpUrl check
    ):
        try:
            if hasattr(obj, "url"):  # pydantic v2
                return str(obj.url)
            elif hasattr(obj, "__root__"):  # pydantic v1
                return str(obj.__root__)
            else:
                return str(obj)
        except Exception as e:
            print(f"Warning: Error serializing pydantic object {type(obj)}: {str(e)}")
            return str(obj)

    # Handle dicts
    if isinstance(obj, dict):
        try:
            result = {}
            for k, v in obj.items():
                serialized_key = str(k)
                serialized_value = make_json_serializable(v)
                result[serialized_key] = serialized_value
            return result
        except Exception as e:
            print(f"Warning: Error serializing dict: {str(e)}")
            return {str(k): str(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        try:
            return [make_json_serializable(i) for i in obj]
        except Exception as e:
            print(f"Warning: Error serializing list/tuple: {str(e)}")
            return [str(i) for i in obj]

    # Handle string representations
    if isinstance(obj, str):
        if obj.startswith("SearchResultItem("):
            try:
                # Try to extract fields using regex (best effort, not perfect)
                title_match = re.search(r"title='(.*?)'", obj)
                link_match = re.search(r"link=HttpUrl\('([^']+)'", obj)
                snippet_match = re.search(r"snippet='(.*?)'", obj)
                source_api_match = re.search(r"source_api='(.*?)'", obj)
                content_match = re.search(r"content='(.*?)'", obj)
                
                link = None
                if link_match:
                    link = link_match.group(1)
                elif "link=HttpUrl('" in obj:
                    # Try a more lenient pattern if the first one failed
                    link = obj.split("link=HttpUrl('")[1].split("'")[0]
                
                return {
                    "title": title_match.group(1) if title_match else None,
                    "link": link,
                    "snippet": snippet_match.group(1) if snippet_match else None,
                    "source_api": source_api_match.group(1) if source_api_match else None,
                    "content": content_match.group(1) if content_match else None,
                }
            except Exception as e:
                print(f"Warning: Error parsing SearchResultItem string: {str(e)}")
                return obj
                
        if obj.startswith("HttpUrl("):
            try:
                if "')" in obj:  # Handle standard format
                    return obj.split("'")[1]
                else:  # Handle other formats
                    return obj.replace("HttpUrl(", "").replace(")", "").strip("'")
            except Exception:
                return obj
                
        return obj

    # Fallback: try to serialize directly, if fails, convert to str
    try:
        json.dumps(obj)
        return obj
    except TypeError:
        if hasattr(obj, "__str__"):
            return str(obj)
        return f"Unserializable object of type {type(obj)}"

@app.post("/api/enrich-profile")
async def enrich_profile(request: Request):
    data = await request.json()
    initial_input: AgentState = {
        "leader_initial_input": data.get("summary") or data.get("linkedin") or "",
        "leadership_info": None,
        "reputation_info": None,
        "strategy_info": None,
        "background_info": None,
        "aggregated_profile": None,
        "error_message": None,
        "next_agent_to_call": None,
        "metadata": [{"source": "api", "data": data}],
        "history": None
    }
    try:
        final_state = await graph_app.ainvoke(initial_input)
        serializable_state = make_json_serializable(final_state)
        return JSONResponse({"success": True, "result": serializable_state})
    except Exception as e:
        return JSONResponse({"success": False, "error": str(e)}, status_code=500)

@app.get("/api/health")
async def health():
    return {"status": "ok"}

# --- WebSocket connection manager ---
class ConnectionManager:
    def __init__(self):
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def broadcast(self, message: str):
        for connection in self.active_connections:
            await connection.send_text(message)

manager = ConnectionManager()

@app.websocket("/ws/enrich-profile")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            try:
                msg = json.loads(data)
            except Exception:
                await websocket.send_text(json.dumps({"type": "error", "data": "Malformed message"}))
                continue
            if msg.get("type") == "enrich":
                form = msg.get("data", {})
                initial_input: AgentState = {
                    "name": form.get("name"),
                    "leader_initial_input": form.get("summary") or form.get("linkedin") or "",
                    "leadership_info": None,
                    "reputation_info": None,
                    "strategy_info": None,
                    "background_info": None,
                    "aggregated_profile": None,
                    "error_message": None,
                    "next_agent_to_call": None,
                    "metadata": [{"source": "ws", "data": form}],
                    "history": None
                }
                try:
                    await websocket.send_text(json.dumps({"type": "progress", "data": "Starting enrichment..."}))
                    final_state = await graph_app.ainvoke(initial_input)
                    serializable_state = make_json_serializable(final_state)
                    await websocket.send_text(json.dumps({"type": "progress", "data": "Enrichment complete."}))
                    await websocket.send_text(json.dumps({"type": "result", "data": serializable_state}))
                except Exception as e:
                    await websocket.send_text(json.dumps({"type": "error", "data": str(e)}))
            else:
                await websocket.send_text(json.dumps({"type": "error", "data": "Unknown message type"}))
    except WebSocketDisconnect:
        manager.disconnect(websocket)

if __name__ == "__main__":
    uvicorn.run("app:app", host="0.0.0.0", port=5000, reload=True)
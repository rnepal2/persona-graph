from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import asyncio
from graph import app as graph_app
from agents.common_state import AgentState
import json

app = FastAPI()

# Allow CORS for frontend dev
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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
        return JSONResponse({"success": True, "result": final_state})
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
                    # Simulate streaming progress (replace with real graph streaming if available)
                    await websocket.send_text(json.dumps({"type": "progress", "data": "Starting enrichment..."}))
                    # If your graph supports streaming, yield steps here
                    final_state = await graph_app.ainvoke(initial_input)
                    await websocket.send_text(json.dumps({"type": "progress", "data": "Enrichment complete."}))
                    await websocket.send_text(json.dumps({"type": "result", "data": final_state}))
                except Exception as e:
                    await websocket.send_text(json.dumps({"type": "error", "data": str(e)}))
            else:
                await websocket.send_text(json.dumps({"type": "error", "data": "Unknown message type"}))
    except WebSocketDisconnect:
        manager.disconnect(websocket)

if __name__ == "__main__":
    uvicorn.run("app:app", host="0.0.0.0", port=5000, reload=True)
import sys
import asyncio

if sys.platform.startswith("win"):
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

import re
import json
import pydantic
import uvicorn
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Request, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from multiprocessing import freeze_support
from concurrent.futures import ThreadPoolExecutor
from graph import app as graph_app
from agents.common_state import AgentState
from utils.database import save_profile, get_all_profiles, get_profile, save_user, get_user_by_email
from utils.models import ExecutiveProfile, User
import hashlib
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

# Temporary user ID for development (in production, this would come from JWT/session)
TEMP_USER_ID = 1

def get_current_user_id():
    """Temporary function to get current user ID - replace with actual auth"""
    # Ensure the user exists in database
    try:
        from utils.database import create_user_if_not_exists
        user_id = create_user_if_not_exists("rnepal", "rnepal@example.com")
        return user_id
    except Exception as e:
        print(f"Error getting user ID: {e}")
        return TEMP_USER_ID

def extract_profile_data_from_state(final_state: dict, form_data: dict) -> dict:
    """Extract profile data from the enrichment result"""
    return {
        'name': form_data.get('name', ''),
        'company': form_data.get('company', ''),
        'title': form_data.get('title', ''),
        'linkedin_url': form_data.get('linkedin', ''),
        'executive_profile': final_state.get('aggregated_profile', ''),
        'professional_background': final_state.get('background_info', ''),
        'leadership_summary': final_state.get('leadership_info', ''),
        'reputation_summary': final_state.get('reputation_info', ''),
        'strategy_summary': final_state.get('strategy_info', ''),
        'references_data': final_state.get('metadata', [])
    }

def extract_profile_data_from_result(result: dict) -> dict:
    """Extract profile data from direct enrichment result (from frontend)"""
    # Extract basic info from multiple possible locations
    basic_info = result.get('basic_info', {})
    
    # Fallback to root level if basic_info is empty
    if not basic_info.get('name'):
        basic_info = {
            'name': result.get('name', ''),
            'company': result.get('company', ''),
            'title': result.get('title', ''),
            'linkedin_url': result.get('linkedin_url', result.get('linkedin', ''))
        }
    
    # Extract references data properly
    metadata = result.get('metadata', [])
    references_data = []
    
    # Handle different metadata structures
    if isinstance(metadata, list):
        for item in metadata:
            if isinstance(item, dict):
                # Check for background_references
                if 'background_references' in item:
                    references_data.extend(item['background_references'])
                # Or if the item itself is a reference
                elif 'title' in item and 'link' in item:
                    references_data.append(item)
    
    return {
        'name': basic_info.get('name', ''),
        'company': basic_info.get('company', ''),
        'title': basic_info.get('title', ''),
        'linkedin_url': basic_info.get('linkedin_url', ''),
        'executive_profile': result.get('aggregated_profile', ''),
        'professional_background': result.get('background_info', ''),
        'leadership_summary': result.get('leadership_info', ''),
        'reputation_summary': result.get('reputation_info', ''),
        'strategy_summary': result.get('strategy_info', ''),
        'references_data': references_data
    }

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

# Profile Management Endpoints

@app.get("/api/profiles")
async def get_user_profiles():
    """Get all profiles accessible to the current user"""
    try:
        user_id = get_current_user_id()
        # Get ALL profiles (not just latest) so frontend can group versions
        profiles = get_all_profiles(user_id, latest_only=False)
        return {"success": True, "profiles": profiles}
    except Exception as e:
        return JSONResponse(
            {"success": False, "error": str(e)},
            status_code=500
        )

@app.get("/api/profile/{profile_id}")
async def get_profile_detail(profile_id: int):
    """Get detailed profile by ID"""
    try:
        user_id = get_current_user_id()
        profile = get_profile(profile_id, user_id)
        if profile:
            return {"success": True, "profile": profile}
        return JSONResponse(
            {"success": False, "error": "Profile not found or access denied"},
            status_code=404
        )
    except Exception as e:
        return JSONResponse(
            {"success": False, "error": str(e)},
            status_code=500
        )

@app.post("/api/save-profile")
async def save_profile_endpoint(request: Request):
    """Save a new profile or create new version"""
    try:
        data = await request.json()
        user_id = get_current_user_id()
        
        # Extract profile data
        profile_data = {
            'name': data.get('name', ''),
            'company': data.get('company', ''),
            'title': data.get('title', ''),
            'linkedin_url': data.get('linkedin_url', ''),
            'executive_profile': data.get('executive_profile', ''),
            'professional_background': data.get('professional_background', ''),
            'leadership_summary': data.get('leadership_summary', ''),
            'reputation_summary': data.get('reputation_summary', ''),
            'strategy_summary': data.get('strategy_summary', ''),
            'references_data': data.get('references_data', {})
        }
        
        # The save_profile function automatically handles versioning
        profile_id = save_profile(profile_data, user_id)
        return {"success": True, "profile_id": profile_id, "message": "Profile saved successfully"}
    except Exception as e:
        return JSONResponse(
            {"success": False, "error": str(e)},
            status_code=500
        )

@app.post("/api/save-enriched-profile")
async def save_enriched_profile(request: Request):
    """Save profile from enrichment result"""
    try:
        data = await request.json()
        user_id = get_current_user_id()
        
        print(f"Received save request with keys: {list(data.keys())}")
        
        # Log some sample data for debugging
        if 'basic_info' in data:
            print(f"Basic info: {data['basic_info']}")
        if 'aggregated_profile' in data:
            print(f"Aggregated profile length: {len(data.get('aggregated_profile', ''))}")
        if 'metadata' in data:
            print(f"Metadata type: {type(data['metadata'])}, length: {len(data.get('metadata', []))}")
            if data['metadata'] and len(data['metadata']) > 0:
                print(f"First metadata item: {data['metadata'][0]}")
        
        # Handle two possible data formats:
        # 1. Direct enrichment result (from ResultsDisplay)
        # 2. Wrapped format with form_data and final_state
        
        if 'form_data' in data and 'final_state' in data:
            # Wrapped format
            form_data = data.get('form_data', {})
            final_state = data.get('final_state', {})
            profile_data = extract_profile_data_from_state(final_state, form_data)
            print(f"Using wrapped format extraction")
        else:
            # Direct result format from frontend
            profile_data = extract_profile_data_from_result(data)
            print(f"Using direct format extraction")
        
        print(f"Extracted profile data keys: {list(profile_data.keys())}")
        print(f"Name: '{profile_data.get('name')}'")
        print(f"Company: '{profile_data.get('company')}'")
        print(f"References count: {len(profile_data.get('references_data', []))}")
        
        # The save_profile function automatically handles versioning based on name + linkedin_url
        profile_id = save_profile(profile_data, user_id)
        return {"success": True, "profile_id": profile_id, "message": "Enriched profile saved successfully"}
    except Exception as e:
        print(f"Error saving enriched profile: {e}")
        import traceback
        traceback.print_exc()
        return JSONResponse(
            {"success": False, "error": str(e)},
            status_code=500
        )

@app.get("/api/profile/{profile_id}/versions")
async def get_profile_versions(profile_id: int):
    """Get all versions of a specific profile"""
    try:
        user_id = get_current_user_id()
        # First check if user has access to this profile
        profile = get_profile(profile_id, user_id)
        if not profile:
            return JSONResponse(
                {"success": False, "error": "Profile not found or access denied"},
                status_code=404
            )
        
        # Get all versions for this profile (by name and linkedin_url)
        all_profiles = get_all_profiles(user_id, latest_only=False)
          # Filter to get versions of the same executive
        versions = [
            p for p in all_profiles 
            if p['name'] == profile['name'] and p['linkedin_url'] == profile['linkedin_url']
        ]
        
        return {"success": True, "versions": versions}
    except Exception as e:
        return JSONResponse(
            {"success": False, "error": str(e)},
            status_code=500
        )

@app.delete("/api/profile/{profile_id}")
async def delete_profile(profile_id: int):
    """Delete a profile by ID"""
    try:
        user_id = get_current_user_id()
        
        # First check if user has access to this profile
        profile = get_profile(profile_id, user_id)
        if not profile:
            return JSONResponse(
                {"success": False, "error": "Profile not found or access denied"},
                status_code=404
            )
        
        # Delete the profile
        from utils.database import delete_profile as db_delete_profile
        success = db_delete_profile(profile_id, user_id)
        
        if success:
            return {"success": True, "message": "Profile deleted successfully"}
        else:
            return JSONResponse(
                {"success": False, "error": "Failed to delete profile"},
                status_code=500
            )
    except Exception as e:
        return JSONResponse(
            {"success": False, "error": str(e)},
            status_code=500
        )

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
                
                # Track final state and execution status
                final_state = None
                stream_generator = None
                successful_agents = []
                failed_agents = []
                graph_completed = False
                
                try:
                    await websocket.send_text(json.dumps({"type": "progress", "data": "Starting enrichment..."}))
                    
                    # Create the stream generator
                    stream_generator = graph_app.astream(initial_input)
                    
                    # Stream the graph execution with enhanced error handling
                    async for event in stream_generator:
                        # Check if WebSocket is still connected before sending
                        if websocket.client_state.value != 1:  # 1 = CONNECTED
                            print("WebSocket disconnected during streaming, breaking loop")
                            break
                            
                        # Check if this is the END event or empty event
                        if not event or len(event) == 0:
                            print("Received END event or empty event - graph execution completed")
                            graph_completed = True
                            break
                            
                        # Process each node in the event
                        for node_name, node_data in event.items():
                            try:
                                await websocket.send_text(json.dumps({
                                    "type": "node_start", 
                                    "data": {"node": node_name}
                                }))
                                
                                # Check for node-level errors
                                if node_data.get('error_message'):
                                    failed_agents.append({
                                        "node": node_name,
                                        "error": node_data['error_message']
                                    })
                                    
                                    # Send error notification but continue processing
                                    await websocket.send_text(json.dumps({
                                        "type": "node_error",
                                        "data": {
                                            "node": node_name,
                                            "error": node_data['error_message']
                                        }
                                    }))
                                    
                                    print(f"Node {node_name} failed with error: {node_data['error_message']}")
                                    
                                else:
                                    successful_agents.append(node_name)
                                
                                # Send partial results as they become available (with safe serialization)
                                partial_result = {}
                                try:
                                    if node_data.get('background_info'):
                                        partial_result['background_info'] = str(node_data['background_info'])
                                    if node_data.get('leadership_info'):
                                        partial_result['leadership_info'] = str(node_data['leadership_info'])
                                    if node_data.get('reputation_info'):
                                        partial_result['reputation_info'] = str(node_data['reputation_info'])
                                    if node_data.get('strategy_info'):
                                        partial_result['strategy_info'] = str(node_data['strategy_info'])
                                    if node_data.get('aggregated_profile'):
                                        partial_result['aggregated_profile'] = str(node_data['aggregated_profile'])
                                    if node_data.get('metadata'):
                                        # Safely serialize metadata
                                        partial_result['metadata'] = make_json_serializable(node_data['metadata'])
                                    
                                    # Add execution status info
                                    partial_result['execution_status'] = {
                                        'successful_agents': successful_agents.copy(),
                                        'failed_agents': failed_agents.copy(),
                                        'current_node': node_name
                                    }
                                    
                                    if partial_result:
                                        await websocket.send_text(json.dumps({
                                            "type": "partial_result",
                                            "data": partial_result
                                        }))
                                        
                                except Exception as serialize_error:
                                    print(f"Error serializing partial results for {node_name}: {serialize_error}")
                                    # Send minimal safe update
                                    await websocket.send_text(json.dumps({
                                        "type": "partial_result",
                                        "data": {
                                            "execution_status": {
                                                "current_node": node_name,
                                                "serialization_error": f"Could not serialize results from {node_name}"
                                            }
                                        }
                                    }))
                                
                                await websocket.send_text(json.dumps({
                                    "type": "node_complete",
                                    "data": {"node": node_name}
                                }))
                                
                                # Store the final state from the last event
                                final_state = node_data
                                
                            except Exception as send_error:
                                print(f"Error sending WebSocket message for {node_name}: {send_error}")
                                failed_agents.append({
                                    "node": node_name,
                                    "error": f"Communication error: {str(send_error)}"
                                })
                                # Don't break - continue with next nodes
                    
                    # ALWAYS send a final result - this is critical
                    print(f"Stream completed. Final state exists: {final_state is not None}")
                    print(f"Successful agents: {successful_agents}")
                    print(f"Failed agents: {failed_agents}")
                    
                    if websocket.client_state.value == 1:
                        try:
                            # Create comprehensive final result - even if completely failed
                            if final_state:
                                final_result = make_json_serializable(final_state)
                            else:
                                # Create minimal result structure if no final state
                                final_result = {
                                    "aggregated_profile": None,
                                    "background_info": None,
                                    "leadership_info": None,
                                    "reputation_info": None,
                                    "strategy_info": None,
                                    "metadata": []
                                }
                            
                            # Add execution summary
                            final_result['execution_summary'] = {
                                'total_agents': len(successful_agents) + len(failed_agents),
                                'successful_agents': successful_agents,
                                'failed_agents': failed_agents,
                                'success_rate': len(successful_agents) / max(1, len(successful_agents) + len(failed_agents)) if (successful_agents or failed_agents) else 0,
                                'status': 'complete_failure' if not successful_agents else ('partial_success' if failed_agents else 'complete_success'),
                                'graph_completed': graph_completed
                            }
                            
                            # Generate user-friendly summary message and ensure aggregated_profile exists
                            if not successful_agents:
                                final_result['user_message'] = "Profile generation failed. Please check your settings and try again."
                                final_result['aggregated_profile'] = "Profile generation encountered errors and could not be completed. Please verify your input and try again."
                            elif failed_agents:
                                error_summary = f"Profile generated with {len(successful_agents)} successful components. "
                                error_summary += f"{len(failed_agents)} components failed."
                                final_result['user_message'] = error_summary
                                # If no aggregated profile exists, create a basic one from available info
                                if not final_result.get('aggregated_profile'):
                                    final_result['aggregated_profile'] = f"Partial profile generated based on available information. Some analysis components failed."
                            else:
                                final_result['user_message'] = "Profile generated successfully with all components."
                            

                            print("Sending final result to client...")
                            await websocket.send_text(json.dumps({"type": "final_result", "data": final_result}))
                            print("Final result sent successfully")
                                
                        except Exception as final_send_error:
                            print(f"Error sending final result: {final_send_error}")
                            # Emergency fallback - send absolute minimal response
                            try:
                                await websocket.send_text(json.dumps({
                                    "type": "final_result", 
                                    "data": {
                                        "aggregated_profile": "Profile generation encountered technical difficulties. Please try again.",
                                        "execution_summary": {
                                            "status": "system_error",
                                            "user_message": "Technical error occurred. Please try again."
                                        }
                                    }
                                }))
                                print("Emergency fallback result sent")
                            except Exception as emergency_error:
                                print(f"Emergency fallback also failed: {emergency_error}")
                    
                except Exception as e:
                    print(f"Error during graph streaming: {e}")
                    if websocket.client_state.value == 1:
                        try:
                            # Always send a final result, even on complete failure
                            if successful_agents:
                                await websocket.send_text(json.dumps({
                                    "type": "final_result",
                                    "data": {
                                        "aggregated_profile": "Profile generation was partially successful but encountered system errors.",
                                        "execution_summary": {
                                            "status": "partial_failure",
                                            "successful_agents": successful_agents,
                                            "failed_agents": failed_agents + [{"node": "system", "error": str(e)}],
                                            "user_message": f"Profile partially generated. System error: {str(e)}"
                                        }
                                    }
                                }))
                            else:
                                await websocket.send_text(json.dumps({
                                    "type": "final_result",
                                    "data": {
                                        "aggregated_profile": "Profile generation failed due to system errors. Please try again.",
                                        "execution_summary": {
                                            "status": "complete_failure",
                                            "user_message": f"Profile generation failed: {str(e)}"
                                        }
                                    }
                                }))
                        except:
                            print("Failed to send error message to WebSocket")
                            
                finally:
                    # Clean up the generator properly
                    if stream_generator is not None:
                        try:
                            await stream_generator.aclose()
                        except Exception as cleanup_error:
                            print(f"Error cleaning up stream generator: {cleanup_error}")
                            
            else:
                await websocket.send_text(json.dumps({"type": "error", "data": "Unknown message type"}))
                
    except WebSocketDisconnect:
        print("WebSocket disconnected normally")
        manager.disconnect(websocket)
    except Exception as e:
        print(f"WebSocket error: {e}")
        try:
            manager.disconnect(websocket)
        except:
            pass

if __name__ == "__main__":
    freeze_support()  # Required for Windows multiprocessing
    print("🚀 Starting Persona-Graph Backend Server...")
    print("📡 Backend will be available at: http://localhost:5000")
    print("🔌 WebSocket endpoint: ws://localhost:5000/ws/enrich-profile")
    print("📊 API Health check: http://localhost:5000/api/health")
    print("💾 Database: SQLite (auto-created in /data directory)")
    print("\n⚡ Starting server with streaming support...")
    
    uvicorn.run(
        "app:app",
        host="0.0.0.0",
        port=5000,
        reload=True,  # Auto-reload on code changes
        log_level="info",
        access_log=True
    )

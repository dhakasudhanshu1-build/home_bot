import uvicorn
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from .ros_node import init_ros, get_node
import json
import logging

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

logger = logging.getLogger("uvicorn")

@app.on_event("startup")
async def startup_event():
    init_ros()
    logger.info("ROS2 Node initialized inside FastAPI startup.")

@app.get("/")
def read_root():
    return {"status": "HomeBot Dashboard API is running"}

@app.websocket("/ws/teleop")
async def websocket_teleop(websocket: WebSocket):
    await websocket.accept()
    node = get_node()
    try:
        while True:
            data = await websocket.receive_text()
            cmd = json.loads(data)
            if 'linear' in cmd and 'angular' in cmd:
                if node:
                    node.publish_cmd_vel(cmd['linear'], cmd['angular'])
    except WebSocketDisconnect:
        logger.info("Teleop WebSocket disconnected")

@app.websocket("/ws/camera")
async def websocket_camera(websocket: WebSocket):
    await websocket.accept()
    node = get_node()
    if not node:
        await websocket.close(code=1011, reason="ROS2 node not ready")
        return
    queue = node.register_camera_client()
    logger.info("Camera WebSocket client connected")
    try:
        while True:
            frame_b64 = await queue.get()
            await websocket.send_text(frame_b64)
    except WebSocketDisconnect:
        logger.info("Camera WebSocket disconnected")
    except Exception as e:
        logger.error(f"Camera WebSocket error: {e}")
    finally:
        node.unregister_camera_client(queue)

@app.websocket("/ws/map")
async def websocket_map(websocket: WebSocket):
    """Stream map data and robot pose to the frontend."""
    await websocket.accept()
    node = get_node()
    if not node:
        await websocket.close(code=1011, reason="ROS2 node not ready")
        return

    queue = node.register_map_client()
    logger.info("Map WebSocket client connected")

    # Send latest map immediately if available
    latest = node.get_latest_map_json()
    if latest:
        await websocket.send_text(latest)

    try:
        while True:
            msg = await queue.get()
            await websocket.send_text(msg)
    except WebSocketDisconnect:
        logger.info("Map WebSocket disconnected")
    except Exception as e:
        logger.error(f"Map WebSocket error: {e}")
    finally:
        node.unregister_map_client(queue)

def main():
    uvicorn.run("hb_dashboard.server:app", host="0.0.0.0", port=8000, reload=False)

if __name__ == "__main__":
    main()

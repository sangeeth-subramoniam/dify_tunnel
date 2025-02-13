from flask import Flask, request, jsonify
import asyncio
import websockets
import json

app = Flask(__name__)

# WebSocket connection (to local machine)
LOCAL_WEBSOCKET_CLIENTS = set()

@app.route("/tunnel")
async def websocket_tunnel():
    """Handles incoming WebSocket connections from local machine"""
    websocket = request.environ["wsgi.websocket"]
    LOCAL_WEBSOCKET_CLIENTS.add(websocket)
    print("✅ Local machine connected to Azure WebSocket Tunnel")

    try:
        while True:
            message = await websocket.recv()
            print(f"🔹 Received response from local machine: {message}")

    except websockets.exceptions.ConnectionClosed:
        print("❌ Local WebSocket Disconnected")
        LOCAL_WEBSOCKET_CLIENTS.remove(websocket)

    return ""

@app.route("/", defaults={"path": ""}, methods=["GET", "POST", "PUT", "DELETE"])
@app.route("/<path:path>", methods=["GET", "POST", "PUT", "DELETE"])
async def proxy(path):
    """Receives API request and forwards it through WebSocket to local machine"""
    if not LOCAL_WEBSOCKET_CLIENTS:
        return jsonify({"error": "No active WebSocket connection"}), 500

    method = request.method
    headers = dict(request.headers)
    body = request.get_data() if request.data else None

    request_payload = {
        "method": method,
        "path": path,
        "headers": headers,
        "body": body
    }

    websocket = next(iter(LOCAL_WEBSOCKET_CLIENTS))

    try:
        await websocket.send(json.dumps(request_payload))
        response = await websocket.recv()
        return jsonify(json.loads(response))

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)

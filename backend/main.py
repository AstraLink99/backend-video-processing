from fastapi import FastAPI, UploadFile, File, WebSocket
from fastapi.middleware.cors import CORSMiddleware
import aiofiles
import pika
import json
import os
from fastapi import BackgroundTasks

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins (frontend can access backend)
    allow_credentials=True,
    allow_methods=["*"],  # Allow all HTTP methods (POST, GET, etc.)
    allow_headers=["*"],  # Allow all headers
)

UPLOAD_DIR = "storage"
os.makedirs(UPLOAD_DIR, exist_ok=True)

metadata_store = {}  # Stores extracted metadata for each video
processing_status = {}

active_connections = {}

# RabbitMQ Config
RABBITMQ_HOST = "localhost"
QUEUE_NAME = "video_tasks"

# Storage Directory
UPLOAD_DIR = "storage"
os.makedirs(UPLOAD_DIR, exist_ok=True)

# Initialize RabbitMQ connection
def setup_rabbitmq():
    """Initialize RabbitMQ Connection & Queue"""
    connection = pika.BlockingConnection(pika.ConnectionParameters(RABBITMQ_HOST))
    channel = connection.channel()
    channel.queue_declare(queue=QUEUE_NAME)  # Declare the queue
    connection.close()

setup_rabbitmq()  # Call this at startup

def send_to_queue(task):
    """Send a task to RabbitMQ"""
    connection = pika.BlockingConnection(pika.ConnectionParameters(RABBITMQ_HOST))
    channel = connection.channel()
    channel.queue_declare(queue=QUEUE_NAME)  # Ensure queue exists
    channel.basic_publish(exchange='', routing_key=QUEUE_NAME, body=json.dumps(task))
    connection.close()

@app.post("/upload")
async def upload_video(file: UploadFile = File(...)):
    client_id = "test_client"  # Pass client ID dynamically in a real app
    file_path = os.path.join(UPLOAD_DIR, file.filename)

    async with aiofiles.open(file_path, 'wb') as out_file:
        while content := await file.read(1024):
            await out_file.write(content)

    # Send task to RabbitMQ
    task = {"filename": file.filename, "client_id": client_id}  
    send_to_queue(task)

    return {"message": "Video uploaded successfully!", "filename": file.filename}

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    await websocket.send_text("WebSocket connected!")
    await websocket.close()

@app.post("/internal/metadata-extraction-status")
async def receive_metadata(metadata: dict, background_tasks: BackgroundTasks):
    """Receives metadata from the worker and stores it"""
    filename = metadata.get("filename")
    if filename:
        metadata_store[filename] = metadata
        print(f"Stored metadata for {filename}")
    return {"message": "Metadata received successfully"}

@app.get("/metadata/{filename}")
async def get_metadata(filename: str):
    """Retrieve stored metadata for a video"""
    metadata = metadata_store.get(filename)
    if metadata:
        return metadata
    return {"error": "Metadata not found"}

@app.websocket("/ws/{client_id}")
async def websocket_endpoint(websocket: WebSocket, client_id: str):
    """Handles WebSocket connections"""
    await websocket.accept()
    active_connections[client_id] = websocket
    print(f"🔗 Client {client_id} connected!")

    try:
        while True:
            data = await websocket.receive_text()
            print(f"Received from {client_id}: {data}")
    except Exception as e:
        print(f"🔴 Client {client_id} disconnected: {e}")
        del active_connections[client_id]

# Function to send updates
async def send_update(client_id: str, message: dict):
    """Sends a WebSocket update if client is connected"""
    if client_id in active_connections:
        await active_connections[client_id].send_json(message)
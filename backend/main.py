import asyncio
from fastapi import FastAPI, UploadFile, File, WebSocket
from fastapi.middleware.cors import CORSMiddleware
import aiofiles
import pika
import json
import os
from fastapi.staticfiles import StaticFiles

app = FastAPI()

# Mount storage to serve processed videos
app.mount("/storage", StaticFiles(directory="storage"), name="storage")

# Fixing CORS errors
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  
    allow_credentials=True,
    allow_methods=["*"], 
    allow_headers=["*"],  
)

UPLOAD_DIR = "storage"
os.makedirs(UPLOAD_DIR, exist_ok=True)

metadata_store = {}  # Stores extracted metadata for each video
processing_status = {}

# Store active WebSocket connections
active_connections = {}

# RabbitMQ Config
RABBITMQ_HOST = "localhost"
QUEUE_NAME = "video_tasks"

# Setup RabbitMQ
def setup_rabbitmq():
    connection = pika.BlockingConnection(pika.ConnectionParameters(RABBITMQ_HOST))
    channel = connection.channel()
    channel.queue_declare(queue=QUEUE_NAME)  
    connection.close()

setup_rabbitmq()  

def send_to_queue(task):
    """Send a task to RabbitMQ"""
    connection = pika.BlockingConnection(pika.ConnectionParameters(RABBITMQ_HOST))
    channel = connection.channel()
    channel.queue_declare(queue=QUEUE_NAME)  
    channel.basic_publish(exchange='', routing_key=QUEUE_NAME, body=json.dumps(task))
    connection.close()

@app.post("/upload")
async def upload_video(file: UploadFile = File(...)):
    client_id = "test_client"  
    file_path = os.path.join(UPLOAD_DIR, file.filename)

    async with aiofiles.open(file_path, 'wb') as out_file:
        while content := await file.read(1024):
            await out_file.write(content)

    task = {"filename": file.filename, "client_id": client_id}  
    send_to_queue(task)

    return {"message": "Video uploaded successfully!", "filename": file.filename}

@app.post("/internal/metadata-extraction-status")
async def receive_metadata(metadata: dict):
    """Receives metadata from the worker and stores it"""
    filename = metadata.get("filename")
    if filename:
        metadata_store[filename] = metadata
        print(f"Stored metadata for {filename}")

        # Send update to WebSocket
        client_id = "test_client"
        await send_update(client_id, {"status": "metadata_done", "metadata": metadata})

    return {"message": "Metadata received successfully", "data": metadata_store}

@app.get("/metadata/{filename}")
async def get_metadata(filename: str):
    """Retrieve stored metadata for a video"""
    return metadata_store.get(filename, {"error": "Metadata not found"})

@app.websocket("/ws/{client_id}")
async def websocket_endpoint(websocket: WebSocket, client_id: str):
    """Handles WebSocket connections and keeps them open"""
    await websocket.accept()
    active_connections[client_id] = websocket
    print(f"🔗 Client {client_id} connected!")

    try:
        while True:
            await asyncio.sleep(10)  
    except Exception as e:
        print(f"🔴 Client {client_id} disconnected: {e}")
    finally:
        del active_connections[client_id]

async def send_update(client_id: str, message: dict):
    """Sends a WebSocket update if client is connected"""
    if client_id in active_connections:
        websocket = active_connections[client_id]
        try:
            await websocket.send_json(message)
            print(f"✅ Sent WebSocket update: {message}")
        except Exception as e:
            print(f"❌ WebSocket send error: {e}")
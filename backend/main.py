from fastapi import FastAPI, UploadFile, File, WebSocket
import aiofiles
import pika
import json
import os

app = FastAPI()

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
    file_path = os.path.join(UPLOAD_DIR, file.filename)
    async with aiofiles.open(file_path, 'wb') as out_file:
        while content := await file.read(1024):
            await out_file.write(content)
    
    # Send task to RabbitMQ
    task = {"filename": file.filename}
    send_to_queue(task)

    return {"message": "Video uploaded successfully!", "filename": file.filename}

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    await websocket.send_text("WebSocket connected!")
    await websocket.close()

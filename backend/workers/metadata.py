import pika
import json
import ffmpeg
import os
import requests
import websockets
import asyncio

# RabbitMQ & FastAPI Config
RABBITMQ_HOST = "localhost"
QUEUE_NAME = "video_tasks"
UPLOAD_DIR = "storage"
FASTAPI_URL = "http://127.0.0.1:8000/internal/metadata-extraction-status"
WEBSOCKET_URL = "ws://127.0.0.1:8000/ws/"

async def send_update(client_id, message):
    """Send WebSocket message to FastAPI server"""
    try:
        async with websockets.connect(WEBSOCKET_URL + client_id) as websocket:
            await websocket.send(json.dumps(message))
    except Exception as e:
        print(f"❌ Error sending WebSocket update: {e}")

def process_metadata(filename):
    """Extract metadata from a video file using ffmpeg"""
    input_path = os.path.join(UPLOAD_DIR, filename)

    try:
        # Run ffprobe to get metadata
        probe = ffmpeg.probe(input_path)
        video_streams = [s for s in probe['streams'] if s['codec_type'] == 'video']

        if not video_streams:
            raise Exception("No video stream found")

        video_info = video_streams[0]  # First video stream
        metadata = {
            "filename": filename,
            "duration": float(probe["format"]["duration"]),
            "resolution": f"{video_info['width']}x{video_info['height']}",
            "codec": video_info["codec_name"]
        }

        print(f"✅ Metadata extracted: {metadata}")
        return metadata

    except Exception as e:
        print(f"❌ Error extracting metadata from {filename}: {e}")
        return None

def callback(ch, method, properties, body):
    """Processes metadata extraction tasks"""
    task = json.loads(body)
    filename = task.get("filename")
    client_id = task.get("client_id", "unknown")  #  Ensure client_id is handled

    print(f"📊 Extracting metadata for: {filename}")

    metadata = process_metadata(filename)
    if metadata:
        # Send metadata to FastAPI
        try:
            response = requests.post(FASTAPI_URL, json=metadata)
            print(f"✅ Metadata sent to FastAPI: {response.status_code}")

            #  Send WebSocket update to notify client
            asyncio.run(send_update(client_id, {
                "status": "metadata_done",
                "filename": filename,
                "metadata": metadata
            }))
        except Exception as e:
            print(f"❌ Error sending metadata: {e}")

    ch.basic_ack(delivery_tag=method.delivery_tag)

# Connect to RabbitMQ and Start Listening
connection = pika.BlockingConnection(pika.ConnectionParameters(RABBITMQ_HOST))
channel = connection.channel()
channel.queue_declare(queue=QUEUE_NAME)
channel.basic_consume(queue=QUEUE_NAME, on_message_callback=callback)

print("📊 Metadata Extraction Worker is listening for tasks...")
channel.start_consuming()

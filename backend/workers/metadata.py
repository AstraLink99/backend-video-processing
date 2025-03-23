import pika
import json
import ffmpeg
import os
import requests
import websockets
import asyncio

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
            print(f"✅ WebSocket update sent: {message}")
    except Exception as e:
        print(f"❌ Error sending WebSocket update: {e}")

def process_metadata(filename):
    input_path = os.path.join(UPLOAD_DIR, filename)
    try:
        probe = ffmpeg.probe(input_path)
        video_streams = [s for s in probe['streams'] if s['codec_type'] == 'video']

        if not video_streams:
            raise Exception("No video stream found")

        video_info = video_streams[0]
        metadata = {
            "filename": filename,
            "duration": float(probe["format"]["duration"]),
            "resolution": f"{video_info['width']}x{video_info['height']}",
            "codec": video_info["codec_name"],
            "processed_video": f"/storage/processed/enhanced_{filename}"
        }

        print(f"✅ Metadata extracted: {metadata}")
        return metadata

    except Exception as e:
        print(f"❌ Error extracting metadata from {filename}: {e}")
        return None

def callback(ch, method, properties, body):
    task = json.loads(body)
    filename = task.get("filename")
    client_id = task.get("client_id", "unknown")

    print(f"📊 Extracting metadata for: {filename}")

    metadata = process_metadata(filename)
    if metadata:
        try:
            response = requests.post(FASTAPI_URL, json=metadata)
            print(f"✅ Metadata sent to FastAPI: {response.status_code}")

            # Send WebSocket update with retry logic
            asyncio.run(send_update(client_id, {
                "status": "metadata_done",
                "filename": filename,
                "metadata": metadata
            }))
        except Exception as e:
            print(f"❌ Error sending metadata update: {e}")

    ch.basic_ack(delivery_tag=method.delivery_tag)

# Connect to RabbitMQ
connection = pika.BlockingConnection(pika.ConnectionParameters(RABBITMQ_HOST))
channel = connection.channel()
channel.queue_declare(queue=QUEUE_NAME)
channel.basic_consume(queue=QUEUE_NAME, on_message_callback=callback)

print("📊 Metadata Extraction Worker is listening for tasks...")
channel.start_consuming()

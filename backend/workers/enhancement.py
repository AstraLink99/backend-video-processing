import pika
import json
import cv2
import websockets
import asyncio
import os
from moviepy.editor import VideoFileClip

# RabbitMQ & WebSocket Config
RABBITMQ_HOST = "localhost"
QUEUE_NAME = "video_tasks"
UPLOAD_DIR = "storage"
PROCESSED_DIR = "storage/processed"
WEBSOCKET_URL = "ws://127.0.0.1:8000/ws/"

# Ensure processed storage exists
os.makedirs(PROCESSED_DIR, exist_ok=True)

async def send_update(client_id, message):
    """Send WebSocket message to FastAPI server"""
    try:
        async with websockets.connect(WEBSOCKET_URL + client_id) as websocket:
            await websocket.send(json.dumps(message))
    except Exception as e:
        print(f"❌ Error sending WebSocket update: {e}")

def enhance_video(filename):
    """Applies simple enhancements (FPS and brightness adjustments)"""
    input_path = os.path.join(UPLOAD_DIR, filename)
    output_path = os.path.join(PROCESSED_DIR, f"enhanced_{filename}")  # Save with the correct filename

    try:
        # Load video
        clip = VideoFileClip(input_path)
        new_clip = clip.fx(lambda c: c.fl_image(lambda img: cv2.convertScaleAbs(img, alpha=1.2, beta=20)))  # Brightness
        new_clip = new_clip.set_fps(30)  # Adjust FPS

        # Save processed video  Auto-detect format from filename
        if filename.endswith(".webm"):
            new_clip.write_videofile(output_path, codec="libvpx", audio_codec="libvorbis")
        else:
            new_clip.write_videofile(output_path, codec="libx264", audio_codec="aac")

        return output_path
    except Exception as e:
        print(f"❌ Error processing {filename}: {e}")
        return None

def callback(ch, method, properties, body):
    """Callback to process video enhancement tasks"""
    task = json.loads(body)
    filename = task.get("filename")
    client_id = task.get("client_id", "unknown")  #  Extract client_id

    print(f"⚙️ Processing video: {filename}")

    enhanced_path = enhance_video(filename)
    if enhanced_path:
        print(f"✅ Enhanced video saved: {enhanced_path}")

        # Send WebSocket update to FastAPI
        asyncio.run(send_update(client_id, {
            "status": "enhancement_done",
            "filename": filename,
            "enhanced_file": enhanced_path
        }))

    ch.basic_ack(delivery_tag=method.delivery_tag)  # Acknowledge message

# Connect to RabbitMQ
connection = pika.BlockingConnection(pika.ConnectionParameters(RABBITMQ_HOST))
channel = connection.channel()
channel.queue_declare(queue=QUEUE_NAME)
channel.basic_consume(queue=QUEUE_NAME, on_message_callback=callback)


print("🎥 Video Enhancement Worker is listening for tasks...")
channel.start_consuming()

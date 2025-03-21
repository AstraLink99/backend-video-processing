import pika
import json
import cv2
import os
from moviepy.editor import VideoFileClip

# RabbitMQ Config
RABBITMQ_HOST = "localhost"
QUEUE_NAME = "video_tasks"
UPLOAD_DIR = "storage"
PROCESSED_DIR = "storage/processed"

# Ensure processed storage exists
os.makedirs(PROCESSED_DIR, exist_ok=True)

def enhance_video(filename):
    """Applies simple enhancements (FPS and brightness adjustments)"""
    input_path = os.path.join(UPLOAD_DIR, filename)
    output_path = os.path.join(PROCESSED_DIR, f"enhanced_{filename}")

    try:
        # Load video
        clip = VideoFileClip(input_path)
        new_clip = clip.fx(lambda c: c.fl_image(lambda img: cv2.convertScaleAbs(img, alpha=1.2, beta=20)))  # Brightness
        new_clip = new_clip.set_fps(30)  # Adjust FPS

        # Save processed video
        new_clip.write_videofile("storage/processed/enhanced_memecry.webm", codec="libvpx", audio_codec="libvorbis")
        return output_path
    except Exception as e:
        print(f"Error processing {filename}: {e}")
        return None

def callback(ch, method, properties, body):
    """Callback to process video enhancement tasks"""
    task = json.loads(body)
    filename = task.get("filename")
    print(f"Processing video: {filename}")

    enhanced_path = enhance_video(filename)
    if enhanced_path:
        print(f"Enhanced video saved: {enhanced_path}")
    
    ch.basic_ack(delivery_tag=method.delivery_tag)  # Acknowledge message

# Connect to RabbitMQ
connection = pika.BlockingConnection(pika.ConnectionParameters(RABBITMQ_HOST))
channel = connection.channel()
channel.queue_declare(queue=QUEUE_NAME)
channel.basic_consume(queue=QUEUE_NAME, on_message_callback=callback)

print("🎥 Video Enhancement Worker is listening for tasks...")
channel.start_consuming()

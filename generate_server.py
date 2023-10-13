import os
import uuid
import time

from fastapi import FastAPI, Form, Request, Query, HTTPException, status, File
from fastapi.responses import FileResponse, HTMLResponse, RedirectResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import asyncio
import aio_pika
import base64
import json

app = FastAPI()
app.mount("/audio", StaticFiles(directory="audio"), name="audio")

# Set up Jinja2 templates
templates = Jinja2Templates(directory="templates")
rabbitmq_connection = None
rabbitmq_channel = None
rabbitmq_queue = None
ack_queue = None  # New variable to store acknowledgment queue
queue_length = 0

# Connection to RabbitMQ using aio-pika
async def setup_rabbitmq():
    global rabbitmq_connection, rabbitmq_channel, rabbitmq_queue, queue_length, ack_queue
    rabbitmq_connection = await aio_pika.connect_robust("amqp://guest:guest@localhost/")
    rabbitmq_channel = await rabbitmq_connection.channel()
    await rabbitmq_channel.set_qos(prefetch_count=1)

    # Declare the queue
    rabbitmq_queue = await rabbitmq_channel.declare_queue("musicgen_queue", durable=False)

    # Declare the acknowledgment queue
    ack_queue = await rabbitmq_channel.declare_queue("acknowledgment_queue", durable=False)

    # Set up the consumer to consume acknowledgment messages
    await ack_queue.consume(handle_acknowledgment)

    queue_length = rabbitmq_queue.declaration_result.message_count  # Initial queue length

async def handle_acknowledgment(message: aio_pika.IncomingMessage):
    global queue_length
    async with message.process():
        # Decrement the queue length
        queue_length -= 1

# Get the connection, channel, and queue in the application startup event
@app.on_event("startup")
async def startup_event():
    print('startup_event has occurred')
    await setup_rabbitmq()

def convert_wav_to_mp3(wav_path):
    # Determine the MP3 file path
    mp3_path = os.path.splitext(wav_path)[0] + ".mp3"

    # Load the WAV file
    sound = AudioSegment.from_wav(wav_path)

    # Export as MP3
    sound.export(mp3_path, format="mp3", bitrate="320k")

    # Delete the WAV file
    os.remove(wav_path)

class MusicGenRequest(BaseModel):
    text: str

@app.post("/musicgen")
async def musicgen(audio_file: bytes = File(...), text: str = Form(...), duration: str = Form(...), response_class=HTMLResponse):
    global rabbitmq_channel, queue_length

    if rabbitmq_channel is None:
        print("RabbitMQ channel not initialized.")
        return RedirectResponse("/list_generated_files", status_code=303)

    # Base64 encode the file data
    audio_file_base64 = base64.b64encode(audio_file).decode("utf-8")

    # Create a dictionary with text, duration, and file data
    message_data = {"text": text, "duration": duration, "audio_file": audio_file_base64}

    # Convert the dictionary to a JSON string
    json_message = json.dumps(message_data)

    # Use `await rabbitmq_channel.publish` instead of `rabbitmq_channel.basic_publish`
    await rabbitmq_channel.default_exchange.publish(
        aio_pika.Message(body=json_message.encode("utf-8")),
        routing_key='musicgen_queue'
    )
    
    # Update the queue length
    queue_length += 1
    
    # Redirect to /list_generated_files
    return RedirectResponse("/list_generated_files", status_code=303)

@app.get("/queue_length", response_class=JSONResponse)
async def get_queue_length():
    global queue_length
    return {"queue_length": queue_length} 

# HTML template to display results
@app.get("/results", response_class=HTMLResponse)
async def results(request: Request, generated_files: list):
    return templates.TemplateResponse("results.html", {"request": request, "generated_files": generated_files})


# Endpoint to list available generated files
@app.get("/list_generated_files", response_class=HTMLResponse)
async def list_generated_files(request: Request):
    generated_files = [f for f in os.listdir("audio") if f.endswith(".mp3")]
    return templates.TemplateResponse("list_files.html", {"request": request, "generated_files": generated_files})

@app.get("/", response_class=HTMLResponse)
async def default_endpoint(request: Request):
    context = {
        "request": request,
        "title": "My MusicGen App",
        "description": "Generate awesome music with FastAPI!",
    }
    return templates.TemplateResponse("default.html", context)
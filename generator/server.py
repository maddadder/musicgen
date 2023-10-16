import os
from typing import Optional
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
acknowledgment_status = {"status": "idle", "result": ""}

# Connection to RabbitMQ using aio-pika
async def setup_rabbitmq():
    global rabbitmq_connection, rabbitmq_channel, rabbitmq_queue, queue_length, ack_queue
    rabbitmq_connection = await aio_pika.connect_robust("amqp://guest:guest@localhost/")
    rabbitmq_channel = await rabbitmq_connection.channel()
    await rabbitmq_channel.set_qos(prefetch_count=1)

    # Declare the exchange
    await rabbitmq_channel.declare_exchange("standard_exchange", type="direct")
    await rabbitmq_channel.declare_exchange("irq_exchange", type="direct")

    # Declare the queue
    rabbitmq_queue = await rabbitmq_channel.declare_queue("standard", durable=False)
    # Bind the queue to the exchange
    await rabbitmq_queue.bind("standard_exchange", routing_key="standard_key")

     # Declare the queue
    rabbitmq_irq = await rabbitmq_channel.declare_queue("irq", durable=False)
    # Bind the queue to the exchange
    await rabbitmq_irq.bind("irq_exchange", routing_key="irq_key")

    # Declare the acknowledgment exchange
    ack_exchange = await rabbitmq_channel.declare_exchange("ack_exchange", type="direct")

    # Declare the acknowledgment queue
    ack_queue = await rabbitmq_channel.declare_queue("acknowledgment_queue", durable=False)

    # Bind the acknowledgment queue to the acknowledgment exchange
    await ack_queue.bind(ack_exchange, routing_key="ack_key")

    # Set up the consumer to consume acknowledgment messages
    await ack_queue.consume(handle_acknowledgment)

    queue_length = rabbitmq_queue.declaration_result.message_count  # Initial queue length

async def handle_acknowledgment(message: aio_pika.IncomingMessage):
    global queue_length, acknowledgment_status
    async with message.process():
        # Decrement the queue length
        queue_length -= 1
        acknowledgment_status = json.loads(message.body.decode("utf-8"))
        audio_data_base64 = acknowledgment_status.get("audio_data", "")

        if audio_data_base64:
            decoded_content = base64.b64decode(audio_data_base64)
            # Save the audio file to disk
            save_path = f"audio/{uuid.uuid4()}.mp3"
            with open(save_path, "wb") as audio_file:
                audio_file.write(decoded_content)
        acknowledgment_status['audio_data'] = None

# Get the connection, channel, and queue in the application startup event
@app.on_event("startup")
async def startup_event():
    print('startup_event has occurred')
    await setup_rabbitmq()

class MusicGenRequest(BaseModel):
    text: str

@app.post("/interrupt")
async def interrupt(response_class=HTMLResponse):

    message_data = {}
    json_message = json.dumps(message_data)

    exchange = await rabbitmq_channel.get_exchange("irq_exchange")
    await exchange.publish(
        aio_pika.Message(body=json_message.encode("utf-8")),
        routing_key='irq_key'
    )
    return JSONResponse(content={"status": "success", "message": "irq successful"})

@app.post("/musicgen")
async def musicgen(audio_file: bytes = File(...), 
                   text: Optional[str] = Form(None),
                   duration: str = Form(...), 
                   response_class=HTMLResponse):
    global rabbitmq_channel, queue_length, acknowledgment_status

    if rabbitmq_channel is None:
        print("RabbitMQ channel not initialized.")
        return RedirectResponse("/list_generated_files", status_code=303)

    # Base64 encode the file data
    audio_file_base64 = base64.b64encode(audio_file).decode("utf-8")

    # Create a dictionary with text, duration, and file data
    message_data = {"text": text, "duration": duration, "audio_file": audio_file_base64}

    # Convert the dictionary to a JSON string
    json_message = json.dumps(message_data)

    exchange = await rabbitmq_channel.get_exchange("standard_exchange")
    await exchange.publish(
        aio_pika.Message(body=json_message.encode("utf-8")),
        routing_key='standard_key'
    )
    # Update the queue length
    queue_length += 1
    acknowledgment_status = {"status": "running", "result": "Loading..."}
    return JSONResponse(content={"status": "success", "message": "Music generation successful"})


@app.get("/queue_length", response_class=JSONResponse)
async def get_queue_length():
    global queue_length
    return {"queue_length": queue_length} 

# Endpoint to get the acknowledgment status
@app.get("/acknowledgment_status", response_class=JSONResponse)
async def get_acknowledgment_status():
    global acknowledgment_status
    return acknowledgment_status

# HTML template to display results
@app.get("/results", response_class=HTMLResponse)
async def results(request: Request, generated_files: list):
    return templates.TemplateResponse("results.html", {"request": request, "generated_files": generated_files})


# Endpoint to list available generated files
@app.get("/list_generated_files", response_class=HTMLResponse)
async def list_generated_files(request: Request):
    generated_files = [f for f in os.listdir("audio") if f.endswith((".mp3", ".txt"))]
    # Sort the files by filename
    generated_files = sorted(generated_files)
    return templates.TemplateResponse("list_files.html", {"request": request, "generated_files": generated_files})

@app.get("/", response_class=HTMLResponse)
async def default_endpoint(request: Request):
    context = {
        "request": request,
        "title": "My MusicGen App",
        "description": "Generate awesome music with FastAPI!",
    }
    return templates.TemplateResponse("default.html", context)
import os
import uuid
import time
from audiocraft.models import MusicGen
from audiocraft.data.audio import audio_write
from fastapi import FastAPI, Form, Request, Query, HTTPException, status
from fastapi.responses import FileResponse, HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from pydub import AudioSegment
import asyncio
import aio_pika

model = MusicGen.get_pretrained('facebook/musicgen-large', device='cuda')
model.set_generation_params(duration=12)

app = FastAPI()

app.mount("/audio", StaticFiles(directory="audio"), name="audio")

# Set up Jinja2 templates
templates = Jinja2Templates(directory="templates")
rabbitmq_connection = None
rabbitmq_channel = None
rabbitmq_queue = None

# Connection to RabbitMQ using aio-pika
async def setup_rabbitmq():
    global rabbitmq_connection, rabbitmq_channel, rabbitmq_queue
    rabbitmq_connection = await aio_pika.connect_robust("amqp://guest:guest@localhost/")
    rabbitmq_channel = await rabbitmq_connection.channel()

    # Declare the queue
    rabbitmq_queue = await rabbitmq_channel.declare_queue("musicgen_queue", durable=False)

async def callback(ch, message, properties, body):
    try:
        text = body.decode("utf-8")
        start = time.time()
        wav = model.generate([text], progress=True)
        wav = wav[0]
        end = time.time()
        print(f"Generation took {end - start} seconds")

        save_path = f"audio/{uuid.uuid4()}"

        print(f"Saving {save_path}")
        audio_write(f'{save_path}', wav.cpu(), model.sample_rate, strategy="loudness")
        convert_wav_to_mp3(f'{save_path}.wav')
    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        await message.ack()


async def musicgen_worker():
    global rabbitmq_channel, rabbitmq_queue
    if rabbitmq_queue is None:
        print("RabbitMQ queue not initialized.")
        return

    async with rabbitmq_queue.iterator() as queue_iter:
        async for message in queue_iter:
            #async with message.process():
            await callback(rabbitmq_channel, message, None, message.body)


# Get the connection, channel, and queue in the application startup event
@app.on_event("startup")
async def startup_event():
    print('startup_event has occurred')
    await setup_rabbitmq()
    # Now that RabbitMQ is initialized, start the worker
    asyncio.create_task(musicgen_worker())

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
async def musicgen(request: MusicGenRequest, response_class=HTMLResponse):
    global rabbitmq_channel

    if rabbitmq_channel is None:
        print("RabbitMQ channel not initialized.")
        return RedirectResponse("/list_generated_files", status_code=303)

    # Use `await rabbitmq_channel.publish` instead of `rabbitmq_channel.basic_publish`
    await rabbitmq_channel.default_exchange.publish(
        aio_pika.Message(body=request.text.encode("utf-8")),
        routing_key='musicgen_queue'
    )
    
    # Redirect to /list_generated_files
    return RedirectResponse("/list_generated_files", status_code=303)


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
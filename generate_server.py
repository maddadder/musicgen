import os
import uuid
import time
import torchaudio
from audiocraft.models import MusicGen
from audiocraft.data.audio import audio_write
from fastapi import FastAPI, Form, Request, Query, HTTPException, status
from fastapi.responses import FileResponse, HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles

model = MusicGen.get_pretrained('facebook/musicgen-large', device='cuda')
model.set_generation_params(duration=12)

app = FastAPI()

app.mount("/audio", StaticFiles(directory="audio"), name="audio")

# Set up Jinja2 templates
templates = Jinja2Templates(directory="templates")

def convert_wav_to_mp3(wav_path):
    # Determine the MP3 file path
    mp3_path = os.path.splitext(wav_path)[0] + ".mp3"

    # Load the WAV file
    sound = AudioSegment.from_wav(wav_path)

    # Export as MP3
    sound.export(mp3_path, format="mp3", bitrate="320k")

    # Delete the WAV file
    os.remove(wav_path)

@app.post("/musicgen")
async def musicgen(text: str = Form(...),response_class=HTMLResponse):
    try:
        generated_files = []
        for i in range(1):  # Generate 1 audio samples
            start = time.time()
            wav = model.generate([text], progress=True)
            wav = wav[0]
            end = time.time()
            print(f"Generation took {end - start} seconds")

            save_path = f"audio/{uuid.uuid4()}"
            generated_files.append(save_path)

            print(f"Saving {save_path}")
            audio_write(f'{save_path}', wav.cpu(), model.sample_rate, strategy="loudness")
            convert_wav_to_mp3(f'{save_path}.wav')

        # Redirect to /list_generated_files
        return RedirectResponse("/list_generated_files", status_code=303)
    except Exception as e:
        print(f"An error occurred: {e}")

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
import os
from fastapi import FastAPI, Form
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import torchaudio
from audiocraft.models import MusicGen
from audiocraft.data.audio import audio_write
import time

model = MusicGen.get_pretrained('facebook/musicgen-medium', device='cuda')
model.set_generation_params(duration=12)

model_melody = MusicGen.get_pretrained('facebook/musicgen-melody', device='cuda')
model_melody.set_generation_params(duration=16)

app = FastAPI()

# Serve static files (including HTML) from a directory named "static"
app.mount("/static", StaticFiles(directory="static"), name="static")

# Set up Jinja2 templates
templates = Jinja2Templates(directory="templates")

@app.post("/musicgen")
def musicgen(text: str = Form(...), response_class=HTMLResponse):
    try:
        generated_files = []
        for i in range(3):  # Generate 3 audio samples
            start = time.time()
            wav = model.generate([text], progress=True)
            wav = wav[0]
            end = time.time()
            print(f"Generation took {end - start} seconds")

            save_path = f"static/{uuid.uuid4()}.wav"
            generated_files.append(save_path)

            print(f"Saving {save_path}")
            audio_write(f'{save_path}', wav.cpu(), model.sample_rate, strategy="loudness")

        return templates.TemplateResponse("results.html", {"request": text, "generated_files": generated_files})
    except Exception as e:
        print(f"An error occurred: {e}")

# HTML template to display results
@app.get("/results", response_class=HTMLResponse)
async def results(request: str, generated_files: list):
    return {"request": request, "generated_files": generated_files}

# Endpoint to list available generated files
@app.get("/list_generated_files", response_class=HTMLResponse)
async def list_generated_files():
    generated_files = [f for f in os.listdir("static") if f.endswith(".wav")]
    return templates.TemplateResponse("list_files.html", {"generated_files": generated_files})

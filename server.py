import subprocess
import os
import uuid
import shutil
import glob
import json
import random
import shutil
from fastapi import FastAPI, File, UploadFile, HTTPException, Form
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
import re
import torchaudio
from audiocraft.models import MusicGen
from audiocraft.data.audio import audio_write
import uuid
import time

model = MusicGen.get_pretrained('facebook/musicgen-medium', device='cuda')
model.set_generation_params(duration=12) 

model_melody = MusicGen.get_pretrained('facebook/musicgen-melody', device='cuda')
model_melody.set_generation_params(duration=16) 

app = FastAPI()

# Serve static files (including HTML) from a directory named "static"
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.post("/musicgen")
def musicgen(text: str = Form(...), response_class=FileResponse):
    try:
        start = time.time()
        wav = model.generate([text], progress=True)
        wav = wav[0]
        end = time.time()
        print(f"Generation took {end - start} seconds")

        save_path = f"/tmp/{uuid.uuid4()}"

        print(f"Saving {save_path}")
        audio_write(f'{save_path}', wav.cpu(), model.sample_rate, strategy="loudness")

        save_path = save_path + ".wav"
        return FileResponse(save_path, media_type="audio/wav")
    except Exception as e:
        print(f"An error occurred: {e}")

@app.post("/melody")
def melody(text: str = Form(...), response_class=FileResponse):
    try:
        start = time.time()
        wav = model_melody.generate([text], progress=True)
        wav = wav[0]
        end = time.time()
        print(f"Generation took {end - start} seconds")

        save_path = f"/tmp/{uuid.uuid4()}"

        print(f"Saving {save_path}")
        audio_write(f'{save_path}', wav.cpu(), model_melody.sample_rate, strategy="loudness")

        save_path = save_path + ".wav"
        return FileResponse(save_path, media_type="audio/wav")
    except Exception as e:
        print(f"An error occurred: {e}")

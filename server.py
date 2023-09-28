import os
import uuid
import time
from fastapi import FastAPI, Form, Request, Query, HTTPException, status
from fastapi.responses import FileResponse, HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles

app = FastAPI()

app.mount("/audio", StaticFiles(directory="audio"), name="audio")

# Set up Jinja2 templates
templates = Jinja2Templates(directory="templates")

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
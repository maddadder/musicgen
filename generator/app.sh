#!/bin/bash

source /home/alice/miniconda3/bin/activate audio

# Start the FastAPI app
#uvicorn server:app --host 0.0.0.0 --port 5001 --log-level error &

# Start the consumer script
python consumer.py

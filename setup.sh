# See README.md for setup instructions

# To run app
conda activate audio
uvicorn generate_server:app --host 0.0.0.0 --port 5001 --reload
#AND in another terminal
python consumer.py

# open browser to: http://server.local:5001

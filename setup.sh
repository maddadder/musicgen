# run this setup once
conda create --name audio python=3.9
#conda deactivate
conda activate audio
pip install 'torch>=2.0'
pip install -U git+https://git@github.com/facebookresearch/audiocraft#egg=audiocraft
conda install "ffmpeg<5" -c conda-forge
pip install git+https://github.com/huggingface/transformers.git

#run the following
uvicorn server:app --host 0.0.0.0 --port 5001


# open browser to: http://antec.local:5001
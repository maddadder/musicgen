# run this setup once
conda create --name audio python=3.9
#conda deactivate
conda activate audio
conda install pytorch torchvision torchaudio pytorch-cuda=11.7 -c pytorch -c nvidia
pip install -U git+https://git@github.com/facebookresearch/audiocraft#egg=audiocraft
conda install "ffmpeg<5" -c conda-forge
pip install git+https://github.com/huggingface/transformers.git
pip install chardet
pip install numpy==1.25

# install rabbitmq 
# with these instructions: https://www.rabbitmq.com/install-debian.html#apt-quick-start-cloudsmith
# then systemctl restart rabbitmq-server
pip install aio-pika

#run the following
conda activate audio
uvicorn generate_server:app --host 0.0.0.0 --port 5001 --reload


# open browser to: http://antec.local:5001
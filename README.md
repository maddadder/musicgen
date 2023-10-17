# musicgen

1. Create environment
sudo apt install nvidia-docker2
```bash
conda create --name audio python=3.9
#conda deactivate
conda activate audio
conda install pytorch torchvision torchaudio pytorch-cuda=12.1 -c pytorch -c nvidia
```
2. test cuda install
```python
import torch
torch.cuda.is_available()
quit()
```

3. Continue installing
```bash
pip install -U git+https://git@github.com/facebookresearch/audiocraft#egg=audiocraft
conda install "ffmpeg<5" -c conda-forge
pip install aio-pika
pip install pika

# install rabbitmq 
# with these instructions: https://www.rabbitmq.com/install-debian.html#apt-quick-start-cloudsmith
# then systemctl restart rabbitmq-server

mkdir audio
```

4. Deploy as a service

```bash
chmod +x generator/app.sh
sudo cp musicgen.service /etc/systemd/system/musicgen.service
sudo systemctl daemon-reload
sudo systemctl start musicgen
sudo systemctl restart musicgen
sudo systemctl enable musicgen
sudo systemctl status musicgen
```
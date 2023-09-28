import os
import uuid
import time
import torchaudio
from audiocraft.models import MusicGen
from audiocraft.data.audio import audio_write

model = MusicGen.get_pretrained('facebook/musicgen-large', device='cuda')
model.set_generation_params(duration=120)

for i in range(100):  # Generate 1 audio samples
    start = time.time()
    wav = model.generate(["progressive techno melodic house music"], progress=True)
    wav = wav[0]
    end = time.time()
    print(f"Generation took {end - start} seconds")

    save_path = f"audio/{uuid.uuid4()}"

    print(f"Saving {save_path}")
    audio_write(f'{save_path}', wav.cpu(), model.sample_rate, strategy="loudness")

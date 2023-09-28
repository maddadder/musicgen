import os
import uuid
import time
import torchaudio
from audiocraft.models import MusicGen
from audiocraft.data.audio import audio_write
from pydub import AudioSegment
import os

model = MusicGen.get_pretrained('facebook/musicgen-large', device='cuda')
model.set_generation_params(duration=120)

def convert_wav_to_mp3(wav_path):
    # Determine the MP3 file path
    mp3_path = os.path.splitext(wav_path)[0] + ".mp3"

    # Load the WAV file
    sound = AudioSegment.from_wav(wav_path)

    # Export as MP3
    sound.export(mp3_path, format="mp3")

    # Delete the WAV file
    os.remove(wav_path)

for i in range(100):  # Generate 1 audio samples
    start = time.time()
    wav = model.generate(["progressive techno melodic house music"], progress=True)
    wav = wav[0]
    end = time.time()
    print(f"Generation took {end - start} seconds")

    save_path = f"audio/{uuid.uuid4()}"

    print(f"Saving {save_path}")
    audio_write(f'{save_path}', wav.cpu(), model.sample_rate, strategy="loudness")
    convert_wav_to_mp3(f'{save_path}.wav')

import asyncio
import aio_pika
from audiocraft.models import MusicGen
from audiocraft.data.audio import audio_write
from pydub import AudioSegment
import os
import uuid
import time
import torchaudio
import json
import base64
from io import BytesIO

model = MusicGen.get_pretrained('facebook/musicgen-melody', device='cuda')

async def callback(message: aio_pika.IncomingMessage):
    async with message.process():
        # Deserialize the JSON message
        message_data = json.loads(message.body.decode("utf-8"))
        
        text = message_data.get("text", "")
        duration = int(message_data.get("duration", ""))
        audio_file_base64 = message_data.get("audio_file", "")

        model.set_generation_params(duration=duration)

        # Base64 decode the file data
        audio_file_data = base64.b64decode(audio_file_base64.encode("utf-8"))
        start = time.time()
        melody_waveform, sr = torchaudio.load(BytesIO(audio_file_data), format="mp3")
        wav = model.generate_with_chroma(
            descriptions=[text],
            melody_wavs=melody_waveform,
            melody_sample_rate=sr,
            progress=True
        )
        wav = wav[0]

        save_path = f"audio/{uuid.uuid4()}"
        print(f"Saving {save_path}")
        audio_write(f'{save_path}', wav.cpu(), model.sample_rate, strategy="loudness")
        convert_wav_to_mp3(f'{save_path}.wav')
        end = time.time()
        print(f"Generation took {end - start}")

        # Acknowledge the message by sending a signal to the acknowledgment queue
        connection = await aio_pika.connect_robust("amqp://guest:guest@localhost/")
        ack_channel = await connection.channel()
        await ack_channel.default_exchange.publish(
            aio_pika.Message(body=message.body),  # You can send a copy of the original message
            routing_key='acknowledgment_queue'
    )

def convert_wav_to_mp3(wav_path):
    mp3_path = os.path.splitext(wav_path)[0] + ".mp3"
    sound = AudioSegment.from_wav(wav_path)
    sound.export(mp3_path, format="mp3", bitrate="320k")
    os.remove(wav_path)

async def consume_audio_generation_tasks():
    connection = await aio_pika.connect_robust("amqp://guest:guest@localhost/")
    channel = await connection.channel()

    queue = await channel.declare_queue("musicgen_queue", durable=False)
    await queue.consume(lambda message: callback(message))

    # Keep the consumer running
    await asyncio.Future()

if __name__ == "__main__":
    asyncio.run(consume_audio_generation_tasks())
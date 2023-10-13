import asyncio
import aio_pika
from audiocraft.models import MusicGen
from audiocraft.data.audio import audio_write
from pydub import AudioSegment
import os
import uuid
import time

model = MusicGen.get_pretrained('facebook/musicgen-large', device='cuda')
model.set_generation_params(duration=12)

async def callback(message: aio_pika.IncomingMessage, ack_channel: aio_pika.channel):
    async with message.process():
        text = message.body.decode("utf-8")
        start = time.time()
        wav = model.generate([text], progress=True)
        wav = wav[0]

        save_path = f"audio/{uuid.uuid4()}"
        print(f"Saving {save_path}")
        audio_write(f'{save_path}', wav.cpu(), model.sample_rate, strategy="loudness")
        convert_wav_to_mp3(f'{save_path}.wav')
        end = time.time()
        print(f"Generation took {end - start}")

        # Acknowledge the message by sending a signal to the acknowledgment queue
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
    await queue.consume(lambda message: callback(message, channel))

    # Keep the consumer running
    await asyncio.Future()

if __name__ == "__main__":
    asyncio.run(consume_audio_generation_tasks())
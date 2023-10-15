from audiocraft.models import MusicGen
from audiocraft.data.audio import audio_write
from pydub import AudioSegment
import os
import uuid
import time
import torchaudio
import json
import base64
import functools
import logging
import threading
import pika
from pika.exchange_type import ExchangeType
from io import BytesIO
import binascii

LOG_FORMAT = ('%(levelname) -10s %(asctime)s %(name) -30s %(funcName) '
              '-35s %(lineno) -5d: %(message)s')
LOGGER = logging.getLogger(__name__)

logging.basicConfig(level=logging.ERROR, format=LOG_FORMAT)

INTERRUPTING = False

def interrupt(ch, delivery_tag, body):
    global INTERRUPTING
    print("interrupt called")
    INTERRUPTING = True
    cb = functools.partial(ack_message, ch, delivery_tag)
    ch.connection.add_callback_threadsafe(cb)

def on_irq_message(ch, method_frame, _header_frame, body, args):
    print('on_irq_message called')
    thrds = args
    delivery_tag = method_frame.delivery_tag

    t = threading.Thread(target=interrupt, args=(ch, delivery_tag, body))
    t.start()
    thrds.append(t)

def on_message(ch, method_frame, _header_frame, body, args):
    print("on_message called")
    thrds = args
    delivery_tag = method_frame.delivery_tag
        
    t = threading.Thread(target=do_work, args=(ch, delivery_tag, body))
    t.start()
    thrds.append(t)

def convert_wav_to_mp3(wav_path):
    mp3_path = os.path.splitext(wav_path)[0] + ".mp3"
    sound = AudioSegment.from_wav(wav_path)
    sound.export(mp3_path, format="mp3", bitrate="320k")
    os.remove(wav_path)

def validate_input(message_data):
    text = message_data.get("text", "")
    duration = message_data.get("duration", "")
    audio_file_base64 = message_data.get("audio_file", "")

    if not text or not duration:
        return False

    try:
        duration = int(duration)
    except ValueError:
        return False

    if audio_file_base64:
        try:
            decoded_content = base64.b64decode(audio_file_base64)

            # Check if the decoded content is larger than the specified size
            if len(decoded_content) < 1024:
                return False

        except (UnicodeDecodeError, binascii.Error):
            return False

    return True

def ack_message(ch, delivery_tag):
    if ch.is_open:
        ch.basic_ack(delivery_tag)
    else:
        pass

def publish_acknowledgment(body):
    connection_params = pika.ConnectionParameters(
        'localhost', credentials=pika.PlainCredentials('guest', 'guest'), heartbeat=5
    )
    with pika.BlockingConnection(connection_params) as ack_connection:
        ack_channel = ack_connection.channel()
        ack_channel.exchange_declare(
            exchange="ack_exchange", exchange_type=ExchangeType.direct
        )
        ack_channel.queue_declare(queue="acknowledgment_queue", durable=False)
        ack_channel.queue_bind(
            queue="acknowledgment_queue", exchange="ack_exchange", routing_key="ack_key"
        )
        ack_channel.basic_publish(
            exchange="ack_exchange",
            routing_key="ack_key",
            body=body,
            properties=pika.BasicProperties(content_type="application/json"),
        )
        
def do_work(ch, delivery_tag, body):
    global INTERRUPTING
    print("do_work called")
    thread_id = threading.get_ident()
    LOGGER.info('Thread id: %s Delivery tag: %s', thread_id, delivery_tag)
    message_data = json.loads(body.decode("utf-8"))

    try:
        if validate_input(message_data):
            text = message_data.get("text", "")
            duration = int(message_data.get("duration", ""))
            audio_file_base64 = message_data.get("audio_file", "")

            model = MusicGen.get_pretrained('facebook/musicgen-melody', device='cuda')
            model.set_generation_params(duration=duration)
            def _progress(generated, to_generate):
                #print(generated, to_generate)
                if INTERRUPTING:
                    raise Exception("INTERRUPTED")
            model.set_custom_progress_callback(_progress)
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
            with open(save_path + '.txt', 'w') as file:
                file.write(text)
            end = time.time()
            print(f"Generation took {end - start}")
    except Exception as e:
        # Handle the exception (e.g., log it)
        print(f"An error occurred: {e}")
    INTERRUPTING = False
    cb = functools.partial(ack_message, ch, delivery_tag)
    ch.connection.add_callback_threadsafe(cb)

    # Publish acknowledgment
    acknowledgment_body = json.dumps({"status": "completed", "task_id": message_data.get("task_id")})
    publish_acknowledgment(acknowledgment_body)




credentials = pika.PlainCredentials('guest', 'guest')
parameters = pika.ConnectionParameters(
    'localhost', credentials=credentials, heartbeat=5)

with pika.BlockingConnection(parameters) as connection:
    channel = connection.channel()
    channel.exchange_declare(
        exchange="standard_exchange",
        exchange_type=ExchangeType.direct,
        passive=False,
        durable=False,
        auto_delete=False
    )
    channel.queue_declare(queue="standard", auto_delete=False)
    channel.queue_bind(
        queue="standard", exchange="standard_exchange", routing_key="standard_key")
    channel.basic_qos(prefetch_count=1)

    channel.exchange_declare(
        exchange="irq_exchange",
        exchange_type=ExchangeType.direct,
        passive=False,
        durable=False,
        auto_delete=False
    )
    channel.queue_declare(queue="irq", auto_delete=False)
    channel.queue_bind(
        queue="irq", exchange="irq_exchange", routing_key="irq_key")
    channel.basic_qos(prefetch_count=1)

    threads = []

    # Consume standard messages
    on_message_callback = functools.partial(on_message, args=(threads))
    channel.basic_consume(on_message_callback=on_message_callback, queue='standard')

    # Consume IRQ messages
    on_irq_message_callback = functools.partial(on_irq_message, args=(threads))
    channel.basic_consume(on_message_callback=on_irq_message_callback, queue='irq')


    try:
        channel.start_consuming()
    except KeyboardInterrupt:
        channel.stop_consuming()

    for thread in threads:
        thread.join()

connection.close()
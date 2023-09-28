import subprocess

def play_audio(file_path):
    try:
        # Use aplay on Linux
        subprocess.run(['aplay', file_path], check=True)

        # Use afplay on macOS
        # subprocess.run(['afplay', file_path], check=True)

    except subprocess.CalledProcessError as e:
        print(f"Error playing the audio: {e}")

# Replace 'your_file.wav' with the path to your audio file
play_audio('musicgen_out.wav')

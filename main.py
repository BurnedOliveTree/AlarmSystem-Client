from pyaudio import PyAudio, paInt16
import wave

FORMAT = paInt16    # data format
CHANNELS = 1        # number if channels
RATE = 44100        # framerate in Hz
CHUNK = 1024        # frames / buffer
TIME = 5            # in seconds

audio = PyAudio()
frames = []

# start recording
stream = audio.open(format=FORMAT, channels=CHANNELS, rate=RATE, input=True, frames_per_buffer=CHUNK)
for i in range(0, int(RATE / CHUNK * TIME)):
    data = stream.read(CHUNK)
    frames.append(data)

# stop recording
stream.stop_stream()
stream.close()
audio.terminate()

with wave.open('file.wav', 'wb') as waveFile:
    waveFile.setnchannels(CHANNELS)
    waveFile.setsampwidth(audio.get_sample_size(FORMAT))
    waveFile.setframerate(RATE)
    waveFile.writeframes(b''.join(frames))
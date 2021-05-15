from threading import Thread
from time import sleep
from pyaudio import PyAudio, paInt16
import wave
import requests


class Recorder:
    FORMAT = paInt16    # data format
    CHANNELS = 1        # number if channels
    RATE = 44100        # framerate in Hz
    CHUNK = 1024        # frames / buffer
    TIME = 5            # in seconds

    def __init__(self):
        self.audio = None
        self.frames = None
        self.stream = None
        self.recording = False

    def start(self):
        self.audio = PyAudio()
        self.frames = []
        self.stream = self.audio.open(format=Recorder.FORMAT, channels=Recorder.CHANNELS, rate=Recorder.RATE,
                                      input=True, frames_per_buffer=Recorder.CHUNK)
        self.recording = True
        while self.recording:
            self.frames.append(self.stream.read(Recorder.CHUNK))

    def stop(self):
        self.recording = False
        sleep(1)
        self.stream.stop_stream()
        self.stream.close()
        self.audio.terminate()

    def save(self):
        with wave.open('file.wav', 'wb') as waveFile:
            waveFile.setnchannels(Recorder.CHANNELS)
            waveFile.setsampwidth(self.audio.get_sample_size(Recorder.FORMAT))
            waveFile.setframerate(Recorder.RATE)
            waveFile.writeframes(b''.join(self.frames))

    @staticmethod
    def upload(ip="0.0.0.0"):
        with open('file.wav', 'rb') as waveFile:
            files = {"record": waveFile}
            requests.post(f"http://{ip}/device/upload-record", files=files)

    def terminal(self):
        i = ''
        while i != 'end':
            i: str = input('python$ ')
            if i == 'start':
                recording_thread = Thread(target=self.start)
                recording_thread.start()
                print('Started recording!')
            if i == 'stop':
                self.stop()
                print('Stopped recording!')
            if i == 'save':
                self.save()
                print('Audio saved!')
            if i == 'upload':
                self.upload()
                print('Audio uploaded to server!')
            if i == 'end':
                break


if __name__ == '__main__':
    record = Recorder()
    record.terminal()

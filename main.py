from threading import Thread
from time import sleep
from pyaudio import PyAudio, paInt16
from pydub import AudioSegment
import RPi.GPIO as GPIO
import wave
import requests
import signal
import sys
import asyncio
import json


DEVICE_ID = 1
SERVER_IP = "192.168.0.31"
SERVER_PORT = "5000"
URL = f"http://{SERVER_IP}:{SERVER_PORT}"
VOLUME_GAIN = 39


ARMED = True
RECORDING_TIME = 30


def sigterm_handler(_signo, _stack_frame):
    sys.exit(0)

signal.signal(signal.SIGTERM, sigterm_handler)


class MovementDetector:
    def __init__(self):
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(24, GPIO.IN)
    
    def check(self):
        if GPIO.input(24):
            return True
        return False

    def __del__(self):
        GPIO.cleanup()


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
            self.frames.append(self.stream.read(Recorder.CHUNK, exception_on_overflow=False))

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
        sound = AudioSegment.from_wav("file.wav")
        sound += VOLUME_GAIN
        sound.export("file.mp3", format="mp3")

    @staticmethod
    def upload(alarm_id):
        with open('file.mp3', 'rb') as waveFile:
            files = {"record": waveFile}
            requests.post(f"{URL}/device/upload-record", files=files, params={"alarm_id": alarm_id})

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
                self.upload(report_alarm())
                print('Audio uploaded to server!')
            if i == 'end':
                break


def report_alarm():
    response = requests.post(f"{URL}/device/report-alarm", params={"device_id": DEVICE_ID})
    print(response.json())
    return response.json()["id"]


async def change_settings():
    while True:
        reader, writer = await asyncio.open_connection('192.168.0.31', 8888)

        global ARMED, RECORDING_TIME
        data = await reader.readline()
        data = json.loads(data.decode('utf-8'))
        ARMED = data['is_armed']
        RECORDING_TIME = data['recording_time']
        print(data)

        print('Close the connection')
        writer.close()
        await writer.wait_closed()


def wrapper():
    asyncio.run(change_settings())


def main():
    try:
        detector = MovementDetector()
        record = Recorder()
        async_thread = Thread(target=wrapper)
        async_thread.start()
        while True:
            if ARMED:
                if detector.check():
                    id = report_alarm()
                    recording_thread = Thread(target=record.start)
                    recording_thread.start()
                    sleep(RECORDING_TIME)
                    record.stop()
                    record.save()
                    record.upload(id)
    finally:
        del detector


if __name__ == '__main__':
    main()
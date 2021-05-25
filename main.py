from threading import Thread
from pydub import AudioSegment
import RPi.GPIO as GPIO
import requests, asyncio, json
import sys, subprocess, signal
from datetime import datetime


DEVICE_ID = 1
SERVER_IP = "192.168.0.31"
SERVER_PORT = "5000"
URL = f"http://{SERVER_IP}:{SERVER_PORT}"
VOLUME_GAIN = 39
DETECTOR_PIN = 24

ARMED = True
RECORDING_TIME = 30


def sigterm_handler(_signo, _stack_frame):
    sys.exit(0)

signal.signal(signal.SIGTERM, sigterm_handler)


class MovementDetector:
    def __init__(self):
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(DETECTOR_PIN, GPIO.IN)
    
    def check(self):
        # return True if detector notices movement
        if GPIO.input(DETECTOR_PIN):
            return True
        return False

    def __del__(self):
        GPIO.cleanup()


class Recorder:
    @staticmethod
    def record(alarm_id):
        # record microphone input for a given time, then increase volume of created audio, convert it to mp3 and remove old wav file
        print('<main>  Starting audio recording...')
        subprocess.run(['nice', '-20', './main.sh', str(RECORDING_TIME), f'file{alarm_id}'])
        sound = AudioSegment.from_wav(f'file{alarm_id}.wav')
        sound += VOLUME_GAIN
        sound.export(f'file{alarm_id}.mp3', format='mp3')
        subprocess.run(['rm', f'file{alarm_id}.wav'])
        print('<main>  Audio recorded and saved!')

    @staticmethod
    def upload(alarm_id):
        # upload recorded file and then delete it
        print('<main>  Starting to upload audio...')
        with open(f'file{alarm_id}.mp3', 'rb') as file:
            files = {"record": file}
            requests.post(f"{URL}/device/upload-record", files=files, params={"alarm_id": alarm_id})
        subprocess.run(['rm', f'file{alarm_id}.mp3'])
        print('<main>  Recording uploaded!')

    @staticmethod
    def terminal():
        # for testing and development purpose
        i = ''
        while i != 'end':
            i: str = input('python$ ')
            if i == 'record':
                Recorder.record()
                print('Started recording!')
            if i == 'upload':
                Recorder.upload(report_alarm())
                print('Audio uploaded to server!')
            if i == 'end':
                break


def report_alarm():
    # upon movement detection, immediately send a report about it and retrieve alarm UID
    print(f'<time>  Sending alarm report: {datetime.now().time()}')
    response = requests.post(f"{URL}/device/report-alarm", params={"device_id": DEVICE_ID})
    print(f'<main>  Alarm ID: {response.json()["id"]}')
    return response.json()["id"]


async def change_settings():
    # awaits and executes any incoming settings changes
    global ARMED, RECORDING_TIME
    try:
        while True:
            print('<async> Waiting for connection...')
            reader, writer = await asyncio.open_connection(SERVER_IP, 8888)

            print('<async> Waiting for data...')
            data = await reader.readline()
            data = json.loads(data.decode('utf-8'))
            ARMED = data['is_armed']
            RECORDING_TIME = data['recording_time']
            print(f'<time>  New settings received: {datetime.now().time()}')
            print(f'<async> New settings received: {ARMED}, {RECORDING_TIME}')

            writer.close()
            await writer.wait_closed()
    finally:
        writer.close()
        await writer.wait_closed()


def wrapper():
    asyncio.run(change_settings())


if __name__ == '__main__':
    with open('settings.json', 'r') as file:
        json_data = json.load(file)
        ARMED = json_data['is_armed']
        RECORDING_TIME = json_data['recording_time']
    print(f'<main>  Settings loaded: {ARMED}, {RECORDING_TIME}')
    try:
        detector = MovementDetector()
        async_thread = Thread(target=wrapper)
        async_thread.start()
        print('<main>  Launching main loop...')
        while True:
            if ARMED:
                if detector.check():
                    print('<main>  Movement detected!')
                    print(f'<time>  Movement detected: {datetime.now().time()}')
                    id = report_alarm()
                    Recorder.record(id)
                    Recorder.upload(id)
    finally:
        print('<main>  Closing...')
        del detector
        with open('settings.json', 'w') as file:
            json.dump({"is_armed": ARMED, "recording_time": RECORDING_TIME}, file)

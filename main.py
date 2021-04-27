from pyaudio import PyAudio, paInt16
import wave

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

    def start(self):
        self.audio = PyAudio()
        self.frames = []
        self.stream = self.audio.open(format=Recorder.FORMAT, channels=Recorder.CHANNELS, rate=Recorder.RATE, input=True, frames_per_buffer=Recorder.CHUNK)
        for i in range(0, int(Recorder.RATE / Recorder.CHUNK * Recorder.TIME)):
            self.frames.append(self.stream.read(Recorder.CHUNK))

        self.stream.stop_stream()
        self.stream.close()
        self.audio.terminate()

    def save(self):
        with wave.open('file.wav', 'wb') as waveFile:
            waveFile.setnchannels(Recorder.CHANNELS)
            waveFile.setsampwidth(self.audio.get_sample_size(Recorder.FORMAT))
            waveFile.setframerate(Recorder.RATE)
            waveFile.writeframes(b''.join(self.frames))

    def terminal(self):
        i = ''
        while i != 'end':
            i: str = input('python$ ')
            if i == 'start':
                print('Started recording!')
                self.start()
                print('Audio recorded!')
            if i == 'save':
                self.save()
                print('Audio saved!')
            if i == 'end':
                break

if __name__ == '__main__':
    record = Recorder()
    record.terminal()

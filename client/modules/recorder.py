import numpy as np
import pyaudio
import matplotlib.pyplot as plt
import librosa
import soundfile


class Recorder:
    is_recording = False

    def __init__(self):
        self.CHUNK = 1024 * 3
        self.THRESHOLD = 0.1
        self.FORMAT = pyaudio.paFloat32
        self.CHANNELS = 1
        self.SAMPLE_RATE = 44100
        self.p = pyaudio.PyAudio()

    def is_silent(self, record_data):
        return max(record_data) < self.THRESHOLD

    def record_to_file(self, data, path):
        soundfile.write(path, data, self.SAMPLE_RATE, subtype='PCM_24')

    def trim(self, record_data):
        threshold = self.THRESHOLD

        def _trim(rc_data):
            record_start = False
            r = []

            for i in rc_data:
                if not record_start and abs(i) > threshold:
                    record_start = True
                    r.append(i)
                elif record_start:
                    r.append(i)
            return r

        record_data = _trim(record_data)

        record_data.reverse()
        record_data = _trim(record_data)
        record_data.reverse()
        record_data = np.hstack(record_data)
        return record_data

    def record_sec(self, second=4):
        stream = self.p.open(format=self.FORMAT,
                             channels=self.CHANNELS,
                             rate=self.SAMPLE_RATE,
                             input=True,
                             output=True,
                             frames_per_buffer=self.CHUNK)

        frames = []
        num_silent_frame = 0
        total_frame = int(self.SAMPLE_RATE / self.CHUNK * second)

        plt.ion()
        fig, ax = plt.subplots()
        #
        x = np.arange(0, self.CHUNK * 2, 2)

        # ax.set_ylim([-2 ** 9, (2 ** 9 - 1)])
        ax.set_ylim([-1.0, 1.0])
        ax.set_xlim(0, self.CHUNK)
        line, = ax.plot(x, np.random.rand(self.CHUNK))

        for i in range(0, total_frame):
            frame = np.frombuffer(stream.read(self.CHUNK), dtype=np.float32)

            line.set_ydata(frame)
            fig.canvas.draw()
            fig.canvas.flush_events()
            if self.is_silent(frame):
                num_silent_frame += 1
            frames.append(frame)

        record = np.hstack(frames)

        # number of silent frames exceed 80%
        # consider none information is recorded
        plt.close()
        stream.stop_stream()
        stream.close()

        if num_silent_frame / total_frame > 0.8:
            print("None recorded")
            return -1
        else:
            # record = self.trim(record)
            self.record_to_file(record, 'wavs/input.wav')
            return 1
        # record = librosa.resample(record, self.SAMPLE_RATE, 16000)

    def record(self):
        p = pyaudio.PyAudio()

        stream = p.open(format=self.FORMAT,
                        channels=self.CHANNELS,
                        rate=self.SAMPLE_RATE,
                        input=True,
                        output=True,
                        frames_per_buffer=self.CHUNK)

        num_silent_chunk = 0
        r = []
        prev = np.zeros(0)

        plt.ion()
        fig, ax = plt.subplots()
        #
        x = np.arange(0, self.CHUNK * 2, 2)

        # ax.set_ylim([-2 ** 9, (2 ** 9 - 1)])
        ax.set_ylim([-1.0, 1.0])
        ax.set_xlim(0, self.CHUNK)
        line, = ax.plot(x, np.random.rand(self.CHUNK))

        while True:
            record_data = np.frombuffer(stream.read(self.CHUNK), dtype=np.float32)
            # print(max(record_data))
            # plt.plot(record_data)
            # plt.show()

            line.set_ydata(record_data)
            fig.canvas.draw()
            fig.canvas.flush_events()
            # plt.pause(0.01)

            silent = self.is_silent(record_data)
            if silent and Recorder.is_recording:
                num_silent_chunk += 1
                r.append(record_data)

                if num_silent_chunk > 3:
                    Recorder.is_recording = False
                    num_silent_chunk = 0
                    print("Stop")

                    record = np.hstack(r)
                    record = librosa.resample(record, self.SAMPLE_RATE, 16000)

                    r = []
            elif not silent:
                if not Recorder.is_recording:
                    Recorder.is_recording = True
                    r.append(prev)
                    print("Recording")

                r.append(record_data)
            prev = record_data

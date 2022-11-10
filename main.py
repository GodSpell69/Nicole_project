'''----GUI----'''
import sys
import struct
from PyQt5 import QtWidgets
from PyQt5.QtCore import QTimer
'''----Graph----'''
import numpy as np
import pyqtgraph as pg
'''----Audio Processing----'''
import pyaudio
import wave
import speech_recognition as sr
import math
import time
import os
from PyQt5.QtCore import pyqtSlot, pyqtSignal, QThread

Threshold = 6
SHORT_NORMALIZE = (1.0/32768.0)
TIMEOUT_LENGTH = 5
swidth = 2

FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 44100
CHUNK = 1024 * 2

p = pyaudio.PyAudio()
stream = p.open(format=FORMAT,
                        channels=CHANNELS,
                        rate=RATE,
                        input=True,
                        output=True,
                        frames_per_buffer=CHUNK)

class MainWindow(QtWidgets.QMainWindow):

    def __init__(self, *args, **kwargs):
        super(MainWindow, self).__init__(*args, **kwargs)
        pg.setConfigOptions(antialias=True)

        self.IDisplay()
        self.IAnimate_Title()
        self.IData()
        self.IAnimate_Graph()
        self.show()

    def IDisplay(self):

        self.traces = dict()
        self.graphWidget =  pg.PlotWidget()
        self.graphWidget.disableAutoRange()
        self.setCentralWidget(self.graphWidget)
        self.setWindowTitle("Waveform")
        self.setGeometry(55, 115, 970, 449)
        self.graphWidget.setTitle("...", color="w", size="30pt")

    def IAnimate_Title(self):

        self.worker = Recorder()
        self.thread2 = QThread()

        self.worker.phrase.connect(self.Update_Title)

        self.worker.moveToThread(self.thread2)

        self.thread2.started.connect(self.worker.listen)

        self.worker.finished.connect(self.thread2.exit)

    def IData(self):
        self.x = np.arange(0, 2 * CHUNK, 2)
        self.f = np.linspace(0, RATE // 2, CHUNK // 2)

    def IAnimate_Graph(self):

        self.timer = QTimer()
        self.timer.setInterval(50)
        self.timer.timeout.connect(self.Update)
        self.timer.start()

    def Set_plotdata(self, name, data_x, data_y):
        if name in self.traces:
            self.traces[name].setData(data_x, data_y)
        else:
            if name == 'waveform':
                self.traces[name] = self.graphWidget.plot(pen='c', width=3)
                self.graphWidget.setYRange(0, 255, padding=0)
                self.graphWidget.setXRange(0, 2 * CHUNK, padding=0.005)
                self.graphWidget.autoRange()

    def Update(self):

        self.wf_data = stream.read(CHUNK)
        self.wf_data = struct.unpack(str(2 * CHUNK) + 'B', self.wf_data)
        self.wf_data = np.array(self.wf_data, dtype='b')[::2] + 128
        self.Set_plotdata(name='waveform', data_x=self.x, data_y=self.wf_data)

    def Update_Title(self,my_title_phrase):

        self.graphWidget.setTitle(my_title_phrase, color="w", size="30pt")

class Recorder(QThread):
    phrase = pyqtSignal(str)

    @staticmethod
    def rms(frame):
        count = len(frame) / swidth
        format = "%dh" % (count)
        shorts = struct.unpack(format, frame)

        sum_squares = 0.0
        for sample in shorts:
            n = sample * SHORT_NORMALIZE
            sum_squares += n * n
        rms = math.pow(sum_squares / count, 0.5)

        return rms * 1000

    def __init__(self, *args, **kwargs):
        super(Recorder, self).__init__()
        self.args = args
        self.kwargs = kwargs

    def record(self):
        print('Noise detected, recording beginning')
        rec = []
        current = time.time()
        end = time.time() + TIMEOUT_LENGTH

        while current <= end:

            data = stream.read(CHUNK)
            if self.rms(data) >= Threshold: end = time.time() + TIMEOUT_LENGTH

            current = time.time()
            rec.append(data)
        self.write(b''.join(rec))

    def write(self, recording):
        f_name_directory = r'D:\Gab\prog\Nicole_project\audiosamples'

        n_files = len(os.listdir(f_name_directory))

        filename = os.path.join(f_name_directory, '{}.wav'.format(n_files))

        wf = wave.open(filename, 'wb')
        wf.setnchannels(CHANNELS)
        wf.setsampwidth(p.get_sample_size(FORMAT))
        wf.setframerate(RATE)
        wf.writeframes(recording)
        wf.close()
        print('Written to file: {}'.format(filename))
        print('Returning to listening')

        self.recognition(filename)

    def recognition(self, filename):

        r = sr.Recognizer()

        recorded_phrase = ""

        with sr.AudioFile(filename) as source:

            r.adjust_for_ambient_noise(source, duration=1)

            #Armazena o que foi dito numa variavel
            audio = r.listen(source)

            try:
                recorded_phrase = r.recognize_google(audio,language='pt-BR')

            except sr.UnknownValueError:
                recorded_phrase = "Not understood"

            self.phrase.emit(recorded_phrase)
        print(recorded_phrase)

    @pyqtSlot()
    def listen(self):
        print('Listening beginning')
        self.flag = True

        while self.flag:
            input = stream.read(CHUNK)
            rms_val = self.rms(input)
            if rms_val > Threshold:
                self.record()

    def stop(self):
        self.flag = False

def main():
    app = QtWidgets.QApplication(sys.argv)
    win = MainWindow()

    win.thread2.start()
    app.exec_()
    sys.exit()

if __name__ == '__main__':
    main()
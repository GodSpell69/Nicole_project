'''----GUI----'''
import sys
import struct
from PyQt5 import QtCore
from PyQt5 import QtWidgets
from PyQt5.QtCore import QTimer
'''----Graph----'''
import numpy as np
import pyqtgraph as pg
'''----Audio Processing----'''
import pyaudio
import wave
import speech_recognition as sr
import multiprocessing as mlti

FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 44100
CHUNK = 1024 * 2

p = pyaudio.PyAudio()
stream = p.open(
    format=FORMAT,
    channels=CHANNELS,
    rate=RATE,
    input=True,
    output=True,
    frames_per_buffer=CHUNK,
    )

frames = []
seconds = 4
phrase = "..."
WORD = "YouTube"

class MainWindow(QtWidgets.QMainWindow):

    def __init__(self, *args, **kwargs):
        super(MainWindow, self).__init__(*args, **kwargs)
        pg.setConfigOptions(antialias=True)

        self.IDisplay()
        self.IAnimate_Title()
        self.IData()
        self.IAnimate_Graph()

    def IDisplay(self):

        self.traces = dict()
        self.graphWidget =  pg.PlotWidget()
        self.graphWidget.disableAutoRange()
        self.setCentralWidget(self.graphWidget)
        self.setWindowTitle("Waveform")
        self.setGeometry(55, 115, 970, 449)
        self.graphWidget.setTitle(phrase, color="w", size="30pt")

    def IAnimate_Title(self):

        self.picktimer = QTimer()
        self.picktimer.singleShot(6000, self.IntersectionTask)

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

    def IntersectionTask(self):
        self.recog_Instance = Audio_Recognition()
        self.recog_Instance.recog_phrase.connect(self.Update_Title)
        self.recog_Instance.Speech_Recog()

    def Update(self):

        self.wf_data = stream.read(CHUNK)
        self.wf_data = struct.unpack(str(2 * CHUNK) + 'B', self.wf_data)
        self.wf_data = np.array(self.wf_data, dtype='b')[::2] + 128
        self.Set_plotdata(name='waveform', data_x=self.x, data_y=self.wf_data)

    def Update_Title(self,my_title_phrase):

        self.graphWidget.setTitle(my_title_phrase, color="w", size="30pt")
        '''if my_title_phrase.count(WORD) > 0:
            self.graphWidget.setTitle(my_title_phrase, color="w", size="30pt")
            QtWidgets.qApp.processEvents()
            kit.playonyt("Mozart")
        else:
            self.graphWidget.setTitle("I didn't understand", color="w", size="30pt")'''

def main():
        app = QtWidgets.QApplication(sys.argv)
        win = MainWindow()
        win.show()
        sys.exit(app.exec_())

def Record():
        for i in range(0, int(RATE/CHUNK*seconds)):
            data = stream.read(CHUNK)
            frames.append(data)
            print(i)
        stream.stop_stream()
        stream.close()
        p.terminate()

        obj = wave.open("output.wav", "wb")
        obj.setnchannels(CHANNELS)
        obj.setsampwidth(p.get_sample_size(FORMAT))
        obj.setframerate(RATE)
        obj.writeframes(b"".join(frames))
        obj.close()

class Audio_Recognition(QtWidgets.QWidget):
    recog_phrase = QtCore.pyqtSignal(str)

    def Speech_Recog(self):

        r = sr.Recognizer()

        recorded_phrase = ""

        with sr.AudioFile("output.wav") as source:

            r.adjust_for_ambient_noise(source, duration=1)

            #Armazena o que foi dito numa variavel
            audio = r.listen(source)

            try:
                recorded_phrase = r.recognize_google(audio,language='pt-BR')

            except sr.UnknownValueError:
                recorded_phrase = "Not understood"

        self.recog_phrase.emit(recorded_phrase)

if __name__ == '__main__':
    p1 = mlti.Process(target=main)
    p1.start()

    Record()
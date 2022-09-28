'''GUI'''
import struct
from PyQt5 import QtWidgets
from PyQt5.QtWidgets import QApplication
import sys

'''Graph'''
import pyqtgraph as pg
from PyQt5 import QtCore
import numpy as np

'''Audio Processing'''
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
seconds = 6

class MainWindow(QtWidgets.QMainWindow):
    def __init__(self, *args, **kwargs):
        super(MainWindow, self).__init__(*args, **kwargs)
        pg.setConfigOptions(antialias=True)
        self.traces = dict()

        '''Display'''
        self.graphWidget =  pg.PlotWidget()
        self.setCentralWidget(self.graphWidget)
        self.setWindowTitle("Waveform")
        self.setGeometry(55, 115, 970, 449)

        '''Data'''
        self.x = np.arange(0, 2 * CHUNK, 2)
        self.f = np.linspace(0, RATE // 2, CHUNK // 2)

        '''Animate'''
        self.timer = QtCore.QTimer()
        self.timer.setInterval(50)
        self.timer.timeout.connect(self.update)
        self.timer.start()  

    def set_plotdata(self, name, data_x, data_y):
        if name in self.traces:
            self.traces[name].setData(data_x, data_y)
        else:
            if name == 'waveform':
                self.traces[name] = self.graphWidget.plot(pen='c', width=3)
                self.graphWidget.setYRange(0, 255, padding=0)
                self.graphWidget.setXRange(0, 2 * CHUNK, padding=0.005)

    def update(self):

        self.wf_data = stream.read(CHUNK)
        self.wf_data = struct.unpack(str(2 * CHUNK) + 'B', self.wf_data)
        self.wf_data = np.array(self.wf_data, dtype='b')[::2] + 128
        self.set_plotdata(name='waveform', data_x=self.x, data_y=self.wf_data)
        self.graphWidget.setTitle("Title", color="w", size="30pt")

def main():
    app = QApplication(sys.argv)
    win = MainWindow()
    win.show()
    sys.exit(app.exec_())

def Record():
    for i in range(0, int(RATE/CHUNK*seconds)):
        data = stream.read(CHUNK)
        frames.append(data)
        print(i)

def Refine_Stream():
    stream.stop_stream()
    stream.close()
    p.terminate()

    obj = wave.open("output.wav", "wb")
    obj.setnchannels(CHANNELS)
    obj.setsampwidth(p.get_sample_size(FORMAT))
    obj.setframerate(RATE)
    obj.writeframes(b"".join(frames))
    obj.close()

def Speech_Recog():

        print("Function Started")

        r = sr.Recognizer()

        #usando o microfone
        with sr.AudioFile("output.wav") as source:

            r.adjust_for_ambient_noise(source, duration=1)

            #Armazena o que foi dito numa variavel
            audio = r.listen(source)

            frase = ""

            try:
            #Passa a variável para o algoritmo reconhecedor de padroes
                frase = r.recognize_google(audio,language='pt-BR')
                print(frase)

            #Se nao reconheceu r.UnknownValueError:
            except sr.UnknownValueError:
                frase = "Não entendi"
                print(frase)

if __name__ == '__main__':
    p2 = mlti.Process(target=main)
    p2.start()

    Record()

    Refine_Stream()

    Speech_Recog()


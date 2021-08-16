import tkinter
from tkinter import *

# matplotlib.use("TkAgg")
import requests

from modules.recorder import Recorder
from modules.voice_modules import VoiceModules
from tts_modules.vietTTS.synthesizer import Synthesizer

LARGE_FONT = ("Verdana", 12)


class RecordGUI(tkinter.Tk):
    def __init__(self, *args, **kwargs):
        Tk.__init__(self, *args, **kwargs)

        container = Frame(self)
        container.pack(side="top", fill="both", expand=True)
        container.grid_rowconfigure(0, weight=1)
        container.grid_columnconfigure(0, weight=1)

        self.frames = {}
        frame = RecordPage(container, self)
        self.frames[RecordPage] = frame

        frame.grid(row=0, column=0, sticky="nsew")

        self.show_frame(RecordPage)

    def show_frame(self, cont):
        frame = self.frames[cont]
        frame.tkraise()


class RecordPage(Frame):
    def __init__(self, parent, controller):
        Frame.__init__(self, parent)

        self.end_record = True
        self.recorder = Recorder()

        self.voice_modules = VoiceModules()
        self.voice_synthesizer = Synthesizer()

        label = Label(self, text="Start Page", font=LARGE_FONT)
        label.pack(pady=10, padx=10)

        # matplot figure
        # self.figure = Figure(figsize=(10, 5), dpi=100)
        # self.figure.subplots_adjust(bottom=0.10, right=0.96, left=0.08, top=0.95, wspace=0.10)
        # self.ax = self.figure.add_subplot(111)
        #
        # x = np.arange(0, self.recorder.CHUNK * 2)
        # self.ax.set_ylim([-1.0, 1.0])
        # self.ax.set_xlim(0, self.recorder.CHUNK)
        # self.plt = self.ax.plot(x, np.random.rand(self.recorder.CHUNK), label='Mic-in')[0]
        #
        # self.canvas = FigureCanvasTkAgg(self.figure, self)
        # self.canvas.get_tk_widget().pack(side=tkinter.TOP,
        #                                  fill=tkinter.BOTH,
        #                                  expand=True)

        # toolbar = NavigationToolbar2Tk(canvas, self)
        # toolbar.update()
        # canvas._tkcanvas.pack(side=tkinter.TOP,
        #                       fill=tkinter.BOTH,
        #                       expand=True)

        rec_button = Button(self, text="Bắt đầu", command=lambda: self.record())
        rec_button.pack()

    def record(self):
        # print("rec func")
        rec = self.recorder.record_sec()
        if rec == -1:
            return None
        input_text = self.voice_modules.speech_to_text()

        print(input_text)

        response = requests.post('http://localhost:5002/webhooks/rest/webhook', json={"message": input_text})

        for r in response.json():
            print(r['text'])
            self.voice_synthesizer.synthesize(r['text'])

    # def animate(self):
    #     self.plt.set_ydata(self.recorder.record_data)
    #     self.canvas.draw_idle()
    #     # selfcanvas.flush_events()
    #     self.after(1000, self.animate())


app = RecordGUI()
app.geometry('600x500')
app.mainloop()

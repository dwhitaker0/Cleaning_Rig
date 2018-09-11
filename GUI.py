import tkinter as tk
from Machines import Numato_Control as Numato
import subprocess as sb
from Machines import Header as H
import pandas as p

config = p.read_csv("config.txt", sep = "=", header = None)


Light_Source = Numato.UVLightSource(str(config.iloc[1,1]))

def Light_On():
    Light_Source.halogen_on()
    Light_Source.deuterium_on()

def Light_Off():
    Light_Source.halogen_off()
    Light_Source.deuterium_off()

def Run_Experiment():
    sb.call(["python", "Auto_Run_Experiments.py"])




root = tk.Tk()
root.title("PMTC Cleaning Rig")
frame = tk.Frame(root)
frame.pack()

H.PMTC_Header()

Quit = tk.Button(frame,
                   text="QUIT",
                   fg="red",
                   command=quit)
Quit.pack(side=tk.LEFT)

ON = tk.Button(frame,
                   text="Light Source ON",
                   fg="green",
                   command=Light_On)
ON.pack(side=tk.LEFT)


OFF = tk.Button(frame,
                   text="Light Source OFF",
                   fg="red",
                   command=Light_Off)
OFF.pack(side=tk.LEFT)


RunExperiment = tk.Button(frame,
                   text="RUN Experiment",
                   command=Run_Experiment)
RunExperiment.pack(side=tk.LEFT)


root.mainloop()

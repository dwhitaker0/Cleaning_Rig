####################
##import required modules##
####################

import threading
import time
import logging
import os
import sys
import numpy as np
import pandas as p
import datetime
import subprocess


import pyqtgraph as pg
from pyqtgraph.Qt import QtGui
from PySide import QtCore

####################
##import machine modules##
####################

from Machines import Camera
from Machines import Watson_Marlow as WM
from Machines import Numato_Control as Numato
import seabreeze.spectrometers as sb
import serial

##Read Config File

config = p.read_csv("config.txt", sep = "=", header = None)

#############
##define threads## :: The camera is run as a seperate thread to allow the interpreter to continue
#############
cam_thread = threading.Thread(name = "Camera", target = Camera.start_video)

#############
##Set up logging##
#############

log_formatter = logging.Formatter('%(asctime)s %(name)-12s %(levelname)-8s %(message)s', datefmt='%d/%m/%Y %H:%M:%S')

#File to log to
today = datetime.date.today()
todaystr = today.isoformat()
logFile =  "./data/" + todaystr + "_logfile.txt"

#Setup File handler
file_handler = logging.FileHandler(logFile)
file_handler.setFormatter(log_formatter)
file_handler.setLevel(logging.INFO)

#Setup Stream Handler (console)
stream_handler = logging.StreamHandler()
stream_handler.setFormatter(log_formatter)
stream_handler.setLevel(logging.INFO)

#Get logger
logger = logging.getLogger('root')
logger.setLevel(logging.INFO)

#Add both Handlers
logger.addHandler(file_handler)
logger.addHandler(stream_handler)


#################
##Connect to machines##
#################

#Pump
Pump = WM.pump_530du(config.iloc[0,1].strip())
logging.info("Connected to Pump")

#Spectrometer
specdevs = sb.list_devices()
spec = sb.Spectrometer(specdevs[0])
logging.info("Connected to: " + str(specdevs[0]))

#Light_Source
Light_Source = Numato.UVLightSource(config.iloc[1,1].strip())

##################
##Connect to Database##
##################

##Place holder for sql database upload##

#import sqlite3

#db = sqlite3.connect ('database/db_1.db')

#cursor = db.cursor()

#experiment_name = "test_extrusion_experiment"
#operator = "DW"
#type = "Extruder"
#info = "Feed:200, Temp:100, SS:200"
#status = "Active"
#time_stamp = dt.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
#start_time = float(time.time())


#cursor.execute('INSERT INTO Experiments(Experiment_Name, Operator, Date_Time, Experiment_Type, Experimental_Information, Status) VALUES(?,?,?,?,?,?)', (experiment_name, operator, time_stamp, type, info, status))

#experiment_ID = cursor.lastrowid
#db.commit()
#logging.info ("Experiment created with ID:", experiment_ID)

#while (i < 10):
#	process_time = time.time() - start_time
#	temp = randint(20,30)
#	cursor.execute('INSERT INTO Temperature_1(Experiment_ID, TimeStamp, Temperature) VALUES(?,?,?)', (experiment_ID, process_time, temp))
#	i = i+1
#	time.sleep(1)
#	print "Temp = ", temp
#	db.commit()

#status = "Complete"
#cursor.execute('UPDATE Experiments SET Status = ? WHERE Experiment_ID = ?', (status, experiment_ID))
#db.commit()

#set-up plot

#QtGui.QApplication.setGraphicsSystem('raster')
app = QtGui.QApplication([])
mw = QtGui.QMainWindow()
mw.setWindowTitle('Spectral Data')
mw.resize(1200,600)
cw = QtGui.QWidget()
mw.setCentralWidget(cw)
l = QtGui.QVBoxLayout()
cw.setLayout(l)

pw = pg.PlotWidget(name='UV Spectrum')  ## giving the plots names allows us to link their axes together
l.addWidget(pw)
#pw2 = pg.PlotWidget(name='Zero Distance')
#l.addWidget(pw2)

mw.show()
## Create an empty plot curve to be filled later, set its pen
p1 = pw.plot(pen=2)
pw.enableAutoRange(enable=True)
pw.setYRange(-2,2,padding=0)
#p2 = pw2.plot(pen=2)
#pw2.enableAutoRange(enable=True)

###########
## Functions ##
###########

def start_dark_reference():
	global dark_ref
	spec.integration_time_micros(spectral_int_time)
	Light_Source.shutter_close()
	time.sleep(2)
	dark_ref = spec.intensities()
	Light_Source.shutter_open()


def start_reference():
	global reference
	Pump.set_speed(pump_speed)
	Pump.start()
	time.sleep(5)
	spec.integration_time_micros(spectral_int_time)
	reference = spec.intensities()
	time.sleep(1)
	Pump.stop()


def start_experiment():
	global wl
	global raw_spectral_data
	global refd_spectral_data
	global start_time
	global spec_time
	#global lambda_max

	wl = spec.wavelengths()
	raw_spectral_data = spec.wavelengths()
	Abs_spectral_data = spec.wavelengths()
	spec_time = time.strftime("%H:%M:%S %d-%m-%Y")
	start_time = float(time.time())
	logger.info ("Experiment started at: " + time.strftime("%H:%M:%S | %d-%m-%Y"))

	#set-up and start pump
	Pump.set_speed(pump_speed)
	Pump.start()


	while (float(time.time()) < start_time+float(experiment_time)):
		spectrum = spec.intensities()
		sp_time = time.strftime("%H:%M:%S %d-%m-%Y")
		raw_spectral_data = np.vstack((raw_spectral_data, spectrum))
		Abs_spectral_data = np.vstack((Abs_spectral_data, np.log10((reference - dark_ref)/(spectrum - dark_ref))))
		spec_time =  np.array([spec_time, sp_time])
		#curr_lambda_max = np.amax(Abs_spectral_data)
		#lambda_max = np.array([lambda_max, curr_lambda_max])

		#Update Plot

		p1.setData(wl,np.log10((reference - dark_ref)/(spectrum - dark_ref)))
		#p2.setData(spec_time, lambda_max)
		pg.QtGui.QApplication.processEvents()

		time.sleep((spectral_int_time/1000000)+0.05)

	logger.info("Experiment complete at: " + time.strftime("%H:%M:%S | %d-%m-%Y"))
	Pump.stop()
	#plt.close(fig)
	final_data = raw_spectral_data
	final_Abs = Abs_spectral_data
	Where_Nan = np.isnan(Abs_spectral_data)
	Where_Inf = np.isinf(Abs_spectral_data)
	final_Abs[Where_Nan] = 0
	final_Abs[Where_Inf] = 0
	np.savetxt(os.path.join(experiment_name) + "/spectral_results.csv", final_data , fmt="%s", delimiter=",")
	np.savetxt(os.path.join(experiment_name) + "/Abs_spectral_results.csv", final_Abs, fmt="%s", delimiter=",")
	np.savetxt(os.path.join(experiment_name) + "/reference.csv", reference, fmt="%s", delimiter=",")
	np.savetxt(os.path.join(experiment_name) + "/dark_reference.csv", dark_ref, fmt="%s", delimiter=",")
	np.savetxt(os.path.join(experiment_name) + "/wl.csv", wl, fmt="%s", delimiter=",")
	np.savetxt(os.path.join(experiment_name) + "/times.csv", spec_time, fmt="%s", delimiter=",")
	logger.info("Spectral data saved as: " + os.path.join(experiment_name) + "/spectral_results.csv")
	time.sleep(10)









###############
## RUNNING CODE ##
###############


#load experiments
Exps = p.read_csv("./Parameters.csv")

input("Insert Blank Coupon")
spectral_int_time = float(Exps.iloc[0, 3])
spectral_int_time = float(spectral_int_time * 1000000)
pump_speed = Exps.iloc[0, 1]
start_dark_reference()
time.sleep(2)
start_reference()
logger.info ("Reference Acquired at: " + time.strftime("%H:%M:%S | %d-%m-%Y"))


for i in range (0, Exps.shape[0]):
	try:

		global experiment_name
		stored_exeption = None
		Exp_Name  = Exps.iloc[i, 0]
		experiment_name = Exp_Name
		experiment_name = "./data/" + todaystr + "/" + experiment_name
		pump_speed = Exps.iloc[i, 1]
		experiment_time = float(Exps.iloc[i, 2])
		experiment_time = float(experiment_time * 60)
		video_time = str(float(experiment_time + 2))
		spectral_int_time = float(Exps.iloc[i, 3])
		spectral_int_time = float(spectral_int_time * 1000000)
		Camera.path = experiment_name
		print (Exp_Name,pump_speed, experiment_time, spectral_int_time)
		logger.info (Exp_Name + "@" + time.strftime("%H:%M:%S | %d-%m-%Y"))

		#create directory

		#if not os.path.exists(experiment_name):
		 #   os.makedirs(experiment_name)

		if os.path.exists(experiment_name):
			print("Experiment already exists . . . . exiting")
			time.sleep (5)
			sys.exit()
		else:
			os.makedirs(experiment_name)

		#cam_thread.start() ##Can be stopped with: Camera.video_rec = 0
		input("Place coupon to be tested in holder and push enter . . .")
		subprocess.Popen(["python", "./Machines/Camera_ext.py", "-p",  experiment_name, "-l",  video_time])
		time.sleep(1)
		start_experiment()

		if stored_exeption:
			break

	except KeyboardInterrupt:
			logger.info("Experiment Interrupted at: " + time.strftime("%H:%M:%S | %d-%m-%Y"))
			stored_exeption = sys.exc_info()

Pump.disconnect()

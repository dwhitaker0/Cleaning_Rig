####################
##import required modules##
####################

import threading
import time
import logging
import os
import sys
import numpy as np
import datetime


import pyqtgraph as pg
from pyqtgraph.Qt import QtGui
from PySide import QtCore

####################
##import machine modules##
####################

from Machines import Camera
from Machines import Watson_Marlow as WM
import seabreeze.spectrometers as sb
import serial

#############
##define threads## :: The camera is run as a seperate thread to allow the interpreter to continue
#############
cam_thread = threading.Thread(name = "Camera", target = Camera.start_video)

##########
## SET_UP ##
##########

#get user input
global experiment_name
experiment_name = input("Enter Experiment Name: ")
experiment_time = float(input("How long should the experiment run? (Minutes) "))
experiment_time = float(experiment_time * 60)
pump_speed =  int(input("Pump Speed (RPM): "))
spectral_int_time =  float(input("Spectral Integration Time (Seconds): "))
start_time = float(time.time())
today = datetime.date.today()  
todaystr = today.isoformat() 
experiment_name = "./data/" + todaystr + "/" + experiment_name
Camera.path = experiment_name
spectral_int_time = float(spectral_int_time * 1000000)



#create directory

#if not os.path.exists(experiment_name):
 #   os.makedirs(experiment_name)

if os.path.exists(experiment_name):
	print("Experiment already exists . . . . exiting")
	time.sleep (5)
	sys.exit()
else:
	os.makedirs(experiment_name)


#############	
##Set up logging##
#############

log_formatter = logging.Formatter('%(asctime)s %(name)-12s %(levelname)-8s %(message)s', datefmt='%d/%m/%Y %H:%M:%S')

#File to log to
logFile = os.path.join(experiment_name) + "/logfile.txt"

#Setup File handler
file_handler = logging.FileHandler(logFile)
file_handler.setFormatter(log_formatter)
file_handler.setLevel(logging.INFO)

#Setup Stream Handler (console)
#stream_handler = logging.StreamHandler()
#stream_handler.setFormatter(log_formatter)
#stream_handler.setLevel(logging.INFO)

#Get logger
logger = logging.getLogger('root')
logger.setLevel(logging.INFO)

#Add both Handlers
logger.addHandler(file_handler)
#logger.addHandler(stream_handler)

	
#################
##Connect to machines##
#################

#Pump
Pump = WM.pump_530du("COM3")
logger.info("Connected to Pump")

#Spectrometer
specdevs = sb.list_devices()
spec = sb.Spectrometer(specdevs[0])
logger.info("Connected to: " + str(specdevs[0]))

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


###########
## Functions ##
###########

def start_dark_reference():
	global dark_ref
	spec.integration_time_micros(spectral_int_time)
	dark_ref = spec.intensities()


def start_reference():
	global reference
	Pump.set_speed(pump_speed)
	Pump.start()
	time.sleep(10)
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
	global lambda_max

	wl = spec.wavelengths()
	raw_spectral_data = spec.wavelengths()
	Abs_spectral_data = spec.wavelengths()
	spec_time = np.array(0) 
	start_time = time.time()
	lambda_max = np.array(0)
	logger.info ("Experiment started at: " + time.strftime("%H:%M:%S | %d-%m-%Y"))
	
	#set-up and start pump
	Pump.set_speed(pump_speed)
	Pump.start()
	
	
	#set-up plot
	
	#QtGui.QApplication.setGraphicsSystem('raster')
	app = QtGui.QApplication([])
	mw = QtGui.QMainWindow()
	mw.setWindowTitle("Cleaning Experimental System")
	#mw.resize(600,400)
	mw.setGeometry(6,150, 650,450 )
	cw = QtGui.QWidget()
	mw.setCentralWidget(cw)
	l = QtGui.QVBoxLayout()
	cw.setLayout(l)

	
	pw = pg.PlotWidget(name="UV Spectrum") 
	l.addWidget(pw)
	pw2 = pg.PlotWidget(name="Lambda Max Vs Time")
	l.addWidget(pw2)

	mw.show()
	## Create an empty plot curve to be filled later, set its pen
	p1 = pw.plot(pen=2, title="UV Spectrum" )
	pw.enableAutoRange(enable=True)
	pw.setYRange(-2,2,padding=0)
	pw.setLabel('left', 'Absorbance', units='Arbitr. Units')
	pw.setLabel('bottom', 'Wavelength', units='nm')
	p2 = pw2.plot(pen=2, symbol = 'o', symbolPen = 2, title="Lambda Max Vs Time")
	pw2.enableAutoRange(enable=True)
	pw2.setLabel('left', 'Max Intensity', units='Arbitr. Units')
	pw2.setLabel('bottom', 'Time', units='s')
		
	while (float(time.time()) < start_time+float(experiment_time)):
		spectrum = spec.intensities()
		sp_time = time.time() 
		raw_spectral_data = np.vstack((raw_spectral_data, spectrum))
		Abs_spectral_data = np.vstack((Abs_spectral_data, np.log10((reference - dark_ref)/(spectrum - dark_ref))))
		spec_time =  np.append(spec_time, [sp_time-start_time])
		curr_lambda_max = np.amax(spectrum - reference)
		lambda_max = np.append(lambda_max, [curr_lambda_max])
		
		#Update Plot
		
		p1.setData(wl,np.log10((reference - dark_ref)/(spectrum - dark_ref)))
		p2.setData(spec_time, lambda_max)
		pg.QtGui.QApplication.processEvents()
		
		time.sleep((spectral_int_time/1000000)+0.05)
		
	logger.info("Experiment complete at: " + time.strftime("%H:%M:%S | %d-%m-%Y"))
	Pump.stop()
	Camera.video_rec = 0
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
	
	

	


	
	
	
###############
## RUNNING CODE ##
###############
input("Close light shutter and push enter . . . ")
time.sleep(5)
start_dark_reference()
input("Open light shutter and push enter . . . ")
input("Place blank coupon in holder and push enter . . . ")
start_reference()
logger.info ("Reference Acquired at: " + time.strftime("%H:%M:%S | %d-%m-%Y"))
cam_thread.start() ##Can be stopped with: Camera.video_rec = 0
input("Place coupon to be tested in holder and push enter . . .")
start_experiment()
Pump.disconnect()

exit()


if __name__ == '__main__':
    import sys
    if (sys.flags.interactive != 1) or not hasattr(QtCore, 'PYQT_VERSION'):
        QtGui.QApplication.instance().exec_()



####################
##import required modules##
####################

import threading
import time
import logging
import os
import numpy as np

####################
##import machine modules##
####################

import Camera
import Watson_Marlow as WM
import seabreeze.spectrometers as sb
import serial

#############
##define threads## :: The camera is run as a seperate thread to allow the interpreter to continue
#############
cam_thread = threading.Thread(name = "Camera", target = Camera.start_video)

#################
##Connect to machines##
#################

#Pump

Pump = WM.pump_530du("COM8")
logging.info("Connected to Pump")

#Spectrometer
specdevs = sb.list_devices()
spec = sb.Spectrometer(specdevs[0])
logging.info("Connected to: " + str(specdevs[0]))


##########
## SET_UP ##
##########

#get user input
global experiment_name
experiment_name = input("Enter Experiment Name: ")
experiment_time = float(input("How long should the experiment run? (in minutes) "))
experiment_time = float(experiment_time * 60)
pump_speed =  float(input("Pump Speed: "))
spectral_int_time =  float(input("Spectral Integration Time: "))
start_time = float(time.time())
Camera.path = experiment_name



#create directory

if not os.path.exists(experiment_name):
    os.makedirs(experiment_name)

#if os.path.exists(experiment_name):
 #   print("Experiment Already Exists")
#	time.sleep (10)
#	exit()
#else:
    #os.makedirs(experiment_name)


#############	
##Set up logging##
#############
logger = logging.getLogger('')
#set up logging to file
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s %(name)-12s %(levelname)-8s %(message)s',
                    datefmt='%d-%m %H:%M:%S',
                    filename='Runlog.log')

#set up logging to console
console = logging.StreamHandler()
console.setLevel(logging.INFO)
# set a format which is simpler for console use
formatter = logging.Formatter('%(name)-12s: %(levelname)-8s %(message)s')
# tell the handler to use this format
console.setFormatter(formatter)
# add the handler to the root logger
logger.addHandler(console)	
	
##################
## Structures and Data ##
##################

#declare required structures


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

	wl = spec.wavelengths()
	raw_spectral_data = spec.wavelengths()
	Abs_spectral_data = spec.wavelengths()
	spec_time = time.strftime("%H:%M:%S %d-%m-%Y") 
	start_time = float(time.time()) 
	logger.info ("Experiment started at: " + time.strftime("%H:%M:%S | %d-%m-%Y"))
	Pump.set_speed(pump_speed)
	Pump.start()
	while (float(time.time()) < start_time+float(experiment_time)):
		spectrum = spec.intensities()
		sp_time = time.strftime("%H:%M:%S %d-%m-%Y") 
		raw_spectral_data = np.vstack((raw_spectral_data, spectrum))
		Abs_spectral_data = np.vstack((Abs_spectral_data, -np.log10((reference - dark_ref)/(spectrum - dark_ref))))
		spec_time =  np.array([spec_time, sp_time])
		time.sleep((spectral_int_time/10000)+0.3)
		
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



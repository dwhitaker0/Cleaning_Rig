

import sys
import serial
import time



def set_on(serial_port, function):
	cmd = ("gpio "+ "set" +" "+ str(function) + "\r")
	serial_port.write(cmd.encode('ascii'))
	time.sleep(1)
	
def set_off(serial_port, function):
	cmd = ("gpio "+ "clear" +" "+ str(function) + "\r")
	serial_port.write(cmd.encode('ascii'))
	time.sleep(1)


	
Shutter = 6
Halogen = 7
Deuterium = 5

	

class UVLightSource: 
	def __init__(self, port): 
		self.port = serial.Serial(port=port, baudrate = 19200,
		timeout  = 1)

	def connect(self): 
		#Open the serial port
		self.port.open()

	def disconnect(self): 
		#Close the serial port
		self.port.close() 
		
	def shutter_open(self):
		set_on(self.port, Shutter)
	
	def deuterium_on(self):
		set_on(self.port, Deuterium)
		
	def halogen_on(self):
		set_on(self.port, Halogen)
		
	def shutter_close(self):
		set_off(self.port, Shutter)
	
	def deuterium_off(self):
		set_off(self.port, Deuterium)
		
	def halogen_off(self):
		set_off(self.port, Halogen)
		
		
		

import os
import sys
import traceback
import time

#include the pyserial package
import serial


#Function to write to serial port
def send_cmd(string,serial_port):
    if string[0:2] == 'SP':
        cmd_send = '1' + string
    else:
        cmd_send = '1' + string + chr(13) + chr(10)
    serial_port.write(cmd_send.encode('ascii'))
    time.sleep(0.3)

   

###############
##Control Functions##
###############

class pump_530du: 
	def __init__(self, port): 
		self.port = serial.Serial(port=port, baudrate = 9600,
		parity   = serial.PARITY_NONE,
		stopbits = serial.STOPBITS_TWO,
		bytesize = serial.EIGHTBITS,
		timeout  = 0.3)

	def connect(self): 
		#Open the serial port
		self.port.open()

	def disconnect(self): 
		#Close the serial port
		self.port.close() 
 
	def start(self):
		send_cmd('GO',self.port)

	def stop(self):
		send_cmd('ST',self.port)
	
	def set_speed(self, speed):
		send_cmd('SP'+str(speed), self.port)


    

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

def Pump_Connect():
	sPump = serial.Serial(
		port        = 'COM3',             
		baudrate = 9600,
		parity   = serial.PARITY_NONE,
		stopbits = serial.STOPBITS_TWO,
		bytesize = serial.EIGHTBITS,
		timeout  = 0.3)
	return sPump

def Pump_Disconnect():
	sPump.close()	

def Pump_Start():
	send_cmd('GO',sPump)

def Pump_Stop():
	send_cmd('ST',sPump)

def Pump_Set_Rate(rate):
	send_cmd('SP'+str(rate), sPump)



    

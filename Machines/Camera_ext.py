import numpy as np
import cv2
import os
import sys
import argparse
import time


# construct the argument parser and parse the arguments
ap = argparse.ArgumentParser()
ap.add_argument("-p", "--path", required=True,
	help="experiment path")
ap.add_argument("-l", "--length", required=True,
	help="length to record")

args = vars(ap.parse_args())

path = args["path"]
start_time = float(time.time())
length = float(args["length"])


cap = cv2.VideoCapture(0)

# Define the codec and create VideoWriter object
fourcc = cv2.VideoWriter_fourcc(*'XVID')
out = cv2.VideoWriter(os.path.join(path) +'/video_output.avi',fourcc, 20.0, (640,480))

while(float(time.time()) < start_time+float(length)):
	ret, frame = cap.read()
	if ret==True:
            # write  frame
		out.write(frame)

		cv2.imshow('frame',frame)
		if cv2.waitKey(1) & 0xFF == ord('q'):
			break
	else:
		break

cap.release()
out.release()
cv2.destroyAllWindows()

import numpy as np
import cv2
import os

video_rec = 1
path = "/"


def start_video():
	cap = cv2.VideoCapture(0)

	# Define the codec and create VideoWriter object
	fourcc = cv2.VideoWriter_fourcc(*'XVID')
	out = cv2.VideoWriter(os.path.join(path) +'/video_output.avi',fourcc, 20.0, (640,480))

	while(video_rec == 1):
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
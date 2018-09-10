import subprocess


experiment_name = "test"
video_time = str(float(2))


subprocess.call(["python", "./Machines/Camera_ext.py", "-p",  experiment_name, "-l",  video_time])

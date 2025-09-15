import time
import subprocess

while True:
    subprocess.run(["poetry", "run", "python", "main.py"])
    time.sleep(3*60) 

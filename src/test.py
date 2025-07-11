# test.py
from datetime import datetime

with open("robot.log", "a") as f:
    f.write(f"Started at {datetime.now()}\n")

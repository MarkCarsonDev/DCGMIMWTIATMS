# DCGMIMWTIATMS

## About
This is a basic program that shows blood-glucose levels in mg/dL on the Windows toolbar from Dexcom's API.
Stands for:

- **D**excom's
- **C**ontinuous
- **G**lucose
- **M**onitor
- **I**n
- **M**y
- **W**indows
- **T**oolbar
    - (**I**n
    - **A**ddition
    - **T**o
    - **M**y
    - **S**kin)

## Setup

First, clone the respository:

`git clone https://github.com/MarkCarsonDev/DCGMIMWTIATMS`


The program can be ran as a script (`python main.py`), or it can be compiled into an executable usng the pyinstaller package:

`pip install -r requirements.txt`

`pyinstaller --onefile --windowed --name "GlucoseMonitor" main.py --clean --noupx`

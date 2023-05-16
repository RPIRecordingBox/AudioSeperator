# Audio Seperator

**Note: it does not perform deep noise reduction, do that before running this program**

## Installation

```
pip install -r requirements.txt
```

## Usage:

```
usage: main.py [-h] [-i INPUT [INPUT ...]] [-o OUTPUT] [-p] [-g [GAIN]] [-s [START]] [-l [LENGTH]]

optional arguments:
  -h, --help            show this help message and exit
  -i INPUT [INPUT ...], --input INPUT [INPUT ...]
                        List of files to input, can either be one 4 channel wave or two 2 channel waves
  -o OUTPUT, --output OUTPUT
                        Out file name, defaults to out.wav
  -p, --plot            Whether to display a plot
  -g [GAIN], --gain [GAIN]
                        Gain to apply to the raw audio data (dB), default: +0 dB
  -s [START], --start [START]
                        Number of seconds in to start at in the file, defaults to 0. Understands HH:MM:SS format
  -l [LENGTH], --length [LENGTH]
                        Length from start to parse, defaults to -1 (the remainder of the file). Understands HH:MM:SS format
```
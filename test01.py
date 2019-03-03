'''
Install the p44-ledchain driver first: https://github.com/plan44/plan44-feed/tree/master/p44-ledchain
(Some help: http://community.onion.io/post/13346)

Activate PWM and module with:
> omega2-ctrl gpiomux set pwm0 pwm
> insmod /lib/modules/4.4.61/p44-ledchain.ko ledchain0=0,10,1

This is currently work in process, thus the commented out sections and so on. Use this as 
a starting point or source of inspiration!
'''

import time
import math

import subprocess

import flatten

NUM_LEDS = 22

values = [100, 0, 0]
values = [0] * (NUM_LEDS * 3)

def map(x, in_min, in_max, out_min, out_max):
    return (x - in_min) * (out_max - out_min) / (in_max - in_min) + out_min

def normalizeSin(x):
    return map(x, -1, 1, 0, 1)

STARTTIME = time.time()
def sin(freq, phaseOffset = 0):
    deltaT = time.time() - STARTTIME
    phase = deltaT * (math.pi * 2) + phaseOffset
    return math.sin(phase * freq)

def normSin(freq, phaseOffset = 0):
    return map(sin(freq, phaseOffset), -1, 1, 0, 1)


i = 0
while True:
    i += 1
    
    # r = normalizeSin(r);
#         g = normalizeSin(g);
#         b = normalizeSin(b);
#
#         values[0] = int(r * 255)
#         values[1] = int(g * 255)
#         values[2] = int(b * 255)
#
#         for j in range(NUM_LEDS - 1):
#             values[(j+1)*3] = values[0]
#             values[(j+1)*3+1] = values[1]
#             values[(j+1)*3+2] = values[2]
#
#         for j in range(NUM_LEDS):
#             if (i % NUM_LEDS != j):
#                 values[j*3] = 0
#                 values[j*3+1] = 0
#                 values[j*3+2] = 0

    color = [
        0,
        0,
        normSin(1/9) * 255, 
        # normSin(1/3, math.pi * 3/2) * 255, 
        # 0,
        # 0
    ]
    values = flatten.flatten(color * NUM_LEDS)
    # for j in range(NUM_LEDS):
    
    for j in range(len(values)):
        values[j] = int(values[j] / 10)
        
    # values[0] = 13
    
    # with open('/dev/ledchain0','wb', buffering=0) as chain:
        # chain.write(bytes(values))
    # chain.close()
    
    bytestr = ""
    for j in range(len(values)):
        bytestr += "\\x{0:02X}".format(*([values[j]]))
    
    myoutput = open("/dev/ledchain0", "w")
    # myoutput = open("/dev/ledchain1", "w")
    subprocess.call(["echo", "-en", bytestr], stdout=myoutput)
    myoutput.close()
    # print(bytestr)
    # print()
        
    time.sleep(1/20)

import numpy as np
from math import atan2, sqrt, cos, sin, acos, pi, copysign
import time
import serial
import VisionModule as vm
#import Interface as inter

CST_ANGLE_MIN = 0
CST_ANGLE_MAX = 180

def checkConstraints(value, min_val, max_val):
    return max(min_val, min(value, max_val))

def send_angles_to_arduino(angles):
    try:
        with serial.Serial('/dev/ttyACM0', 9600, timeout=1) as arduino:
            time.sleep(1)
            data = ",".join(str(int(a)) for a in angles) + "\n"
            arduino.write(data.encode())
            print("Sent to Arduino:", data)
    except Exception as e:
        print("Serial Error:", e)

def simple_IK(targetXYZG):
    d1 = 11.522
    d2 = 12.203
    d3 = 12.43
    d4 = 12.31

    x0, y0, z0, g0 = targetXYZG

    q1 = atan2(y0, x0) * 180 / pi
    xyr = sqrt(x0**2 + y0**2)
    q0 = 80

    lx = d4 * cos(q0 * pi / 180)
    lz = d4 * sin(q0 * pi / 180)
    x1 = xyr - lx
    z1 = z0 + lz - d1

    h = sqrt(x1**2 + z1**2)

    a1 = atan2(z1, x1)
    a2 = acos((d2**2 - d3**2 + h**2) / (2 * d2 * h))
    q2 = (a1 + a2) * 180 / pi

    a3 = acos((d2**2 + d3**2 - h**2) / (2 * d2 * d3))
    q3 = 180 - a3 * 180 / pi

    q4 = q0 - (q3 - q2) + 5
    q2 += 15

    angles = [q1, 90 - q2, q3 - 90, q4, g0, 90]
    return [checkConstraints(a, CST_ANGLE_MIN, CST_ANGLE_MAX) for a in angles]

def CBtoXY(targetCBsq, params, color):
    wletterWeight = [-4, -3, -2, -1, 1, 2, 3, 4]
    bletterWeight = [4, 3, 2, 1, -1, -2, -3, -4]
    bnumberWeight = [8, 7, 6, 5, 4, 3, 2, 1]

    if targetCBsq[0] == 'k':
        x = 6 * params["sqSize"]
        y = 6 * params["sqSize"]
    else:
        if color:
            sqletter = bletterWeight[ord(targetCBsq[0]) - 97]
            sqNumber = bnumberWeight[int(targetCBsq[1]) - 1]
        else:
            sqletter = wletterWeight[ord(targetCBsq[0]) - 97]
            sqNumber = int(targetCBsq[1])

        x = params["baseradius"] + params["cbFrame"] + params["sqSize"] * sqNumber - params["sqSize"] * 0.5
        y = params["sqSize"] * sqletter - copysign(params["sqSize"] * 0.5, sqletter)

    return x, y


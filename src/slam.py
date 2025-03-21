import pygame # type: ignore
import tkinter.filedialog
import qwiic_otos # type: ignore
import sys
import time
import os
import motorController
import board # type: ignore
import adafruit_bno055 # type: ignore
import threading

from future.moves import pickle # type: ignore
from drawBoard import *
from ctypes import *
from adafruit_servokit import ServoKit # type: ignore


class Hindernisse:
    x = 0
    y = 0
    farbe = 0
    NICHTS = 0
    RED = 1
    GREEN = 2
    def __init__(self, x, y, farbe = 0):
        self.x = x
        self.y = y
        self.farbe = farbe
        # noinspection PyListCreation
    
class Slam:
    loopCounter = 10
    loopCounterGyro = 0
    angle = 0
    xpos = 0
    ypos = 0
    lastXpos = 5000
    lastYpos = 5000
    direction = 0
    CW = 0
    CCW = 1
    def __init__(self):
        self.hindernisse = []
        self.hindernisse.append(Hindernisse(x=2000, y=2408))
        self.hindernisse.append(Hindernisse(x=2008, y=2594))
        self.hindernisse.append(Hindernisse(x=1505, y=2397))
        self.hindernisse.append(Hindernisse(x=1508, y=2600))
        self.hindernisse.append(Hindernisse(x=1000, y=2405))
        self.hindernisse.append(Hindernisse(x=1008, y=2602))
        self.hindernisse.append(Hindernisse(x=600, y=2014))
        self.hindernisse.append(Hindernisse(x=405, y=2000))
        self.hindernisse.append(Hindernisse(x=600, y=1505))
        self.hindernisse.append(Hindernisse(x=394, y=1505))
        self.hindernisse.append(Hindernisse(x=597, y=994))
        self.hindernisse.append(Hindernisse(x=394, y=1005))
        self.hindernisse.append(Hindernisse(x=1000, y=602))
        self.hindernisse.append(Hindernisse(x=997, y=405))
        self.hindernisse.append(Hindernisse(x=1497, y=602))
        self.hindernisse.append(Hindernisse(x=1497, y=417))
        self.hindernisse.append(Hindernisse(x=1994, y=594))
        self.hindernisse.append(Hindernisse(x=1997, y=414))
        self.hindernisse.append(Hindernisse(x=2408, y=1000))
        self.hindernisse.append(Hindernisse(x=2594, y=1005))
        self.hindernisse.append(Hindernisse(x=2400, y=1494))
        self.hindernisse.append(Hindernisse(x=2600, y=1494))
        self.hindernisse.append(Hindernisse(x=2397, y=2000))
        self.hindernisse.append(Hindernisse(x=2605, y=2002))
        
        self.xpos = 0
        self.ypos = 0
        self.angleStart = 0
        self.speed = 0
        i2c = board.I2C()
        self.sensor = adafruit_bno055.BNO055_I2C(i2c)

        script_dir = os.path.abspath(os.path.dirname(__file__))
        lib_path = os.path.join(script_dir, "sg.so")

        self.lidar = CDLL(lib_path)
        self.lidar.initLidar()

        arr = [1]
        self.scan = (c_int * 361)(*arr)


        # Create instance of device
        self.myOtos = qwiic_otos.QwiicOTOS()

        # Check if it's connected
        if self.myOtos.is_connected() == False:
            print("The device isn't connected to the system. Please check your connection", \
                file=sys.stderr)
            return

        # Initialize the device
        self.myOtos.begin()
        
        print("Calibrating IMU...")

        # Calibrate the IMU, which removes the accelerometer and gyroscope offsets
        self.myOtos.calibrateImu()
        self.myOtos.setLinearUnit(self.myOtos.kLinearUnitMeters)
        self.myOtos.setAngularUnit(self.myOtos.kAngularUnitDegrees)
        self.myOtos.setLinearScalar(1.022494887525562)
        # self.myOtos.setLinearScalar(0.9)
        self.myOtos.setAngularScalar(0.9947222222222221)
        self.myOtos.resetTracking()

    def startpostionsetzen(self):
        average = 0
        scans = 0
        for i in range (-5,6):
            if self.scan[i] > 0:
                average = average + self.scan[i]
                scans += 1
        average = average / scans

        if (average > 1870) and (average < 1970):
            self.angleStart = 0
            self.direction = self.CW
            self.setPostion(average, 3000 - self.scan[90]) 
        if (average > 1345) and (average < 1450):
            self.angleStart = 180
            self.direction = self.CCW
            self.setPostion(self.scan[180], 3000 - self.scan[-90])
        if (average > 1550) and (average < 1660):
            self.angleStart = 180
            self.direction = self.CCW
            self.setPostion(self.scan[180], 3000 - self.scan[-90])
        if (average > 1040) and (average < 1200):
            self.angleStart = 0
            self.direction = self.CW
            self.setPostion(average, 3000 - self.scan[90])
        

        if (self.scan[180] > 70) and (self.scan[180] < 170) and (self.scan[90] < 400):
            self.angleStart = 0
            self.direction = self.CW
            self.setPostion(2000 - self.scan[180], 3000 - self.scan[90])
        elif (self.scan[180] > 70) and (self.scan[180] < 170) and (self.scan[-90] < 400):
            self.angleStart = 180
            self.direction = self.CCW
            self.setPostion(2000 - self.scan[0], 3000 - self.scan[90])

        # 1870 - 1970
        # 1345 - 1450
        # 1550 - 1660
        # 1040 - 1200
    def setPostion(self, x, y):
        myPosition = self.myOtos.getPosition()
        myPosition.x = -x / 1000
        myPosition.y = y / 1000
        self.myOtos.setPosition(myPosition)
        
    def update(self):
        myPosition = self.myOtos.getPosition()
        
        # sp=self.myOtos.getVelocity()  #buggy, do not use
        if (self.lastXpos == 5000):
            self.speed = 0
        else:
            self.speed =  math.sqrt(math.pow(myPosition.x-self.lastXpos,2) + math.pow(myPosition.y-self.lastYpos,2))*100

        self.lastXpos = myPosition.x
        self.lastYpos = myPosition.y

        
        # if self.loopCounterGyro > 199:
        #     #print("update........................................................................................................................................................................................................................................................................")
        #     myPosition.h = -self.sensor.euler[0] + self.angleStart
        #     self.myOtos.setPosition(myPosition)
        #     self.loopCounterGyro = 0
        # else:
        #     self.loopCounterGyro += 1
        
        if self.loopCounter >= 9:
            self.lidar.getScan(self.scan)
            self.loopCounter = 0
        else:
            self.loopCounter += 1
        
        self.xpos = -myPosition.x * 1000
        self.ypos = myPosition.y * 1000
        self.angle = myPosition.h + self.angleStart

        # print("Euler angle: {}".format(sensor.euler[0]))
    def hindernisseErkennung(self, scan, toScan, camera):

        
        camera.captureImage()
        
        xposes = []
        yposes = []
        for i in range(len(scan)):
            rad = (i + self.angle) / 180 * math.pi
            xposes.append(math.cos(rad) * -scan[i] + self.xpos)
            yposes.append(math.sin(rad) * scan[i] + self.ypos)

        for i in range(len(self.hindernisse)):
            if i in toScan:
                self.hindernisse[i].farbe = Hindernisse.NICHTS
                dots = 0
                angles = []
                for b in range(len(xposes)):
                    if (math.pow((xposes[b] - self.hindernisse[i].x),2) + math.pow((yposes[b] - self.hindernisse[i].y),2) < math.pow(100,2)) and (self.scan[b] > 200):
                        dots += 1
                        angles.append(b)
                if dots > 1:
                    angle = 0
                    for c in angles:
                        angle += c
                    angle = angle / len(angles)
                    if angle > 180:
                        angle = angle - 360
                    angle = -angle
                    print(angle)
                    closetAngle = 0
                    for d in range(len(camera.blocksAngle)):
                        if abs(camera.blocksAngle[d] - angle) < abs(camera.blocksAngle[closetAngle] - angle):
                            closetAngle = d
                    
                    print(closetAngle)
                    if len(camera.blocksAngle) > 0:
                        if camera.blocksColor[closetAngle] == camera.RED:
                            self.hindernisse[i].farbe = Hindernisse.RED
                        if camera.blocksColor[closetAngle] == camera.GREEN:
                            self.hindernisse[i].farbe = Hindernisse.GREEN
                    else:
                        self.hindernisse[i].farbe = Hindernisse.RED

    def reposition(self):
        average = 0
        scans = 0
        angle = int(self.angle+0.5)
        angle = 180-angle
        for i in range (angle-5,angle+6):
            if self.scan[i] > 0:
                average = average + self.scan[i]
                scans += 1
        if scans > 0:
            average = average / scans
        
        print(math.floor(self.ypos), math.floor(3000 - average), self.angle)
        
        if self.angle > -140 and self.angle > 140:                              # rechts/180
            self.setPostion(average, self.xpos)
        if self.angle > 130 and self.angle < 50:                                # unten/90
            self.setPostion(average, self.ypos)
        if self.angle > -40 and self.angle < 40:                                # links/0
            self.setPostion(3000 - average, self.xpos)
        if self.angle > -130 and self.angle < -50:                              # oben/-90
            self.setPostion(3000 - average, self.ypos)
        
        average = 0
        scans = 0
        
        if self.direction == self.CW:
            average = 0
            scans = 0
            for i in range (angle-5-90,angle+6-90):
                if self.scan[i] > 0:
                    average = average + self.scan[i]
                    scans += 1
            if scans > 0:
                average = average / scans
        
        if self.direction == self.CCW:
            average = 0
            scans = 0
            for i in range (angle-5+90,angle+6+90):
                if self.scan[i] > 0:
                    average = average + self.scan[i]
                    scans += 1
            if scans > 0:
                average = average / scans
        
#      print(average)

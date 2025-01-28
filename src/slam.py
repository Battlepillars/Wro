import pygame # type: ignore
import tkinter.filedialog
import qwiic_otos # type: ignore
import sys
import time
import os
import motorController
import board # type: ignore
import adafruit_bno055 # type: ignore

from future.moves import pickle # type: ignore
from drawBoard import *
from ctypes import *
from adafruit_servokit import ServoKit # type: ignore


class Slam:
    loopCounter = 10
    loopCounterGyro = 0
    angle = 0
    xpos = 0
    ypos = 0
    
    def __init__(self):
        self.xstart = 0#2800
        self.ystart = 0#2800
        self.xpos = 0
        self.ypos = 0
        self.angleStart = 0
        self.speed = 0
        i2c = board.I2C()  # uses board.SCL and board.SDA
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
        self.myOtos.setLinearScalar(1.079959499506092)
        # self.myOtos.setLinearScalar(0.9)
        self.myOtos.setAngularScalar(0.996375801505436)
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
            self.ystart = 3000 - self.scan[90]
            self.xstart = average    
        if (average > 1345) and (average < 1450):
            self.angleStart = 180
            self.ystart = 3000 - self.scan[-90]
            self.xstart = self.scan[180]
        if (average > 1550) and (average < 1660):
            self.angleStart = 180
            self.ystart = 3000 - self.scan[-90]
            self.xstart = self.scan[180]
        if (average > 1040) and (average < 1200):
            self.angleStart = 0
            self.ystart = 3000 - self.scan[90]
            self.xstart = average
        

        if (self.scan[180] > 70) and (self.scan[180] < 170) and (self.scan[90] < 400):
            self.angleStart = 0
            self.ystart = 3000 - self.scan[90]
            self.xstart = 2000 - self.scan[180]
        elif (self.scan[180] > 70) and (self.scan[180] < 170) and (self.scan[-90] < 400):
            self.angleStart = 180
            self.ystart = 3000 - self.scan[-90]
            self.xstart = 2000 - self.scan[0]

        # 1870 - 1970
        # 1345 - 1450
        # 1550 - 1660
        # 1040 - 1200

    def update(self):
        sp=self.myOtos.getVelocity()
        self.speed =  math.sqrt(math.pow(sp.x,2) + math.pow(sp.y,2))
        myPosition = self.myOtos.getPosition()
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
        
        self.ypos = -myPosition.x * 1000 + self.ystart
        self.xpos = -myPosition.y * 1000 + self.xstart
        self.angle = myPosition.h + self.angleStart        

        # print("Euler angle: {}".format(sensor.euler[0]))
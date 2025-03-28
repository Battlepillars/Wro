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
            self.direction = self.CW
            self.setPostion(average, 3000 - self.scan[90],0) 
        if (average > 1345) and (average < 1450):
            self.direction = self.CCW
            self.setPostion(self.scan[180], 3000 - self.scan[-90],180)
        if (average > 1550) and (average < 1660):
            self.direction = self.CCW
            self.setPostion(self.scan[180], 3000 - self.scan[-90],180)
        if (average > 1040) and (average < 1200):
            
            self.direction = self.CW
            self.setPostion(average, 3000 - self.scan[90],0)
        

        if (self.scan[180] > 70) and (self.scan[180] < 170) and (self.scan[90] < 400):
            self.direction = self.CW
            self.setPostion(2000 - self.scan[180], 3000 - self.scan[90],0)
        elif (self.scan[180] > 70) and (self.scan[180] < 170) and (self.scan[-90] < 400):
            self.direction = self.CCW
            self.setPostion(2000 - self.scan[0], 3000 - self.scan[90],180)

        # 1870 - 1970
        # 1345 - 1450
        # 1550 - 1660
        # 1040 - 1200
    def setPostion(self, x, y,angle=-5000):
        myPosition = self.myOtos.getPosition()
        myPosition.x = -x / 1000
        myPosition.y = y / 1000
        if (angle > -5000):
            myPosition.h=angle
        self.myOtos.setPosition(myPosition)
        self.xpos = x
        self.ypos = y
        self.lastXpos = x
        self.lastYpos = y
        
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
        self.angle = myPosition.h 

        # print("Euler angle: {}".format(sensor.euler[0]))
    def hindernisseErkennung(self, scan, toScan, camera):
        camera.captureImage()
        for d in range(len(camera.blocksAngle)):
            print("Block Angle: ", camera.blocksAngle[d], "Color: ", camera.blocksColor[d],"\n")
        xposes = []
        yposes = []
        for i in range(len(scan)):
            rad = (i + self.angle) / 180 * math.pi
            xposes.append(math.cos(rad) * -scan[i] + self.xpos) # Koordinaten aus dem Lidar Winkelscan berechnen
            yposes.append(math.sin(rad) * scan[i] + self.ypos)

        for i in range(len(self.hindernisse)):                  # Hindernisse sind die vordefinierten möglichen Positionen
            if i in toScan:                                     # To scan : welche Hindernisse aktuell überprüft werden sollen
                self.hindernisse[i].farbe = Hindernisse.NICHTS
                dots = 0
                angles = []
                for b in range(len(xposes)):                    # Checken ob Hindernis in der Nähe der lidarpunkte ist
                    if (math.pow((xposes[b] - self.hindernisse[i].x),2) + math.pow((yposes[b] - self.hindernisse[i].y),2) < math.pow(100,2)) and (self.scan[b] > 200):
                        dots += 1
                        angles.append(b)
                if dots > 1:
                    angle = 0
                    for c in angles:
                        print("Angle: ",c)
                        while c > 180:
                            c -= 360
                        angle += c
                    angle = angle / len(angles)
                    angle = -angle
                    print("Hinderniss: ",i," erkannt, winkel: ",angle)
                    closestAngle = 0
                    for d in range(len(camera.blocksAngle)):
                        if abs(camera.blocksAngle[d] - angle) < abs(camera.blocksAngle[closestAngle] - angle):
                            closestAngle = d
                    
                    print(closestAngle)
                    if len(camera.blocksAngle) > 0:
                        if camera.blocksColor[closestAngle] == camera.RED:
                            self.hindernisse[i].farbe = Hindernisse.RED
                        if camera.blocksColor[closestAngle] == camera.GREEN:
                            self.hindernisse[i].farbe = Hindernisse.GREEN
                    else:
                        self.hindernisse[i].farbe = Hindernisse.RED

    def calcualteScanAngel(self, angleToScan):
        average = 0
        scans = 0
        scanAngle = int(angleToScan - self.angle + 0.5)
        while scans <= 0:
            for i in range (scanAngle-5,scanAngle+6):
                if self.scan[i] > 0:
                    average = average + self.scan[i]
                    scans += 1
        average = average / scans
        print("scanAngle:", scanAngle, "average:", average, "average3:", 3000 - average)
        return average


    def reposition(self):
        #print("X:", self.xpos, "Y:", self.ypos, "Angle:", self.angle, "average:", average, "average3:", 3000 - average)
        
        angleCheck = self.angle
        while angleCheck > 180:
            angleCheck -= 360
        while angleCheck < -180:
            angleCheck += 360
        print("angleCheck:", angleCheck)
        
        if angleCheck < -140 or angleCheck > 140:                              # rechts/180
            print("5")
            average = self.calcualteScanAngel(0)
            self.setPostion(average, self.ypos)
        if angleCheck < 130 and angleCheck > 50:                                # unten/90
            print("6")
            average = self.calcualteScanAngel(-90)
            self.setPostion(self.xpos, average)
        if angleCheck > -40 and angleCheck < 40:                                # links/0
            print("7")
            average = self.calcualteScanAngel(180)
            self.setPostion(3000 - average, self.ypos)
        if angleCheck > -130 and angleCheck < -50:                              # oben/-90
            print("8")
            average = self.calcualteScanAngel(90)
            self.setPostion(self.xpos, 3000 - average)

        average = 0
        scans = 0
        
        if self.direction == self.CW:
            if angleCheck < -140 or angleCheck > 140:                              # rechts/180
                print("9")
                average = self.calcualteScanAngel(-90)
                self.setPostion(self.xpos, average)
            if angleCheck < 130 and angleCheck > 50:                                # unten/90
                print("10")
                average = self.calcualteScanAngel(180)
                self.setPostion(3000 - average, self.ypos)
            if angleCheck > -40 and angleCheck < 40:                                # links/0
                print("11")
                average = self.calcualteScanAngel(90)
                self.setPostion(self.xpos, 3000 - average)
            if angleCheck > -130 and angleCheck < -50:                              # oben/-90
                print("12")
                average = self.calcualteScanAngel(0)
                self.setPostion(average, self.ypos)

        if self.direction == self.CCW:
            if angleCheck < -140 or angleCheck > 140:                              # rechts/180
                print("1")
                average = self.calcualteScanAngel(90)
                self.setPostion(self.xpos, 3000 - average)
            if angleCheck < 130 and angleCheck > 50:                                # unten/90
                print("2")
                average = self.calcualteScanAngel(0)
                self.setPostion(average, self.ypos)
            if angleCheck > -40 and angleCheck < 40:                                # links/0
                print("3")
                average = self.calcualteScanAngel(-90)
                self.setPostion(self.xpos, average)
            if angleCheck > -130 and angleCheck < -50:                              # oben/-90
                print("4")
                average = self.calcualteScanAngel(180)
                self.setPostion(3000 - average, self.ypos)
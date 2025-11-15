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
import logging
import math
import numpy as np

from future.moves import pickle # type: ignore
from drawBoard import *
from ctypes import *
from adafruit_servokit import ServoKit # type: ignore


def calculateAngularWidth(diameter_mm, distance_mm):
    """
    Calculate the apparent angular width of an object in degrees.
    
    An object with diameter diameter_mm at distance distance_mm
    appears at a certain angle to the observer.
    
    Args:
        diameter_mm: Diameter of the object in millimeters (e.g. 120mm)
        distance_mm: Distance to the observer in millimeters
    
    Returns:
        Angle in degrees at which the object appears
        
    Formula: angular_width = 2 * arctan(diameter / (2 * distance))
    """
    if distance_mm <= 0:
        raise ValueError("Distance must be greater than 0")
    
    # Calculate the half angle (in radians)
    half_angle_rad = math.atan(diameter_mm / (2 * distance_mm))
    
    # Double for the full angle and convert to degrees
    angular_width_deg = 2 * math.degrees(half_angle_rad)
    
    return angular_width_deg

def meanAngle(angle1, angle2):
    """
    Calculate the mean of two angles    

    Args:
        angle1 (float): First angle in degrees
        angle2 (float): Second angle in degrees
        
    Returns:
        float: Mean angle in degrees, normalized to [-180, 180]
    """
    # Convert angles to radians
    rad1 = math.radians(angle1)
    rad2 = math.radians(angle2)
    
    # Convert to unit vectors
    x1, y1 = math.cos(rad1), math.sin(rad1)
    x2, y2 = math.cos(rad2), math.sin(rad2)
    
    # Calculate mean vector
    mean_x = (x1 + x2) / 2
    mean_y = (y1 + y2) / 2
    
    # Convert back to angle
    mean_angle = math.degrees(math.atan2(mean_y, mean_x))
    
    # Normalize to [-180, 180]
    while mean_angle > 180:
        mean_angle -= 360
    while mean_angle < -180:
        mean_angle += 360
        
    return mean_angle



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
    resetAngleStart=170
    resetAngleEnd=190
    slope=1
    intercept=500
    c1=0
    playmat = Playmat
    loopCounter = 10
    loopCounterGyro = 0
    infoCounter = 0
    wheelAngle = 0
    angle = 0
    xpos = 0
    ypos = 0
    lastXpos1 = 5000
    lastYpos1 = 5000
    lastXpos2 = 5000
    lastYpos2 = 5000
    xToRepos=0
    yToRepos=0
    direction = 0
    eventType = 0
    CW = 0
    CCW = 1
    ER = 0
    HR = 1
    crash = 0
    errorDriveList = []
    lastRepostion = 0
    lastQuadrant = 0
    ignoreSpeedUpdate = 0
    repostionEnable = 0
    noCurveReposition = 0
    healthy1 = 1
    healthy2 = 1
    errorsOtos1 = 0
    errorsOtos2 = 0
    errorsOtosSpeed1 = 0
    errorsOtosSpeed2 = 0

    file_path = "/home/pi/Wro/src/log.log"

    open(file_path, 'w').close()
        
    logger = logging.getLogger("")
    logging.basicConfig(filename='./log.log', encoding='utf-8', level=logging.WARN)
    logger.warn(' Slam init  *************************************************************')
    def __init__(self):
        
        
        self.hindernisse = []
        self.hindernisse.append(Hindernisse(x=2000, y=2400))
        self.hindernisse.append(Hindernisse(x=2000, y=2600))
        self.hindernisse.append(Hindernisse(x=1500, y=2400))
        self.hindernisse.append(Hindernisse(x=1500, y=2600))
        self.hindernisse.append(Hindernisse(x=1000, y=2400))
        self.hindernisse.append(Hindernisse(x=1000, y=2600))
        
        self.hindernisse.append(Hindernisse(x=600, y=2000))
        self.hindernisse.append(Hindernisse(x=400, y=2000))
        self.hindernisse.append(Hindernisse(x=600, y=1500))
        self.hindernisse.append(Hindernisse(x=400, y=1500))
        self.hindernisse.append(Hindernisse(x=600, y=1000))
        self.hindernisse.append(Hindernisse(x=400, y=1000))
        
        self.hindernisse.append(Hindernisse(x=1000, y=600))
        self.hindernisse.append(Hindernisse(x=1000, y=400))
        self.hindernisse.append(Hindernisse(x=1500, y=600))
        self.hindernisse.append(Hindernisse(x=1500, y=400))
        self.hindernisse.append(Hindernisse(x=2000, y=600))
        self.hindernisse.append(Hindernisse(x=2000, y=400))
        
        self.hindernisse.append(Hindernisse(x=2400, y=1000))
        self.hindernisse.append(Hindernisse(x=2600, y=1000))
        self.hindernisse.append(Hindernisse(x=2400, y=1500))
        self.hindernisse.append(Hindernisse(x=2600, y=1500))
        self.hindernisse.append(Hindernisse(x=2400, y=2000))
        self.hindernisse.append(Hindernisse(x=2600, y=2000))

        self.xpos = 0
        self.ypos = 0
        self.speed = 0
        self.speed1 = 0
        self.speed2 = 0
        i2c = board.I2C()
        #self.sensor = adafruit_bno055.BNO055_I2C(i2c)

        script_dir = os.path.abspath(os.path.dirname(__file__))
        lib_path = os.path.join(script_dir, "sg.so")
        
        
        self.lidar = CDLL(lib_path)
        self.lidar.initLidar()
        
        arr = [1]
        self.scan = (c_int * 361)(*arr)
        


        # Create instance of device
        #self.myOtos = qwiic_otos.QwiicOTOS()
        self.myOtos1 = qwiic_otos.QwiicOTOS(0x17)
        self.myOtos2 = qwiic_otos.QwiicOTOS(0x19)

        # Check if it's connected
        if self.myOtos1.is_connected() == False:
            print("The device 1 isn't connected to the system. Please check your connection", \
                file=sys.stderr)
            return
        if self.myOtos2.is_connected() == False:
            print("The device 2 isn't connected to the system. Please check your connection", \
                file=sys.stderr)
            return

        # Initialize the device
        self.myOtos1.begin()
        self.myOtos2.begin()
        
        self.myOtos1.setLinearUnit(self.myOtos1.kLinearUnitMeters)
        self.myOtos1.setAngularUnit(self.myOtos1.kAngularUnitDegrees)
        self.myOtos2.setLinearUnit(self.myOtos2.kLinearUnitMeters)
        self.myOtos2.setAngularUnit(self.myOtos2.kAngularUnitDegrees)
        self.myOtos1.setSignalProcessConfig(0b1101)
        self.myOtos2.setSignalProcessConfig(0b1101)
        print("Calibrating IMU...")

        # Calibrate the IMU, which removes the accelerometer and gyroscope offsets
        self.myOtos1.calibrateImu(255)
        self.myOtos2.calibrateImu(255)

        # German Playfield / MyDisplay
        # self.myOtos1.setLinearScalar(1.060)
        # self.myOtos2.setLinearScalar(1.040)
            
            
        # Singapur playfield
        self.myOtos1.setLinearScalar(0.980)
        self.myOtos2.setLinearScalar(0.970)        
        
        
        # self.myOtos1.setAngularScalar(0.9933)
        self.myOtos1.setAngularScalar(0.9920)
        # self.myOtos2.setAngularScalar(0.9915)
        self.myOtos2.setAngularScalar(0.9890)

        # Set offset for myOtos1
        offset = self.myOtos1.getOffset()
        print("Offset: ",offset)
        offset.x = -0.011  
#        offset.y = -0.060 
        offset.y = +0.005  
        offset.h = 0      # no heading offset
        self.myOtos1.setOffset(offset)

        # Set offset for myOtos2
        offset.x = -0.045  # 20mm in meters
        offset.h = 0      # no heading offset
        self.myOtos1.setOffset(offset)

        self.myOtos1.resetTracking()
        self.myOtos2.resetTracking()
        

    def startpostionsetzen(self):
        average = 0
        scans = 0
        for i in range (-5,6):
            if self.scan[i] > 0:
                average = average + self.scan[i]
                scans += 1
        average = average / scans
        
        self.logger.warning("Set start position. Average: %.2f", average)

        winkelkorrektur = 0

        if (average > 1870) and (average < 1970):
            self.direction = self.CW
            self.eventType = self.ER
            self.setPostion(average, 3000 - self.scan[90],0+winkelkorrektur)
            self.logger.warning("Startposition: 1")
        if (average > 1345) and (average < 1450):
            self.direction = self.CCW
            self.eventType = self.ER
            self.setPostion(self.scan[180], 3000 - self.scan[-90],180+winkelkorrektur)
            self.logger.warning("Startposition: 2")
        if (average > 1550) and (average < 1660):
            self.direction = self.CCW
            self.eventType = self.ER
            self.setPostion(self.scan[180], 3000 - self.scan[-90],180+winkelkorrektur)
            self.logger.warning("Startposition: 3")
        if (average > 1040) and (average < 1200):
            self.direction = self.CW
            self.eventType = self.ER
            self.setPostion(average, 3000 - self.scan[90],0+winkelkorrektur)
            self.logger.warning("Startposition: 4")
        

        if (self.scan[180] > 70) and (self.scan[180] < 170) and (self.scan[90] < 400):
            self.direction = self.CW
            self.eventType = self.HR
            self.setPostion(2000 - self.scan[180], 3000 - self.scan[90],0+winkelkorrektur)
            self.logger.warning("Startposition: 5")
            self.logger.warning("180: %.0f 90: %.0f",self.scan[180],self.scan[90])
        elif (self.scan[180] > 70) and (self.scan[180] < 170) and (self.scan[-90] < 400):
            
            self.direction = self.CCW
            self.eventType = self.HR
            self.setPostion(2000 - self.scan[0], 3000 - self.scan[-90],180+winkelkorrektur)
            self.logger.warning("Startposition: 6")
            self.logger.warning("0: %.0f -90: %.0f",self.scan[0],self.scan[-90])

        # 1870 - 1970
        # 1345 - 1450
        # 1550 - 1660
        # 1040 - 1200
    def setPostion(self, x, y,angle=-5000):
        myPosition = self.myOtos1.getPosition()
        myPosition.y = -x / 1000
        myPosition.x = -y / 1000
        if (angle > -5000):
            myPosition.h=angle
        self.myOtos1.setPosition(myPosition)


        myPosition = self.myOtos2.getPosition()
        myPosition.y = -x / 1000
        myPosition.x = -y / 1000
        if (angle > -5000):
            myPosition.h=angle
        self.myOtos2.setPosition(myPosition)

        self.xpos = x
        self.ypos = y
        self.lastXpos = x
        self.lastYpos = y
        self.ignoreSpeedUpdate = 1
        
    def otusHealthReset(self):
        self.healthy1 = 1
        self.healthy2 = 0
        self.errorsOtos1 = 0
        self.errorsOtos2 = 0
        self.errorsOtosSpeed1 = 0
        self.errorsOtosSpeed2 = 0
        self.logger.warning('Reset health of Otos')
        
    def update(self):
        
        myPosition1 = self.myOtos1.getPosition()
        
        if (self.lastXpos1 == 5000):
            self.speed1 = 0
        else:
            if self.ignoreSpeedUpdate != 1:
                self.speed1 =  math.sqrt(math.pow(myPosition1.x-self.lastXpos1,2) + math.pow(myPosition1.y-self.lastYpos1,2))*100

        self.lastXpos1 = myPosition1.x
        self.lastYpos1 = myPosition1.y


        myPosition2 = self.myOtos2.getPosition()
        
        if (self.lastXpos2 == 5000):
            self.speed2 = 0
        else:
            if self.ignoreSpeedUpdate == 1:
                self.ignoreSpeedUpdate = 0
            else:
                self.speed2 =  math.sqrt(math.pow(myPosition2.x-self.lastXpos2,2) + math.pow(myPosition2.y-self.lastYpos2,2))*100

        self.lastXpos2 = myPosition2.x
        self.lastYpos2 = myPosition2.y
        

        myPosition1.x= -myPosition1.x * 1000
        myPosition1.y= -myPosition1.y * 1000
        myPosition2.x= -myPosition2.x * 1000
        myPosition2.y= -myPosition2.y * 1000
        
        if self.healthy1 == 1 and self.healthy2 == 1:
            if self.speed1+0.15 < self.speed2:
                self.errorsOtos1 += 1
            else:
                if self.errorsOtos1 > 0:
                    self.errorsOtos1 -= 1
                    
            if self.speed2+0.15 < self.speed1:
                self.errorsOtos2 += 1
            else:
                if self.errorsOtos2 > 0:
                    self.errorsOtos2 -= 1
            if (myPosition1.x < -100) or (myPosition1.x > 3100) or (myPosition1.y < -100) or (myPosition1.y > 3100):
                self.healthy1=-2
                self.logger.warning('Otos1 out of bounds: %i, %i', myPosition1.x, myPosition1.y)
            
            
            if self.speed1 > 2:
                self.errorsOtosSpeed1 += 1
            else:
                if self.errorsOtosSpeed1 > 0:
                    self.errorsOtosSpeed1 -= 1
            
            if self.speed2 > 2:
                self.errorsOtosSpeed2 += 1
            else:
                if self.errorsOtosSpeed2 > 0:
                    self.errorsOtosSpeed2 -= 1

            if (myPosition2.x < -100) or (myPosition2.x > 3100) or (myPosition2.y < -100) or (myPosition2.y > 3100):
                self.healthy2=-2
                self.logger.warning('Otos2 out of bounds: %i, %i', myPosition2.x, myPosition2.y)


        if self.errorsOtos1 > 20 and self.healthy1>0 :
            self.healthy1 = 0
            self.logger.warning('Otos1 not healthy, errors: %i',self.errorsOtos1)
        if self.errorsOtos2 > 20 and self.healthy2>0 :
            self.healthy2 = 0
            self.logger.warning('Otos2 not healthy, errors: %i',self.errorsOtos2)
        if self.errorsOtosSpeed1 > 5 and self.healthy1>0:
            self.healthy1 = -1
            self.logger.warning('Otos1 speed not healthy, errors: %i',self.errorsOtosSpeed1)
        if self.errorsOtosSpeed2 > 5 and self.healthy2>0:
            self.healthy2 = -1
            self.logger.warning('Otos2 speed not healthy, errors: %i',self.errorsOtosSpeed2)

        if self.healthy1 == 1 and self.healthy2 == 1:
            self.xpos = (myPosition1.y + myPosition2.y) / 2
            self.ypos = (myPosition1.x + myPosition2.x) / 2
            
            self.angle = meanAngle(myPosition1.h, myPosition2.h)
            self.speed = (self.speed1 + self.speed2) / 2
            self.infoCounter += 1
            if self.infoCounter >= 30:
                self.logger.warning('A1: %.2f  A2: %.2f Mean angle: %.2f',myPosition1.h,myPosition2.h,self.angle)
                self.logger.warning("speedav: %.2f Speed1: %.2f Speed2: %.2f",self.speed,self.speed1,self.speed2)
                self.logger.warning("X: %.0f Y: %.0f pos1: %.0f/%.0f pos2: %.0f/%.0f",self.xpos,self.ypos,myPosition1.x,myPosition1.y,myPosition2.x,myPosition2.y)
                self.infoCounter = 0
        elif self.healthy1 == 1:
            self.xpos = myPosition1.y
            self.ypos = myPosition1.x
            self.angle = myPosition1.h
            self.speed = self.speed1
        else:
            self.xpos = myPosition2.y
            self.ypos = myPosition2.x
            self.angle = myPosition2.h
            self.speed = self.speed2

        # print(f"{myPosition1.h:.2f}, {myPosition2.h:.2f}")

        if self.loopCounter >= 9:
            self.lidar.getScan(self.scan)
            self.loopCounter = 0
        else:
            self.loopCounter += 1
            
        if self.repostionEnable == 1:
            self.repositionDrive()

        # print("Euler angle: {}".format(sensor.euler[0]))

            
    def hindernisseErkennung(self, scan, toScan, camera, checkHeightNear):
        """
        Detect obstacles using LiDAR and determine their colors using the camera.
        
        This function combines LiDAR distance measurements with camera color detection
        to identify and classify obstacles at predefined positions on the competition field.
        
        Args:
            scan: Array of LiDAR distance measurements (360 degrees)
            toScan: List of obstacle indices to check (limits scanning to relevant positions)
            camera: Camera object for capturing images and detecting colored obstacles
            checkHeightNear: Boolean flag for near-distance obstacle detection mode
            
        Returns:
            found: Total number of LiDAR points detected near obstacles
        """
        found = 0
        
        # Set detection threshold based on distance
        # Near obstacles require fewer LiDAR points for reliable detection
        if checkHeightNear:
            dotsNeeded = 1  # Lower threshold for near obstacles
        else:
            dotsNeeded = 0  # Standard threshold for distant obstacles
        
        # Capture camera image for color detection
        camera.captureImage(checkHeightNear)
        xposes = []
        yposes = []
        for i in range(len(scan)):
            # Convert degree angle to radians and account for robot's current heading
            rad = (i + self.angle) / 180 * math.pi
            # Calculate world coordinates from LiDAR angle scan
            xposes.append(math.cos(rad) * -scan[i] + self.xpos) 
            yposes.append(math.sin(rad) * scan[i] + self.ypos)  

        # Step 2: Check each predefined obstacle position against LiDAR data
        # hindernisse = the predefined possible obstacle positions
        for i in range(len(self.hindernisse)):
            # toScan = which obstacles should currently be checked (performance optimization)
            if i in toScan:
                # Reset obstacle status to "nothing detected"
                self.hindernisse[i].farbe = Hindernisse.NICHTS
                dots = 0        # Counter for LiDAR points near this obstacle position
                angles = []     # List to store angles of detected points
                
                # Calculate distance from robot to obstacle position
                distance = math.sqrt(math.pow((self.xpos - self.hindernisse[i].x), 2) +  math.pow((self.ypos - self.hindernisse[i].y), 2))
                angularWidth = calculateAngularWidth(100, distance)
                logging.warning("Obstacle %i at distance %.2f mm has angular width %.2f degrees", i, distance, angularWidth)

                # Step 3: Check if obstacle is near any LiDAR points
                for b in range(len(xposes)):
                    # Calculate if LiDAR point is within 120mm radius of expected obstacle position
                    # and has valid distance reading (> 200mm filters out noise)
                    
                    if (math.pow((xposes[b] - self.hindernisse[i].x), 2) + 
                        math.pow((yposes[b] - self.hindernisse[i].y), 2) < math.pow(120, 2)) and (self.scan[b] > 200):
                        dots += 1           # Count detected point
                        angles.append(b)    # Store angle index for camera matching
                        logging.warning("LiDAR point at (%.0f, %.0f) detected for obstacle %i", xposes[b], yposes[b], i)
                
                logging.warning("Obstacle %i dots found:",dots)
                
                # Step 4: If sufficient LiDAR points detected, process obstacle
                if dots > dotsNeeded:
                    found += dots  # Add to total detection count
                    
                    # Calculate relative angle from current position to obstacle
                    # Current position: (self.xpos, self.ypos)
                    # Target position: (self.hindernisse[i].x, self.hindernisse[i].y)
                    # Current heading: self.angle
                    
                    # Calculate vector from current position to obstacle
                    dx = self.hindernisse[i].x - self.xpos
                    dy = self.hindernisse[i].y - self.ypos
                    
                    # Calculate absolute angle to target (in degrees)
                    angle_to_target = -math.degrees(math.atan2(dy, dx))-180
                    
                    # Calculate relative angle (difference between target angle and current heading)
                    angle = -(angle_to_target - self.angle)
                    
                    # Normalize angle to [-180, 180] range
                    while angle > 180:
                        angle -= 360
                    while angle < -180:
                        angle += 360

                    logging.warning("Obstacle %i: pos=(%.0f,%.0f) target=(%.0f,%.0f) heading=%.2f angle_to_target=%.2f relative_angle=%.2f dots: %i",
                                    i, self.xpos, self.ypos, self.hindernisse[i].x, self.hindernisse[i].y,
                                    self.angle, angle_to_target, angle, dots)

                    # Step 5: Match LiDAR detection with camera color detection
                    # Find camera-detected block closest to calculated LiDAR angle
                    closestAngle = 0
                    objectDetected = False
                    for d in range(len(camera.blocksAngle)):    # richtige Farbe auswählen

                        logging.warning("Camera block angle: %.2f vs LiDAR angle: %.2f diff: %.2f", camera.blocksAngle[d], angle, abs(camera.blocksAngle[d] - angle))
                        if (abs(camera.blocksAngle[d] - angle) < angularWidth):
                            logging.warning("-> within angular width of obstacle")
                            objectDetected = True
                            if (abs(camera.blocksAngle[d] - angle) < abs(camera.blocksAngle[closestAngle] - angle)):
                                closestAngle = d
                    # Step 6: Assign color to detected obstacle based on camera detection
                    if len(camera.blocksAngle) > 0 and objectDetected:
                        # Color detected by camera - assign it to obstacle
                        if camera.blocksColor[closestAngle] == camera.RED:
                            self.hindernisse[i].farbe = Hindernisse.RED
                            logging.warning("-> Set obstacle %i color to RED", i)
                        if camera.blocksColor[closestAngle] == camera.GREEN:
                            self.hindernisse[i].farbe = Hindernisse.GREEN
                            logging.warning("-> Set obstacle %i color to GREEN", i)
                    else:
                        # Fallback: if no camera detection, set obstacle color to "nothing"
                        self.hindernisse[i].farbe = Hindernisse.NICHTS
                        logging.warning("-> No camera blocks detected, obstacle %i color set to NOTHING", i)
        
        return found

    def calcualteScanAngel(self, angleToScan):
        average = 0
        scans = 0
        scanAngle = int(angleToScan - self.angle + 0.5)
        while scans <= 0:
            for i in range (scanAngle-5,scanAngle+6):
                # self.logger.warning('Scan angle: %i', i)
                v=i
                if v>360:
                    v = i - 360
                if (v < 0):
                    v = i + 360     
                
                if self.scan[v] > 0:
                    average = average + self.scan[v]
                    scans += 1
        average = average / scans
        self.logger.warning('calcualteScanAngel  angleToScan: %i, self.angle: %i scans: %i  Average: %.2f', angleToScan, self.angle, scans, average)
        # print("scanAngle:", scanAngle, "average:", average, "average3:", 3000 - average)
        return average

    def repositionOneDirFront(self, angleCheck):
        # print("X:", self.xpos, "Y:", self.ypos, "Angle:", self.angle, "average:", average, "average3:", 3000 - average)
        self.logger.warn('-----------------------------------------------------------------------------------------')
        self.logger.warning('Manual Repostion Front angleCheckOverwrite: %i x: %i y: %i angle: %i',angleCheck,self.xpos,self.ypos,self.angle)

        if angleCheck ==0:                              # rechts/180
            
            average = self.calcualteScanAngel(0)
            self.setPostion(average, self.ypos)
            self.logger.warning('v1 x-> %i ',average)
        if angleCheck ==-90:                                # unten/90
            # print("6")
            average = self.calcualteScanAngel(-90)
            self.setPostion(self.xpos, average)
            self.logger.warning('v2 y-> %i ',average)
        if angleCheck == 180 or angleCheck == -180:                                # links/0
            # print("7")
            average = self.calcualteScanAngel(180)
            self.setPostion(3000 - average, self.ypos)
            self.logger.warning('v3 x-> %i ',3000-average)
        if angleCheck ==90:                              # oben/-90
            # print("8")
            average = self.calcualteScanAngel(90)
            self.setPostion(self.xpos, 3000 - average)
            self.logger.warning('v4 y-> %i ',3000-average)


    def repositionOneDirSide(self, angleCheck):
        # print("X:", self.xpos, "Y:", self.ypos, "Angle:", self.angle, "average:", average, "average3:", 3000 - average)
        self.logger.warn('-----------------------------------------------------------------------------------------')
        self.logger.warning('Manual Repostion Side angleCheckOverwrite: %i x: %i y: %i angle: %i',angleCheck,self.xpos,self.ypos,self.angle)


        if angleCheck == 0:                              # rechts/180
            average = self.calcualteScanAngel(0)
            self.setPostion(average, self.ypos)
            self.logger.warning('v1 x-> %i ',average)
        if angleCheck == -90:                                # unten/90
            # print("6")
            average = self.calcualteScanAngel(-90)
            self.setPostion(self.xpos, average)
            self.logger.warning('v2 y-> %i ',average)
        if angleCheck == 180 or angleCheck == -180:                                # links/0
            # print("7")
            average = self.calcualteScanAngel(180)
            self.setPostion(3000 - average, self.ypos)
            self.logger.warning('v3 x-> %i ',3000-average)
        if angleCheck == 90:                              # oben/-90
            # print("8")
            average = self.calcualteScanAngel(90)
            self.setPostion(self.xpos, 3000 - average)
            self.logger.warning('v4 y-> %i ',3000-average)


    def reposition(self, angleCheckOverwrite = 1000):
        # print("X:", self.xpos, "Y:", self.ypos, "Angle:", self.angle, "average:", average, "average3:", 3000 - average)
        self.logger.warn('-----------------------------------------------------------------------------------------')
        self.logger.warning('Manual Repostion angleCheckOverwrite: %i x: %i y: %i angle: %i',angleCheckOverwrite,self.xpos,self.ypos,self.angle)
            
        
        angleCheck = self.angle
        if angleCheckOverwrite <= 500:
            angleCheck = angleCheckOverwrite

        while angleCheck > 180:
            angleCheck -= 360
        while angleCheck < -180:
            angleCheck += 360
        # print("angleCheck:", angleCheck)
        
        if angleCheck < -140 or angleCheck > 140:                              # rechts/180
            
            average = self.calcualteScanAngel(0)
            self.setPostion(average, self.ypos)
            self.logger.warning('v1 x-> %i ',average)
        if angleCheck < 130 and angleCheck > 50:                                # unten/90
            # print("6")
            average = self.calcualteScanAngel(-90)
            self.setPostion(self.xpos, average)
            self.logger.warning('v2 y-> %i ',average)
        if angleCheck > -40 and angleCheck < 40:                                # links/0
            # print("7")
            average = self.calcualteScanAngel(180)
            self.setPostion(3000 - average, self.ypos)
            self.logger.warning('v3 x-> %i ',3000-average)
        if angleCheck > -130 and angleCheck < -50:                              # oben/-90
            # print("8")
            average = self.calcualteScanAngel(90)
            self.setPostion(self.xpos, 3000 - average)
            self.logger.warning('v4 y-> %i ',3000-average)

        average = 0
        scans = 0
        
        if self.direction == self.CW:
            if angleCheck < -140 or angleCheck > 140:                              # rechts/180
                # print("9")
                average = self.calcualteScanAngel(-90)
                self.setPostion(self.xpos, average)
                self.logger.warning('v5 y-> %i ',average)
            if angleCheck < 130 and angleCheck > 50:                                # unten/90
                # print("10")
                average = self.calcualteScanAngel(180)
                self.setPostion(3000 - average, self.ypos)
                self.logger.warning('v6 x-> %i ',3000-average)
            if angleCheck > -40 and angleCheck < 40:                                # links/0
                # print("11")
                average = self.calcualteScanAngel(90)
                self.setPostion(self.xpos, 3000 - average)
                self.logger.warning('v7 y-> %i ',3000-average)
            if angleCheck > -130 and angleCheck < -50:                              # oben/-90
                # print("12")
                average = self.calcualteScanAngel(0)
                self.setPostion(average, self.ypos)
                self.logger.warning('v8 x-> %i ',average)

        if self.direction == self.CCW:
            if angleCheck < -140 or angleCheck > 140:                              # rechts/180
                # print("1")
                average = self.calcualteScanAngel(90)
                self.setPostion(self.xpos, 3000 - average)
                self.logger.warning('v9 y-> %i ',3000-average)
            if angleCheck < 130 and angleCheck > 50:                                # unten/90
                # print("2")
                average = self.calcualteScanAngel(0)
                self.setPostion(average, self.ypos)
                self.logger.warning('v10 x-> %i ',average)
            if angleCheck > -40 and angleCheck < 40:                                # links/0
                # print("3")
                average = self.calcualteScanAngel(-90)
                self.setPostion(self.xpos, average)
                self.logger.warning('v11 y-> %i ',average)
            if angleCheck > -130 and angleCheck < -50:                              # oben/-90
                # print("4")
                average = self.calcualteScanAngel(180)
                self.setPostion(3000 - average, self.ypos)
                self.logger.warning('v12 x-> %i ',3000-average)

    def repositionDrive(self):
        # print("Repostioning")
        currentRepostion = 0
        angleCheck = self.angle

        while angleCheck > 180:
            angleCheck -= 360
        while angleCheck < -180:
            angleCheck += 360
        # print("angleCheck:", angleCheck)
        
        average = -1
        angleRange = 30
        
        dir=0
        
        
        quadrant=0
        
        qudrantRange = 1050
        
        if (self.xpos < qudrantRange and self.ypos < qudrantRange):                 # 1: oben links
            quadrant = 1
        if (self.xpos < qudrantRange and self.ypos > 3000-qudrantRange):            # 2: unten links
            quadrant = 2
        if (self.xpos > 3000-qudrantRange and self.ypos < qudrantRange):            # 3: oben rechts
            quadrant = 3
        if (self.xpos > 3000-qudrantRange and self.ypos > 3000-qudrantRange):       # 4: unten rechts
            quadrant = 4
        
        
        if angleCheck < -180 + angleRange or angleCheck > 180 - angleRange:                               # 1: rechts/180
            dir=int(180 - self.angle) + 0.5
            currentRepostion = 1
        elif angleCheck < 90 + angleRange and angleCheck > 90 - angleRange:                               # 2: unten/90
            dir=int(90 - self.angle + 0.5)
            currentRepostion = 2
        elif angleCheck < angleRange and angleCheck > -angleRange:                                        # 3: links/0
            dir=int(0 - self.angle + 0.5)
            currentRepostion = 3
        elif angleCheck < -90 + angleRange and angleCheck > -90 - angleRange:                             # 4: oben/-90
            dir=int(-90 - self.angle + 0.5)
            currentRepostion = 4
        

        
        average=self.lidar.checkDir(int(dir))
        

        
        if average < 0:
            #print(" ",average, end="", flush=True)
            # print(".", end="")
            return
        
        # self.c1+=1
        # if self.c1 > 3:
        #     self.c1 = 0
        #     self.logger.warn('x %i y%i  sp %.2f dist %.0f quadrant %i  dir: %i currentReposition: %i',self.xpos,self.ypos,self.speed,average,quadrant,dir,currentRepostion)
            
        if quadrant == 1 and not(currentRepostion == 3 or currentRepostion == 4):
            return
        if quadrant == 2 and not(currentRepostion == 2 or currentRepostion == 3):
            return
        if quadrant == 3 and not(currentRepostion == 1 or currentRepostion == 4):
            return
        if quadrant == 4 and not(currentRepostion == 1 or currentRepostion == 2):
            return  
        #print(average,math.floor(self.speed*100)/100)
        
        if (self.noCurveReposition):
            return
        
        average = average - 30
        
        if (average < 750):
            return
        
        if (quadrant == self.lastQuadrant or quadrant==0):
            return
        
        # if currentRepostion == self.lastRepostion:
        #     return
        # if currentRepostion == 1 and self.xpos < 2000:
        #     return
        # if currentRepostion == 2 and self.ypos < 2000:
        #     return
        # if currentRepostion == 3 and self.xpos > 1000:
        #     return
        # if currentRepostion == 4 and self.ypos > 1000:
        #     return
        
        
        # print("Repostioned: " + str(currentRepostion) + " last: " + str(self.lastRepostion) + " average: " + str(average))
        self.logger.warn('-------------------------------------------------------------------------------')
        self.logger.warn('Floating Reposition dir %i   av %.0f dir %.0f  angle %.0f',currentRepostion,average,dir,self.angle)
        print("rp: ",currentRepostion," av ", average," dir ", dir," angle ", self.angle)
        if currentRepostion == 1:
            self.playmat.log("fr x: " + str(math.floor(self.xpos)) + " -> " + str(math.floor(3000 - average)))
            print("x: ", math.floor(self.xpos), " -> ", math.floor(3000 - average))
            self.logger.warn('X %.0f -> %.0f',math.floor(self.xpos), math.floor(3000 - average))
            self.setPostion(3000 - average, self.ypos)
        if currentRepostion == 2:
            self.playmat.log("fr y: " + str(math.floor(self.ypos)) + " -> " + str(math.floor(3000 - average)))
            print("y: ", math.floor(self.ypos), " -> ", math.floor(3000 - average))
            self.logger.warn('Y %.0f -> %.0f',math.floor(self.ypos), math.floor(3000 - average))
            self.setPostion(self.xpos, 3000 - average)
        if currentRepostion == 3:
            self.playmat.log("fr x: " + str(math.floor(self.xpos)) + " -> " + str(math.floor(average)))
            print("x: ", math.floor(self.xpos), " -> ", math.floor(average))
            self.logger.warn('X %.0f -> %.0f', math.floor(self.xpos), math.floor(average))
            self.setPostion(average, self.ypos)
        if currentRepostion == 4:
            self.playmat.log("fr y: " + str(math.floor(self.ypos)) + " -> " + str(math.floor(average)))
            print("y: ", math.floor(self.ypos), " -> ", math.floor(average))
            self.logger.warn('Y %.0f -> %.0f',math.floor(self.ypos), math.floor(average))
            self.setPostion(self.xpos, average)
        self.lastRepostion = currentRepostion
        self.lastQuadrant = quadrant





    def resetAngle(self):
        angleStart=int(self.angle)+140
        angleEnd=int(self.angle)+160
        self.resetAngleStart=angleStart
        self.resetAngleEnd=angleEnd
    
        # Create 2D array for coordinates: [[x0, y0], [x1, y1], ...]
        linex=np.array([])
        liney=np.array([])
        
        for i in range(angleStart,angleEnd):
            if self.scan[i] > 0:
                rad = (i + self.angle) / 180 * math.pi
                x = math.cos(rad) * -self.scan[i] + self.xpos
                y = math.sin(rad) * self.scan[i] + self.ypos
                linex = np.append(linex, x)
                liney = np.append(liney, y)
                logging.warning("Point added to line: %.1f, %.1f", x, y)





        # linex=np.array([1000.2,1000.7,1000.8,1000.5])
        # liney=np.array([2636.9,2625.2,2615.1,2605.7])
        
        # Calculate line using Least Absolute Deviations (LAD) - L1 norm minimization
        from scipy.optimize import minimize
        
        # Objective function: sum of absolute deviations
        def lad_objective(params):
            slope, intercept = params
            predicted_y = slope * linex + intercept
            return np.sum(np.abs(liney - predicted_y))
        
        # Initial guess using simple median-based method
        initial_slope = (np.median(liney[-10:]) - np.median(liney[:10])) / (np.median(linex[-10:]) - np.median(linex[:10]))
        initial_intercept = np.median(liney) - initial_slope * np.median(linex)
        
        # Minimize LAD objective
        result = minimize(lad_objective, [initial_slope, initial_intercept], method='Nelder-Mead')
        slope, intercept = result.x
        
        self.slope = slope
        self.intercept = intercept
        logging.warning("LAD regression result: slope=%.2f, intercept=%.2f", slope, intercept)
        line_angle = math.degrees(math.atan(slope))
        logging.warning("Line angle calculated from LAD regression: %.2f degrees", line_angle)

        while (line_angle<0):
            line_angle=line_angle+180
        while (line_angle>180):
            line_angle=line_angle-180
            
        myAngle = self.angle+90
        while (myAngle<0):
            myAngle=myAngle+180
        while (myAngle>180):
            myAngle=myAngle-180    
            
        angleDiff = line_angle - myAngle
        logging.warning("Robot angle +90 adjusted: current=%.2f, line=%.2f, diff=%.2f", myAngle, line_angle, angleDiff)
        if abs(angleDiff) < 80:
            self.logger.warning("Reset angle from %.2f to %.2f (diff %.2f)", self.angle, self.angle + angleDiff, angleDiff)
            self.setPostion(self.xpos, self.ypos, self.angle + angleDiff/2)
        else:
            self.logger.warning("Angle difference too large (%.2f), not resetting angle", angleDiff)
        # sys.exit()

    def parkWallScan(self):
        # print("X:", self.xpos, "Y:", self.ypos, "Angle:", self.angle, "average:", average, "average3:", 3000 - average)
        self.logger.warn('-----------------------------------------------------------------------------------------')
        self.logger.warning('Park Wall Repostion x: %i y: %i angle: %i',self.xpos,self.ypos,self.angle)
        
        averageL = 1625 - self.calcualteScanAngel(0)
        averageR = 2000 - self.calcualteScanAngel(180)
        average = (averageL + averageR) / 2
        
        self.setPostion(average, self.ypos)
        self.logger.warning('x-> %i ',average)

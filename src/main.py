# noinspection PyUnresolvedReferences
# start mit debugger :
#python3 -Xfrozen_modules=off -m debugpy --listen 10.0.0.25:5678 --wait-for-client main.py
#python -m pip install --upgrade debugpy
import debugpy # type: ignore
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
import gpiozero # type: ignore
import os, shutil
import logging
import math

from slam import *
from motorController import *
from future.moves import pickle # type: ignore
from drawBoard import *
from camera import *
from scan_tours import scan_inner_tour, scan_outer_tour
from unpark import unparkCW
from scan import scan
from ctypes import *
from adafruit_servokit import ServoKit # type: ignore



import board # type: ignore
from rainbowio import colorwheel # type: ignore

import adafruit_is31fl3741 # type: ignore
from adafruit_is31fl3741.adafruit_rgbmatrixqt import Adafruit_RGBMatrixQT # type: ignore

i2c = board.I2C()
lamp = Adafruit_RGBMatrixQT(i2c, allocate=adafruit_is31fl3741.PREFER_BUFFER)
lamp.set_led_scaling(0xFF)
lamp.global_current = 0xFF
lamp.enable = True

lamp.fill(0xff0000)  # fill the matrix with black
lamp.show()

# lamp.fill(0x000000) 
# lamp.pixel(0, 0, 0xff0000)
# lamp.pixel(5, 0, 0xff0000)
# lamp.show()


backupVersion = 3


slam = Slam()
kit = ServoKit(channels=16)
kit.servo[0].set_pulse_width_range(1160, 2440)
kit.servo[3].set_pulse_width_range(1000, 2000)

running2 = True
running3 = True
orders = []
sem = threading.Semaphore()
takePicture=0

def main():

    global startTime
    global vPressed
    global slam
    global orders
    global takePicture
    global sem

    slam.logger.warning('main init')
    

    manual = 0
    pictureNum=0
    running = True
    camera = Camera()
    robot = Robot(1)
    pygame.init()
    startTime = time.time()
    vPressed = 0
    wPressed = 0
    sPressed = 0
    aPressed = 0
    dPressed = 0
    speedManual = 0
    steerManual = 0
    info = 1
    wx = 3100
    wy = 3100
    firstCapture = 1
    placing = 0
    playmat = Playmat(1, wx, wy)
    os.environ['SDL_VIDEO_WINDOW_POS'] = "%d,%d" % (0,0)
    #screen = pygame.display.set_mode((wx * playmat.matScale + 300, wy * playmat.matScale), pygame.RESIZABLE)
    screen = pygame.display.set_mode((1920,1000), pygame.RESIZABLE)
    
    pygame.display.set_caption("WroONator4000")
    clock = pygame.time.Clock()
    global running2
    global running3
    last_val = 0xFFFF
    clThread = threading.Thread(target=controlLoop, args=(robot, camera, playmat), daemon=True)
    cmdlThread = threading.Thread(target=commandLoop, args=(slam, ), daemon=True)
    #cmdlThread.setDaemon(True)
    #clThread.setDaemon(True)
    clThread.start()
    cmdlThread.start()
    
    while running:
        #camera.captureImage()
        # print("Speed : ",slam.speed)
        robot.xpos = slam.xpos
        robot.ypos = slam.ypos
        robot.angle = slam.angle
        if vPressed > 0:
            vPressed -= 1
        
        if placing == 1:
            pos = pygame.mouse.get_pos()
            slam.xpos = pos[0] / playmat.matScale
            slam.ypos = pos[1] / playmat.matScale
        
                    
        if manual == 1:
            print(aPressed, dPressed, wPressed, sPressed)
            if (wPressed == 0) and (sPressed == 0):
                kit.servo[3].angle = 90
                print("Stop")
            if (aPressed == 0) and (dPressed == 0):
                steerManual = 0
                print("Steer 0")
            setServoAngle(kit,90 + steerManual,slam)
            
        #print("Wps: ",wPressed, "Sps: ",sPressed, "Aps: ",aPressed, "Dps: ",dPressed, "Manual: ",manual, "SpeedManual: ",speedManual, "SteerManual: ",steerManual)
        

        for event in pygame.event.get():

            # if event.type == pygame.MOUSEBUTTONUP:
            #     placing = 0
            # if event.type == pygame.MOUSEBUTTONDOWN:
            #     placing = 1            
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_c:
                    running = False
                    running2 = False
                    running3 = False
                    kit.servo[3].angle = 90
                    time.sleep(0.1)
                    setServoAngle(kit,90,slam)
                    kit.servo[3].angle = 90
                    slam.lidar.disconnect()
                    return 1
                if event.key == pygame.K_x:
                    running = False
                    running2 = False
                    running3 = False
                    kit.servo[3].angle = 90
                    time.sleep(0.1)
                    setServoAngle(kit,90,slam)
                    kit.servo[3].angle = 90
                    slam.lidar.disconnect()
                    return 0  # Exit code 1 means "don't restart"
                if event.key == pygame.K_v:
                    vPressed = 5
                if event.key == pygame.K_f:
                    print(math.floor(pygame.mouse.get_pos()[0] / playmat.matScale), math.floor(pygame.mouse.get_pos()[1] / playmat.matScale))
                if event.key == pygame.K_u:
                    slam.reposition()
                if event.key == pygame.K_g:
                    print("orders.append(Order(x="+str(math.floor(pygame.mouse.get_pos()[0] / playmat.matScale)-50)+", y="+str(math.floor(pygame.mouse.get_pos()[1] / playmat.matScale)-50)+",speed=0.5,brake=1,type=Order.DESTINATION))")
                if event.key == pygame.K_k:
                    orders.append(Order(x=pygame.mouse.get_pos()[0] / playmat.matScale, y=pygame.mouse.get_pos()[1] / playmat.matScale, speed=0.5, brake=1, type=Order.DESTINATION))
                if event.key == pygame.K_SPACE:
                    running2 = False
                    running3 = False
                    orders.clear()
                    time.sleep(0.1)
                    setServoAngle(kit,90,slam)
                    kit.servo[3].angle = 90
                if event.key == pygame.K_t:
                    orders.clear()
                    orders.append(Order(toScan=[0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23],type=Order.SCAN))
                if event.key == pygame.K_z:
                    orders.clear()
                    orders.append(Order(toScan=[0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23],checkHeightNear=True,type=Order.SCAN))
                if event.key == pygame.K_e:
                    slam.setPostion(pygame.mouse.get_pos()[0] / playmat.matScale, pygame.mouse.get_pos()[1] / playmat.matScale)
                if event.key == pygame.K_r:
                    slam.setPostion(slam.xpos, slam.ypos, slam.angle+90)
                
                    
                if event.key == pygame.K_m:
                    manual = 1
                    running2 = False
                    orders.clear()
                    orders.append(Order(type=Order.MANUAL))
                
                if event.key == pygame.K_w:
                    kit.servo[3].angle = 99 + 35
                    wPressed = 1
                if event.key == pygame.K_s:
                    kit.servo[3].angle = 80 - 25
                    sPressed = 1
                if event.key == pygame.K_a:
                    steerManual = 90
                    aPressed = 1
                if event.key == pygame.K_d:
                    steerManual = -90
                    dPressed = 1
                    
            if event.type == pygame.KEYUP:
                if event.key == pygame.K_w:
                    wPressed = 0
                if event.key == pygame.K_s:
                    sPressed = 0
                if event.key == pygame.K_a:
                    aPressed = 0
                if event.key == pygame.K_d:
                    dPressed = 0

            
            if event.type == pygame.QUIT:
                running = False
                running2 = False
                running3 = False
                time.sleep(0.1)
                setServoAngle(kit,90)
                kit.servo[3].angle = 90
                slam.lidar.disconnect()
        
        keys = pygame.key.get_pressed()

        sem.acquire()
        playmat.draw(screen, info, camera, robot)
        robot.draw(screen, playmat.matScale, slam.scan, slam)
        if info == 1:
            playmat.Infos(screen, robot, slam, playmat.matScale, startTime, time, lamp)
        if firstCapture == 1 and takePicture:
            folder = "/home/pi/Wro/src/capture"
            for filename in os.listdir(folder):
                file_path = os.path.join(folder, filename)
                try:
                    if os.path.isfile(file_path) or os.path.islink(file_path):
                        os.unlink(file_path)
                    elif os.path.isdir(file_path):
                        shutil.rmtree(file_path)
                except Exception as e:
                    print('Failed to delete %s. Reason: %s' % (file_path, e))
            firstCapture = 0
        if takePicture:
            takePicture = False
            fileName="capture/screen"+str(pictureNum)+".jpg"
            pygame.image.save(screen, fileName)
            pictureNum += 1
            
        sem.release()
        clock.tick(10)
        pygame.display.flip()

def normalizeAngle(angle):
    """
    Normalize an angle to be between -180 and 180 degrees.
    
    Args:
        angle (float): The angle in degrees to normalize
        
    Returns:
        float: The normalized angle between -180 and 180 degrees
    """
    while (angle>180):
        angle -= 360
    while (angle<-180):
        angle += 360
    return angle

class Order:
    DESTINATION=0
    KURVE=1
    SCAN=2
    WINKEL=3
    REPOSITION=4
    TIME=5
    DESTINATIONTIME=6
    MANUAL=7
    REPOSITIONSINGLE=8
    TIMEPOWER=9
    CW=100
    CCW=101
    def __init__(self,speed=0,brake=0,type=0,x=0,y=0,steer=0,dist=0,timeDrive=0,toScan=[],zielwinkel=0,angleCheckOverwrite=1000,num=0,dir=0,rotation=0,checkHeightNear=False):
        if (rotation == 0):
            self.x = x
            self.y = y
        elif (rotation == 90):
            self.x = y
            self.y = -x+3000
            if (angleCheckOverwrite != 1000):
                angleCheckOverwrite += rotation
            zielwinkel += rotation
        elif (rotation == -90):
            self.x = 1500-(y-1500)
            self.y = x
            if (angleCheckOverwrite != 1000):
                angleCheckOverwrite += rotation
            zielwinkel += rotation           
        elif (rotation == 180):
            self.x = 3000-x
            self.y = 3000-y
            if (angleCheckOverwrite != 1000):
                angleCheckOverwrite += rotation
            zielwinkel += rotation
        elif (rotation == 1500):          # SÜd in CCW
            self.x = 1500-(y-1500)
            self.y = x                  #drehen um 90 grad
            self.y=  3000-self.y        #spiegeln an y=1500
            zielwinkel = 180-(zielwinkel+90)
            if (angleCheckOverwrite != 1000):
                angleCheckOverwrite = 180-(angleCheckOverwrite+90)
        elif (rotation == 1180):          # West in CCW
            self.x = 3000-x
            self.y = 3000-y             #drehen um 180 grad
            self.x= 3000-self.x         #spiegeln an x=1500
            zielwinkel = -(zielwinkel)
            if (angleCheckOverwrite != 1000):
                angleCheckOverwrite = -(angleCheckOverwrite)
        elif (rotation == 1090):          # Nord in CCW
            self.x = y
            self.y = -x+3000            #drehen um 90 grad
            self.y=  3000-self.y        #spiegeln an y=1500
            zielwinkel = 180-(zielwinkel-90)
            if (angleCheckOverwrite != 1000):
                angleCheckOverwrite = 180-(angleCheckOverwrite-90)
        else:
            print("Error in Order rotation: " + str(rotation))
            sys.exit("Exiting program due to invalid rotation value in Order.")

        
        rotation = normalizeAngle(rotation)
        # print("zielwinkel normalized : " + str(zielwinkel))
        self.speed = speed
        self.brake = brake
        self.type = type
        self.steer = steer
        self.dist = dist
        self.timeDrive = timeDrive
        self.toScan = toScan
        self.zielwinkel = zielwinkel
        self.angleCheckOverwrite = angleCheckOverwrite
        self.num = num
        self.dir = dir
        self.checkHeightNear = checkHeightNear


def waitCompleteOrders():
    global running2
    while orders.__len__() > 0 and running2:
        time.sleep(0.01)
    return running2
def checkForColor(color, start, end):
    for i in range(start, end):
        #print("color: " + str(slam.hindernisse[i].farbe))
        if slam.hindernisse[i].farbe == color:
            return True
    return False

def commandLoop(slam):
    global orders
    global startTime
    
    button = gpiozero.Button("BOARD37")
    

    c=0
    for i in range(0, 20):
        if not button.is_pressed:       #button is inverted, 1= not pressed, 0= pressed
            c += 1
        time.sleep(0.01)

    lamp.fill(0x00ff00)
    lamp.show()

    if c<15:
        c=0
        while c<20:
            if not button.is_pressed:   #button is inverted, 1= not pressed, 0= pressed
                c += 1
            else:
                c -= 1
            if (c<0):
                c = 0
            time.sleep(0.01)
        time.sleep(1.0)
    else:
        print("Press v to start")
        while vPressed <= 0:
            time.sleep(0.05)
    lamp.fill(0x000000)
    lamp.show()
    slam.myOtos1.resetTracking()
    slam.myOtos2.resetTracking()
    slam.myOtos1.calibrateImu(255)
    slam.myOtos2.calibrateImu(255)
    time.sleep(0.2) 
    slam.otusHealthReset()
    slam.startpostionsetzen()
    time.sleep(0.5)                    
    startTime = time.time()
    
    ausparkenCWMachen = 1
    
    if ausparkenCWMachen == 1:
        unparkCW(orders, Order, waitCompleteOrders, checkForColor)
        scan(orders, Order, waitCompleteOrders, checkForColor)
    
    elif slam.eventType == slam.ER:           
        speedi = 0.75
        slam.repostionEnable = 1
        
        if slam.direction == slam.CW:                #                                                         Eröffnungsrennen  CW
            
            
            orders.append(Order(x=450, y=2500,speed=speedi,brake=0,type=Order.DESTINATION,num=100))
            
            for i in range(0,3):
                if i >= 1:
                    orders.append(Order(x=450, y=2700,speed=speedi,brake=0,type=Order.DESTINATION,num=101))
                orders.append(Order(x=300, y=450,speed=speedi,brake=0,type=Order.DESTINATION,num=102))
                orders.append(Order(x=2550, y=300,speed=speedi,brake=0,type=Order.DESTINATION,num=103))
                orders.append(Order(x=2700, y=2550,speed=speedi,brake=0,type=Order.DESTINATION,num=104))
            
            orders.append(Order(x=1500, y=2700,speed=speedi,brake=1,type=Order.DESTINATION,num=105))
        else:                                                                #                                    Eröffnungsrennen  CCW  
            orders.append(Order(x=2550, y=2500,speed=speedi,brake=0,type=Order.DESTINATION,num=105))
            
            for i in range(0,3):
                if i >= 1:
                    orders.append(Order(x=2550, y=2700,speed=speedi,brake=0,type=Order.DESTINATION,num=106))
                orders.append(Order(x=2700, y=450,speed=speedi,brake=0,type=Order.DESTINATION,num=107))
                orders.append(Order(x=450, y=300,speed=speedi,brake=0,type=Order.DESTINATION,num=108))
                orders.append(Order(x=300, y=2550,speed=speedi,brake=0,type=Order.DESTINATION,num=109))
            
            orders.append(Order(x=1500, y=2700,speed=speedi,brake=1,type=Order.DESTINATION,num=110))
    
    
    
    else:
        if slam.direction == slam.CW:                                                                               #Hindernissrennen CW
            orders.append(Order(steer=-90, dist=70, speed=0.2, brake=1, type=Order.KURVE))                         
            orders.append(Order(steer=0, dist=25, speed=-0.2, brake=1, type=Order.KURVE))
            orders.append(Order(steer=-90, dist=100, speed=0.2, brake=1, type=Order.KURVE))                        
            orders.append(Order(steer=0, dist=150, speed=0.2, brake=1, type=Order.KURVE))

            # orders.append(Order(steer=-90, dist=170, speed=0.2, brake=1, type=Order.KURVE))                         # Ausparken
            # orders.append(Order(steer=0, dist=150, speed=0.2, brake=1, type=Order.KURVE))
            
            
            orders.append(Order(zielwinkel=-5, speed=0.2, brake=1, dir=Order.CCW, type=Order.WINKEL))
            waitCompleteOrders()
            slam.repostionEnable = 1
            time.sleep(0.3)
            orders.append(Order(toScan=[4, 5],type=Order.SCAN))                                                     # Scan starthindernisse
            time.sleep(0.3)
            if not waitCompleteOrders():
                return
            
            
            
            speedScan = 0.5

            if checkForColor(Hindernisse.RED, 0, 6):                                                                # scannen bereich  west
                scan_inner_tour(orders, speedScan,0,6, Order, waitCompleteOrders, checkForColor)
            else:
                orders.append(Order(x=1050, y=2800,speed=speedScan,brake=1,type=Order.DESTINATION,num=112,rotation=0)) 
                scan_outer_tour(orders, speedScan,0,6, Order, waitCompleteOrders, checkForColor)
            
            if checkForColor(Hindernisse.RED, 6, 12):                                                                # scannen bereich  nord            
                scan_inner_tour(orders, speedScan,-90,12, Order, waitCompleteOrders, checkForColor)
            else:
                scan_outer_tour(orders, speedScan,-90,12, Order, waitCompleteOrders, checkForColor)                                                           
                
            if checkForColor(Hindernisse.RED, 12, 18):                                                               # scannen bereich ost
                scan_inner_tour(orders, speedScan,180,18, Order, waitCompleteOrders, checkForColor)
            else:
                scan_outer_tour(orders, speedScan,180,18, Order, waitCompleteOrders, checkForColor)
                




            if checkForColor(Hindernisse.RED, 18, 24):                                                                
                #print("Red")
                #orders.append(Order(x=2185, y=1054,speed=speedScan,brake=1,type=Order.DESTINATION,num=134))
                orders.append(Order(x=2179, y=2064,speed=speedScan,brake=1,type=Order.DESTINATION,num=135))
                orders.append(Order(x=2650, y=2284,speed=speedScan,brake=1,type=Order.DESTINATION,num=136))
            elif checkForColor(Hindernisse.GREEN, 18, 24):
                #print("Green")
                #orders.append(Order(x=2842, y=1054,speed=speedScan,brake=1,type=Order.DESTINATION,num=137))
                orders.append(Order(x=2842, y=2050,speed=speedScan,brake=1,type=Order.DESTINATION,num=138))
                orders.append(Order(x=2650, y=2368,speed=speedScan,brake=1,type=Order.DESTINATION,num=139))
        
            
            
            orders.append(Order(zielwinkel=0, speed=0.2, brake=1, type=Order.WINKEL,dir=Order.CW))                 
            if not waitCompleteOrders():
                return
            time.sleep(0.3)
            orders.append(Order(type=Order.REPOSITION))
            time.sleep(0.5) 
            orders.append(Order(toScan=[0, 1],type=Order.SCAN))
            time.sleep(0.3)
            if not waitCompleteOrders():
                return
            


            # while vPressed <= 0:
            #     time.sleep(0.1)



            speedi = 0.6
            for i in range(0,2):
                if checkForColor(Hindernisse.GREEN, 0, 6):
                    #print("Green")
                    orders.append(Order(x=2100, y=2550,speed=speedi,brake=0,type=Order.DESTINATION,num=145))
                    slam.repostionEnable = 0
                    orders.append(Order(x=1600, y=2600,speed=speedi,brake=0,type=Order.DESTINATION,num=146))
                    orders.append(Order(x=1000, y=2800,speed=speedi,brake=1,type=Order.DESTINATION,num=147))
                    orders.append(Order(zielwinkel=0, speed=0.2, brake=1, type=Order.WINKEL))
                    if not waitCompleteOrders():
                        return
                    time.sleep(0.3)
                    slam.repositionOneDirFront(0)
                    time.sleep(0.5) 
                    slam.lastQuadrant = 2
                    slam.repostionEnable = 1
                else:
                    #print("Red")
                    orders.append(Order(x=2000, y=2200,speed=speedi,brake=0,type=Order.DESTINATION,num=148))
                    orders.append(Order(x=1000, y=2200,speed=speedi,brake=0,type=Order.DESTINATION,num=149))

                if checkForColor(Hindernisse.GREEN, 0, 6) and checkForColor(Hindernisse.RED, 6, 12):
                    #print("Green")
                    orders.append(Order(x=800, y=2600,speed=speedi,brake=0,type=Order.DESTINATION,num=150))
                elif checkForColor(Hindernisse.RED, 0, 6) and checkForColor(Hindernisse.GREEN, 6, 12):
                    #print("Red")
                    orders.append(Order(x=500, y=2400,speed=speedi,brake=0,type=Order.DESTINATION,num=151))

                if checkForColor(Hindernisse.GREEN, 6, 12):
                    #print("Green")
                    orders.append(Order(x=200, y=2100,speed=speedi,brake=0,type=Order.DESTINATION,num=152))
                    orders.append(Order(x=200, y=950,speed=speedi,brake=0,type=Order.DESTINATION,num=153))
                else:
                    #print("Red")
                    orders.append(Order(x=800, y=2000,speed=speedi,brake=0,type=Order.DESTINATION,num=154))
                    orders.append(Order(x=800, y=1000,speed=speedi,brake=0,type=Order.DESTINATION,num=155))


                if checkForColor(Hindernisse.GREEN, 6, 12) and checkForColor(Hindernisse.RED, 12, 18):
                    #print("Green")
                    orders.append(Order(x=400, y=800,speed=speedi,brake=0,type=Order.DESTINATION,num=156))
                elif checkForColor(Hindernisse.RED, 6, 12) and checkForColor(Hindernisse.GREEN, 12, 18):
                    #print("Red")
                    orders.append(Order(x=600, y=500,speed=speedi,brake=1,type=Order.DESTINATION,num=157))

                if checkForColor(Hindernisse.GREEN, 12, 18):
                    #print("Green")
                    orders.append(Order(x=900, y=200,speed=speedi,brake=0,type=Order.DESTINATION,num=158))
                    orders.append(Order(x=2100, y=200,speed=speedi,brake=0,type=Order.DESTINATION,num=159))
                else:
                    #print("Red")
                    orders.append(Order(x=1000, y=800,speed=speedi,brake=0,type=Order.DESTINATION,num=160))
                    orders.append(Order(x=2025, y=800,speed=speedi,brake=0,type=Order.DESTINATION,num=161))


                if checkForColor(Hindernisse.GREEN, 12, 18) and checkForColor(Hindernisse.RED, 18, 24):
                    #print("Green")
                    orders.append(Order(x=2200, y=400,speed=speedi,brake=0,type=Order.DESTINATION,num=162))
                elif checkForColor(Hindernisse.RED, 12, 18) and checkForColor(Hindernisse.GREEN, 18, 24):
                    #print("Red")
                    orders.append(Order(x=2500, y=600,speed=speedi,brake=0,type=Order.DESTINATION,num=163))

                if checkForColor(Hindernisse.GREEN, 18, 24):
                    #print("Green")
                    orders.append(Order(x=2800, y=900,speed=speedi,brake=0,type=Order.DESTINATION,num=164))
                    orders.append(Order(x=2800, y=2000,speed=speedi,brake=1,type=Order.DESTINATION,num=165))
                    if not waitCompleteOrders():
                        return
                    time.sleep(0.5)
                    orders.append(Order(angleCheckOverwrite=0,type=Order.REPOSITION))
                    if not waitCompleteOrders():
                        return
                    # while vPressed <= 0:
                    #     time.sleep(0.1)
                elif (i == 0) or checkForColor(Hindernisse.GREEN, 0, 1):
                    #print("Red")
                    orders.append(Order(x=2200, y=1000,speed=speedi,brake=0,type=Order.DESTINATION,num=166))
                    orders.append(Order(x=2200, y=1800,speed=speedi,brake=1,type=Order.DESTINATION,num=167))
                    
                    if checkForColor(Hindernisse.RED, 0, 6):
                        #orders.append(Order(x=2200, y=2020,speed=speedScan,brake=1,type=Order.DESTINATION,num=168))
                        orders.append(Order(zielwinkel=90, speed=0.2, brake=1, type=Order.WINKEL))
                        if not waitCompleteOrders():
                            return
                        time.sleep(0.5)
                        orders.append(Order(angleCheckOverwrite=0,type=Order.REPOSITION))
                        if not waitCompleteOrders():
                            return
                        orders.append(Order(x=slam.xpos, y=1970,speed=speedi,brake=0,type=Order.DESTINATION,num=1672))
                    else:
                        orders.append(Order(x=2200, y=2000,speed=speedi,brake=0,type=Order.DESTINATION,num=1673))
                    

                if checkForColor(Hindernisse.GREEN, 18, 24) and checkForColor(Hindernisse.RED, 0, 6):
                    #print("Green")
                    orders.append(Order(x=2600, y=2250,speed=speedi,brake=0,type=Order.DESTINATION,num=169))
                elif checkForColor(Hindernisse.RED, 18, 24) and checkForColor(Hindernisse.GREEN, 0, 6) and ((i == 0) or checkForColor(Hindernisse.GREEN, 0, 1)):
                    #print("Red")
                    orders.append(Order(x=2400, y=2300,speed=speedi,brake=1,type=Order.DESTINATION,num=170))
                    orders.append(Order(zielwinkel=90, speed=0.2, brake=1, type=Order.WINKEL))
                    if not waitCompleteOrders():
                        return
                    time.sleep(0.5)
                    orders.append(Order(angleCheckOverwrite=0,type=Order.REPOSITION))
                    if not waitCompleteOrders():
                        return
                
                if checkForColor(Hindernisse.RED, 18, 24) and (i == 1) and not(checkForColor(Hindernisse.GREEN, 0, 1)):
                    orders.append(Order(x=2200, y=1000,speed=speedi,brake=0,type=Order.DESTINATION,num=175))
                    orders.append(Order(x=2200, y=1800,speed=speedi,brake=1,type=Order.DESTINATION,num=176))
                    if not waitCompleteOrders():
                        return
                    time.sleep(0.5)
                    orders.append(Order(angleCheckOverwrite=0,type=Order.REPOSITION))
                    if not waitCompleteOrders():
                        return
                    orders.append(Order(x=2200, y=2000,speed=speedi,brake=1,type=Order.DESTINATION,num=180))
            
            #orders.append(Order(angleCheckOverwrite=-180,type=Order.REPOSITIONSINGLE,num=78))
            #slam.repositionOneDirSide(-180)

            # -------------------------------------------------------------------------------------------------------------------           Einparken CW

            if checkForColor(Hindernisse.GREEN, 0, 1) and checkForColor(Hindernisse.RED, 18, 24):                   #einparken rot-grün
                slam.logger.warning("Einparken rot-grün")
                orders.append(Order(x=1850, y=2600,speed=0.5, brake=1,type=Order.DESTINATION,num=172))
                orders.append(Order(zielwinkel=0, speed=0.2, brake=1, type=Order.WINKEL))
                if not waitCompleteOrders():
                    return
                time.sleep(3.5)
                orders.append(Order(steer=0, dist=250, speed=-0.5, brake=1, type=Order.KURVE))
                if not waitCompleteOrders():
                    return
                time.sleep(0.5)
                orders.append(Order(type=Order.REPOSITION))
                if not waitCompleteOrders():
                    return
                time.sleep(0.5)
                orders.append(Order(x=1860, y=2600,speed=0.3, brake=1,type=Order.DESTINATION,num=172))
                orders.append(Order(zielwinkel=90, speed=0.2, brake=1, type=Order.WINKEL))
                orders.append(Order(x=1860, y=3000, speed=0.3, timeDrive=3, type=Order.DESTINATIONTIME))
                orders.append(Order(speed=147, timeDrive=1.0, type=Order.TIMEPOWER))
            
            elif checkForColor(Hindernisse.GREEN, 0, 1):                                                            #einparken grün-grün  
                slam.logger.warning("Einparken grün-grün")
                # orders.append(Order(x=1920, y=2600,speed=0.5, brake=1,type=Order.DESTINATION,num=172))
                # orders.append(Order(zielwinkel=90, speed=0.2, brake=1, type=Order.WINKEL))
                # orders.append(Order(x=1880, y=3000, speed=0.2, timeDrive=3, type=Order.DESTINATIONTIME))
                orders.append(Order(x=2500, y=2500,speed=0.5, brake=1,type=Order.DESTINATION,num=1721))
                orders.append(Order(x=1840, y=2600,speed=0.5, brake=1,type=Order.DESTINATION,num=172))
                
                
                orders.append(Order(zielwinkel=0, speed=0.2, brake=1, type=Order.WINKEL))
                if not waitCompleteOrders():
                    return
                time.sleep(3.5)
                orders.append(Order(steer=0, dist=300, speed=-0.5, brake=1, type=Order.KURVE))
                if not waitCompleteOrders():
                    return
                time.sleep(0.5)
                orders.append(Order(type=Order.REPOSITION))
                if not waitCompleteOrders():
                    return
                time.sleep(0.5)
                orders.append(Order(x=1860, y=2600,speed=0.3, brake=1,type=Order.DESTINATION,num=172))
                orders.append(Order(zielwinkel=90, speed=0.2, brake=1, type=Order.WINKEL))
                orders.append(Order(x=1860, y=3000, speed=0.3, timeDrive=3, type=Order.DESTINATIONTIME))
                orders.append(Order(speed=147, timeDrive=1.0, type=Order.TIMEPOWER))
            
            elif checkForColor(Hindernisse.RED, 18, 24):
                slam.logger.warning("Einparken rot-nix")                                                      #einparken rot-nix  oder rot-rot
                
                # orders.append(Order(x=2200, y=2100,speed=0.5, brake=1,type=Order.DESTINATION,num=424))    
                orders.append(Order(zielwinkel=0, speed=0.2, brake=1, type=Order.WINKEL))
                        
                # orders.append(Order(x=1900, y=2200,speed=0.5, brake=1,type=Order.DESTINATION,num=173))
                orders.append(Order(x=1840, y=2200,speed=0.5, brake=1,type=Order.DESTINATION,num=423))
                orders.append(Order(zielwinkel=90, speed=0.2, brake=1, type=Order.WINKEL))
                
                if not waitCompleteOrders():
                    return
                time.sleep(3.5)
                if checkForColor(Hindernisse.RED, 0, 1):
                    slam.repositionOneDirSide(0)
                else:
                    slam.repositionOneDirSide(180)
                if not waitCompleteOrders():
                    return
                time.sleep(0.5)
                
                orders.append(Order(x=1860, y=3000, speed=0.2, timeDrive=6, type=Order.DESTINATIONTIME))
                orders.append(Order(speed=147, timeDrive=1.0, type=Order.TIMEPOWER))

            else:                                                                                             #einparken grün-nix
                slam.logger.warning("Einparken grün-nix")
                orders.append(Order(x=1900, y=2200,speed=0.5, brake=1,type=Order.DESTINATION,num=173))
                orders.append(Order(x=1840, y=2200,speed=0.5, brake=1,type=Order.DESTINATION,num=423))
                orders.append(Order(zielwinkel=90, speed=0.2, brake=1, type=Order.WINKEL))
                
                if not waitCompleteOrders():
                    return
                time.sleep(3.5)
                if checkForColor(Hindernisse.RED, 0, 1):
                    slam.repositionOneDirSide(0)
                else:
                    slam.repositionOneDirSide(180)
                if not waitCompleteOrders():
                    return
                time.sleep(0.5)
                
                
                if checkForColor(Hindernisse.RED, 0, 1):
                    orders.append(Order(x=1860, y=3000, speed=0.2, timeDrive=6, type=Order.DESTINATIONTIME))
                else:
                    orders.append(Order(x=1830, y=3000, speed=0.2, timeDrive=6, type=Order.DESTINATIONTIME))


                orders.append(Order(speed=147, timeDrive=1.0, type=Order.TIMEPOWER))
                    
        
        
        
        
        
        # -----------------------------------------------------------------------------------------------           Hindernissrennen CCW
        
        
        
        else:                                                                                           #           Hindernissrennen CCW
            orders.append(Order(steer=90, dist=55, speed=0.2, brake=1, type=Order.KURVE,num=1))          #           CCW Ausparken
            if not waitCompleteOrders():
                return
            time.sleep(0.2)   
            orders.append(Order(steer=0, dist=25, speed=-0.2, brake=1, type=Order.KURVE,num=3))
            if not waitCompleteOrders():
                return
            time.sleep(0.2) 
            orders.append(Order(steer=90, dist=80, speed=0.2, brake=1, type=Order.KURVE,num=1))
            orders.append(Order(steer=0, dist=50, speed=0.2, brake=1, type=Order.KURVE,num=1))    
            orders.append(Order(steer=-90, dist=290, speed=0.2, brake=1, type=Order.KURVE,num=3))
            orders.append(Order(x=2200, y=2800,speed=0.5,brake=1,type=Order.DESTINATION,num=4))
            orders.append(Order(zielwinkel=180, speed=0.2, brake=1, type=Order.WINKEL,dir=Order.CCW,num=5))
            
            if not waitCompleteOrders():
                return
            time.sleep(0.1)   
            orders.append(Order(steer=0, dist=50, speed=-0.2, brake=1, type=Order.KURVE,num=3))
            if not waitCompleteOrders():
                return
            time.sleep(0.1)
            
            orders.append(Order(zielwinkel=-95, speed=0.2, brake=1, type=Order.WINKEL,dir=Order.CCW,num=5))
            
            
            # orders.append(Order(steer=90, dist=160, speed=0.2, brake=1, type=Order.KURVE,num=1))        #           CCW Ausparken
            # orders.append(Order(steer=-90, dist=290, speed=0.2, brake=1, type=Order.KURVE,num=3))
            if not waitCompleteOrders():
                return
            slam.repostionEnable = 1
            
            speedScan = 0.5
            
            
            # orders.append(Order(x=2200, y=2800,speed=speedScan,brake=1,type=Order.DESTINATION,num=4))
            # if not waitCompleteOrders():
                # return
            # time.sleep(0.5)
            # orders.append(Order(steer=0, dist=40, speed=-0.2, brake=1, type=Order.KURVE,num=420))
            # orders.append(Order(zielwinkel=-90, speed=0.2, brake=1, type=Order.WINKEL,dir=Order.CCW,num=5))
            if not waitCompleteOrders():
                return
            time.sleep(0.3)
            orders.append(Order(type=Order.REPOSITION,num=6))
            time.sleep(0.5) 
            orders.append(Order(toScan=[20, 21, 22, 23],type=Order.SCAN,num=7))                   #         Hindernisse 20-23 scannen OST
            time.sleep(0.3)
            if not waitCompleteOrders():
                return
            
            
            if checkForColor(Hindernisse.GREEN, 18, 24):
                orders.append(Order(x=2200, y=2000,speed=speedScan,brake=1,type=Order.DESTINATION,num=8))           # Grün gefunden

                
            elif checkForColor(Hindernisse.RED, 18, 24):                                                            #Rot gefunden
                #print("red")
                orders.append(Order(x=2790, y=2049,speed=speedScan,brake=1,type=Order.DESTINATION,num=11))
            else:
                orders.append(Order(x=2500, y=1830,speed=speedScan,brake=1,type=Order.DESTINATION,num=14))          #nachscannen
                if not waitCompleteOrders():
                    return
                time.sleep(0.3)
                orders.append(Order(toScan=[18, 19],type=Order.SCAN,num=15))           #         Hindernisse 18-24 scannen OST  2ter versuch
                time.sleep(0.3)
                if not waitCompleteOrders():
                    return
                if checkForColor(Hindernisse.RED, 18, 24):
                    #print("red")
                    orders.append(Order(x=2800, y=1000, speed=speedScan, brake=1, type=Order.DESTINATION,num=19))
                else:  
                    #print("green")
                    orders.append(Order(x=2200, y=1000,speed=speedScan,brake=1,type=Order.DESTINATION,num=20))

            
            print("scan north")
            if checkForColor(Hindernisse.GREEN, 18, 24):                                                                # scannen bereich  nord
                scan_inner_tour(orders, speedScan,1090,12, Order, waitCompleteOrders, checkForColor)
            else:
                scan_outer_tour(orders, speedScan,1090,12, Order, waitCompleteOrders, checkForColor)

            print("scan west")
            if checkForColor(Hindernisse.GREEN, 12, 18):                                                                # scannen bereich  west
                scan_inner_tour(orders, speedScan,1180,6, Order, waitCompleteOrders, checkForColor)
            else:
                scan_outer_tour(orders, speedScan,1180,6, Order, waitCompleteOrders, checkForColor)
                
            print("scan south")
            if checkForColor(Hindernisse.GREEN, 6, 12):                                                                # scannen bereich  süd
                scan_inner_tour(orders, speedScan,1500,0, Order, waitCompleteOrders, checkForColor)
            else:
                scan_outer_tour(orders, speedScan,1500,0, Order, waitCompleteOrders, checkForColor)
            
            if checkForColor(Hindernisse.GREEN, 0, 6):    
                orders.append(Order(x=2000, y=2250,speed=speedScan,brake=1,type=Order.DESTINATION,num=412))
            else:    
                orders.append(Order(x=1500, y=2600,speed=speedScan,brake=1,type=Order.DESTINATION,num=411))
                orders.append(Order(x=2000, y=2580,speed=speedScan,brake=1,type=Order.DESTINATION,num=410))




            speedi = 0.6
            
            for i in range(0,2):
                if (i>0):
                    if checkForColor(Hindernisse.RED, 0, 6):
                        #print("Red")
                        orders.append(Order(x=1000, y=2770,speed=speedi,brake=0,type=Order.DESTINATION,num=56))
                        orders.append(Order(x=1520, y=2600,speed=speedi,brake=0,type=Order.DESTINATION,num=57))
                        orders.append(Order(x=2000, y=2560,speed=speedi,brake=0,type=Order.DESTINATION,num=58))
                    else:
                        #print("Green")
                        if not(checkForColor(Hindernisse.GREEN, 6, 12)) or (i == 0):
                            orders.append(Order(x=1000, y=2200,speed=speedi,brake=0,type=Order.DESTINATION,num=59))
                        orders.append(Order(x=2000, y=2200,speed=speedi,brake=1,type=Order.DESTINATION,num=60))


                if checkForColor(Hindernisse.RED, 0, 6) and checkForColor(Hindernisse.GREEN, 18, 24):
                    #print("Red")
                    orders.append(Order(x=2200, y=2600,speed=speedi,brake=0,type=Order.DESTINATION,num=61))
                elif checkForColor(Hindernisse.GREEN, 0, 6) and checkForColor(Hindernisse.RED, 18, 24):
                    #print("Green")
                    orders.append(Order(x=2550, y=2500,speed=speedi,brake=0,type=Order.DESTINATION,num=62))


                if checkForColor(Hindernisse.RED, 18, 24):
                    #print("Red")
                    if checkForColor(Hindernisse.RED, 0, 6):
                        orders.append(Order(x=2700, y=2250,speed=speedi,brake=0,type=Order.DESTINATION,num=98))
                    orders.append(Order(x=2800, y=2000,speed=speedi,brake=0,type=Order.DESTINATION,num=63))
                    orders.append(Order(x=2800, y=1000,speed=speedi,brake=0,type=Order.DESTINATION,num=64))
                else:
                    #print("Green")
                    orders.append(Order(x=2200, y=2000,speed=speedi,brake=0,type=Order.DESTINATION,num=65))
                    orders.append(Order(x=2200, y=1000,speed=speedi,brake=1,type=Order.DESTINATION,num=66))


                if checkForColor(Hindernisse.RED, 18, 24) and checkForColor(Hindernisse.GREEN, 12, 18):
                    #print("Red")
                    orders.append(Order(x=2600, y=800,speed=speedi,brake=0,type=Order.DESTINATION,num=67))
                elif checkForColor(Hindernisse.GREEN, 18, 24) and checkForColor(Hindernisse.RED, 12, 18):
                    #print("Green")
                    orders.append(Order(x=2400, y=500,speed=speedi,brake=0,type=Order.DESTINATION,num=68))

                if checkForColor(Hindernisse.RED, 12, 18):
                    #print("Red")
                    if checkForColor(Hindernisse.RED, 18, 24):
                        orders.append(Order(x=2600, y=450,speed=speedi,brake=0,type=Order.DESTINATION,num=69))
                    orders.append(Order(x=2100, y=230,speed=speedi,brake=0,type=Order.DESTINATION,num=70))
                    orders.append(Order(x=900, y=200,speed=speedi,brake=0,type=Order.DESTINATION,num=71))
                else:
                    #print("Green")
                    orders.append(Order(x=2000, y=800,speed=speedi,brake=0,type=Order.DESTINATION,num=72))
                    orders.append(Order(x=1000, y=800,speed=speedi,brake=1,type=Order.DESTINATION,num=73))


                if checkForColor(Hindernisse.RED, 12, 18) and checkForColor(Hindernisse.GREEN, 6, 12):
                    #print("Red")
                    orders.append(Order(x=800, y=400,speed=speedi,brake=0,type=Order.DESTINATION,num=74))
                elif checkForColor(Hindernisse.GREEN, 12, 18) and checkForColor(Hindernisse.RED, 6, 12):
                    #print("Green")
                    orders.append(Order(x=500, y=600,speed=speedi,brake=0,type=Order.DESTINATION,num=75))

                if checkForColor(Hindernisse.RED, 6, 12):
                    #print("Red")
                    orders.append(Order(x=230, y=900,speed=speedi,brake=0,type=Order.DESTINATION,num=76))
                    orders.append(Order(x=200, y=2050,speed=speedi,brake=1,type=Order.DESTINATION,num=77))
                    if (i == 0) or checkForColor(Hindernisse.GREEN, 2, 6):
                        if not waitCompleteOrders():
                            return
                        time.sleep(0.5)
                        print("1")
                        orders.append(Order(angleCheckOverwrite=180,type=Order.REPOSITION,num=78))
                        if not waitCompleteOrders():
                            return
                else:
                    #print("Green")
                    orders.append(Order(x=800, y=1000,speed=speedi,brake=0,type=Order.DESTINATION,num=79))
                    orders.append(Order(x=800, y=1800,speed=speedi,brake=1,type=Order.DESTINATION,num=80))
                    if checkForColor(Hindernisse.GREEN, 0, 6) and (i == 0):
                        #orders.append(Order(x=800, y=2050,speed=speedScan,brake=1,type=Order.DESTINATION,num=81))
                        if not waitCompleteOrders():
                            return
                        time.sleep(0.5)
                        print("2")
                        orders.append(Order(angleCheckOverwrite=180,type=Order.REPOSITION,num=82))
                        if not waitCompleteOrders():
                            return
                        orders.append(Order(x=slam.xpos, y=1970,speed=speedi,brake=1,type=Order.DESTINATION,num=802))
                    else:
                        orders.append(Order(x=800, y=2000,speed=speedi,brake=1,type=Order.DESTINATION,num=803))
                    
                if checkForColor(Hindernisse.RED, 6, 12) and checkForColor(Hindernisse.GREEN, 0, 6) and (i == 0):
                    #print("Red")
                    orders.append(Order(x=400, y=2250,speed=speedi,brake=0,type=Order.DESTINATION,num=83))
                elif checkForColor(Hindernisse.GREEN, 6, 12) and checkForColor(Hindernisse.RED, 0, 6):
                    #print("Green")
                    orders.append(Order(x=600, y=2300,speed=speedi,brake=1,type=Order.DESTINATION,num=84))
                    if not waitCompleteOrders():
                        return
                    time.sleep(0.5)
                    print("3")
                    orders.append(Order(angleCheckOverwrite=180,type=Order.REPOSITION,num=85))
                    if not waitCompleteOrders():
                        return
                elif checkForColor(Hindernisse.RED, 6, 12) and checkForColor(Hindernisse.RED, 0, 6):
                    orders.append(Order(x=200, y=2600,speed=speedi,brake=1,type=Order.DESTINATION,num=86))
                    
                    
                    
                    
            #   --------------------------------------------------------------------------------------------  Einparken CCW
            # if checkForColor(Hindernisse.RED, 2, 6) and checkForColor(Hindernisse.GREEN, 6, 12):                # von Grün nach Rot
            #     # orders.append(Order(x=1000, y=2770,speed=0.5,brake=0,type=Order.DESTINATION,num=176))
            #     # orders.append(Order(x=1400, y=2600,speed=0.5,brake=0,type=Order.DESTINATION,num=175))
            #     # orders.append(Order(x=1760, y=2600, speed=0.5, brake=1,type=Order.DESTINATION,num=171))
            #     # orders.append(Order(zielwinkel=90, speed=0.2, brake=1, type=Order.WINKEL))
            #     # orders.append(Order(x=1870, y=3000, speed=0.2, timeDrive=2, type=Order.DESTINATIONTIME))
            #     orders.append(Order(x=700, y=2770,speed=0.5,brake=1,type=Order.DESTINATION,num=177))
            #     if not waitCompleteOrders():
            #         return
            #     time.sleep(0.5)
            #     print("4")
            #     orders.append(Order(angleCheckOverwrite=180,type=Order.REPOSITION,num=78))
            #     if not waitCompleteOrders():
            #         return    
            #     orders.append(Order(x=1000, y=2770,speed=0.5,brake=0,type=Order.DESTINATION,num=178))
            #     orders.append(Order(x=1350, y=2600,speed=0.5,brake=0,type=Order.DESTINATION,num=175))
            #     orders.append(Order(zielwinkel=180, speed=0.2, brake=1, type=Order.WINKEL))
            #     if not waitCompleteOrders():
            #         return 
            #     time.sleep(0.5)
            #     slam.repositionOneDirFront(180)
            #     time.sleep(0.2)
            #     orders.append(Order(x=1780, y=2600, speed=0.5, brake=1,type=Order.DESTINATION,num=171))
            #     orders.append(Order(zielwinkel=90, speed=0.2, brake=1, type=Order.WINKEL))
            #     orders.append(Order(x=1860, y=3000, speed=0.2, timeDrive=2, type=Order.DESTINATIONTIME))           
            if checkForColor(Hindernisse.RED, 2, 6):                                                          # von Rot/Grün  nach Rot      
                orders.append(Order(x=600, y=2700,speed=0.5,brake=1,type=Order.DESTINATION,num=177))
                if not waitCompleteOrders():
                    return
                time.sleep(0.5)
                print("4")
                orders.append(Order(angleCheckOverwrite=180,type=Order.REPOSITION,num=78))
                if not waitCompleteOrders():
                    return    
                orders.append(Order(zielwinkel=180, speed=0.2, brake=1, type=Order.WINKEL))
                orders.append(Order(x=1000, y=2770,speed=0.5,brake=0,type=Order.DESTINATION,num=178))
                orders.append(Order(x=1350, y=2600,speed=0.5,brake=0,type=Order.DESTINATION,num=175))
                orders.append(Order(zielwinkel=180, speed=0.2, brake=1, type=Order.WINKEL))
                if not waitCompleteOrders():
                    return 
                time.sleep(0.5)
                slam.repositionOneDirFront(180)
                time.sleep(4)
                orders.append(Order(x=1770, y=2450, speed=0.4, brake=1,type=Order.DESTINATION,num=171))
                orders.append(Order(zielwinkel=180, speed=0.2, brake=1, type=Order.WINKEL))
                if not waitCompleteOrders():
                    return 
                orders.append(Order(steer=0, dist=200, speed=-0.3, brake=1, type=Order.KURVE,num=420))
                if not waitCompleteOrders():
                    return 
                time.sleep(0.5)
                slam.repositionOneDirFront(180)
                time.sleep(0.5)               
                orders.append(Order(x=1850, y=2540, speed=0.4, brake=0,type=Order.DESTINATION,num=179))
                
                orders.append(Order(zielwinkel=90, speed=0.2, brake=1, type=Order.WINKEL))
                orders.append(Order(x=1860, y=3000, speed=0.2, timeDrive=5, type=Order.DESTINATIONTIME))
                orders.append(Order(speed=147, timeDrive=1.0, type=Order.TIMEPOWER))
            
            elif checkForColor(Hindernisse.GREEN, 6, 12): 
                orders.append(Order(x=1500, y=2200, speed=0.5, brake=1,type=Order.DESTINATION,num=400))         # von Grün nach Grün   
                if not waitCompleteOrders():
                    return
                time.sleep(3.5)
                orders.append(Order(angleCheckOverwrite=-180,type=Order.REPOSITIONSINGLE,num=78))
                if not waitCompleteOrders():
                    return  
                time.sleep(0.5)
                
            
                orders.append(Order(x=1760, y=2200, speed=0.5, brake=1,type=Order.DESTINATION,num=401))
                orders.append(Order(zielwinkel=90, speed=0.2, brake=1, type=Order.WINKEL))
                if not waitCompleteOrders():
                    return 
                time.sleep(0.5)
                slam.repositionOneDirSide(-180)
                time.sleep(0.1)
                
                orders.append(Order(x=1860, y=3000, speed=0.2, timeDrive=4, type=Order.DESTINATIONTIME))
                orders.append(Order(speed=147, timeDrive=1.0, type=Order.TIMEPOWER))
            
            else:                                                                                               # von Rot nach Grün                                   
                orders.append(Order(x=900, y=2200,speed=0.5, brake=1,type=Order.DESTINATION,num=173))
                if not waitCompleteOrders():
                    return
                time.sleep(0.5)
                orders.append(Order(angleCheckOverwrite=0,type=Order.REPOSITION,num=82))
                if not waitCompleteOrders():
                    return
                orders.append(Order(x=1760, y=2200, speed=0.5, brake=1,type=Order.DESTINATION,num=171))
                if not waitCompleteOrders():
                    return 
                time.sleep(3.5)
                orders.append(Order(zielwinkel=90, speed=0.2, brake=1, type=Order.WINKEL))
                if not waitCompleteOrders():
                    return 
                time.sleep(0.5)
                slam.repositionOneDirSide(-180)
                time.sleep(0.1)
                
                orders.append(Order(x=1860, y=3000, speed=0.2, timeDrive=4, type=Order.DESTINATIONTIME))
                orders.append(Order(speed=147, timeDrive=1.0, type=Order.TIMEPOWER))


def printOrder():
    global orders
    if orders.__len__() == 0:
        print("No Order",end="")
        slam.logger.warning('     -> No Order')
        return
    if orders[0].type == Order.DESTINATION:
        print("Destination: ", orders[0].x, orders[0].y,end="")
        slam.logger.warning('%i    -> Destination  %i  %i',orders[0].num, orders[0].x, orders[0].y)
    elif orders[0].type == Order.KURVE:
        print("KURVE: ", orders[0].dist, orders[0].steer,orders[0].speed,end="")
        slam.logger.warning('%i    -> KURVE  %i  %i %f',orders[0].num, orders[0].dist, orders[0].steer, orders[0].speed)
    elif orders[0].type == Order.SCAN:
        print("SCAN: ", orders[0].toScan,end="")
        slam.logger.warning('%i    -> SCAN',orders[0].num)
    elif orders[0].type == Order.WINKEL:
        print("WINKEL: ", orders[0].zielwinkel,end="")
        slam.logger.warning('%i    -> WINKEL  %i',orders[0].num, orders[0].zielwinkel)
    elif orders[0].type == Order.REPOSITION:
        print("REPOSITION: ",end="")
        slam.logger.warning('%i    -> REPOSITION',orders[0].num, orders[0].zielwinkel)
    elif orders[0].type == Order.TIME:
        print("TIME: ", orders[0].timeDrive,end="")
        slam.logger.warning('%i    -> TIME  %i',orders[0].num, orders[0].timeDrive)



def nextOrder():
    global orders
    
#    printOrder()
    orders.pop(0)
    print("-> ",end="")
    printOrder()
    print("")


def controlLoop(robot, camera, playmat):
    driveBase = DriveBase(slam, kit)
    global running3
    global takePicture
    global sem
    global startTime
    setServoAngle(kit,90)
    kit.servo[3].angle = 90
    
    slam.update()
    slam.startpostionsetzen()
    startZeit = 0
    ausgabe = 0

    global orders
    
    # Loop frequency measurement variables
    loop_count = 0
    last_time = time.time()
    
    # Set target frequency and loop time
    target_frequency = 100.0
    loop_time = 1.0 / target_frequency  
    next_loop_time = time.time() + loop_time

    while running3:
        # Measure loop frequency
        loop_count += 1
        current_time = time.time()
        if current_time - last_time >= 1.0:  # Every second
            frequency = loop_count / (current_time - last_time)
            # print(f"Control Loop Frequency: {frequency:.2f} Hz")
            loop_count = 0
            last_time = current_time
        
        slam.update()
        if slam.crash == 1:
            print("Crash detected, recovering...")
            driveBase.crashRecovery()
        if orders.__len__() > 0:
            if orders[0].type == Order.KURVE or orders[0].type == Order.WINKEL:
                slam.noCurveReposition=1
            else:
                slam.noCurveReposition=0
            if (robot.semDb.acquire(blocking=False)):
                robot.circlexList.clear()
                robot.circleyList.clear()
                robot.circleNumList.clear()
                for i in range(len(orders)):
                    if orders[i].type == Order.DESTINATION:
                        robot.circlexList.append(orders[i].x)
                        robot.circleyList.append(orders[i].y)
                        robot.circleNumList.append(orders[i].num)
                        
                robot.semDb.release()
            if orders[0].type == Order.MANUAL:
                pass
            elif orders[0].type == Order.DESTINATION:
                robot.circlex = orders[0].x
                robot.circley = orders[0].y
                playmat.speedSetpoint = orders[0].speed
                if driveBase.driveTo(orders[0].x,orders[0].y,orders[0].speed,orders[0].brake):
                    nextOrder()
            elif orders[0].type == Order.KURVE:
                if driveBase.drivekürvchen(orders[0].dist,orders[0].steer,orders[0].speed,orders[0].brake):
                    nextOrder()
            elif orders[0].type == Order.SCAN:
                sem.acquire()
                found=slam.hindernisseErkennung(slam.scan,orders[0].toScan, camera, orders[0].checkHeightNear)
                slam.logger.warning('Found %i on first scan', found)
                if (found == 0):
                    time.sleep(0.2) 
                    slam.loopCounter=10
                    slam.update()
                    found=slam.hindernisseErkennung(slam.scan,orders[0].toScan, camera, orders[0].checkHeightNear)
                    slam.logger.warning('Found %i on second scan', found)

                takePicture = True
                sem.release()
                nextOrder()
            elif orders[0].type == Order.WINKEL:
                if driveBase.driveToWinkel(orders[0].zielwinkel,orders[0].speed,orders[0].brake,orders[0].dir):
                    nextOrder()
            elif orders[0].type == Order.REPOSITION:
                sem.acquire()
                slam.reposition(orders[0].angleCheckOverwrite)
                takePicture = True
                sem.release()
                nextOrder()
            elif orders[0].type == Order.REPOSITIONSINGLE:
                sem.acquire()
                slam.repositionOneDirFront(orders[0].angleCheckOverwrite)
                takePicture = True
                sem.release()
                nextOrder()
            elif orders[0].type == Order.TIME:
                if driveBase.driveTime(orders[0].timeDrive,orders[0].speed,startTime):
                    nextOrder()
            elif orders[0].type == Order.TIMEPOWER:
                if driveBase.driveTimePower(orders[0].timeDrive,orders[0].speed,startTime):
                    nextOrder()
            elif orders[0].type == Order.DESTINATIONTIME:
                if driveBase.driveToTime(orders[0].x,orders[0].y,orders[0].speed,orders[0].timeDrive,startTime):
                    nextOrder()
        else:
            setServoAngle(kit,90,slam)
            kit.servo[3].angle = 90
            



        sleep_time = next_loop_time - time.time()
        if sleep_time > 0:
            time.sleep(sleep_time)
        next_loop_time = time.time() + loop_time



    return 1  # Normal exit - allow restart


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)

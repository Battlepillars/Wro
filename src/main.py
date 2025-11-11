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
from unpark import *
from scanRound import scanRound
from driveRound import driveRound
from park import park
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

show = 0
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
    virtual_cursor_x = 0
    virtual_cursor_y = 0
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
    global show
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
            
            """
            Keyboard Commands Overview:
            
            PROGRAM CONTROL:
            - c: Exit program (restart possible)
            - x: Exit program (no restart)
            - SPACE: Stop command execution, clear orders
            - v: Start signal (at program startup)
            
            DEBUG/POSITIONING:
            - u: Execute manual repositioning
            - i: Recalculate angle
            - e: Set position to mouse position
            - r: Rotate robot by 90°
            - f: Print mouse position
            - o: Enter X/Y coordinates for virtual cursor
            
            COMMANDS/SCAN:
            - k: Add drive command to mouse position
            - g: Print order command to mouse position in console
            - t: Perform complete scan of all 24 obstacles
            - z: Perform scan with "checkHeightNear" (close range)
            
            MANUAL DRIVE MODE:
            - m: Activate manual drive mode
            - w: Drive forward (manual mode only)
            - s: Drive backward (manual) / Show info (normal mode)
            - a: Steer left (manual mode only)
            - d: Steer right (manual mode only)
            """
            
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_o:
                    virtual_cursor_x = (float(input("x"))*playmat.matScale) + (50 * playmat.matScale)
                    virtual_cursor_y = (float(input("y"))*playmat.matScale) + (50 * playmat.matScale)
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
                if event.key == pygame.K_i:
                    def test_park():
                        slam.hindernisse[23].farbe = Hindernisse.GREEN
                        park(orders, Order, waitCompleteOrders, checkForColor, Order.CW, 18, slam)
                    parkThread = threading.Thread(target=test_park, daemon=True)
                    parkThread.start()
                    #slam.resetAngle()
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
                    if manual == 1:
                        kit.servo[3].angle = 80 - 25
                        sPressed = 1
                    else:
                        show = 1
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
            playmat.Infos(screen, robot, slam, playmat.matScale, startTime, time, lamp, virtual_cursor_x, virtual_cursor_y)
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
    DRIVETOY=10
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
        elif (rotation == 1500):          # South in CCW
            self.x = 1500-(y-1500)
            self.y = x                  # rotate 90 degrees
            self.y=  3000-self.y        # mirror at y=1500
            zielwinkel = 180-(zielwinkel+90)
            if (angleCheckOverwrite != 1000):
                angleCheckOverwrite = 180-(angleCheckOverwrite+90)
        elif (rotation == 1180):          # West in CCW
            self.x = 3000-x
            self.y = 3000-y             # rotate 180 degrees
            self.x= 3000-self.x         # mirror at x=1500
            zielwinkel = -(zielwinkel)
            if (angleCheckOverwrite != 1000):
                angleCheckOverwrite = -(angleCheckOverwrite)
        elif (rotation == 1090):          # North in CCW
            self.x = y
            self.y = -x+3000            # rotate 90 degrees
            self.y=  3000-self.y        # mirror at y=1500
            zielwinkel = 180-(zielwinkel-90)
            if (angleCheckOverwrite != 1000):
                angleCheckOverwrite = 180-(angleCheckOverwrite-90)
        elif (rotation == 1000):          # North in CCW
            self.x = 3000-x             # mirror at x
            self.y = y
            zielwinkel = 180-(zielwinkel)
            if (angleCheckOverwrite != 1000):
                angleCheckOverwrite = 180-(angleCheckOverwrite)
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
    global show
    while orders.__len__() > 0 and running2 and show == 0:
        time.sleep(0.01)
    return running2
def checkForColor(color, start, end):
    if start > slam.hindernisse.__len__() or end > slam.hindernisse.__len__():
        end = end - 24
        start = start - 24
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
    while slam.xpos == 0 and slam.ypos == 0 and running2:
        lamp.fill(0x000001)
        lamp.show()
        time.sleep(0.05)
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

    runTestCode = False
    
    if runTestCode:
        park(orders, Order, waitCompleteOrders, checkForColor, Order.CW, 18, slam)
        return
        orders.append(Order(zielwinkel=-45, speed=0.2, brake=1, dir=Order.CW, type=Order.WINKEL))
        orders.append(Order(y=2800, zielwinkel=-90, speed=-0.2, brake=1, type=Order.DRIVETOY))
    
    elif slam.eventType == slam.HR:
        if slam.direction == slam.CW:
            unparkCW(orders, Order, waitCompleteOrders, checkForColor)
            slam.repostionEnable = 1
            scanRound(orders, Order, waitCompleteOrders, checkForColor, 0, 6)
            scanRound(orders, Order, waitCompleteOrders, checkForColor, -90, 12)
            scanRound(orders, Order, waitCompleteOrders, checkForColor, 180, 18)
            scanRound(orders, Order, waitCompleteOrders, checkForColor, 90, 0)
            
            if not waitCompleteOrders():
                return
            orders.append(Order(zielwinkel=-90, speed=0.2, brake=1, dir=Order.CW, type=Order.WINKEL))
            if not waitCompleteOrders():
                return
            time.sleep(0.3)
            orders.append(Order(angleCheckOverwrite=-90,type=Order.REPOSITION))
            if not waitCompleteOrders():
                return
            time.sleep(0.3)
            for i in range(0,2):
                driveRound(orders, Order, waitCompleteOrders, checkForColor, 0, 6, slam)
                driveRound(orders, Order, waitCompleteOrders, checkForColor, -90, 12, slam)
                driveRound(orders, Order, waitCompleteOrders, checkForColor, 180, 18, slam, i==1) 
                if i == 0:
                    driveRound(orders, Order, waitCompleteOrders, checkForColor, 90, 0, slam)
                
                if not waitCompleteOrders():
                    return
            park(orders, Order, waitCompleteOrders, checkForColor, Order.CW, 18, slam)
        else:
            unparkCCW(orders, Order, waitCompleteOrders, checkForColor)
            slam.repostionEnable = 1
            scanRound(orders, Order, waitCompleteOrders, checkForColor, 1000, 18)
            scanRound(orders, Order, waitCompleteOrders, checkForColor, 1090, 12)
            scanRound(orders, Order, waitCompleteOrders, checkForColor, 1180, 6)
            scanRound(orders, Order, waitCompleteOrders, checkForColor, 1500, 0)
            
            if not waitCompleteOrders():
                return
            orders.append(Order(zielwinkel=-90, speed=0.2, brake=1, dir=Order.CCW, type=Order.WINKEL))
            if not waitCompleteOrders():
                return
            time.sleep(0.3)
            orders.append(Order(type=Order.REPOSITION))
            if not waitCompleteOrders():
                return
            time.sleep(0.3)
            for i in range(0,2):
                driveRound(orders, Order, waitCompleteOrders, checkForColor, 1000, 18, slam)
                driveRound(orders, Order, waitCompleteOrders, checkForColor, 1090, 12, slam)
                driveRound(orders, Order, waitCompleteOrders, checkForColor, 1180, 6, slam, i==1) 
                if i == 0:
                    driveRound(orders, Order, waitCompleteOrders, checkForColor, 1500, 0, slam)
                
                if not waitCompleteOrders():
                    return
            park(orders, Order, waitCompleteOrders, checkForColor, Order.CCW, 11, slam)


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
    global show
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
            if orders[0].type == Order.MANUAL or show == 1:
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
            elif orders[0].type == Order.DRIVETOY:
                if driveBase.driveToY(orders[0].y,orders[0].zielwinkel,orders[0].speed,orders[0].brake):
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

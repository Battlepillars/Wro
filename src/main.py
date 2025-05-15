# noinspection PyUnresolvedReferences
# start mit debugger :
#python3 -Xfrozen_modules=off -m debugpy --listen 10.0.0.25:5678 --wait-for-client main.py
#python -m pip install --upgrade debugpy
import debugpy
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

from slam import *
from motorController import *
from future.moves import pickle # type: ignore
from drawBoard import *
from camera import *
from ctypes import *
from adafruit_servokit import ServoKit # type: ignore


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
    slam.logger.warn('main init')

    pictureNum=0
    running = True
    camera = Camera()
    robot = Robot(1)
    pygame.init()
    startTime = time.time()
    vPressed = 0
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

        for event in pygame.event.get():

            if event.type == pygame.MOUSEBUTTONUP:
                placing = 0
            if event.type == pygame.MOUSEBUTTONDOWN:
                placing = 1
                
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_c:
                    running = False
                    running2 = False
                    running3 = False
                    kit.servo[3].angle = 90
                    time.sleep(0.1)
                    setServoAngle(kit,90)
                    kit.servo[3].angle = 90
                    slam.lidar.disconnect()
                if event.key == pygame.K_v:
                    vPressed = 5
                if event.key == pygame.K_f:
                    print(math.floor(pygame.mouse.get_pos()[0] / playmat.matScale), math.floor(pygame.mouse.get_pos()[1] / playmat.matScale))
                if event.key == pygame.K_r:
                    slam.reposition()
                if event.key == pygame.K_g:
                    print("orders.append(Order(x="+str(math.floor(pygame.mouse.get_pos()[0] / playmat.matScale)-50)+", y="+str(math.floor(pygame.mouse.get_pos()[1] / playmat.matScale)-50)+",speed=0.5,brake=1,type=Order.DESTINATION))")
                if event.key == pygame.K_t:
                    orders.append(Order(x=pygame.mouse.get_pos()[0] / playmat.matScale, y=pygame.mouse.get_pos()[1] / playmat.matScale, speed=0.5, brake=1, type=Order.DESTINATION))
                if event.key == pygame.K_SPACE:
                    running2 = False
                    running3 = False
                    orders.clear()
                    time.sleep(0.1)
                    setServoAngle(kit,90)
                    kit.servo[3].angle = 90

            if event.type == pygame.QUIT:
                running = False
                running2 = False
                running3 = False
                time.sleep(0.1)
                setServoAngle( kit,90)
                kit.servo[3].angle = 90
                slam.lidar.disconnect()
                
        keys = pygame.key.get_pressed()

        sem.acquire()
        playmat.draw(screen, info, camera, robot)
        robot.draw(screen, playmat.matScale, slam.scan, slam)
        if info == 1:
            playmat.Infos(screen, robot, slam, playmat.matScale, startTime, time)
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

class Order:
    DESTINATION=0
    KURVE=1
    SCAN=2
    WINKEL=3
    REPOSITION=4
    TIME=5
    DESTINATIONTIME=6
    def __init__(self,speed=0,brake=0,type=0,x=0,y=0,steer=0,dist=0,timeDrive=0,toScan=[],zielwinkel=0,angleCheckOverwrite=1000,num=0):
        self.x = x
        self.y = y
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
    
    if button.is_pressed:
        while button.is_pressed:
            time.sleep(0.1)
        time.sleep(1.2)
    else:
        print("Press v to start")
        while vPressed <= 0:
            time.sleep(0.1)
    time.sleep(1)        
    slam.myOtos.calibrateImu(255)
    slam.startpostionsetzen()
    time.sleep(0.1)   
    startTime = time.time()
    
    if slam.eventType == slam.ER:           
        speedi = 0.75
        slam.repostionEnable = 1
        
        if slam.direction == slam.CW:                                       #                                    Eröffnungsrennen  CW
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
        if slam.direction == slam.CW:
            orders.append(Order(steer=-90, dist=170, speed=0.2, brake=1, type=Order.KURVE))
            orders.append(Order(steer=0, dist=150, speed=0.2, brake=1, type=Order.KURVE))
            orders.append(Order(steer=90, dist=170, speed=0.2, brake=1, type=Order.KURVE))
            waitCompleteOrders()
            slam.repostionEnable = 1
            time.sleep(0.5)
            orders.append(Order(toScan=[4, 5],type=Order.SCAN))
            time.sleep(0.5)
            if not waitCompleteOrders():
                return
            
            
            
            speedScan = 0.5

            if checkForColor(Hindernisse.RED, 0, 6):
                #print("Red")
                orders.append(Order(x=1050, y=2207,speed=speedScan,brake=1,type=Order.DESTINATION,num=110))
                orders.append(Order(x=734, y=2607,speed=speedScan,brake=1,type=Order.DESTINATION,num=111))
            else:
                #print("Green")
                orders.append(Order(x=1041, y=2839,speed=speedScan,brake=1,type=Order.DESTINATION,num=112))
                orders.append(Order(x=604, y=2762,speed=speedScan,brake=1,type=Order.DESTINATION,num=113))
            
            
            orders.append(Order(zielwinkel=-90, speed=0.5, brake=1, type=Order.WINKEL))
            if not waitCompleteOrders():
                return
            time.sleep(0.5)
            orders.append(Order(type=Order.REPOSITION))
            orders.append(Order(toScan=[6, 7, 8, 9, 10, 11],type=Order.SCAN))
            time.sleep(0.5)
            if not waitCompleteOrders():
                return
            

            if checkForColor(Hindernisse.RED, 6, 12):
                #print("red")
                orders.append(Order(x=823, y=2008, speed=speedScan, brake=1, type=Order.DESTINATION,num=114))
                orders.append(Order(x=829, y=988, speed=speedScan, brake=1, type=Order.DESTINATION,num=115))
                orders.append(Order(x=244, y=641, speed=speedScan, brake=1, type=Order.DESTINATION,num=116))
            elif checkForColor(Hindernisse.GREEN, 6, 12):
                #print("green")
                orders.append(Order(x=182, y=2049,speed=speedScan,brake=1,type=Order.DESTINATION,num=117))
                orders.append(Order(x=235, y=616,speed=speedScan,brake=1,type=Order.DESTINATION,num=118))
            else:
                orders.append(Order(x=500, y=1830,speed=speedScan,brake=1,type=Order.DESTINATION,num=119))
                if not waitCompleteOrders():
                    return
                time.sleep(0.5)
                orders.append(Order(toScan=[6, 7, 8, 9, 10, 11],type=Order.SCAN))
                time.sleep(0.5)
                if not waitCompleteOrders():
                    return
                if checkForColor(Hindernisse.RED, 6, 12):
                    #print("red")
                    orders.append(Order(x=829, y=988, speed=speedScan, brake=1, type=Order.DESTINATION,num=120))
                    orders.append(Order(x=244, y=641, speed=speedScan, brake=1, type=Order.DESTINATION,num=121))
                else:
                    #print("green")
                    orders.append(Order(x=200, y=1000, speed=speedScan, brake=1, type=Order.DESTINATION,num=122))
                    orders.append(Order(x=235, y=616,speed=speedScan,brake=1,type=Order.DESTINATION,num=123))
            
            orders.append(Order(zielwinkel=180, speed=0.5, brake=1, type=Order.WINKEL))
            if not waitCompleteOrders():
                return
            time.sleep(0.5)
            orders.append(Order(type=Order.REPOSITION))
            orders.append(Order(toScan=[12, 13, 14, 15, 16, 17],type=Order.SCAN))
            time.sleep(0.5)
            if not waitCompleteOrders():
                return
            
            
            if checkForColor(Hindernisse.RED, 12, 18):
                #print("Red")
                orders.append(Order(x=1050, y=861, speed=speedScan, brake=1, type=Order.DESTINATION,num=124))
                orders.append(Order(x=2000, y=750, speed=speedScan, brake=1, type=Order.DESTINATION,num=125))
                orders.append(Order(x=2256, y=427,speed=speedScan,brake=1,type=Order.DESTINATION,num=126))
            elif checkForColor(Hindernisse.GREEN, 12, 18):
                #print("Green")
                orders.append(Order(x=1054, y=229,speed=speedScan,brake=1,type=Order.DESTINATION,num=127))
                orders.append(Order(x=2449, y=291,speed=speedScan,brake=1,type=Order.DESTINATION,num=128))
            else:
                orders.append(Order(x=1250, y=500,speed=speedScan,brake=1,type=Order.DESTINATION,num=129))
                if not waitCompleteOrders():
                    return
                time.sleep(0.5)
                orders.append(Order(toScan=[12, 13, 14, 15, 16, 17],type=Order.SCAN))
                time.sleep(0.5)
                if not waitCompleteOrders():
                    return
                if checkForColor(Hindernisse.RED, 12, 18):
                    #print("red")
                    orders.append(Order(x=2000, y=750, speed=speedScan, brake=1, type=Order.DESTINATION,num=130))
                    orders.append(Order(x=2256, y=427,speed=speedScan,brake=1, type=Order.DESTINATION,num=131))
                else:
                    #print("green")
                    orders.append(Order(x=2000, y=300, speed=speedScan, brake=1, type=Order.DESTINATION,num=132)) 
                    orders.append(Order(x=2500, y=300,speed=speedScan,brake=1, type=Order.DESTINATION,num=133))
                
            orders.append(Order(zielwinkel=90, speed=0.5, brake=1, type=Order.WINKEL))
            if not waitCompleteOrders():
                return
            time.sleep(0.5)
            orders.append(Order(type=Order.REPOSITION))
            orders.append(Order(toScan=[18, 19, 20, 21, 22, 23],type=Order.SCAN))
            time.sleep(0.5)
            if not waitCompleteOrders():
                return


            if checkForColor(Hindernisse.RED, 18, 24):
                #print("Red")
                orders.append(Order(x=2185, y=1054,speed=speedScan,brake=1,type=Order.DESTINATION,num=134))
                orders.append(Order(x=2179, y=2064,speed=speedScan,brake=1,type=Order.DESTINATION,num=135))
                orders.append(Order(x=2650, y=2284,speed=speedScan,brake=1,type=Order.DESTINATION,num=136))
            elif checkForColor(Hindernisse.GREEN, 18, 24):
                #print("Green")
                orders.append(Order(x=2842, y=1054,speed=speedScan,brake=1,type=Order.DESTINATION,num=137))
                orders.append(Order(x=2842, y=2050,speed=speedScan,brake=1,type=Order.DESTINATION,num=138))
                orders.append(Order(x=2650, y=2368,speed=speedScan,brake=1,type=Order.DESTINATION,num=139))
            else:
                orders.append(Order(x=2500, y=1250,speed=speedScan,brake=1,type=Order.DESTINATION,num=140))
                if not waitCompleteOrders():
                    return
                time.sleep(0.5)
                orders.append(Order(toScan=[18, 19, 20, 21, 22, 23],type=Order.SCAN))
                time.sleep(0.5)
                if not waitCompleteOrders():
                    return
                if checkForColor(Hindernisse.RED, 18, 24):
                    #print("red")
                    orders.append(Order(x=2179, y=2064,speed=speedScan,brake=1,type=Order.DESTINATION,num=141))
                    orders.append(Order(x=2650, y=2284,speed=speedScan,brake=1,type=Order.DESTINATION,num=142))
                else:
                    #print("green")
                    orders.append(Order(x=2850, y=2100, speed=speedScan, brake=1, type=Order.DESTINATION,num=143)) 
                    orders.append(Order(x=2650, y=2370,speed=speedScan, brake=1,type=Order.DESTINATION,num=144))
            
            
            orders.append(Order(zielwinkel=0, speed=0.5, brake=1, type=Order.WINKEL))
            if not waitCompleteOrders():
                return
            time.sleep(0.5)
            orders.append(Order(type=Order.REPOSITION))
            orders.append(Order(toScan=[0, 1],type=Order.SCAN))
            time.sleep(0.5)
            if not waitCompleteOrders():
                return
            


            # while vPressed <= 0:
            #     time.sleep(0.1)



            speedi = 0.75
            for i in range(0,2):
                if checkForColor(Hindernisse.GREEN, 0, 6):
                    #print("Green")
                    orders.append(Order(x=2100, y=2550,speed=speedi,brake=0,type=Order.DESTINATION,num=145))
                    orders.append(Order(x=1600, y=2600,speed=speedi,brake=0,type=Order.DESTINATION,num=146))
                    orders.append(Order(x=1000, y=2800,speed=speedi,brake=0,type=Order.DESTINATION,num=147))
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
                    orders.append(Order(x=200, y=1000,speed=speedi,brake=0,type=Order.DESTINATION,num=153))
                else:
                    #print("Red")
                    orders.append(Order(x=800, y=2000,speed=speedi,brake=0,type=Order.DESTINATION,num=154))
                    orders.append(Order(x=800, y=1000,speed=speedi,brake=0,type=Order.DESTINATION,num=155))


                if checkForColor(Hindernisse.GREEN, 6, 12) and checkForColor(Hindernisse.RED, 12, 18):
                    #print("Green")
                    orders.append(Order(x=400, y=800,speed=speedi,brake=0,type=Order.DESTINATION,num=156))
                elif checkForColor(Hindernisse.RED, 6, 12) and checkForColor(Hindernisse.GREEN, 12, 18):
                    #print("Red")
                    orders.append(Order(x=600, y=500,speed=speedi,brake=0,type=Order.DESTINATION,num=157))

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
                    orders.append(Order(x=2200, y=2000,speed=speedi,brake=0,type=Order.DESTINATION,num=167))
                    if checkForColor(Hindernisse.RED, 0, 6):
                        orders.append(Order(x=2200, y=2020,speed=speedScan,brake=1,type=Order.DESTINATION,num=168))
                        orders.append(Order(zielwinkel=90, speed=0.2, brake=1, type=Order.WINKEL))
                        if not waitCompleteOrders():
                            return
                        time.sleep(0.5)
                        orders.append(Order(angleCheckOverwrite=0,type=Order.REPOSITION))
                        if not waitCompleteOrders():
                            return

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
                    orders.append(Order(x=2200, y=2000,speed=speedi,brake=1,type=Order.DESTINATION,num=176))
                    if not waitCompleteOrders():
                        return
                    time.sleep(0.5)
                    orders.append(Order(angleCheckOverwrite=0,type=Order.REPOSITION))
                    if not waitCompleteOrders():
                        return
                    

            if checkForColor(Hindernisse.GREEN, 0, 1) and checkForColor(Hindernisse.RED, 18, 24):
                orders.append(Order(x=1920, y=2600, speed=0.5, brake=1,type=Order.DESTINATION,num=171))
                orders.append(Order(zielwinkel=90, speed=0.2, brake=1, type=Order.WINKEL))
                orders.append(Order(x=1870, y=3000, speed=0.2, timeDrive=2, type=Order.DESTINATIONTIME))
            
            elif checkForColor(Hindernisse.GREEN, 0, 1):    
                orders.append(Order(x=1920, y=2600,speed=0.5, brake=1,type=Order.DESTINATION,num=172))
                orders.append(Order(zielwinkel=90, speed=0.2, brake=1, type=Order.WINKEL))
                orders.append(Order(x=1880, y=3000, speed=0.2, timeDrive=2, type=Order.DESTINATIONTIME))
            
            elif checkForColor(Hindernisse.RED, 18, 24):
                orders.append(Order(x=1900, y=2200,speed=0.5, brake=1,type=Order.DESTINATION,num=173))
                orders.append(Order(zielwinkel=90, speed=0.2, brake=1, type=Order.WINKEL))
                orders.append(Order(x=1870, y=3000, speed=0.2, timeDrive=4.5, type=Order.DESTINATIONTIME))
            
            else:
                orders.append(Order(x=1970, y=2200, speed=0.5, brake=1,type=Order.DESTINATION,num=174))
                orders.append(Order(zielwinkel=90, speed=0.2, brake=1, type=Order.WINKEL))
                orders.append(Order(x=1870, y=3000, speed=0.2, timeDrive=4, type=Order.DESTINATIONTIME))
        
        
        
        
        
        
        
        
        else:                                                                                           # CCW Ausparken
            
            orders.append(Order(steer=90, dist=170, speed=0.2, brake=1, type=Order.KURVE,num=1))
            orders.append(Order(steer=0, dist=150, speed=0.2, brake=1, type=Order.KURVE,num=2))
            orders.append(Order(steer=-90, dist=170, speed=0.2, brake=1, type=Order.KURVE,num=3))
            if not waitCompleteOrders():
                return
            slam.repostionEnable = 1
            # orders.append(Order(steer=90, dist=55, speed=0.2, brake=1, type=Order.KURVE))
            # waitCompleteOrders()
            # time.sleep(1)
            # orders.append(Order(steer=-90, dist=30, speed=-0.2, brake=1, type=Order.KURVE))
            # orders.append(Order(steer=90, dist=120, speed=0.2, brake=1, type=Order.KURVE))
            # orders.append(Order(steer=-90, dist=170, speed=0.2, brake=1, type=Order.KURVE))
            
            speedScan = 0.5

            #orders.append(Order(x=2100, y=2500,speed=speedScan,brake=1,type=Order.DESTINATION))
            orders.append(Order(x=2400, y=2700,speed=speedScan,brake=1,type=Order.DESTINATION,num=4))
            
            
            orders.append(Order(zielwinkel=-90, speed=0.5, brake=1, type=Order.WINKEL,num=5))
            if not waitCompleteOrders():
                return
            time.sleep(0.5)
            orders.append(Order(type=Order.REPOSITION,num=6))
            orders.append(Order(toScan=[18, 19, 20, 21, 22, 23],type=Order.SCAN,num=7))                   #         Hindernisse 18-24 scannen OST
            time.sleep(0.5)
            if not waitCompleteOrders():
                return
            
            

            if checkForColor(Hindernisse.GREEN, 18, 24):
                #print("green")
                orders.append(Order(x=2177, y=2008, speed=speedScan, brake=1, type=Order.DESTINATION,num=8))
                orders.append(Order(x=2171, y=988, speed=speedScan, brake=1, type=Order.DESTINATION,num=9))
                orders.append(Order(x=2756, y=641, speed=speedScan, brake=1, type=Order.DESTINATION,num=10))
            elif checkForColor(Hindernisse.RED, 18, 24):
                #print("red")
                orders.append(Order(x=2790, y=2049,speed=speedScan,brake=1,type=Order.DESTINATION,num=11))
                orders.append(Order(x=2800, y=1100,speed=speedScan,brake=1,type=Order.DESTINATION,num=12))
                orders.append(Order(x=2765, y=616,speed=speedScan,brake=1,type=Order.DESTINATION,num=13))
            else:
                orders.append(Order(x=2500, y=1830,speed=speedScan,brake=1,type=Order.DESTINATION,num=14))
                if not waitCompleteOrders():
                    return
                time.sleep(0.5)
                orders.append(Order(toScan=[18, 19, 20, 21, 22, 23],type=Order.SCAN,num=15))           #         Hindernisse 18-24 scannen OST  2ter versuch
                time.sleep(0.5)
                if not waitCompleteOrders():
                    return
                if checkForColor(Hindernisse.GREEN, 18, 24):
                    #print("green")
                    orders.append(Order(x=2171, y=988, speed=speedScan, brake=1, type=Order.DESTINATION,num=17))
                    orders.append(Order(x=2756, y=641, speed=speedScan, brake=1, type=Order.DESTINATION,num=18))
                else:
                    #print("red")
                    orders.append(Order(x=2800, y=1000, speed=speedScan, brake=1, type=Order.DESTINATION,num=19))
                    orders.append(Order(x=2765, y=616,speed=speedScan,brake=1,type=Order.DESTINATION,num=20))
            
            orders.append(Order(zielwinkel=0, speed=0.5, brake=1, type=Order.WINKEL,num=21))
            if not waitCompleteOrders():
                return
            time.sleep(0.5)
            orders.append(Order(type=Order.REPOSITION))
            orders.append(Order(toScan=[12, 13, 14, 15, 16, 17],type=Order.SCAN,num=22))               #         Hindernisse 12-18 scannen   NORD
            time.sleep(0.5)
            if not waitCompleteOrders():
                return
            
            
            if checkForColor(Hindernisse.GREEN, 12, 18):
                #print("Green")
                orders.append(Order(x=2100, y=800, speed=speedScan, brake=1, type=Order.DESTINATION,num=23))
                orders.append(Order(x=900, y=800, speed=speedScan, brake=1, type=Order.DESTINATION,num=24))
                orders.append(Order(x=744, y=427,speed=speedScan,brake=1,type=Order.DESTINATION,num=25))
            elif checkForColor(Hindernisse.RED, 12, 18):
                #print("Red")
                orders.append(Order(x=2100, y=230,speed=speedScan,brake=1,type=Order.DESTINATION,num=26))
                orders.append(Order(x=900, y=200,speed=speedScan,brake=1,type=Order.DESTINATION,num=27))
                orders.append(Order(x=551, y=291,speed=speedScan,brake=1,type=Order.DESTINATION,num=28))
            else:
                orders.append(Order(x=750, y=500,speed=speedScan,brake=1,type=Order.DESTINATION,num=29))
                if not waitCompleteOrders():
                    return
                time.sleep(0.5)
                orders.append(Order(toScan=[12, 13, 14, 15, 16, 17],type=Order.SCAN,num=30))               #         Hindernisse 12-18 scannen   NORD  2ter versuch
                time.sleep(0.5)
                if not waitCompleteOrders():
                    return
                if checkForColor(Hindernisse.GREEN, 12, 18):
                    #print("green")
                    orders.append(Order(x=1000, y=800, speed=speedScan, brake=1, type=Order.DESTINATION,num=31))
                    orders.append(Order(x=744, y=427,speed=speedScan,brake=1, type=Order.DESTINATION,num=32))
                else:
                    #print("red")
                    orders.append(Order(x=1000, y=300, speed=speedScan, brake=1, type=Order.DESTINATION,num=33)) 
                    orders.append(Order(x=500, y=300,speed=speedScan,brake=1, type=Order.DESTINATION,num=34))
                
            orders.append(Order(zielwinkel=90, speed=0.5, brake=1, type=Order.WINKEL,num=35))
            if not waitCompleteOrders():
                return
            time.sleep(0.5)
            orders.append(Order(type=Order.REPOSITION,num=36))
            orders.append(Order(toScan=[6, 7, 8, 9, 10, 11],type=Order.SCAN,num=37))                           #         Hindernisse 6-12 scannen   WEST   
            time.sleep(0.5)
            if not waitCompleteOrders():
                return


            if checkForColor(Hindernisse.GREEN, 6, 12):
                #print("Green")
                orders.append(Order(x=800, y=1100,speed=speedScan,brake=1,type=Order.DESTINATION,num=38))
                orders.append(Order(x=800, y=2100,speed=speedScan,brake=1,type=Order.DESTINATION,num=39))
                orders.append(Order(x=350, y=2284,speed=speedScan,brake=1,type=Order.DESTINATION,num=40))
            elif checkForColor(Hindernisse.RED, 6, 12):
                #print("Red")
                orders.append(Order(x=230, y=1050,speed=speedScan,brake=1,type=Order.DESTINATION,num=42))
                orders.append(Order(x=200, y=2100,speed=speedScan,brake=1,type=Order.DESTINATION,num=43))
                orders.append(Order(x=350, y=2368,speed=speedScan,brake=1,type=Order.DESTINATION,num=44))
            else:
                orders.append(Order(x=500, y=1250,speed=speedScan,brake=1,type=Order.DESTINATION,num=45))
                if not waitCompleteOrders():
                    return
                time.sleep(0.5)
                orders.append(Order(toScan=[6, 7, 8, 9, 10, 11],type=Order.SCAN,num=46))                    #         Hindernisse 6-12 scannen  WEST  2ter versuch 
                time.sleep(0.5)
                if not waitCompleteOrders():
                    return
                if checkForColor(Hindernisse.GREEN, 6, 12):
                    #print("green")
                    orders.append(Order(x=821, y=2064,speed=speedScan,brake=1,type=Order.DESTINATION,num=48))
                    orders.append(Order(x=350, y=2284,speed=speedScan,brake=1, type=Order.DESTINATION,num=49))
                else:
                    #print("red")
                    orders.append(Order(x=150, y=2100, speed=speedScan, brake=1, type=Order.DESTINATION,num=50)) 
                    orders.append(Order(x=350, y=2370,speed=speedScan, brake=1,type=Order.DESTINATION,num=51))
            
            
            orders.append(Order(zielwinkel=180, speed=0.2, brake=1, type=Order.WINKEL,num=52))
            if not waitCompleteOrders():
                return
            time.sleep(0.5)

            orders.append(Order(type=Order.REPOSITION,num=53))
            orders.append(Order(toScan=[2, 3, 4, 5],type=Order.SCAN,num=54))                                #         Hindernisse 2-5 scannen   SÜD
            time.sleep(0.5)
            if not waitCompleteOrders():
                return

            speedi = 0.5
            
            for i in range(0,2):
                if checkForColor(Hindernisse.RED, 0, 6):
                    #print("Red")
                    orders.append(Order(x=1000, y=2770,speed=speedi,brake=0,type=Order.DESTINATION,num=56))
                    orders.append(Order(x=1400, y=2600,speed=speedi,brake=0,type=Order.DESTINATION,num=57))
                    orders.append(Order(x=2000, y=2600,speed=speedi,brake=0,type=Order.DESTINATION,num=58))
                else:
                    #print("Green")
                    orders.append(Order(x=1000, y=2200,speed=speedi,brake=0,type=Order.DESTINATION,num=59))
                    orders.append(Order(x=2000, y=2200,speed=speedi,brake=0,type=Order.DESTINATION,num=60))


                if checkForColor(Hindernisse.RED, 0, 6) and checkForColor(Hindernisse.GREEN, 18, 24):
                    #print("Red")
                    orders.append(Order(x=2200, y=2600,speed=speedi,brake=0,type=Order.DESTINATION,num=61))
                elif checkForColor(Hindernisse.GREEN, 0, 6) and checkForColor(Hindernisse.RED, 18, 24):
                    #print("Green")
                    orders.append(Order(x=2550, y=2500,speed=speedi,brake=0,type=Order.DESTINATION,num=62))


                if checkForColor(Hindernisse.RED, 18, 24):
                    #print("Red")
                    orders.append(Order(x=2700, y=2250,speed=speedi,brake=0,type=Order.DESTINATION,num=98))
                    orders.append(Order(x=2800, y=2000,speed=speedi,brake=0,type=Order.DESTINATION,num=63))
                    orders.append(Order(x=2800, y=1000,speed=speedi,brake=0,type=Order.DESTINATION,num=64))
                else:
                    #print("Green")
                    orders.append(Order(x=2200, y=2000,speed=speedi,brake=0,type=Order.DESTINATION,num=65))
                    orders.append(Order(x=2200, y=1000,speed=speedi,brake=0,type=Order.DESTINATION,num=66))


                if checkForColor(Hindernisse.RED, 18, 24) and checkForColor(Hindernisse.GREEN, 12, 18):
                    #print("Red")
                    orders.append(Order(x=2600, y=800,speed=speedi,brake=0,type=Order.DESTINATION,num=67))
                elif checkForColor(Hindernisse.GREEN, 18, 24) and checkForColor(Hindernisse.RED, 12, 18):
                    #print("Green")
                    orders.append(Order(x=2400, y=500,speed=speedi,brake=0,type=Order.DESTINATION,num=68))

                if checkForColor(Hindernisse.RED, 12, 18):
                    #print("Red")
                    orders.append(Order(x=2600, y=450,speed=speedi,brake=0,type=Order.DESTINATION,num=69))
                    orders.append(Order(x=2100, y=230,speed=speedi,brake=0,type=Order.DESTINATION,num=70))
                    orders.append(Order(x=900, y=200,speed=speedi,brake=0,type=Order.DESTINATION,num=71))
                else:
                    #print("Green")
                    orders.append(Order(x=2000, y=800,speed=speedi,brake=0,type=Order.DESTINATION,num=72))
                    orders.append(Order(x=900, y=800,speed=speedi,brake=0,type=Order.DESTINATION,num=73))


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
                    if i == 0:
                        if not waitCompleteOrders():
                            return
                        time.sleep(0.5)
                        orders.append(Order(angleCheckOverwrite=180,type=Order.REPOSITION,num=78))
                        if not waitCompleteOrders():
                            return
                else:
                    #print("Green")
                    orders.append(Order(x=800, y=1000,speed=speedi,brake=0,type=Order.DESTINATION,num=79))
                    orders.append(Order(x=800, y=2000,speed=speedi,brake=0,type=Order.DESTINATION,num=80))
                    if checkForColor(Hindernisse.GREEN, 0, 6):
                        orders.append(Order(x=800, y=2020,speed=speedScan,brake=1,type=Order.DESTINATION,num=81))
                        if not waitCompleteOrders():
                            return
                        time.sleep(0.5)
                        orders.append(Order(angleCheckOverwrite=180,type=Order.REPOSITION,num=82))
                        if not waitCompleteOrders():
                            return
                    
                if checkForColor(Hindernisse.RED, 6, 12) and checkForColor(Hindernisse.GREEN, 0, 6):
                    #print("Red")
                    orders.append(Order(x=400, y=2250,speed=speedi,brake=0,type=Order.DESTINATION,num=83))
                elif checkForColor(Hindernisse.GREEN, 6, 12) and checkForColor(Hindernisse.RED, 0, 6):
                    #print("Green")
                    orders.append(Order(x=600, y=2300,speed=speedi,brake=1,type=Order.DESTINATION,num=84))
                    if not waitCompleteOrders():
                        return
                    time.sleep(0.5)
                    orders.append(Order(angleCheckOverwrite=180,type=Order.REPOSITION,num=85))
                    if not waitCompleteOrders():
                        return
                elif checkForColor(Hindernisse.RED, 6, 12) and checkForColor(Hindernisse.RED, 0, 6):
                    orders.append(Order(x=200, y=2600,speed=speedi,brake=1,type=Order.DESTINATION,num=86))

            if checkForColor(Hindernisse.RED, 2, 6) and checkForColor(Hindernisse.GREEN, 6, 12):
                orders.append(Order(x=1000, y=2770,speed=0.5,brake=0,type=Order.DESTINATION,num=176))
                orders.append(Order(x=1400, y=2600,speed=0.5,brake=0,type=Order.DESTINATION,num=175))
                orders.append(Order(x=1760, y=2600, speed=0.5, brake=1,type=Order.DESTINATION,num=171))
                orders.append(Order(zielwinkel=90, speed=0.2, brake=1, type=Order.WINKEL))
                orders.append(Order(x=1870, y=3000, speed=0.2, timeDrive=2, type=Order.DESTINATIONTIME))
            
            elif checkForColor(Hindernisse.RED, 2, 6):
                orders.append(Order(x=700, y=2770,speed=0.5,brake=1,type=Order.DESTINATION,num=176))
                if not waitCompleteOrders():
                    return
                time.sleep(0.5)
                orders.append(Order(angleCheckOverwrite=0,type=Order.REPOSITION,num=78))
                if not waitCompleteOrders():
                    return    
                orders.append(Order(x=1000, y=2770,speed=0.5,brake=0,type=Order.DESTINATION,num=176))
                orders.append(Order(x=1400, y=2600,speed=0.5,brake=0,type=Order.DESTINATION,num=175))
                orders.append(Order(x=1760, y=2600, speed=0.5, brake=1,type=Order.DESTINATION,num=171))
                orders.append(Order(zielwinkel=90, speed=0.2, brake=1, type=Order.WINKEL))
                orders.append(Order(x=1860, y=3000, speed=0.2, timeDrive=2, type=Order.DESTINATIONTIME))
            
            elif checkForColor(Hindernisse.GREEN, 6, 12):
                orders.append(Order(x=1900, y=2200,speed=0.5, brake=1,type=Order.DESTINATION,num=173))
                orders.append(Order(zielwinkel=90, speed=0.2, brake=1, type=Order.WINKEL))
                orders.append(Order(x=1870, y=3000, speed=0.2, timeDrive=4.5, type=Order.DESTINATIONTIME))
            
            else:
                orders.append(Order(x=1970, y=2200, speed=0.5, brake=1,type=Order.DESTINATION,num=174))
                orders.append(Order(zielwinkel=90, speed=0.2, brake=1, type=Order.WINKEL))
                orders.append(Order(x=1870, y=3000, speed=0.2, timeDrive=4, type=Order.DESTINATIONTIME))


def printOrder():
    global orders
    if orders.__len__() == 0:
        print("No Order",end="")
        slam.logger.warn('     -> No Order')
        return
    if orders[0].type == Order.DESTINATION:
        print("Destination: ", orders[0].x, orders[0].y,end="")
        slam.logger.warn('%i    -> Destination  %i  %i',orders[0].num, orders[0].x, orders[0].y)
    elif orders[0].type == Order.KURVE:
        print("KURVE: ", orders[0].dist, orders[0].steer,end="")
        slam.logger.warn('%i    -> KURVE  %i  %i',orders[0].num, orders[0].dist, orders[0].steer)
    elif orders[0].type == Order.SCAN:
        print("SCAN: ", orders[0].toScan,end="")
        slam.logger.warn('%i    -> SCAN',orders[0].num)
    elif orders[0].type == Order.WINKEL:
        print("WINKEL: ", orders[0].zielwinkel,end="")
        slam.logger.warn('%i    -> WINKEL  %i',orders[0].num, orders[0].zielwinkel)
    elif orders[0].type == Order.REPOSITION:
        print("REPOSITION: ",end="")
        slam.logger.warn('%i    -> REPOSITION',orders[0].num, orders[0].zielwi)
    elif orders[0].type == Order.TIME:
        print("TIME: ", orders[0].timeDrive,end="")
        slam.logger.warn('%i    -> TIME  %i',orders[0].num, orders[0].timeDrive)

def nextOrder():
    global orders
    # printOrder()
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
    startZeit = time.perf_counter_ns()
    global orders

    while running3:
        slam.update()
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
            if orders[0].type == Order.DESTINATION:
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
                slam.hindernisseErkennung(slam.scan,orders[0].toScan, camera)
                takePicture = True
                sem.release()
                nextOrder()
            elif orders[0].type == Order.WINKEL:
                if driveBase.driveToWinkel(orders[0].zielwinkel,orders[0].speed,orders[0].brake):
                    nextOrder()
            elif orders[0].type == Order.REPOSITION:
                sem.acquire()
                slam.reposition(orders[0].angleCheckOverwrite)
                takePicture = True
                sem.release()
                nextOrder()
            elif orders[0].type == Order.TIME:
                if driveBase.driveTime(orders[0].timeDrive,orders[0].speed,startTime):
                    nextOrder()
            elif orders[0].type == Order.DESTINATIONTIME:
                if driveBase.driveToTime(orders[0].x,orders[0].y,orders[0].speed,orders[0].timeDrive,startTime):
                    nextOrder()
        else:
            setServoAngle(kit,90)
            kit.servo[3].angle = 90
        
        variable = ((time.perf_counter_ns() - startZeit) / 1000 / 1000)
        if 0.01 - (variable / 1000) > 0:
            time.sleep(0.01 - (variable / 1000))
            ausgabe = 0
        else:
            ausgabe = 1
        # startZeit+= 1000*1000*10
        startZeit = time.perf_counter_ns()
        # if ausgabe == 1:
        #     print("time: ", variable)




if __name__ == "__main__":
    main()

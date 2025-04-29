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
import gpiozero

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
kit.servo[0].set_pulse_width_range(1100, 2100)
kit.servo[3].set_pulse_width_range(1000, 2000)
running2 = True
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
    placing = 0
    playmat = Playmat(1, wx, wy)
    os.environ['SDL_VIDEO_WINDOW_POS'] = "%d,%d" % (0,0)
    #screen = pygame.display.set_mode((wx * playmat.matScale + 300, wy * playmat.matScale), pygame.RESIZABLE)
    screen = pygame.display.set_mode((1920,1000), pygame.RESIZABLE)
    
    pygame.display.set_caption("WroONator4000")
    clock = pygame.time.Clock()
    global running2
    last_val = 0xFFFF
    clThread = threading.Thread(target=controlLoop, args=(robot, camera, playmat))
    clThread.start()
    cmdlThread = threading.Thread(target=commandLoop, args=(slam, ))
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
                if event.key == pygame.K_SPACE:
                    running = False
                    running2 = False
                    time.sleep(0.1)
                    kit.servo[0].angle = 90
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
                if event.key == pygame.K_c:
                    orders.clear()

            if event.type == pygame.QUIT:
                running = False
                running2 = False
                time.sleep(0.1)
                kit.servo[0].angle = 90
                kit.servo[3].angle = 90
                slam.lidar.disconnect()
                
        keys = pygame.key.get_pressed()

        sem.acquire()
        playmat.draw(screen, info, camera, robot)
        robot.draw(screen, playmat.matScale, slam.scan, slam)
        if info == 1:
            playmat.Infos(screen, robot, slam, playmat.matScale, startTime, time)
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
    def __init__(self,speed=0,brake=0,type=0,x=0,y=0,steer=0,dist=0,timeDrive=0,toScan=[],zielwinkel=0,angleCheckOverwrite=1000):
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


def waitCompleteOrders():
    global running2
    while orders.__len__() > 0 and running2:
        time.sleep(0.01)
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
    # print("Press v to start")
    # while vPressed <= 0:
    #     time.sleep(0.1)
    while button.is_pressed:
        time.sleep(0.1)
    time.sleep(1.2)
    startTime = time.time()
    
    if slam.eventType == slam.ER:
        speedi = 0.75
            
        if slam.direction == slam.CW:
            orders.append(Order(x=450, y=2500,speed=speedi,brake=0,type=Order.DESTINATION))
            
            for i in range(0,3):
                if i >= 1:
                    orders.append(Order(x=450, y=2700,speed=speedi,brake=0,type=Order.DESTINATION))
                orders.append(Order(x=300, y=450,speed=speedi,brake=0,type=Order.DESTINATION))
                orders.append(Order(x=2550, y=300,speed=speedi,brake=0,type=Order.DESTINATION))
                orders.append(Order(x=2700, y=2550,speed=speedi,brake=0,type=Order.DESTINATION))
            
            orders.append(Order(x=1500, y=2700,speed=speedi,brake=1,type=Order.DESTINATION))
        else:
            orders.append(Order(x=2550, y=2500,speed=speedi,brake=0,type=Order.DESTINATION))
            
            for i in range(0,3):
                if i >= 1:
                    orders.append(Order(x=2550, y=2700,speed=speedi,brake=0,type=Order.DESTINATION))
                orders.append(Order(x=2700, y=450,speed=speedi,brake=0,type=Order.DESTINATION))
                orders.append(Order(x=450, y=300,speed=speedi,brake=0,type=Order.DESTINATION))
                orders.append(Order(x=300, y=2550,speed=speedi,brake=0,type=Order.DESTINATION))
            
            orders.append(Order(x=1500, y=2700,speed=speedi,brake=1,type=Order.DESTINATION))
    
    
    
    
    
    else:
        if slam.direction == slam.CW:
            orders.append(Order(steer=-90, dist=170, speed=0.2, brake=1, type=Order.KURVE))
            orders.append(Order(steer=0, dist=150, speed=0.2, brake=1, type=Order.KURVE))
            orders.append(Order(steer=90, dist=170, speed=0.2, brake=1, type=Order.KURVE))
            waitCompleteOrders()
            time.sleep(0.5)
            orders.append(Order(toScan=[4, 5],type=Order.SCAN))
            time.sleep(0.5)
            waitCompleteOrders()
            
            
            speedScan = 0.5

            if checkForColor(Hindernisse.RED, 0, 6):
                #print("Red")
                orders.append(Order(x=1050, y=2207,speed=speedScan,brake=1,type=Order.DESTINATION))
                orders.append(Order(x=734, y=2607,speed=speedScan,brake=1,type=Order.DESTINATION))
            else:
                #print("Green")
                orders.append(Order(x=1041, y=2839,speed=speedScan,brake=1,type=Order.DESTINATION))
                orders.append(Order(x=604, y=2762,speed=speedScan,brake=1,type=Order.DESTINATION))
            
            
            orders.append(Order(zielwinkel=-90, speed=0.5, brake=1, type=Order.WINKEL))
            waitCompleteOrders()
            time.sleep(0.5)
            orders.append(Order(type=Order.REPOSITION))
            orders.append(Order(toScan=[6, 7, 8, 9, 10, 11],type=Order.SCAN))
            time.sleep(0.5)
            waitCompleteOrders()
            

            if checkForColor(Hindernisse.RED, 6, 12):
                #print("red")
                orders.append(Order(x=823, y=2008, speed=speedScan, brake=1, type=Order.DESTINATION))
                orders.append(Order(x=829, y=988, speed=speedScan, brake=1, type=Order.DESTINATION))
                orders.append(Order(x=244, y=641, speed=speedScan, brake=1, type=Order.DESTINATION))
            elif checkForColor(Hindernisse.GREEN, 6, 12):
                #print("green")
                orders.append(Order(x=182, y=2049,speed=speedScan,brake=1,type=Order.DESTINATION))
                orders.append(Order(x=235, y=616,speed=speedScan,brake=1,type=Order.DESTINATION))
            else:
                orders.append(Order(x=500, y=1830,speed=speedScan,brake=1,type=Order.DESTINATION))
                waitCompleteOrders()
                time.sleep(0.5)
                orders.append(Order(toScan=[6, 7, 8, 9, 10, 11],type=Order.SCAN))
                time.sleep(0.5)
                waitCompleteOrders()
                if checkForColor(Hindernisse.RED, 6, 12):
                    #print("red")
                    orders.append(Order(x=829, y=988, speed=speedScan, brake=1, type=Order.DESTINATION))
                    orders.append(Order(x=244, y=641, speed=speedScan, brake=1, type=Order.DESTINATION))
                else:
                    #print("green")
                    orders.append(Order(x=200, y=1000, speed=speedScan, brake=1, type=Order.DESTINATION))
                    orders.append(Order(x=235, y=616,speed=speedScan,brake=1,type=Order.DESTINATION))
            
            orders.append(Order(zielwinkel=180, speed=0.5, brake=1, type=Order.WINKEL))
            waitCompleteOrders()
            time.sleep(0.5)
            orders.append(Order(type=Order.REPOSITION))
            orders.append(Order(toScan=[12, 13, 14, 15, 16, 17],type=Order.SCAN))
            time.sleep(0.5)
            waitCompleteOrders()
            
            
            if checkForColor(Hindernisse.RED, 12, 18):
                #print("Red")
                orders.append(Order(x=1050, y=861, speed=speedScan, brake=1, type=Order.DESTINATION))
                orders.append(Order(x=2000, y=750, speed=speedScan, brake=1, type=Order.DESTINATION))
                orders.append(Order(x=2256, y=427,speed=speedScan,brake=1,type=Order.DESTINATION))
            elif checkForColor(Hindernisse.GREEN, 12, 18):
                #print("Green")
                orders.append(Order(x=1054, y=229,speed=speedScan,brake=1,type=Order.DESTINATION))
                orders.append(Order(x=2449, y=291,speed=speedScan,brake=1,type=Order.DESTINATION))
            else:
                orders.append(Order(x=1250, y=500,speed=speedScan,brake=1,type=Order.DESTINATION))
                waitCompleteOrders()
                time.sleep(0.5)
                orders.append(Order(toScan=[12, 13, 14, 15, 16, 17],type=Order.SCAN))
                time.sleep(0.5)
                waitCompleteOrders()
                if checkForColor(Hindernisse.RED, 12, 18):
                    #print("red")
                    orders.append(Order(x=2000, y=750, speed=speedScan, brake=1, type=Order.DESTINATION))
                    orders.append(Order(x=2256, y=427,speed=speedScan,brake=1, type=Order.DESTINATION))
                else:
                    #print("green")
                    orders.append(Order(x=2000, y=300, speed=speedScan, brake=1, type=Order.DESTINATION)) 
                    orders.append(Order(x=2500, y=300,speed=speedScan,brake=1, type=Order.DESTINATION))
                
            orders.append(Order(zielwinkel=90, speed=0.5, brake=1, type=Order.WINKEL))
            waitCompleteOrders()
            time.sleep(0.5)
            orders.append(Order(type=Order.REPOSITION))
            orders.append(Order(toScan=[18, 19, 20, 21, 22, 23],type=Order.SCAN))
            time.sleep(0.5)
            waitCompleteOrders()


            if checkForColor(Hindernisse.RED, 18, 24):
                #print("Red")
                orders.append(Order(x=2185, y=1054,speed=speedScan,brake=1,type=Order.DESTINATION))
                orders.append(Order(x=2179, y=2064,speed=speedScan,brake=1,type=Order.DESTINATION))
                orders.append(Order(x=2650, y=2284,speed=speedScan,brake=1,type=Order.DESTINATION))
            elif checkForColor(Hindernisse.GREEN, 18, 24):
                #print("Green")
                orders.append(Order(x=2842, y=1054,speed=speedScan,brake=1,type=Order.DESTINATION))
                orders.append(Order(x=2650, y=2368,speed=speedScan,brake=1,type=Order.DESTINATION))
            else:
                orders.append(Order(x=2500, y=1250,speed=speedScan,brake=1,type=Order.DESTINATION))
                waitCompleteOrders()
                time.sleep(0.5)
                orders.append(Order(toScan=[18, 19, 20, 21, 22, 23],type=Order.SCAN))
                time.sleep(0.5)
                waitCompleteOrders()
                if checkForColor(Hindernisse.RED, 18, 24):
                    #print("red")
                    orders.append(Order(x=2179, y=2064,speed=speedScan,brake=1,type=Order.DESTINATION))
                    orders.append(Order(x=2650, y=2284,speed=speedScan,brake=1,type=Order.DESTINATION))
                else:
                    #print("green")
                    orders.append(Order(x=2850, y=2100, speed=speedScan, brake=1, type=Order.DESTINATION)) 
                    orders.append(Order(x=2650, y=2370,speed=speedScan, brake=1,type=Order.DESTINATION))
            
            
            orders.append(Order(zielwinkel=0, speed=0.5, brake=1, type=Order.WINKEL))
            waitCompleteOrders()
            time.sleep(0.5)
            orders.append(Order(type=Order.REPOSITION))
            orders.append(Order(toScan=[0, 1, 4, 5],type=Order.SCAN))
            time.sleep(0.5)
            waitCompleteOrders()


            # while vPressed <= 0:
            #     time.sleep(0.1)



            speedi = 0.75
            for i in range(0,2):
                if checkForColor(Hindernisse.GREEN, 0, 6):
                    #print("Green")
                    orders.append(Order(x=2100, y=2600,speed=speedi,brake=0,type=Order.DESTINATION))
                    orders.append(Order(x=1600, y=2600,speed=speedi,brake=0,type=Order.DESTINATION))
                    orders.append(Order(x=1000, y=2800,speed=speedi,brake=0,type=Order.DESTINATION))
                else:
                    #print("Red")
                    orders.append(Order(x=2000, y=2200,speed=speedi,brake=0,type=Order.DESTINATION))
                    orders.append(Order(x=1000, y=2200,speed=speedi,brake=0,type=Order.DESTINATION))

                if checkForColor(Hindernisse.GREEN, 0, 6) and checkForColor(Hindernisse.RED, 6, 12):
                    #print("Green")
                    orders.append(Order(x=800, y=2600,speed=speedi,brake=0,type=Order.DESTINATION))
                elif checkForColor(Hindernisse.RED, 0, 6) and checkForColor(Hindernisse.GREEN, 6, 12):
                    #print("Red")
                    orders.append(Order(x=500, y=2400,speed=speedi,brake=0,type=Order.DESTINATION))

                if checkForColor(Hindernisse.GREEN, 6, 12):
                    #print("Green")
                    orders.append(Order(x=200, y=2100,speed=speedi,brake=0,type=Order.DESTINATION))
                    orders.append(Order(x=200, y=1000,speed=speedi,brake=0,type=Order.DESTINATION))
                else:
                    #print("Red")
                    orders.append(Order(x=800, y=2000,speed=speedi,brake=0,type=Order.DESTINATION))
                    orders.append(Order(x=800, y=1000,speed=speedi,brake=0,type=Order.DESTINATION))


                if checkForColor(Hindernisse.GREEN, 6, 12) and checkForColor(Hindernisse.RED, 12, 18):
                    #print("Green")
                    orders.append(Order(x=400, y=800,speed=speedi,brake=0,type=Order.DESTINATION))
                elif checkForColor(Hindernisse.RED, 6, 12) and checkForColor(Hindernisse.GREEN, 12, 18):
                    #print("Red")
                    orders.append(Order(x=600, y=500,speed=speedi,brake=0,type=Order.DESTINATION))

                if checkForColor(Hindernisse.GREEN, 12, 18):
                    #print("Green")
                    orders.append(Order(x=900, y=200,speed=speedi,brake=0,type=Order.DESTINATION))
                    orders.append(Order(x=2100, y=200,speed=speedi,brake=0,type=Order.DESTINATION))
                else:
                    #print("Red")
                    orders.append(Order(x=1000, y=800,speed=speedi,brake=0,type=Order.DESTINATION))
                    orders.append(Order(x=2100, y=800,speed=speedi,brake=0,type=Order.DESTINATION))


                if checkForColor(Hindernisse.GREEN, 12, 18) and checkForColor(Hindernisse.RED, 18, 24):
                    #print("Green")
                    orders.append(Order(x=2200, y=400,speed=speedi,brake=0,type=Order.DESTINATION))
                elif checkForColor(Hindernisse.RED, 12, 18) and checkForColor(Hindernisse.GREEN, 18, 24):
                    #print("Red")
                    orders.append(Order(x=2500, y=600,speed=speedi,brake=0,type=Order.DESTINATION))

                if checkForColor(Hindernisse.GREEN, 18, 24):
                    #print("Green")
                    orders.append(Order(x=2800, y=900,speed=speedi,brake=0,type=Order.DESTINATION))
                    orders.append(Order(x=2800, y=2000,speed=speedi,brake=1,type=Order.DESTINATION))
                    waitCompleteOrders()
                    time.sleep(0.5)
                    orders.append(Order(angleCheckOverwrite=0,type=Order.REPOSITION))
                    waitCompleteOrders()
                    # while vPressed <= 0:
                    #     time.sleep(0.1)
                else:
                    #print("Red")
                    orders.append(Order(x=2200, y=1000,speed=speedi,brake=0,type=Order.DESTINATION))
                    orders.append(Order(x=2200, y=2000,speed=speedi,brake=0,type=Order.DESTINATION))
                    if checkForColor(Hindernisse.RED, 0, 6):
                        orders.append(Order(x=2200, y=2020,speed=speedScan,brake=1,type=Order.DESTINATION))
                        waitCompleteOrders()
                        time.sleep(0.5)
                        orders.append(Order(angleCheckOverwrite=0,type=Order.REPOSITION))
                        waitCompleteOrders()

                if checkForColor(Hindernisse.GREEN, 18, 24) and checkForColor(Hindernisse.RED, 0, 6):
                    #print("Green")
                    orders.append(Order(x=2600, y=2250,speed=speedi,brake=0,type=Order.DESTINATION))
                elif checkForColor(Hindernisse.RED, 18, 24) and checkForColor(Hindernisse.GREEN, 0, 6):
                    #print("Red")
                    orders.append(Order(x=2400, y=2300,speed=speedi,brake=1,type=Order.DESTINATION))
                    waitCompleteOrders()
                    time.sleep(0.5)
                    orders.append(Order(angleCheckOverwrite=0,type=Order.REPOSITION))
                    waitCompleteOrders()

            if checkForColor(Hindernisse.GREEN, 0, 1) and checkForColor(Hindernisse.RED, 18, 24):
                orders.append(Order(x=1980, y=2600,speed=0.5, brake=1,type=Order.DESTINATION))
                orders.append(Order(zielwinkel=90, speed=0.2, brake=1, type=Order.WINKEL))
                orders.append(Order(timeDrive=1, speed=0.2, type=Order.TIME))
            
            elif checkForColor(Hindernisse.GREEN, 0, 1):    
                orders.append(Order(x=1940, y=2600,speed=0.5, brake=1,type=Order.DESTINATION))
                orders.append(Order(zielwinkel=90, speed=0.2, brake=1, type=Order.WINKEL))
                orders.append(Order(timeDrive=1, speed=0.2, type=Order.TIME))
            
            elif checkForColor(Hindernisse.RED, 18, 24):
                orders.append(Order(x=1900, y=2200,speed=0.5, brake=1,type=Order.DESTINATION))
                orders.append(Order(zielwinkel=90, speed=0.2, brake=1, type=Order.WINKEL))
                orders.append(Order(timeDrive=4, speed=0.2, type=Order.TIME))
            
            else:
                orders.append(Order(x=1950, y=2200,speed=0.5, brake=1,type=Order.DESTINATION))
                orders.append(Order(zielwinkel=90, speed=0.2, brake=1, type=Order.WINKEL))
                orders.append(Order(timeDrive=4, speed=0.2, type=Order.TIME))
        
        
        
        
        
        
        
        
        else:       # CCW Ausparken
            orders.append(Order(steer=90, dist=55, speed=0.2, brake=1, type=Order.KURVE))
            waitCompleteOrders()
            time.sleep(1)
            orders.append(Order(steer=-90, dist=30, speed=-0.2, brake=1, type=Order.KURVE))
            orders.append(Order(steer=90, dist=120, speed=0.2, brake=1, type=Order.KURVE))
            orders.append(Order(steer=-90, dist=170, speed=0.2, brake=1, type=Order.KURVE))
            
            speedScan = 0.5

            #orders.append(Order(x=2100, y=2500,speed=speedScan,brake=1,type=Order.DESTINATION))
            orders.append(Order(x=2400, y=2700,speed=speedScan,brake=1,type=Order.DESTINATION))
            
            
            orders.append(Order(zielwinkel=-90, speed=0.5, brake=1, type=Order.WINKEL))
            waitCompleteOrders()
            time.sleep(0.5)
            orders.append(Order(type=Order.REPOSITION))
            orders.append(Order(toScan=[18, 19, 20, 21, 22, 23],type=Order.SCAN))
            time.sleep(0.5)
            waitCompleteOrders()
            

            if checkForColor(Hindernisse.GREEN, 18, 24):
                #print("green")
                orders.append(Order(x=2177, y=2008, speed=speedScan, brake=1, type=Order.DESTINATION))
                orders.append(Order(x=2171, y=988, speed=speedScan, brake=1, type=Order.DESTINATION))
                orders.append(Order(x=2756, y=641, speed=speedScan, brake=1, type=Order.DESTINATION))
            elif checkForColor(Hindernisse.RED, 18, 24):
                #print("red")
                orders.append(Order(x=2818, y=2049,speed=speedScan,brake=1,type=Order.DESTINATION))
                orders.append(Order(x=2800, y=1100,speed=speedScan,brake=1,type=Order.DESTINATION))
                orders.append(Order(x=2765, y=616,speed=speedScan,brake=1,type=Order.DESTINATION))
            else:
                orders.append(Order(x=2500, y=1830,speed=speedScan,brake=1,type=Order.DESTINATION))
                waitCompleteOrders()
                time.sleep(0.5)
                orders.append(Order(toScan=[18, 19, 20, 21, 22, 23],type=Order.SCAN))
                time.sleep(0.5)
                waitCompleteOrders()
                if checkForColor(Hindernisse.GREEN, 18, 24):
                    #print("green")
                    orders.append(Order(x=2171, y=988, speed=speedScan, brake=1, type=Order.DESTINATION))
                    orders.append(Order(x=2756, y=641, speed=speedScan, brake=1, type=Order.DESTINATION))
                else:
                    #print("red")
                    orders.append(Order(x=2800, y=1000, speed=speedScan, brake=1, type=Order.DESTINATION))
                    orders.append(Order(x=2765, y=616,speed=speedScan,brake=1,type=Order.DESTINATION))
            
            orders.append(Order(zielwinkel=0, speed=0.5, brake=1, type=Order.WINKEL))
            waitCompleteOrders()
            time.sleep(0.5)
            orders.append(Order(type=Order.REPOSITION))
            orders.append(Order(toScan=[12, 13, 14, 15, 16, 17],type=Order.SCAN))
            time.sleep(0.5)
            waitCompleteOrders()
            
            
            if checkForColor(Hindernisse.GREEN, 12, 18):
                #print("Green")
                orders.append(Order(x=2100, y=800, speed=speedScan, brake=1, type=Order.DESTINATION))
                orders.append(Order(x=900, y=800, speed=speedScan, brake=1, type=Order.DESTINATION))
                orders.append(Order(x=744, y=427,speed=speedScan,brake=1,type=Order.DESTINATION))
            elif checkForColor(Hindernisse.RED, 12, 18):
                #print("Red")
                orders.append(Order(x=2100, y=200,speed=speedScan,brake=1,type=Order.DESTINATION))
                orders.append(Order(x=900, y=200,speed=speedScan,brake=1,type=Order.DESTINATION))
                orders.append(Order(x=551, y=291,speed=speedScan,brake=1,type=Order.DESTINATION))
            else:
                orders.append(Order(x=750, y=500,speed=speedScan,brake=1,type=Order.DESTINATION))
                waitCompleteOrders()
                time.sleep(0.5)
                orders.append(Order(toScan=[12, 13, 14, 15, 16, 17],type=Order.SCAN))
                time.sleep(0.5)
                waitCompleteOrders()
                if checkForColor(Hindernisse.GREEN, 12, 18):
                    #print("green")
                    orders.append(Order(x=1000, y=800, speed=speedScan, brake=1, type=Order.DESTINATION))
                    orders.append(Order(x=744, y=427,speed=speedScan,brake=1, type=Order.DESTINATION))
                else:
                    #print("red")
                    orders.append(Order(x=1000, y=300, speed=speedScan, brake=1, type=Order.DESTINATION)) 
                    orders.append(Order(x=500, y=300,speed=speedScan,brake=1, type=Order.DESTINATION))
                
            orders.append(Order(zielwinkel=90, speed=0.5, brake=1, type=Order.WINKEL))
            waitCompleteOrders()
            time.sleep(0.5)
            orders.append(Order(type=Order.REPOSITION))
            orders.append(Order(toScan=[6, 7, 8, 9, 10, 11],type=Order.SCAN))
            time.sleep(0.5)
            waitCompleteOrders()


            if checkForColor(Hindernisse.GREEN, 6, 12):
                #print("Green")
                orders.append(Order(x=800, y=1100,speed=speedScan,brake=1,type=Order.DESTINATION))
                orders.append(Order(x=800, y=2100,speed=speedScan,brake=1,type=Order.DESTINATION))
                orders.append(Order(x=350, y=2284,speed=speedScan,brake=1,type=Order.DESTINATION))
            elif checkForColor(Hindernisse.RED, 6, 12):
                #print("Red")
                orders.append(Order(x=200, y=1050,speed=speedScan,brake=1,type=Order.DESTINATION))
                orders.append(Order(x=200, y=2100,speed=speedScan,brake=1,type=Order.DESTINATION))
                orders.append(Order(x=350, y=2368,speed=speedScan,brake=1,type=Order.DESTINATION))
            else:
                orders.append(Order(x=500, y=1250,speed=speedScan,brake=1,type=Order.DESTINATION))
                waitCompleteOrders()
                time.sleep(0.5)
                orders.append(Order(toScan=[6, 7, 8, 9, 10, 11],type=Order.SCAN))
                time.sleep(0.5)
                waitCompleteOrders()
                if checkForColor(Hindernisse.GREEN, 6, 12):
                    #print("green")
                    orders.append(Order(x=821, y=2064,speed=speedScan,brake=1,type=Order.DESTINATION))
                    orders.append(Order(x=350, y=2284,speed=speedScan,brake=1, type=Order.DESTINATION))
                else:
                    #print("red")
                    orders.append(Order(x=150, y=2100, speed=speedScan, brake=1, type=Order.DESTINATION)) 
                    orders.append(Order(x=350, y=2370,speed=speedScan, brake=1,type=Order.DESTINATION))
            
            
            orders.append(Order(zielwinkel=180, speed=0.5, brake=1, type=Order.WINKEL))
            waitCompleteOrders()
            time.sleep(0.5)
            orders.append(Order(type=Order.REPOSITION))
            orders.append(Order(toScan=[2, 3, 4, 5],type=Order.SCAN))
            time.sleep(0.5)
            waitCompleteOrders()
            
            
            
            
            
            speedi = 0.5
            
            for i in range(0,2):
                if checkForColor(Hindernisse.RED, 0, 6):
                    #print("Red")
                    orders.append(Order(x=1000, y=2800,speed=speedi,brake=0,type=Order.DESTINATION))
                    orders.append(Order(x=1400, y=2600,speed=speedi,brake=0,type=Order.DESTINATION))
                    orders.append(Order(x=2000, y=2600,speed=speedi,brake=0,type=Order.DESTINATION))
                else:
                    #print("Green")
                    orders.append(Order(x=1000, y=2200,speed=speedi,brake=0,type=Order.DESTINATION))
                    orders.append(Order(x=2000, y=2200,speed=speedi,brake=0,type=Order.DESTINATION))

                if checkForColor(Hindernisse.RED, 0, 6) and checkForColor(Hindernisse.GREEN, 6, 12):
                    #print("Red")
                    orders.append(Order(x=2200, y=2600,speed=speedi,brake=0,type=Order.DESTINATION))
                elif checkForColor(Hindernisse.GREEN, 0, 6) and checkForColor(Hindernisse.RED, 6, 12):
                    #print("Green")
                    orders.append(Order(x=2500, y=2400,speed=speedi,brake=0,type=Order.DESTINATION))

                if checkForColor(Hindernisse.RED, 6, 12):
                    #print("Red")
                    orders.append(Order(x=2800, y=2100,speed=speedi,brake=0,type=Order.DESTINATION))
                    orders.append(Order(x=2800, y=1000,speed=speedi,brake=0,type=Order.DESTINATION))
                else:
                    #print("Green")
                    orders.append(Order(x=2200, y=2000,speed=speedi,brake=0,type=Order.DESTINATION))
                    orders.append(Order(x=2200, y=1000,speed=speedi,brake=0,type=Order.DESTINATION))


                if checkForColor(Hindernisse.RED, 6, 12) and checkForColor(Hindernisse.GREEN, 12, 18):
                    #print("Red")
                    orders.append(Order(x=2600, y=800,speed=speedi,brake=0,type=Order.DESTINATION))
                elif checkForColor(Hindernisse.GREEN, 6, 12) and checkForColor(Hindernisse.RED, 12, 18):
                    #print("Green")
                    orders.append(Order(x=2400, y=500,speed=speedi,brake=0,type=Order.DESTINATION))

                if checkForColor(Hindernisse.RED, 12, 18):
                    #print("Red")
                    orders.append(Order(x=2100, y=200,speed=speedi,brake=0,type=Order.DESTINATION))
                    orders.append(Order(x=900, y=200,speed=speedi,brake=0,type=Order.DESTINATION))
                else:
                    #print("Green")
                    orders.append(Order(x=2000, y=800,speed=speedi,brake=0,type=Order.DESTINATION))
                    orders.append(Order(x=900, y=800,speed=speedi,brake=0,type=Order.DESTINATION))


                if checkForColor(Hindernisse.RED, 12, 18) and checkForColor(Hindernisse.GREEN, 18, 24):
                    #print("Red")
                    orders.append(Order(x=800, y=400,speed=speedi,brake=0,type=Order.DESTINATION))
                elif checkForColor(Hindernisse.GREEN, 12, 18) and checkForColor(Hindernisse.RED, 18, 24):
                    #print("Green")
                    orders.append(Order(x=500, y=600,speed=speedi,brake=0,type=Order.DESTINATION))

                if checkForColor(Hindernisse.RED, 18, 24):
                    #print("Red")
                    orders.append(Order(x=200, y=900,speed=speedi,brake=0,type=Order.DESTINATION))
                    orders.append(Order(x=200, y=2000,speed=speedi,brake=1,type=Order.DESTINATION))
                    waitCompleteOrders()
                    time.sleep(0.5)
                    orders.append(Order(angleCheckOverwrite=0,type=Order.REPOSITION))
                    waitCompleteOrders()
                    # while vPressed <= 0:
                    #     time.sleep(0.1)
                else:
                    #print("Green")
                    orders.append(Order(x=800, y=1000,speed=speedi,brake=0,type=Order.DESTINATION))
                    orders.append(Order(x=800, y=2000,speed=speedi,brake=0,type=Order.DESTINATION))
                    if checkForColor(Hindernisse.GREEN, 0, 6):
                        orders.append(Order(x=800, y=2020,speed=speedScan,brake=1,type=Order.DESTINATION))
                        waitCompleteOrders()
                        time.sleep(0.5)
                        orders.append(Order(angleCheckOverwrite=0,type=Order.REPOSITION))
                        waitCompleteOrders()

                if checkForColor(Hindernisse.RED, 18, 24) and checkForColor(Hindernisse.GREEN, 0, 6):
                    #print("Red")
                    orders.append(Order(x=400, y=2250,speed=speedi,brake=0,type=Order.DESTINATION))
                elif checkForColor(Hindernisse.GREEN, 18, 24) and checkForColor(Hindernisse.RED, 0, 6):
                    #print("Green")
                    orders.append(Order(x=600, y=2300,speed=speedi,brake=1,type=Order.DESTINATION))
                    waitCompleteOrders()
                    time.sleep(0.5)
                    orders.append(Order(angleCheckOverwrite=0,type=Order.REPOSITION))
                    waitCompleteOrders()

            if checkForColor(Hindernisse.RED, 0, 1) and checkForColor(Hindernisse.GREEN, 18, 24):
                orders.append(Order(x=1020, y=2600,speed=0.5, brake=1,type=Order.DESTINATION))
                orders.append(Order(zielwinkel=90, speed=0.2, brake=1, type=Order.WINKEL))
                orders.append(Order(timeDrive=1, speed=0.2, type=Order.TIME))
            
            elif checkForColor(Hindernisse.RED, 0, 1):    
                orders.append(Order(x=1060, y=2600,speed=0.5, brake=1,type=Order.DESTINATION))
                orders.append(Order(zielwinkel=90, speed=0.2, brake=1, type=Order.WINKEL))
                orders.append(Order(timeDrive=1, speed=0.2, type=Order.TIME))
            
            elif checkForColor(Hindernisse.GREEN, 18, 24):
                orders.append(Order(x=1100, y=2200,speed=0.5, brake=1,type=Order.DESTINATION))
                orders.append(Order(zielwinkel=90, speed=0.2, brake=1, type=Order.WINKEL))
                orders.append(Order(timeDrive=4, speed=0.2, type=Order.TIME))
            
            else:
                orders.append(Order(x=1050, y=2200,speed=0.5, brake=1,type=Order.DESTINATION))
                orders.append(Order(zielwinkel=90, speed=0.2, brake=1, type=Order.WINKEL))
                orders.append(Order(timeDrive=4, speed=0.2, type=Order.TIME))


def controlLoop(robot, camera, playmat):
    driveBase = DriveBase(slam, kit)
    global running2
    global takePicture
    global sem
    global startTime
    kit.servo[0].angle = 90
    kit.servo[3].angle = 90
    
    slam.update()
    slam.startpostionsetzen()
    startZeit = 0
    ausgabe = 0
    startZeit = time.perf_counter_ns()
    global orders

    while running2:
        slam.update()
        if orders.__len__() > 0:
            robot.circlexList.clear()
            robot.circleyList.clear()
            for i in range(len(orders)):
                if orders[i].type == Order.DESTINATION:
                    robot.circlexList.append(orders[i].x)
                    robot.circleyList.append(orders[i].y)
            if orders[0].type == Order.DESTINATION:
                robot.circlex = orders[0].x
                robot.circley = orders[0].y
                playmat.speedSetpoint = orders[0].speed
                if driveBase.driveTo(orders[0].x,orders[0].y,orders[0].speed,orders[0].brake):
                    # print("        *********** Next Order **********")
                    orders.pop(0)
            elif orders[0].type == Order.KURVE:
                if driveBase.drivekürvchen(orders[0].dist,orders[0].steer,orders[0].speed,orders[0].brake):
                    # print("        *********** Next Order **********")
                    orders.pop(0)
            elif orders[0].type == Order.SCAN:
                sem.acquire()
                slam.hindernisseErkennung(slam.scan,orders[0].toScan, camera)
                takePicture = True
                sem.release()
                # print("        *********** Next Order **********")
                orders.pop(0)
            elif orders[0].type == Order.WINKEL:
                if driveBase.driveToWinkel(orders[0].zielwinkel,orders[0].speed,orders[0].brake):
                    # print("        *********** Next Order **********")
                    orders.pop(0)
            elif orders[0].type == Order.REPOSITION:
                sem.acquire()
                slam.reposition(orders[0].angleCheckOverwrite)
                takePicture = True
                sem.release()
                # print("        *********** Next Order **********")
                orders.pop(0)
            elif orders[0].type == Order.TIME:
                if driveBase.driveTime(orders[0].timeDrive,orders[0].speed,startTime):
                    # print("        *********** Next Order **********")
                    orders.pop(0)
        else:
            kit.servo[0].angle = 90
            kit.servo[3].angle = 90
        
        variable = ((time.perf_counter_ns() - startZeit) / 1000 / 1000)
        if 0.01 - (variable / 1000) > 0:
            time.sleep(0.01 - (variable / 1000))
            ausgabe = 0
        else:
            ausgabe = 1
        startZeit = time.perf_counter_ns()
        # if ausgabe == 1:
        #     print("time: ", variable)



if __name__ == "__main__":
    main()
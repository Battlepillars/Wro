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
kit.servo[0].set_pulse_width_range(950, 2050)
kit.servo[3].set_pulse_width_range(1000, 2000)
running2 = True
orders = []
sem = threading.Semaphore()
takePicture=0

def main():

    

    global slam
    global orders
    global takePicture
    global sem
    pictureNum=0
    running = True
    camera = Camera()
    robot = Robot(1)
    pygame.init()
    global vPressed
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
    clThread = threading.Thread(target=controlLoop, args=(robot, camera))
    clThread.start()
    cmdlThread = threading.Thread(target=commandLoop, args=())
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
                    print("orders.append(Order(x="+str(math.floor(pygame.mouse.get_pos()[0] / playmat.matScale))+", y="+str(math.floor(pygame.mouse.get_pos()[1] / playmat.matScale))+",speed=0.5,brake=1,type=Order.DESTINATION))")
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
            playmat.Infos(screen, robot, slam, playmat.matScale)
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
    def __init__(self,speed=0,brake=0,type=0,x=0,y=0,steer=0,dist=0,toScan=[],zielwinkel=0):
        self.x = x
        self.y = y
        self.speed = speed
        self.brake = brake
        self.type = type
        self.steer = steer
        self.dist = dist
        self.toScan = toScan
        self.zielwinkel = zielwinkel


def waitCompleteOrders():
    global running2
    while orders.__len__() > 0 and running2:
        time.sleep(0.01)
def checkForColor(color, start, end):
    for i in range(start, end):
        print("color: " + str(slam.hindernisse[i].farbe))
        if slam.hindernisse[i].farbe == color:
            return True
    return False

def commandLoop():
    global orders
    # print("Press v to start")
    # while vPressed <= 0:
    #     time.sleep(0.1)
    # slam.setPostion(520,427,180)
    # slam.direction = slam.CW
    # orders.append(Order(type=Order.REPOSITION))
    # orders.append(Order(toScan=[12, 13, 14, 15, 16, 17],type=Order.SCAN))
    
    print("Press v to start")
    while vPressed <= 0:
        time.sleep(0.1)
    orders.append(Order(steer=-90, dist=170, speed=0.2, brake=1, type=Order.KURVE))
    orders.append(Order(steer=0, dist=150, speed=0.2, brake=1, type=Order.KURVE))
    orders.append(Order(steer=90, dist=170, speed=0.2, brake=1, type=Order.KURVE))
    waitCompleteOrders()
    time.sleep(0.5)
    orders.append(Order(toScan=[0, 1, 2, 3, 4, 5],type=Order.SCAN))
    
    print("Capture 1")
    while vPressed <= 0:
        time.sleep(0.1)

    if checkForColor(Hindernisse.GREEN, 0, 6):
        print("Green object detected")
        orders.append(Order(x=1041, y=2839,speed=0.5,brake=1,type=Order.DESTINATION))
        orders.append(Order(x=604, y=2762,speed=0.5,brake=1,type=Order.DESTINATION))
    else:
        print("No green object detected")
        orders.append(Order(x=1050, y=2207,speed=0.5,brake=1,type=Order.DESTINATION))
        orders.append(Order(x=734, y=2607,speed=0.5,brake=1,type=Order.DESTINATION))
    
    
    orders.append(Order(zielwinkel=-90, speed=0.2, brake=1, type=Order.WINKEL))
    waitCompleteOrders()
    time.sleep(0.5)
    orders.append(Order(toScan=[6, 7, 8, 9, 10, 11],type=Order.SCAN))
    orders.append(Order(type=Order.REPOSITION))
    
    print("Capture 2")
    while vPressed <= 0:
        time.sleep(0.1)

    orders.append(Order(x=823, y=2008, speed=0.5, brake=0, type=Order.DESTINATION))
    orders.append(Order(x=829, y=988, speed=0.5, brake=0, type=Order.DESTINATION))
    orders.append(Order(x=244, y=641, speed=0.5, brake=1, type=Order.DESTINATION))
    
    # orders.append(Order(x=182, y=2049,speed=0.5,brake=1,type=Order.DESTINATION))
    # orders.append(Order(x=235, y=616,speed=0.5,brake=1,type=Order.DESTINATION))
    
    orders.append(Order(zielwinkel=180, speed=0.2, brake=1, type=Order.WINKEL))
    waitCompleteOrders()
    time.sleep(0.5)
    orders.append(Order(toScan=[12, 13, 14, 15, 16, 17],type=Order.SCAN))
    orders.append(Order(type=Order.REPOSITION))
    print("Capture 3")
    while vPressed <= 0:
        time.sleep(0.1)

def controlLoop(robot, camera):
    driveBase = DriveBase(slam, kit)
    global running2
    global takePicture
    global sem
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
            if orders[0].type == Order.DESTINATION:
                robot.circlex = orders[0].x
                robot.circley = orders[0].y
                if driveBase.driveTo(orders[0].x,orders[0].y,orders[0].speed,orders[0].brake):
                    print("        *********** Next Order **********")
                    orders.pop(0)
            elif orders[0].type == Order.KURVE:
                if driveBase.drivekürvchen(orders[0].dist,orders[0].steer,orders[0].speed,orders[0].brake):
                    print("        *********** Next Order **********")
                    orders.pop(0)
            elif orders[0].type == Order.SCAN:
                sem.acquire()
                slam.hindernisseErkennung(slam.scan,orders[0].toScan, camera)
                takePicture = True
                sem.release()
                print("        *********** Next Order **********")
                orders.pop(0)
            elif orders[0].type == Order.WINKEL:
                if driveBase.driveToWinkel(orders[0].zielwinkel,orders[0].speed,orders[0].brake):
                    print("        *********** Next Order **********")
                    orders.pop(0)
            elif orders[0].type == Order.REPOSITION:
                slam.reposition()
                print("        *********** Next Order **********")
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

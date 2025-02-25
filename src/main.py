# noinspection PyUnresolvedReferences
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
from ctypes import *
from adafruit_servokit import ServoKit # type: ignore

matScale = 0.34
backupVersion = 3

slam = Slam()
kit = ServoKit(channels=16)
kit.servo[0].set_pulse_width_range(950, 2050)
kit.servo[3].set_pulse_width_range(1000, 2000)
running2 = True
orders = []


def main():
    global slam
    global orders
    running = True
    robot = Robot(matScale)
    pygame.init()
    info = 1
    wx = 3100
    wy = 3100
    placing = 0
    playmat = Playmat(matScale, wx, wy)
    os.environ['SDL_VIDEO_WINDOW_POS'] = "%d,%d" % (560,0)
    screen = pygame.display.set_mode((wx * matScale + 300, wy * matScale), pygame.RESIZABLE)
    
    pygame.display.set_caption("WroONator4000")
    clock = pygame.time.Clock()
    global running2
    last_val = 0xFFFF

    clThread = threading.Thread(target=controlLoop, args=(robot,))
    clThread.start()
    cmdlThread = threading.Thread(target=commandLoop)
    cmdlThread.start()
    
    while running:
        # print("Speed : ",slam.speed)
        robot.xpos = slam.xpos
        robot.ypos = slam.ypos
        robot.angle = slam.angle

        if placing == 1:
            pos = pygame.mouse.get_pos()
            slam.xstart = pos[0] / robot.matScale
            slam.ystart = pos[1] / robot.matScale

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
                
                if event.key == pygame.K_f:
                    print(math.floor(pygame.mouse.get_pos()[0] / matScale) - 50, math.floor(pygame.mouse.get_pos()[1] / matScale) - 50)
                if event.key == pygame.K_g:
                    print("orders.append(Order(x="+str(math.floor(pygame.mouse.get_pos()[0] / matScale) - 50)+", y="+str(math.floor(pygame.mouse.get_pos()[1] / matScale) - 50)+",speed=0.5,brake=1,type=Order.DESTINATION))")
                if event.key == pygame.K_t:
                    orders.append(Order(x=(pygame.mouse.get_pos()[0] / matScale) - 50, y=(pygame.mouse.get_pos()[1] / matScale) - 50, speed=0.5, brake=1, type=Order.DESTINATION))
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


        playmat.draw(screen, info)
        robot.draw(screen, playmat.matScale, slam.scan, slam)
        # if idnfo == 1:
        #     playmat.Infos(screen, robot, slam.speed,0)

        clock.tick(10)
        pygame.display.flip()

class Order:
    DESTINATION=0
    KURVE=1
    SCAN=2
    WINKEL=3
    def __init__(self,speed,brake,type,x=0,y=0,steer=0,dist=0,toScan=[],zielwinkel=0):
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
    while orders.__len__() > 0:
        time.sleep(0.01)
def commandLoop():
    global orders
    # orders.append(Order(x=700,y=2500,speed=1,brake=0,type=Order.DESTINATION))
    # orders.append(Order(x=500,y=700,speed=1,brake=0,type=Order.DESTINATION))
    # orders.append(Order(x=2200,y=500,speed=1,brake=0,type=Order.DESTINATION))
    # orders.append(Order(x=2500,y=2200,speed=1,brake=0,type=Order.DESTINATION))
    # orders.append(Order(x=1479,y=2314,speed=1,brake=0,type=Order.DESTINATION))

    orders.append(Order(steer=-90, dist=170, speed=0.2, brake=1, type=Order.KURVE))
    orders.append(Order(steer=0, dist=150, speed=0.2, brake=1, type=Order.KURVE))
    orders.append(Order(steer=90, dist=170, speed=0.2, brake=1, type=Order.KURVE))
    orders.append(Order(x=1485, y=2614, speed=0.5, brake=1, type=Order.DESTINATION))
    waitCompleteOrders()
    time.sleep(2)
    orders.append(Order(toScan=[0, 1, 2, 3, 4, 5], speed=0.2, brake=1, type=Order.SCAN))

    orders.append(Order(x=991, y=2841, speed=0.5, brake=1, type=Order.DESTINATION))
    orders.append(Order(x=391, y=2838, speed=0.5, brake=1, type=Order.DESTINATION))
    orders.append(Order(x=391, y=2517, speed=0.5, brake=1, type=Order.DESTINATION))
    waitCompleteOrders()
    time.sleep(2)
    orders.append(Order(toScan=[6, 7, 8, 9, 10, 11], speed=0.2, brake=1, type=Order.SCAN))

    orders.append(Order(x=823, y=2008, speed=0.5, brake=0, type=Order.DESTINATION))
    orders.append(Order(x=829, y=988, speed=0.5, brake=0, type=Order.DESTINATION))
    orders.append(Order(x=244, y=641, speed=0.5, brake=1, type=Order.DESTINATION))
    orders.append(Order(zielwinkel=180, speed=0.2, brake=1, type=Order.WINKEL))
    waitCompleteOrders()
    time.sleep(2)
    orders.append(Order(toScan=[12, 13, 14, 15, 16, 17], speed=0.2, brake=1, type=Order.SCAN))

def controlLoop(robot):
    driveBase = DriveBase(slam, kit)
    global running2
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
                slam.hindernisseErkennung(slam.scan,orders[0].toScan)
                print("        *********** Next Order **********")
                orders.pop(0)
            elif orders[0].type == Order.WINKEL:
                if driveBase.driveToWinkel(orders[0].zielwinkel,orders[0].speed,orders[0].brake):
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

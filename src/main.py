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
kit.servo[0].set_pulse_width_range(1000, 2000)
kit.servo[3].set_pulse_width_range(1000, 2000)
running2 = True

def main():
    running = True
    robot = Robot(matScale)
    pygame.init()
    info = 1
    wx = 3100
    wy = 3100
    placing = 0
    playmat = Playmat(matScale, wx, wy)
    screen = pygame.display.set_mode((wx * matScale + 300, wy * matScale), pygame.RESIZABLE)
    pygame.display.set_caption("WroONator4000")
    clock = pygame.time.Clock()
    global running2
    last_val = 0xFFFF

    clThread = threading.Thread(target=controlLoop)
    clThread.start()
    
    while running:
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
    def __init__(self,x,y,speed,brake):
        self.x = x
        self.y = y
        self.speed = speed
        self.brake = brake

def controlLoop():
    driveBase = DriveBase(slam, kit)
    global running2
    kit.servo[0].angle = 90
    kit.servo[3].angle = 90
    slam.update()
    slam.startpostionsetzen()
    startZeit = 0
    ausgabe = 0
    startZeit = time.perf_counter_ns()
    orders = []
    orders.append(Order(700,2500,0.5,1))
    orders.append(Order(500,700,0.5,1))
    orders.append(Order(2200,500,0.5,1))
    orders.append(Order(2500,2200,0.5,1))
    currentOrder = 0
    while running2:
        slam.update()
        if driveBase.driveTo(orders[currentOrder].x,orders[currentOrder].y,orders[currentOrder].speed,orders[currentOrder].brake):
            if currentOrder < 3:
                currentOrder += 1
            else:
                currentOrder = 0
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

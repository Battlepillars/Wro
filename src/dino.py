import random
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
import adafruit_is31fl3741 # type: ignore

from ctypes import *
from rainbowio import colorwheel # type: ignore
from adafruit_is31fl3741.adafruit_rgbmatrixqt import Adafruit_RGBMatrixQT # type: ignore

i2c = board.I2C()
lamp = Adafruit_RGBMatrixQT(i2c, allocate=adafruit_is31fl3741.PREFER_BUFFER)
lamp.set_led_scaling(0xFF)
lamp.global_current = 0xFF
lamp.enable = True


script_dir = os.path.abspath(os.path.dirname(__file__))
lib_path = os.path.join(script_dir, "sg.so")

lidar = CDLL(lib_path)
lidar.initLidar()

def main():
    running = True
    xDino = 1
    yDino = 8
    xCactus = []
    yCactus = []
    lastCactus = 0
    loop = 0
    loopJump = 0
    pressed = False
    dist = 0
    jumping = False
    
    
    pygame.init()
    
    WIDTH, HEIGHT = 300, 100
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("Dino")
    clock = pygame.time.Clock()
    font = pygame.font.SysFont(None, 48)
    
    while running:
        screen.fill((30, 30, 30))
        text = font.render("Dino", True, (255, 255, 255))
        rect = text.get_rect(center=(WIDTH // 2, HEIGHT // 2))
        screen.blit(text, rect)
        
        dist = lidar.checkDir(0)
        if dist > 0:
            if dist < 200:
                pressed = True
            else:
                pressed = False
        

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type == pygame.KEYDOWN:
                running = False
                # if event.key == pygame.K_c:
                #     running = False
        
        if pressed and yDino == 8:
            loopJump = 0
            jumping = True

        if jumping and yDino == 8 and loopJump > 0:
            jumping = False

        if jumping:
            if not jump(loopJump) == None:
                yDino = jump(loopJump)
            
        moveCactus(xCactus, yCactus, loop)
        lastCactus = newCactus(lastCactus, xCactus, yCactus)

        loopJump += 1
        loop += 1
        if loop >= 20:
            loop = 0

        lamp.fill(0x000000)
        
        lamp.pixel(xDino, yDino, 0x0000ff)
        lamp.pixel(xDino, yDino-1, 0x0000ff)

        for i in range(len(xCactus)):
            lamp.pixel(xCactus[i], yCactus[i], 0x00ff00)
            lamp.pixel(xCactus[i], yCactus[i]-1, 0x00ff00)
        
        if not running:
            lamp.fill(0x000000)
            lidar.disconnect()

        lamp.show()
        clock.tick(100)
        pygame.display.flip()

def jump(loopJump):
    if loopJump == 0:
        return 7
    if loopJump == 10:
        return 6
    if loopJump == 30:
        return 5
    if loopJump == 80:
        return 6
    if loopJump == 100:
        return 7
    if loopJump == 110:
        return 8
    

def moveCactus(xCactus, yCactus, loop):
    toPop = []
    if loop == 0:
        for i in range(len(xCactus)):
            xCactus[i] -= 1
            if xCactus[i] < 0:
                toPop.append(i)
        for i in toPop:
            xCactus.pop(i)
            yCactus.pop(i)

def newCactus(lastCactus, xCactus, yCactus):
    if lastCactus <= 0:
        if random.randint(0, 150) == 0:
            lastCactus = 100
            xCactus.append(13)
            yCactus.append(8)
    else:
        lastCactus -= 1
    return lastCactus

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
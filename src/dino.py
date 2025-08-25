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
    CactusType = []
    floor = [0xff7700, 0xff7700, 0xff7700, 0xff7700, 0xff7700, 0xff7700, 0xff7700, 0x00ffff, 0xff7700, 0xff7700, 0xff7700, 0xff7700, 0xff7700]
    lastCactus = 0
    loop = 0
    loopJump = 0
    pressed = False
    dist = 0
    jumping = False
    speed = 1
    speedCalc = 1
    start_time = pygame.time.get_ticks()
    elapsed = 0
    lastHit = 0
    points = 0
    pointsCalc = 0
    pointColor = 0
    showPoints = True
    
    
    pygame.init()
    
    WIDTH, HEIGHT = 300, 100
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("Dino")
    clock = pygame.time.Clock()
    font = pygame.font.SysFont(None, 48)
    
    while running:
        elapsed = (pygame.time.get_ticks() - start_time) / 1000  # Convert milliseconds to seconds
        
        if elapsed > speedCalc * 7:
            speedCalc += 1
            speed += 0.2
        
        if elapsed > pointsCalc/1:
            points += 1
            pointsCalc += 1
        
        if points > 99:
            points = 0
            pointColor = (pointColor + 1) % 5  # Cycle through 0-4
        
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
                if event.key == pygame.K_c:
                    running = False
                if event.key == pygame.K_p:
                    if showPoints:
                        showPoints = False
                    else:
                        showPoints = True
                if event.key == pygame.K_SPACE:
                    pressed = True
        
        if pressed and yDino == 8:
            loopJump = 0
            jumping = True
        
        if jumping and yDino == 8 and loopJump > 0:
            jumping = False
        
        if jumping:
            if not jump(loopJump, speed) == None:
                yDino = jump(loopJump, speed)
            
        floor = moveCactus(xCactus, yCactus, loop, floor, CactusType)
        lastCactus = newCactus(lastCactus, xCactus, yCactus, speed, CactusType)
        
        for i in range(len(xCactus)):
            if xCactus[i] == xDino and yCactus[i] == yDino:
                lastHit = 100
        
        
        loopJump += 1
        loop += 1
        if loop >= 20 / speed:
            loop = 0
        
        lamp.fill(0x000000)
        
        if showPoints:
            drawPoints(points, pointColor)
        
        if lastHit > 0:
            lastHit -= 1
            # lamp.pixel(6, 2, 0xff0000)
        
        lamp.pixel(xDino, yDino-1, 0x0000ff)
        lamp.pixel(xDino, yDino-2, 0x0000ff)
        
        for i in range(len(xCactus)):
            if CactusType[i] == 0:
                lamp.pixel(xCactus[i], yCactus[i]-1, 0x00ff00)
                lamp.pixel(xCactus[i], yCactus[i]-2, 0x00ff00)
            elif CactusType[i] == 1:
                lamp.pixel(xCactus[i], yCactus[i]-1, 0x00ff00)
                lamp.pixel(xCactus[i], yCactus[i]-2, 0x00ff00)
                lamp.pixel(xCactus[i], yCactus[i]-3, 0x00ff00)
            elif CactusType[i] == 2:
                lamp.pixel(xCactus[i], yCactus[i]-1, 0x00ff00)
                lamp.pixel(xCactus[i], yCactus[i]-2, 0x00ff00)
                if xCactus[i] < 12:
                    lamp.pixel(xCactus[i]+1, yCactus[i]-1, 0x00ff00)
                    lamp.pixel(xCactus[i]+1, yCactus[i]-2, 0x00ff00)
            elif CactusType[i] == 3:
                lamp.pixel(xCactus[i], yCactus[i]-1, 0x00ff00)
                lamp.pixel(xCactus[i], yCactus[i]-2, 0x00ff00)
                lamp.pixel(xCactus[i], yCactus[i]-3, 0x00ff00)
                if xCactus[i] < 12:
                    lamp.pixel(xCactus[i]+1, yCactus[i]-1, 0x00ff00)
                    lamp.pixel(xCactus[i]+1, yCactus[i]-2, 0x00ff00)
                    lamp.pixel(xCactus[i]+1, yCactus[i]-3, 0x00ff00)
            
        for i in range(len(floor)):
            lamp.pixel(i, 8, floor[i])

        if not running:
            lamp.fill(0x000000)
            lidar.disconnect()
        
        lamp.show()
        clock.tick(100)
        pygame.display.flip()

def drawPoints(points, pointColor):
    if points > 9:
        x = 4
    else:
        x = 8
    y = 0
    colors = [0x00ff00, 0x00ffe5, 0x0000ff, 0xff00ff, 0xff0000]
    for digit in str(points):
        drawNumber(int(digit), x, y, colors[pointColor])
        x += 4

def jump(loopJump, speed):
    time = math.floor(15 / (speed * 0.5))
    
    # time = 15
    if loopJump == 0:
        return 7
    if loopJump == 10:
        return 6
    if loopJump == 20:
        return 5
    if loopJump == 40:
        return 4
    if loopJump == 40 + time:
        return 5
    if loopJump == 60 + time:
        return 6
    if loopJump == 70 + time:
        return 7
    if loopJump == 80 + time:
        return 8

def moveCactus(xCactus, yCactus, loop, floor, CactusType):
    toPop = []
    if loop == 0:
        for i in range(len(xCactus)):
            xCactus[i] -= 1
            if xCactus[i] < 0:
                toPop.append(i)
        for i in toPop:
            xCactus.pop(i)
            yCactus.pop(i)
            CactusType.pop(i)
    
        floor.pop(0)
        if ((random.randint(0, 3) == 0) or floor.count(0x00ffff) < 1) and floor[11] != 0x00ffff and xCactus.count(12) == 0:
            floor.append(0x00ffff)  # Add a different color for the floor
        else:
            floor.append(0xff7700)
    return floor

def newCactus(lastCactus, xCactus, yCactus, speed, CactusType):
    if lastCactus <= 0:
        if random.randint(0, math.floor(140 / (speed * 0.5))) == 0:
            lastCactus = 220 / (speed * 0.5)
            xCactus.append(13)
            yCactus.append(8)
            CactusType.append(random.randint(0, 3))
    else:
        lastCactus -= 1
    return lastCactus

def drawNumber(num, x, y, color):
    if num == 0:
        lamp.pixel(x, y, color)
        lamp.pixel(x+1, y, color)
        lamp.pixel(x+2, y, color)

        lamp.pixel(x, y+1, color)
        lamp.pixel(x, y+2, color)
        lamp.pixel(x, y+3, color)

        lamp.pixel(x+2, y+1, color)
        lamp.pixel(x+2, y+2, color)
        lamp.pixel(x+2, y+3, color)

        lamp.pixel(x, y+4, color)
        lamp.pixel(x+1, y+4, color)
        lamp.pixel(x+2, y+4, color)
    elif num == 1:
        lamp.pixel(x+1, y, color)
        lamp.pixel(x+1, y+1, color)
        lamp.pixel(x+1, y+2, color)
        lamp.pixel(x+1, y+3, color)
        lamp.pixel(x+1, y+4, color)

        lamp.pixel(x, y+1, color)
        lamp.pixel(x, y+4, color)
        lamp.pixel(x+2, y+4, color)
    elif num == 2:
        lamp.pixel(x+1, y, color)
        lamp.pixel(x+1, y+3, color)
        lamp.pixel(x+1, y+4, color)
        lamp.pixel(x, y+1, color)
        lamp.pixel(x+2, y+1, color)
        lamp.pixel(x+2, y+2, color)
        lamp.pixel(x, y+4, color)
        lamp.pixel(x+2, y+4, color)
    elif num == 3:
        lamp.pixel(x, y, color)
        lamp.pixel(x+1, y, color)
        lamp.pixel(x+2, y, color)

        lamp.pixel(x+2, y+1, color)

        lamp.pixel(x+1, y+2, color)
        lamp.pixel(x+2, y+2, color)
        lamp.pixel(x+2, y+3, color)

        lamp.pixel(x, y+4, color)
        lamp.pixel(x+1, y+4, color)
        lamp.pixel(x+2, y+4, color)
    elif num == 4:
        lamp.pixel(x, y, color)
        lamp.pixel(x, y+1, color)
        lamp.pixel(x, y+2, color)

        lamp.pixel(x+2, y, color)
        lamp.pixel(x+2, y+1, color)
        lamp.pixel(x+2, y+2, color)
        lamp.pixel(x+2, y+3, color)
        lamp.pixel(x+2, y+4, color)

        lamp.pixel(x+1, y+2, color)
    elif num == 5:
        lamp.pixel(x, y, color)
        lamp.pixel(x+1, y, color)
        lamp.pixel(x+2, y, color)

        lamp.pixel(x, y+1, color)
        lamp.pixel(x, y+2, color)
        lamp.pixel(x+1, y+2, color)
        lamp.pixel(x+2, y+3, color)
        lamp.pixel(x, y+4, color)
        lamp.pixel(x+1, y+4, color)
    elif num == 6:
        lamp.pixel(x, y, color)
        lamp.pixel(x+1, y, color)
        lamp.pixel(x+2, y, color)
        lamp.pixel(x, y+2, color)
        lamp.pixel(x+1, y+2, color)
        lamp.pixel(x+2, y+2, color)
        lamp.pixel(x, y+4, color)
        lamp.pixel(x+1, y+4, color)
        lamp.pixel(x+2, y+4, color)

        lamp.pixel(x, y+1, color)
        lamp.pixel(x, y+3, color)
        lamp.pixel(x+2, y+3, color)
    elif num == 7:
        lamp.pixel(x, y, color)
        lamp.pixel(x+1, y, color)
        lamp.pixel(x+2, y, color)

        lamp.pixel(x+2, y+1, color)
        lamp.pixel(x+2, y+2, color)
        lamp.pixel(x+2, y+3, color)
        lamp.pixel(x+2, y+4, color)
    elif num == 8:
        lamp.pixel(x, y, color)
        lamp.pixel(x+1, y, color)
        lamp.pixel(x+2, y, color)
        lamp.pixel(x, y+2, color)
        lamp.pixel(x+1, y+2, color)
        lamp.pixel(x+2, y+2, color)
        lamp.pixel(x, y+4, color)
        lamp.pixel(x+1, y+4, color)
        lamp.pixel(x+2, y+4, color)
        
        lamp.pixel(x, y+1, color)
        lamp.pixel(x+2, y+1, color)
        lamp.pixel(x, y+3, color)
        lamp.pixel(x+2, y+3, color)
    elif num == 9:
        lamp.pixel(x, y, color)
        lamp.pixel(x+1, y, color)
        lamp.pixel(x+2, y, color)
        lamp.pixel(x, y+2, color)
        lamp.pixel(x+1, y+2, color)
        lamp.pixel(x+2, y+2, color)
        lamp.pixel(x, y+4, color)
        lamp.pixel(x+1, y+4, color)
        lamp.pixel(x+2, y+4, color)
        
        lamp.pixel(x, y+1, color)
        lamp.pixel(x+2, y+1, color)
        lamp.pixel(x+2, y+3, color)

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
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
import random

from ctypes import *
from rainbowio import colorwheel # type: ignore
from adafruit_is31fl3741.adafruit_rgbmatrixqt import Adafruit_RGBMatrixQT # type: ignore

i2c = board.I2C()
lamp = Adafruit_RGBMatrixQT(i2c, allocate=adafruit_is31fl3741.PREFER_BUFFER)
lamp.set_led_scaling(0xFF)
lamp.global_current = 0xFF
lamp.enable = True


myOtos1 = qwiic_otos.QwiicOTOS(0x17)

# Check if it's connected
if myOtos1.is_connected() == False:
    print("The device 1 isn't connected to the system. Please check your connection", \
        file=sys.stderr)
# Initialize the device
myOtos1.begin()

myOtos1.setLinearUnit(myOtos1.kLinearUnitMeters)
myOtos1.setSignalProcessConfig(0b1101)
print("Calibrating IMU...")

# Calibrate the IMU, which removes the accelerometer and gyroscope offsets
myOtos1.calibrateImu(255)
myOtos1.setLinearScalar(0.980)     
myOtos1.setAngularScalar(0.9933)
myOtos1.resetTracking()

script_dir = os.path.abspath(os.path.dirname(__file__))   #led display size: 13*9  (9*13 (0,0)-bottom left)
lib_path = os.path.join(script_dir, "sg.so")

lidar = CDLL(lib_path)
lidar.initLidar()

def main():
    running = True
    pressed = False
    dist = 0
    start_time = pygame.time.get_ticks()
    elapsed = 0
    loop = 0
    cubes = makeCubes()
    balls = []
    shootingSpeed = 150
    
    
    pygame.init()
    
    WIDTH, HEIGHT = 300, 100
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("ball")
    clock = pygame.time.Clock()
    font = pygame.font.SysFont(None, 48)
    
    
    while running:
        elapsed = (pygame.time.get_ticks() - start_time) / 1000  # Convert milliseconds to seconds
        loop += 1
        if loop % shootingSpeed == 0:
            makeBall(balls, myPosition)
        
        screen.fill((30, 30, 30))
        text = font.render(str(shootingSpeed), True, (255, 255, 255))
        rect = text.get_rect(center=(WIDTH // 2, HEIGHT // 2))
        screen.blit(text, rect)
        
        dist = lidar.checkDir(0)
        myPosition = myOtos1.getPosition()
        
        
        pressed = 200 > dist > 0
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type == pygame.MOUSEBUTTONUP:
                pass
            if event.type == pygame.MOUSEBUTTONDOWN:
                shootingSpeed -= 10
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_c:
                    running = False
        
        moveBall(balls, cubes, myPosition)
        moveCubes(cubes)
        
        lamp.fill(0x000000)
        lamp.pixel(8, 9, 0x0000ff)
        for cube in cubes:                                 # draw cubes
            lamp.pixel(cube.x, cube.y, 0x0000ff)

        for ball in balls:
            lamp.pixel(math.floor(ball.x/100), math.floor(ball.y/100), 0xff0000)    # draw ball

        lamp.pixel(0, 3, 0x00ff00)
        lamp.pixel(0, 4, 0x00ff00)
        lamp.pixel(0, 5, 0x00ff00)
        lamp.pixel(1, 4, 0x00ff00)
        
        if not running:
            lamp.fill(0x000000)
            lidar.disconnect()
        
        lamp.show()
        clock.tick(100)
        pygame.display.flip()

class Ball:
    def __init__(self,x=0, y=0, dir=0, speed=0):
        self.x = x
        self.y = y
        self.dir = dir
        self.speed = speed

class Cube:
    def __init__(self,x=0, y=0):
        self.x = x
        self.y = y

def makeBall(balls, myPosition):
    balls.append(Ball(x=0, y=400, dir= -myPosition.h, speed=10))

def moveBall(balls, cubes, myPosition):
    for ball in balls:
        ball.x += math.cos(math.radians(ball.dir)) * ball.speed
        ball.y += math.sin(math.radians(ball.dir)) * ball.speed

        for cube in cubes:
            if math.floor(ball.x/100) == cube.x and math.floor(ball.y/100) == cube.y:
                balls.remove(ball)
                cubes.remove(cube)
    
        if ball.x > 1300 or ball.y < 0 or ball.y > 900:
            balls.remove(ball)

def moveCubes(cubes):
    for cube in cubes:
        cube.x -= 1

def makeCubes():
    cubes = []
    for i in range(12, 8, -1): #]-1;8]
        for u in range (8, -1, -1): #]9;12[
            if random.randrange(0, 2) == 0:
                cubes.append(Cube(x=i, y=u))
    # for cube in cubes:
    #     print("Cube at:", cube.x, cube.y)
    return cubes

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
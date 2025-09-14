import pygame # type: ignore
import pygame.rect # type: ignore
import math
import numpy as np # type: ignore
import cv2 as cv2 # type: ignore
import threading

import board # type: ignore
from rainbowio import colorwheel # type: ignore

import adafruit_is31fl3741 # type: ignore
from adafruit_is31fl3741.adafruit_rgbmatrixqt import Adafruit_RGBMatrixQT # type: ignore

# import main

class Robot:
    xpos = 0  
    ypos = 0
    xstart = 0
    ystart = 0
    angleStart = 0
    angle = 0
    matScaleOld = 0
    circlex = 0
    circley = 0
    circlexList = []
    circleyList = []
    circleNumList = []




    def __init__(self, matScale):
        self.matScaleOld = matScale
        self.robot = None
        self.matScale = matScale
        print("Init Robot")
        self.robotSource = pygame.image.load("img/Roboter.tif")
        self.robotWidth = self.robotSource.get_width()
        self.robotHeight = self.robotSource.get_height()
        self.robot = pygame.transform.scale(self.robotSource, (self.robotWidth * matScale, self.robotHeight * matScale))
        self.semDb = threading.Semaphore()

    def draw(self, screen, matScale, scan, slam):
        xoff = 50 * matScale
        yoff = 50 * matScale
        self.matScale = matScale
        myAngle = self.angle
        sxs = screen.get_width()
        sys = screen.get_height()
        screenx = (self.xpos * self.matScale)
        screeny = (self.ypos * self.matScale)
        font = pygame.font.Font('freesansbold.ttf',20)
        green = (0, 255, 0)
        blue = (0, 0, 128)
        self.semDb.acquire()
        
        for i in range(len(slam.hindernisse)):
            if slam.hindernisse[i].farbe == 2: # 2=GREEN
                pygame.draw.circle(screen, (0, 255, 0), (slam.hindernisse[i].x * matScale + xoff, slam.hindernisse[i].y * matScale + yoff), 100 * matScale)
            elif slam.hindernisse[i].farbe == 1: # 1=RED
                pygame.draw.circle(screen, (255, 0, 0), (slam.hindernisse[i].x * matScale + xoff, slam.hindernisse[i].y * matScale + yoff), 100 * matScale)
            else:
                pygame.draw.circle(screen, (0, 0, 255), (slam.hindernisse[i].x * matScale + xoff, slam.hindernisse[i].y * matScale + yoff), 100 * matScale)
                
                
        for i in range(len(self.circlexList)):
            
            pygame.draw.circle(screen, (0, 255, 0), ((self.circlexList[i] + 50) * matScale, (self.circleyList[i] + 50) * matScale), 30 * matScale)
            
            text = font.render(str(self.circleNumList[i]), True, green, blue)
            
            #print("runder ",self.circleNumList[i]," ",((self.circlex + 50) * matScale, (self.circley + 50) * matScale))
            screen.blit(text, (10+int((self.circlexList[i] + 50) * matScale),10+int((self.circleyList[i] + 50)) * matScale)) 
        self.semDb.release()    
        pygame.draw.circle(screen, (255, 0, 0), ((self.circlex + 50) * matScale, (self.circley + 50) * matScale), 50 * matScale)
        


        for i in range(len(scan)):
            if scan[i] > 0:
                rad = (i + self.angle) / 180 * math.pi
                x = math.cos(rad) * -scan[i] + self.xpos
                y = math.sin(rad) * scan[i] + self.ypos
                pygame.draw.circle(screen, (255, 0, 0), (x * matScale + xoff, y * matScale + yoff), 10 * matScale)
                # pygame.draw.circle(screen, (255, 0, 0), (500 * matScale, 500 * matScale), 500 * matScale)


        
        # pygame.draw.line(screen, (0,255,0), (0 * matScale + xoff, 0 * matScale + yoff), (3000 * matScale + xoff , 0 * matScale + yoff), int(50 * matScale))
        
        if self.matScaleOld != self.matScale:
            self.robot = pygame.transform.scale(self.robotSource, (self.robotWidth * matScale, self.robotHeight * matScale))

        robotTurned = pygame.transform.rotate(self.robot, 90 + myAngle)

        rw = robotTurned.get_width()
        rh = robotTurned.get_height()
        screen.blit(robotTurned, (screenx - rw / 2 + xoff, screeny - rh / 2 + yoff))

class Playmat:
    bgImg = None
    scroll = 0
    logList = []
    speedSetpoint = 0
    averageSpeedPercent = 0
    averageSpeedPercentCalc = 0
    lastAngle = 0
    lastTime = 0
    
    @staticmethod
    def log(msg):
        Playmat.logList.append(msg)
        if len(Playmat.logList) > 10:
            Playmat.logList.pop(0)

    def __init__(self, matScale, wx, wy):
        self.wx = wx
        self.wy = wy
        self.matScale = matScale
        print("Init Playmat")
        self.bgImgFull = pygame.image.load("img/WRO2024-FE-Spielfeldmatte.tif")
        self.bgImg = pygame.transform.scale(self.bgImgFull, (self.wx * self.matScale, self.wy * self.matScale))

    def draw(self, screen, info, camera, robot):
        screenys = screen.get_height()

        screen.fill((0, 0, 0))
        if self.bgImg.get_height() != screenys:
            screenxs = screenys / self.wy * self.wx
            self.matScale = screenxs / self.wy
            #print("***************************************************\nMatScale: ", self.matScale)
            self.bgImg = pygame.transform.scale(self.bgImgFull, (screenxs, screenys))
        screen.blit(self.bgImg, (0, 0))
        
        frame = camera.imgCam
        frame = np.rot90(frame)
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        frame = pygame.surfarray.make_surface(frame)
        frame = pygame.transform.scale(frame, (screen.get_width() - self.wx * self.matScale, (screen.get_width() - self.wx * self.matScale) * 0.55078125))
        
        
        xoff = 50 * self.matScale
        yoff = 50 * self.matScale
        
        for i in range(len(camera.blocksAngleDraw)):
            rad = (-camera.blocksAngleDraw[i] + robot.angle) / 180 * math.pi
            x = math.cos(rad) * -2000 + robot.xpos
            y = math.sin(rad) * 2000 + robot.ypos
            if camera.blocksColorDraw[i] == camera.GREEN:
                pygame.draw.line(screen, (0,255,0), (robot.xpos * self.matScale + xoff, robot.ypos * self.matScale + yoff), (x * self.matScale + xoff, y * self.matScale + yoff), int(5 * self.matScale))
            if camera.blocksColorDraw[i] == camera.RED:
                pygame.draw.line(screen, (255,0,0), (robot.xpos * self.matScale + xoff, robot.ypos * self.matScale + yoff), (x * self.matScale + xoff, y * self.matScale + yoff), int(5 * self.matScale))
        if len(camera.blocksAngleDraw) > 0:
            camera.blocksAngleDraw.clear()
            camera.blocksColorDraw.clear()
        
        screen.blit(frame, (self.wx * self.matScale, 0))


    def Infos(self,screen,robot,slam,matScale,startTime,time,lamp,virtual_cursor_x, virtual_cursor_y):
        pygame.draw.circle(screen, (255, 0, 0), (virtual_cursor_x, virtual_cursor_y), 8, 2)
        pygame.draw.line(screen, (255, 0, 0), (virtual_cursor_x - 10, virtual_cursor_y), (virtual_cursor_x + 10, virtual_cursor_y), 2)
        pygame.draw.line(screen, (255, 0, 0), (virtual_cursor_x, virtual_cursor_y - 10), (virtual_cursor_x, virtual_cursor_y + 10), 2)
        green = (0, 255, 0)
        blue = (0, 0, 128)
        self.font = pygame.font.Font('freesansbold.ttf',20)
        
        # speedTest = 0.5
        # sppedsettest = 1
        
        # lamp.fill(0x000000) 
        # lamp.pixel(0, 0, 0xff0000)
        # lamp.pixel(5, 0, 0xff0000)
        # lamp.show()
        
        turnSpeed = (self.lastAngle - slam.angle) / (time.time()-self.lastTime)
        # print("turnSpeed: ", turnSpeed)
        self.lastAngle = slam.angle
        self.lastTime = time.time()
        
        # if math.floor(turnSpeed*100)/100 == 0.05:
        #     turnSpeed = 0
        
        # lamp.fill(0x000000) 
        
        # for i in range(0, 13):
        #     lamp.pixel(i, 5, 0x000000)
        #     lamp.pixel(i, 6, 0x000000)
        # for i in range(0, math.floor(13*abs(turnSpeed)/(1/10))):
        #     lamp.pixel(i, 5, 0x00ff00)
        #     lamp.pixel(i, 6, 0x00ff00)
        # lamp.show()
        
        # slam.wheelAngle = 0.5
        
        widthWheel = 700 * matScale
        wheelAngleCalc = slam.wheelAngle
        
        if wheelAngleCalc > 0:
            wheelAngleCalc = 0
            
        
        pygame.draw.rect(screen, (255, 255, 255), ((self.wx + 1300) * self.matScale, 500 * matScale + ((screen.get_width() - self.wx * self.matScale) * 0.55078125), widthWheel + 20 * matScale, 90 * matScale))
        pygame.draw.rect(screen, (170, 0, 0), ((self.wx + 1310) * self.matScale, 510 * matScale + ((screen.get_width() - self.wx * self.matScale) * 0.55078125), widthWheel, 70 * matScale))
        
        if slam.wheelAngle != 0:
            pygame.draw.rect(screen, (0, 255, 0), ((self.wx + 1660) * self.matScale + (widthWheel/2 * (wheelAngleCalc)), 510 * matScale + ((screen.get_width() - self.wx * self.matScale) * 0.55078125), widthWheel/2 * abs(slam.wheelAngle), 70 * matScale))
        
        pygame.draw.rect(screen, (0, 0, 0), ((self.wx + 1655) * self.matScale, 510 * matScale + ((screen.get_width() - self.wx * self.matScale) * 0.55078125), 10 * matScale, 70 * matScale))

        
        # pygame.draw.rect(surface, color, rect(left, top, width, height))
        
        height = 700 * matScale
        
        pygame.draw.rect(screen, (255, 255, 255), ((self.wx + 990) * self.matScale, 190 * matScale + ((screen.get_width() - self.wx * self.matScale) * 0.55078125), 90 * matScale, height + 20 * matScale))
        pygame.draw.rect(screen, (170, 0, 0), ((self.wx + 1000) * self.matScale, 200 * matScale + ((screen.get_width() - self.wx * self.matScale) * 0.55078125), 70 * matScale, height))
        pygame.draw.rect(screen, (100, 65, 180), ((self.wx + 1000) * self.matScale, 200 * matScale + height-height*self.speedSetpoint + ((screen.get_width() - self.wx * self.matScale) * 0.55078125), 70 * matScale, height * self.speedSetpoint))
        
        pygame.draw.rect(screen, (0, 255, 0), ((self.wx + 1000) * self.matScale, 200 * matScale + height-height*slam.speed + ((screen.get_width() - self.wx * self.matScale) * 0.55078125), 70 * matScale, height * slam.speed))

        lamp.fill(0x000000)
        
        for i in range(0, 13):
            lamp.pixel(i, 2, 0x000000)
            lamp.pixel(i, 3, 0x000000)
            
        for i in range(0, math.floor(self.speedSetpoint*13)):
            lamp.pixel(i, 2, 0xff0000)
            lamp.pixel(i, 3, 0xff0000)
        
        for i in range(0, math.floor(slam.speed*13)):
            lamp.pixel(i, 2, 0x00ff00)
            lamp.pixel(i, 3, 0x00ff00)
        
        lamp.pixel(math.floor(self.speedSetpoint*13), 2, 0xff0000)
        lamp.pixel(math.floor(self.speedSetpoint*13), 3, 0xff0000)
        
        if slam.healthy1 == 1:
            lamp.pixel(12, 0, 0x00ff00)
            lamp.pixel(12, 1, 0x00ff00)
            lamp.pixel(11, 0, 0x00ff00)
            lamp.pixel(11, 1, 0x00ff00)
        elif slam.healthy1 == 0:
            lamp.pixel(12, 0, 0xff0000)
            lamp.pixel(12, 1, 0xff0000)
            lamp.pixel(11, 0, 0xff0000)
            lamp.pixel(11, 1, 0xff0000)
        elif slam.healthy1 == -2:
            lamp.pixel(12, 0, 0x0000ff)
            lamp.pixel(12, 1, 0x0000ff)
            lamp.pixel(11, 0, 0x0000ff)
            lamp.pixel(11, 1, 0x0000ff)
        else:
            lamp.pixel(12, 0, 0xffff00)
            lamp.pixel(12, 1, 0xffff00)
            lamp.pixel(11, 0, 0xffff00)
            lamp.pixel(11, 1, 0xffff00)

        if slam.healthy2 == 1:
            lamp.pixel(12, 7, 0x00ff00)
            lamp.pixel(12, 8, 0x00ff00)
            lamp.pixel(11, 7, 0x00ff00)
            lamp.pixel(11, 8, 0x00ff00)
        elif slam.healthy2 == 0:
            lamp.pixel(12, 7, 0xff0000)
            lamp.pixel(12, 8, 0xff0000)
            lamp.pixel(11, 7, 0xff0000)
            lamp.pixel(11, 8, 0xff0000)
        elif slam.healthy2 == -2:
            lamp.pixel(12, 7, 0x0000ff)
            lamp.pixel(12, 8, 0x0000ff)
            lamp.pixel(11, 7, 0x0000ff)
            lamp.pixel(11, 8, 0x0000ff)
        else:
            lamp.pixel(12, 7, 0xffff00)
            lamp.pixel(12, 8, 0xffff00)
            lamp.pixel(11, 7, 0xffff00)
            lamp.pixel(11, 8, 0xffff00)
        
        lamp.show()
        
        if (self.speedSetpoint > 0) and (slam.speed < 10):
            percentSpeed = slam.speed / self.speedSetpoint
            if slam.speed > self.speedSetpoint * 0.25:
                self.averageSpeedPercent += percentSpeed
                self.averageSpeedPercentCalc += 1
            
            #pygame.draw.rect(screen, (0, 255, 0), ((self.wx + 1000) * self.matScale, 200 * matScale + height-height*percentSpeed + ((screen.get_width() - self.wx * self.matScale) * 0.55078125), 70 * matScale, height * percentSpeed))


        prints = 9
        for i in range(prints + len(self.logList)):
            if i == 0:
                text = self.font.render("x: " + str(math.floor(robot.xpos)), True, green, blue)
            if i == 1:
                text = self.font.render("y: " + str(math.floor(robot.ypos)), True, green, blue)
            if i == 2:
                text = self.font.render("r: " + str(robot.angle), True, green, blue)
            if i == 3:
                #text = self.font.render("matscale: "+str(matScale), True, green, blue)
                text = self.font.render("wheel: " + str(slam.wheelAngle), True, green, blue)
            if i == 4:
                text = self.font.render(str(math.floor(pygame.mouse.get_pos()[0] / matScale)-50) + " " + str(math.floor(pygame.mouse.get_pos()[1] / matScale)-50), True, green, blue)
            if i == 5:
                text = self.font.render("Time: " + str(math.floor((time.time()-startTime)*10)/10), True, green, blue)
            if i == 6:
                text = self.font.render("Speed: " + str(math.floor((slam.speed)*10)/10), True, green, blue)
            if (i == 7) and (self.averageSpeedPercentCalc > 0):
                text = self.font.render("Speed: " + str(math.floor((self.averageSpeedPercent/self.averageSpeedPercentCalc)*100))  + "%", True, green, blue)
            for j in range(len(self.logList)):
                if i == prints-1:
                    text = self.font.render("Log: ", True, green, blue)
                if i == prints + j:
                    text = self.font.render(self.logList[j], True, green, blue)
                    break
            screen.blit(text, (self.wx * self.matScale,(i * 20) + ((screen.get_width() - self.wx * self.matScale) * 0.55078125)))
import pygame # type: ignore
import pygame.rect # type: ignore
import math
import numpy as np
import cv2 as cv2


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

    def __init__(self, matScale):
        self.matScaleOld = matScale
        self.robot = None
        self.matScale = matScale
        print("Init Robot")
        self.robotSource = pygame.image.load("img/Roboter.tif")
        self.robotWidth = self.robotSource.get_width()
        self.robotHeight = self.robotSource.get_height()
        self.robot = pygame.transform.scale(self.robotSource, (self.robotWidth * matScale, self.robotHeight * matScale))


    def draw(self, screen, matScale, scan, slam):
        xoff = 50 * matScale
        yoff = 50 * matScale
        self.matScale = matScale
        myAngle = self.angle
        sxs = screen.get_width()
        sys = screen.get_height()
        screenx = (self.xpos * self.matScale)
        screeny = (self.ypos * self.matScale)
        pygame.draw.circle(screen, (255, 0, 0), ((self.circlex + 50) * matScale, (self.circley + 50) * matScale), 50 * matScale)
        for i in range(len(slam.hindernisse)):
            if slam.hindernisse[i].farbe == 2: # 2=GREEN
                pygame.draw.circle(screen, (0, 255, 0), (slam.hindernisse[i].x * matScale + xoff, slam.hindernisse[i].y * matScale + yoff), 100 * matScale)
            elif slam.hindernisse[i].farbe == 1: # 1=RED
                pygame.draw.circle(screen, (255, 0, 0), (slam.hindernisse[i].x * matScale + xoff, slam.hindernisse[i].y * matScale + yoff), 100 * matScale)
            else:
                pygame.draw.circle(screen, (0, 0, 255), (slam.hindernisse[i].x * matScale + xoff, slam.hindernisse[i].y * matScale + yoff), 100 * matScale)

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
            print("***************************************************\nMatScale: ", self.matScale)
            self.bgImg = pygame.transform.scale(self.bgImgFull, (screenxs, screenys))
        screen.blit(self.bgImg, (0, 0))
        
        frame = camera.imgCam
        frame = np.rot90(frame)
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        frame = pygame.surfarray.make_surface(frame)
        frame = pygame.transform.scale(frame, (screen.get_width() - self.wx * self.matScale, (screen.get_width() - self.wx * self.matScale) * 0.55078125))
        
        
        xoff = 50 * self.matScale
        yoff = 50 * self.matScale
        
        for i in range(len(camera.blocksAngle)):
            rad = (-camera.blocksAngle[i] + robot.angle) / 180 * math.pi
            x = math.cos(rad) * -2000 + robot.xpos
            y = math.sin(rad) * 2000 + robot.ypos
            
            if camera.blocksColor[i] == camera.GREEN:
                pygame.draw.line(screen, (0,255,0), (robot.xpos * self.matScale + xoff, robot.ypos * self.matScale + yoff), (x * self.matScale + xoff, y * self.matScale + yoff), int(5 * self.matScale))
            if camera.blocksColor[i] == camera.RED:
                pygame.draw.line(screen, (255,0,0), (robot.xpos * self.matScale + xoff, robot.ypos * self.matScale + yoff), (x * self.matScale + xoff, y * self.matScale + yoff), int(5 * self.matScale))

        screen.blit(frame, (self.wx * self.matScale, 0))


    def Infos(self,screen,robot,slam,matScale):
        green = (0, 255, 0)
        blue = (0, 0, 128)
        self.font = pygame.font.Font('freesansbold.ttf',20)
        for i in range(5):
            if i == 0:
                text = self.font.render('x: ' + str(robot.xpos), True, green, blue)
            if i == 1:
                text = self.font.render('y: ' + str(robot.ypos), True, green, blue)
            if i == 2:
                text = self.font.render('r: ' + str(robot.angle), True, green, blue)
            if i == 3:
                text = self.font.render("matscale: "+str(matScale), True, green, blue)
                # text = self.font.render("rot = rechts, grün = links", True, green, blue)
            if i == 4:
                text = self.font.render(str(math.floor(pygame.mouse.get_pos()[0] / matScale)) + " " + str(math.floor(pygame.mouse.get_pos()[1] / matScale)), True, green, blue) 
            # if i == 3:
            #     text = self.font.render('speed x: ' + str(speed.x), True, green, blue)
            # if i == 4:
            #     text = self.font.render('speed y: ' + str(speed.y), True, green, blue)
            # if i == 5:
            #     text = self.font.render('speed max x: ' + str(speedMax[0]), True, green, blue)
            # if i == 6:
            #     text = self.font.render('speed max y: ' + str(speedMax[1]), True, green, blue)
            screen.blit(text, (self.wx * self.matScale,(i * 20) + ((screen.get_width() - self.wx * self.matScale) * 0.55078125)))
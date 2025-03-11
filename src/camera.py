#!/usr/bin/python3

import time
import cv2 as cv
import numpy as np
import libcamera
import argparse
import imutils

from libcamera import Transform
from matplotlib import pyplot as plt
from picamera2 import Picamera2


class Camera():
    
    imgCam = np.zeros((1536,846,3), np.uint8)
    
    def captureImage(self):
        cv.startWindowThread()

        picam2 = Picamera2()
        picam2.set_controls({'HdrMode': libcamera.controls.HdrModeEnum.SingleExposure})
        picam2.configure(picam2.create_preview_configuration(main={"format": 'XRGB8888', "size": (640, 480)}))
        picam2.start()


        resolution = (1536, 846)
        config = picam2.create_still_configuration(transform=Transform(vflip=True,hflip=True),main={"size": resolution})

        preview_config = picam2.create_preview_configuration(transform=Transform(vflip=True))

        imgclear = picam2.switch_mode_and_capture_array(config, delay=10)
        imgIn = cv.blur(imgclear,(10,10))

        imgIn = imgIn[379:413, 0:1535]

        #picam2.capture_file("test.jpg")

        #imgIn = cv.imread('test.jpg')
        #imgIn = picam2.capture_array("main")
        hsv = cv.cvtColor(imgIn, cv.COLOR_RGB2HSV)
        img = cv.cvtColor(imgIn, cv.COLOR_BGR2RGB)
        imgclear = cv.cvtColor(imgclear, cv.COLOR_BGR2RGB)


        assert hsv is not None, "file could not be read, check with os.path.exists()"



        # lower boundary RED color range values; Hue (0 - 10)
        lower1 = np.array([0, 100, 20])
        upper1 = np.array([10, 255, 255])
        
        # upper boundary RED color range values; Hue (160 - 180)
        lower2 = np.array([160,100,20])
        upper2 = np.array([179,255,255])
        
        lower_mask = cv.inRange(hsv, lower1, upper1)
        upper_mask = cv.inRange(hsv, lower2, upper2)

        maskred = lower_mask + upper_mask

        lowerGreen = np.array([35, 100, 20])
        upperGreen = np.array([95, 255, 255])

        maskgreen = cv.inRange(hsv, lowerGreen, upperGreen)


        # Bitwise-AND mask and original image
        res = cv.bitwise_and(img, img, mask=maskred)
        res2 = cv.bitwise_and(img, img, mask=maskgreen)

        cntsgreen = cv.findContours(maskgreen.copy(), cv.RETR_EXTERNAL,cv.CHAIN_APPROX_SIMPLE)
        cntsred = cv.findContours(maskred.copy(), cv.RETR_EXTERNAL,cv.CHAIN_APPROX_SIMPLE)

        cntsred = imutils.grab_contours(cntsred)
        cntsgreen = imutils.grab_contours(cntsgreen)

        cv.line(imgclear,(0,413),(1536,413),(255,0,0),1)
        cv.line(imgclear,(0,379),(1536,379),(255,0,0),1)
        for c in cntsgreen:
            # compute the center of the contour
            M = cv.moments(c)
            if M["m00"] != 0:
                cX = int(M["m10"] / M["m00"])
                cY = int(M["m01"] / M["m00"])
            else:
                cX, cY = 0, 0
            # draw the contour and center of the shape on the image
            cv.drawContours(imgclear, [c], -1, (0, 255, 0), 2)
            cv.line(imgclear,(cX,0),(cX,846),(0,255,0),3)
            cv.circle(imgclear, (cX, cY), 7, (0, 255, 0), -1)
            print("Green at: ",cX)
            
            # show the image

        for c in cntsred:
            # compute the center of the contour
            M = cv.moments(c)
            if M["m00"] != 0:
                cX = int(M["m10"] / M["m00"])
                cY = int(M["m01"] / M["m00"])
            else:
                cX, cY = 0, 0
            # draw the contour and center of the shape on the image
            cv.drawContours(imgclear, [c], -1, (0, 255, 0), 2)
            cv.line(imgclear,(cX,0),(cX,846),(0,0,255),3)
            cv.circle(imgclear, (cX, cY), 7, (0, 0, 255), -1)
            print("Red at: ",cX)
            
            # show the image
        #cv.imshow("Image", imgclear)

        self.imgCam = imgclear
        #cv.imshow('frame', img)
        #cv.imshow('mask', maskred)
        #cv.imshow('res', res)
        #cv.imshow('res2', res2)

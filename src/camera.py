import time
import cv2 as cv # type: ignore
import numpy as np # type: ignore
import libcamera # type: ignore
import argparse
import imutils # type: ignore

from drawBoard import *
from libcamera import Transform # type: ignore
from matplotlib import pyplot as plt # type: ignore
from picamera2 import Picamera2 # type: ignore


class Camera():
    """@brief Camera interface for color-based obstacle detection.

    Captures a blurred horizontal scan band, thresholds HSV for RED/GREEN,
    extracts contour centers, and maps them to angular offsets from optical
    midline. Results stored in blocksAngle / blocksColor lists.
    """
    
    imgCam = np.zeros((1536,846,3), np.uint8)
    blocksAngle = []
    blocksColor = []
    blocksAngleDraw = []
    blocksColorDraw = []
    RED = 0
    GREEN = 1
    pictureNum=0
    
    def __init__(self):
        """@brief Initialize Picamera2 and configure capture settings.

        Sets HDR mode, resolution, and starts the camera stream.
        @return None
        """
        self.picam2 = Picamera2()
        self.picam2.set_controls({'HdrMode': libcamera.controls.HdrModeEnum.SingleExposure})
        resolution = (1536, 846)
        self.config = self.picam2.create_still_configuration(transform=Transform(vflip=False,hflip=True),main={"size": resolution})   #hflip=True
        self.picam2.configure(self.config)
        #self.picam2.switch_mode_and_capture_array(self.config, delay=10)
        self.picam2.start()
    
    def captureImage(self, checkHeightNear):
        """@brief Capture frame, extract scan band, detect RED/GREEN blobs.

        Performs blur, HSV conversion, masking for color ranges (including
        wrap-around red hues), then records each contour's horizontal angle.
        @param checkHeightNear bool If True, lowers scan band for near obstacle perspective.
        @return None (populates blocksAngle/blocksColor + imgCam for drawing)
        """
        self.blocksAngle = []
        self.blocksColor = []
        self.blocksAngleDraw = []
        self.blocksColorDraw = []
        imgclear = self.picam2.capture_array()
        imgIn = cv.blur(imgclear,(10,10))
        checkStart=450                    # Scanbalken einstellen, kleiner -> balken weiter oben
        checkHeight=30
        
        if checkHeightNear:
            checkStart += 150
        
        checkEnd=checkStart+checkHeight
        
        hsv = cv.cvtColor(imgIn, cv.COLOR_RGB2HSV)
        cv.imwrite(f'capture/hsvGanz{self.pictureNum}.jpg', hsv)
        imgIn = imgIn[checkStart:checkEnd, 0:1535]

        hsv = cv.cvtColor(imgIn, cv.COLOR_RGB2HSV)
        img = cv.cvtColor(imgIn, cv.COLOR_BGR2RGB)
        imgclear = cv.cvtColor(imgclear, cv.COLOR_BGR2RGB)

        assert hsv is not None, "file could not be read, check with os.path.exists()"

        # in photo shop: rgb -> vsh
        
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

        cv.line(imgclear,(0,checkEnd),(1536,checkEnd),(255,0,0),2)
        cv.line(imgclear,(0,checkStart),(1536,checkStart),(255,0,0),2)
        
        mid = 788       # This value sets the midpoint of the image, which is used as a reference to calculate the angle of detected blocks.
        split  = 19.12  # This value is used to scale the difference between the midpoint of the image and the x-coordinate of the detected block's center to calculate the angle.
        
        for c in cntsgreen:
            # compute the center of the contour
            M = cv.moments(c)
            if M["m00"] != 0:
                cX = int(M["m10"] / M["m00"])
                cY = int(M["m01"] / M["m00"])
                # draw the contour and center of the shape on the image
                cv.drawContours(imgclear, [c], -1, (0, 255, 0), 2)
                cv.line(imgclear,(cX,0),(cX,846),(0,255,0),3)
                cv.circle(imgclear, (cX, cY), 7, (0, 255, 0), -1)
                
                #print("Green at: ", (mid - cX) / split)
                self.blocksAngle.append((mid - cX) / split)
                self.blocksColor.append(self.GREEN)
                self.blocksAngleDraw.append((mid - cX) / split)
                self.blocksColorDraw.append(self.GREEN)

        for c in cntsred:
            # compute the center of the contour
            M = cv.moments(c)
            if M["m00"] != 0:
                cX = int(M["m10"] / M["m00"])
                cY = int(M["m01"] / M["m00"])
                # draw the contour and center of the shape on the image
                cv.drawContours(imgclear, [c], -1, (0, 255, 0), 2)
                cv.line(imgclear,(cX,0),(cX,846),(0,0,255),3)
                cv.circle(imgclear, (cX, cY), 7, (0, 0, 255), -1)
                
                #print("Red at: ", (mid - cX) / split)
                self.blocksAngle.append((mid - cX) / split)
                self.blocksColor.append(self.RED)
                self.blocksAngleDraw.append((mid - cX) / split)
                self.blocksColorDraw.append(self.RED)
        
        cv.imwrite(f'capture/hsvStreifen{self.pictureNum}.jpg', hsv)
        cv.imwrite(f'capture/capture{self.pictureNum}.jpg', imgclear)
        # cv.imwrite('capture/imgclear.jpg', imgclear)
        self.imgCam = imgclear
        self.pictureNum = self.pictureNum+1
        

#!/usr/bin/env python
#-------------------------------------------------------------------------------
# qwiic_otos_ex3_calibration.py
#
# This example demonstrates how to calibrate the SparkFun Qwiic Optical
# Tracking Odometry Sensor (OTOS).

# This example should be used to calibrate the linear and angular scalars of
# the OTOS to get the most accurate tracking performance. The linear scalar
# can be used to compensate for scaling issues with the x and y measurements,
# while the angular scalar can be used to compensate for scaling issues with
# the heading measurement. Note that if the heading measurement is off, that
# can also cause the x and y measurements to be off, so it's recommended to
# calibrate the angular scalar first.
#-------------------------------------------------------------------------------
# Written by SparkFun Electronics, May 2024
#
# This python library supports the SparkFun Electroncis Qwiic ecosystem
#
# More information on Qwiic is at https:#www.sparkfun.com/qwiic
#
# Do you like this library? Help support SparkFun. Buy a board!
#===============================================================================
# Copyright (c) 2023 SparkFun Electronics
#
# Permission is hereby granted, free of charge, to any person obtaining a copy 
# of this software and associated documentation files (the "Software"), to deal 
# in the Software without restriction, including without limitation the rights 
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell 
# copies of the Software, and to permit persons to whom the Software is 
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all 
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR 
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, 
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE 
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER 
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, 
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE 
# SOFTWARE.
#===============================================================================

import qwiic_otos
import sys
import time
import select
import tty
import termios

def reset(myOtos1,myOtos2):
    """Reset function called when a key is pressed during the main loop"""
    print("\r\n=== RESET FUNCTION CALLED ===")
    print("System reset completed!")
    print("===============================\r\n")
    myOtos1.calibrateImu(255)
    myOtos2.calibrateImu(255)
    myOtos1.resetTracking()
    myOtos2.resetTracking()

def kbhit():
    """Check if a key has been pressed (non-blocking)"""
    return select.select([sys.stdin], [], [], 0) == ([sys.stdin], [], [])

def runExample():
    print("\nQwiic OTOS Example 3 - Calibration\n")

    # Create instance of device
    myOtos1 = qwiic_otos.QwiicOTOS(0x17)
    myOtos2 = qwiic_otos.QwiicOTOS(0x19)

    # Check if it's connected
    if myOtos1.is_connected() == False:
        print("The device 1 isn't connected to the system. Please check your connection", \
            file=sys.stderr)
        return
    if myOtos2.is_connected() == False:
        print("The device 2 isn't connected to the system. Please check your connection", \
            file=sys.stderr)
        return

    # Initialize the device
    
    myOtos1.begin()
    myOtos1.setLinearUnit(myOtos1.kLinearUnitMeters)

    myOtos2.begin()
    myOtos2.setLinearUnit(myOtos2.kLinearUnitMeters)


    # myOtos1.setSignalProcessConfig(0b1111)
    # myOtos2.setSignalProcessConfig(0b1111)

    # c=myOtos1.getSignalProcessConfig()
    # print("Signal Process Config 1: ", bin(c))
    # c2=myOtos2.getSignalProcessConfig()
    # print("Signal Process Config 2: ", bin(c2))

    print("Press any key during the loop to call reset function...")
    print("Press Ctrl+C or 'q' to quit the program.")
    
    print("Ensure the OTOS is flat and stationary during calibration!")
    for i in range(1, 0, -1):
        print("Calibrating in %d seconds..." % i)
        time.sleep(1)

    print("Calibrating IMU...")

    # The IMU on the OTOS includes a gyroscope and accelerometer, which could
    # have an offset. Note that as of firmware version 1.0, the calibration
    # will be lost after a power cycle; the OTOS performs a quick calibration
    # when it powers up, but it is recommended to perform a more thorough
    # calibration at the start of all your programs. Note that the sensor must
    # be completely stationary and flat during calibration! When calling
    # calibrateImu(), you can specify the number of samples to take and whether
    # to wait until the calibration is complete. If no parameters are provided,
    # it will take 255 samples and wait until done; each sample takes about
    # 2.4ms, so about 612ms total
    myOtos1.calibrateImu(255)
    myOtos2.calibrateImu(255)

    # Alternatively, you can specify the number of samples and whether to wait
    # until it's done. If you don't want to wait, you can asynchronously check
    # how many samples remain with the code below. Once zero samples remain,
    # the calibration is done!
    # myOtos.calibrateImu(255, False)
    # done = False
    # while(done == False):
    #     # Check how many samples remain
    #     samplesRemaining = myOtos.getImuCalibrationProgress()

    #     # If 0 samples remain, the calibration is done
    #     if(samplesRemaining == 0):
    #         done = True

    # Here we can set the linear and angular scalars, which can compensate for
    # scaling issues with the sensor measurements. Note that as of firmware
    # version 1.0, these values will be lost after a power cycle, so you will
    # need to set them each time you power up the sensor. They can be any value
    # from 0.872 to 1.127 in increments of 0.001 (0.1%). It is recommended to
    # first set both scalars to 1.0, then calibrate the angular scalar, then
    # the linear scalar. To calibrate the angular scalar, spin the robot by
    # multiple rotations (eg. 10) to get a precise error, then set the scalar
    # to the inverse of the error. Remember that the angle wraps from -180 to
    # 180 degrees, so for example, if after 10 rotations counterclockwise
    # (positive rotation), the sensor reports -15 degrees, the required scalar
    # would be 3600/3585 = 1.004. To calibrate the linear scalar, move the
    # robot a known distance and measure the error; do this multiple times at
    # multiple speeds to get an average, then set the linear scalar to the
    # inverse of the error. For example, if you move the robot 100 inches and
    # the sensor reports 103 inches, set the linear scalar to 100/103 = 0.971
    myOtos1.setLinearScalar(0.989)
#    myOtos2.setLinearScalar(0.970)
    myOtos2.setLinearScalar(1.010)
    
    # myOtos1.setAngularScalar(0.9933)
    myOtos1.setAngularScalar(0.9941)
    # myOtos2.setAngularScalar(0.9915)
    myOtos2.setAngularScalar(0.9936)

    myOtos1.setSignalProcessConfig(0b1101)
    myOtos2.setSignalProcessConfig(0b1101)



    # Reset the tracking algorithm - this resets the position to the origin,
    # but can also be used to recover from some rare tracking errors
    
    myOtos1.resetTracking()
    myOtos2.resetTracking()
    
   

    # Main loop


    
    # Set terminal to non-canonical mode for immediate key detection
    old_settings = termios.tcgetattr(sys.stdin)
    tty.setraw(sys.stdin.fileno())
    
    try:
        while True:
            # Check for keyboard input (non-blocking)
            if kbhit():
                key = sys.stdin.read(1)
                
                # Check for Ctrl+C (ASCII 3) or 'q' to quit
                if ord(key) == 3 or key.lower() == 'q':  # Ctrl+C or 'q'
                    print("\r\nExiting program...")
                    break
                else:
                    reset(myOtos1, myOtos2)  # Call reset function for other keys
            
            
            # Get the latest position, which includes the x and y coordinates, plus
            # the heading angle
            myPosition1 = myOtos1.getPosition()
            myPosition2 = myOtos2.getPosition()
            
            # Get velocity information
            myVelocity1 = myOtos1.getVelocity()
            myVelocity2 = myOtos2.getVelocity()

            # Print measurement
            print("\r\nX1 : {:.1f} Y1 : {:.1f} H1: {:.1f} \r".format(myPosition1.x * 1000, myPosition1.y * 1000, myPosition1.h))
            print("X2 : {:.1f} Y2 : {:.1f} H2: {:.1f} \r".format(myPosition2.x * 1000, myPosition2.y * 1000, myPosition2.h))

            # Wait a bit so we don't spam the serial port
            time.sleep(0.5)
    
    finally:
        # Restore terminal settings
        termios.tcsetattr(sys.stdin, termios.TCSADRAIN, old_settings)

if __name__ == '__main__':
    try:
        runExample()
    except (KeyboardInterrupt, SystemExit) as exErr:
        print("\nEnding Example")
        sys.exit(0)

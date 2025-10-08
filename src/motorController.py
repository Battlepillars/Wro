import statistics
from slam import *
from drawBoard import *



class PIDController:
    def __init__(self, Kp, Ki, Kd, setpoint, min, max, drive = 0):
        self.Kp = Kp
        self.Ki = Ki
        self.Kd = Kd
        self.setpoint = setpoint
        self.previous_error = 0
        self.integral = 0
        self.min = min
        self.max = max
        self.drive = drive
    def reset(self):
        self.previous_error = 0
        self.integral = 0
        

    def compute(self, process_variable, dt, slam=None):
            # Calculate error
            error = self.setpoint - process_variable
            
            # if (self.drive == 1) and (slam != None):
            #     if len(slam.errorDriveList) > 41:
            #         slam.errorDriveList.pop(0)
            #     slam.errorDriveList.append(1 - (process_variable/self.setpoint))
            #     # print("errorDriveList: ", slam.errorDriveList, " mean: ", statistics.mean(slam.errorDriveList), " speed: ", slam.speed)
            #     if (statistics.mean(slam.errorDriveList) > 0.9) and (slam.speed < 0.1) and (len(slam.errorDriveList) > 40):
            #         slam.crash = 1
            
            # Proportional term
            P_out = self.Kp * error
            
            # Integral term
            self.integral += error * dt
            
            if self.Ki * self.integral > self.max:
                self.integral = self.max / self.Ki
            if self.Ki * self.integral < self.min:
                self.integral = self.min / self.Ki
            I_out = self.Ki * self.integral
            
            # Derivative term
            derivative = (error - self.previous_error) / dt
            D_out = self.Kd * derivative
            
            # Compute total output
            output = P_out + I_out + D_out
            
            # Update previous error
            self.previous_error = error
            if output > self.max:
                output = self.max
            if output < self.min:
                output = self.min
            
            # if (self.drive == 1) and (slam != None):
            #     if len(slam.errorDriveList) > 100:
            #         slam.errorDriveList.pop(0)
            #     slam.errorDriveList.append(output)
            #     # print("errorDriveList: ", slam.errorDriveList, " mean: ", statistics.mean(slam.errorDriveList), " speed: ", slam.speed)
            #     if (statistics.mean(slam.errorDriveList) > (self.max/1.2)) and (slam.speed < 0.2) and (len(slam.errorDriveList) > 100):
            #         slam.crash = 1
            
            return output

def setServoAngle(kit,angle,slam=None):
    servoMitte=80
    
    target = angle - 90 + servoMitte
    if target > 180:
        target = 180
    if target < 0:
        target = 0
    
    #170 links    # 0,01111111111111111111111111111111
    #80 mitte
    #0 rechts     # 0,0125
    
    
    
    kit.servo[0].angle = target
    if slam != None:
        if target == 80:
            slam.wheelAngle = 0
        elif target > 80:
            slam.wheelAngle = -(target - 80) * 1/90
        else:
            slam.wheelAngle = -(target - 80) * 1/80
        #slam.wheelAngle = target 


class DriveBase:
    slam:Slam
    kit:ServoKit
    zielWinkel = 5000
    distanci = 0
    startTimeDrive = 5000
    lastKurveSpeed=1

    def __init__(self, slam, kit):
        self.slam = slam
        self.kit = kit
        # if slam.eventType == slam.ER:
        #     self.pidController = PIDController(Kp=20, Ki=5, Kd=1.00, setpoint=1, min=-30, max=40, drive=1)
        #     self.pidSteer = PIDController(Kp=3, Ki=0, Kd=0, setpoint=0, min=-90, max=90)
        # else:
        #     self.pidController = PIDController(Kp=20, Ki=5, Kd=1.00, setpoint=1, min=-30, max=40, drive=1)
        #     self.pidSteer = PIDController(Kp=5, Ki=0, Kd=0, setpoint=0, min=-90, max=90)
        
        self.pidController = PIDController(Kp=20, Ki=5, Kd=1.00, setpoint=1, min=-50, max=40, drive=1)
        self.pidSteer = PIDController(Kp=2, Ki=0, Kd=0, setpoint=0, min=-90, max=90)

    def driveTo(self, x, y, speed, brake):
        """
        Drive the robot to a specific coordinate (x, y) with controlled speed and optional braking.
        
        Args:
            x (float): Target x-coordinate in millimeters
            y (float): Target y-coordinate in millimeters  
            speed (float): Desired speed in m/s (positive for forward, negative for reverse)
            brake (int): Braking mode (1 = enable progressive braking near target, 0 = no braking)
            
        Returns:
            bool: True when target is reached (within 30mm), False while still driving
        """
        # Set the target speed for the PID controller
        self.pidController.setpoint = speed
        
        # Calculate straight-line distance from current position to target
        distance = math.sqrt(math.pow((self.slam.xpos - x),2) + math.pow((self.slam.ypos - y),2))
        
        # Calculate the required heading angle to reach the target
        # atan2 gives angle from current position to target, negated to match robot coordinate system
        zielwinkel = -(math.atan2(self.slam.ypos - y, self.slam.xpos - x) / math.pi * 180)
        
        # Calculate heading error (difference between current and required heading)
        fehlerwinkel = -zielwinkel + self.slam.angle
        
        # Normalize heading error to [-180, +180] degree range
        # This ensures we always take the shortest angular path to the target
        while fehlerwinkel > 180:
            fehlerwinkel -= 360
        while fehlerwinkel < -180:
            fehlerwinkel += 360
        
        # Initialize target angle on first call (5000 is sentinel value for "not set")
        if self.zielWinkel == 5000:
            self.zielWinkel = zielwinkel
        
        # Calculate distance along the original target line (corrected for any heading drift)
        # This gives us the "useful" distance - how much progress we've made toward the target
        distanceLine = distance * math.cos((self.zielWinkel - zielwinkel) / 180 * math.pi)
        
        # Progressive braking: reduce speed as we approach the target
        # When within 200mm and braking enabled, scale speed proportionally to remaining distance
        if (abs(distanceLine) < 200) and (brake == 1):
            self.pidController.setpoint = speed * distanceLine / 200
        
        # Calculate steering correction using PID controller
        # fehlerwinkel is the input, outputSteer is the steering angle correction
        outputSteer = self.pidSteer.compute(fehlerwinkel,1)
        
        # Calculate motor speed correction using PID controller
        # Compares actual speed (slam.speed) with target speed (setpoint)
        output = self.pidController.compute(self.slam.speed,0.5,self.slam)
        
        # Limit steering output to prevent excessive steering angles
        # ±55 degrees is the maximum safe steering for faster driving
        if (outputSteer>55):
            outputSteer = 55
        if (outputSteer<-55):
            outputSteer = -55
            
        # Apply steering: 90° is straight ahead, add correction for turning
        setServoAngle(self.kit,90 + outputSteer,self.slam)
        
        # Apply motor control: 99° is forward base speed, add PID correction
        self.kit.servo[3].angle = 99 + output
        
        # Check if we've reached the target (within 30mm tolerance)
        if distanceLine < 30:
            # Reset target angle for next movement command
            self.zielWinkel = 5000
            # Stop the motor (90° = neutral position)
            self.kit.servo[3].angle = 90
            return True  # Target reached
        else:
            return False  # Still driving to target

    def drivekürvchen(self, dist, angli, speed, brake):
        if (speed<0 and self.lastKurveSpeed > 0):
            self.pidController.reset()
            print("+++++++++++++++++++++++++++++++++++++++++++++reset PID Controller")
        self.lastKurveSpeed = speed
        self.pidController.setpoint = speed
        speedTotal = self.slam.speed

        self.distanci = self.distanci + speedTotal * 10
        distenceLeft = dist - self.distanci

        if (distenceLeft < 30) and (brake == 1):
            if (speed>0):
                self.pidController.setpoint = 0.1
            else:
                self.pidController.setpoint = -0.1

        if (distenceLeft < 10) and (brake == 1):
            self.pidController.setpoint = 0

        if speed < 0:
            output = self.pidController.compute(-speedTotal,0.5)
        else:
            output = self.pidController.compute(speedTotal,0.5)


        setServoAngle(self.kit,90+angli,self.slam)

        if (self.pidController.setpoint==0):
            self.kit.servo[3].angle=90
        else:
            if (speed>0):
                self.kit.servo[3].angle = 110 + output
            else:
                self.kit.servo[3].angle = 80 + output
        #print("distenceLeft: ",math.floor(distenceLeft)," setpoint: ",self.pidController.setpoint," speedTotal: ",speedTotal, " output: ", math.floor(output))
        if (distenceLeft<10) and ((speedTotal<0.05) or (brake == 0)):
            self.distanci = 0
            self.kit.servo[3].angle = 90
            self.lastKurveSpeed=1
            return True
        else:
            return False
        
    def driveToWinkel(self, zielwinkel, speed, brake,dir):
        self.pidController.setpoint = speed
        fehlerwinkel = -zielwinkel + self.slam.angle


        while fehlerwinkel > 180:
            fehlerwinkel -= 360
        while fehlerwinkel < -180:
            fehlerwinkel += 360

        if (abs(fehlerwinkel) < 50) and (brake == 1):
            if speed > 0:
                self.pidController.setpoint = 0.1
            elif speed < 0:
                self.pidController.setpoint = -0.1

        if (dir==0):
            if fehlerwinkel < 0:
                outputSteer = 90
            else:
                outputSteer = -90
        elif (dir==100):               # CW 100=orders.CW
            outputSteer = -90
        else:
            outputSteer = 90           #CCW

        if speed < 0:
            speedTotal = -self.slam.speed
        else:
            speedTotal = self.slam.speed
        output = self.pidController.compute(speedTotal, 0.5)
        #print(" head: ", math.floor(self.slam.angle), "zielwinkel: ", math.floor(zielwinkel), "Fehlerwinkel: ", fehlerwinkel)

        if speed < 0:
            outputSteer = -outputSteer
        setServoAngle(self.kit, 90 + outputSteer,self.slam)
        # print(output)
        
        if (output>0):
            self.kit.servo[3].angle = 99 + output
        else:
            self.kit.servo[3].angle = 91 + output

        if abs(fehlerwinkel) < 4:
            self.kit.servo[3].angle = 90
            return True
        else:
            return False



    def driveToTime(self, x, y, speed, timeDrive, startTime):
        self.pidController.setpoint = speed

        zielwinkel = -(math.atan2(self.slam.ypos - y, self.slam.xpos - x) / math.pi * 180)

        if self.startTimeDrive == 5000:
            self.startTimeDrive = time.time()-startTime
    
        timeLeft = timeDrive - (time.time()-startTime - self.startTimeDrive) 

        fehlerwinkel = -zielwinkel + self.slam.angle
        while fehlerwinkel > 180:
            fehlerwinkel -= 360
        while fehlerwinkel < -180:
            fehlerwinkel += 360

        if self.zielWinkel == 5000:
            self.zielWinkel = zielwinkel


        outputSteer = self.pidSteer.compute(fehlerwinkel,1)

        output = self.pidController.compute(self.slam.speed,0.5)


        setServoAngle(self.kit,90 + outputSteer,self.slam)
        self.kit.servo[3].angle = 99 + output

        if timeLeft < 0.1:
            self.kit.servo[3].angle = 90
            self.startTimeDrive = 5000
            return True
        else:
            return False
    
    
    def driveTimePower(self, timeDrive, speed, startTime):
        

        if self.startTimeDrive == 5000:
            self.startTimeDrive = time.time()-startTime
    
        timeLeft = timeDrive - (time.time()-startTime - self.startTimeDrive) 

        setServoAngle(self.kit, 90, self.slam) 


        self.kit.servo[3].angle = speed

        if timeLeft < 0.1:
            self.kit.servo[3].angle = 90
            self.startTimeDrive = 5000
            return True
        else:
            return False
    def driveTime(self, timeDrive, speed):
        self.pidController.setpoint = speed
        speedTotal = self.slam.speed

        if self.startTimeDrive == 5000:
            self.startTimeDrive = time.time()-startTime
    
        timeLeft = timeDrive - (time.time()-startTime - self.startTimeDrive) 

        if speed < 0:
            output = self.pidController.compute(-speedTotal,0.5)
        else:
            output = self.pidController.compute(speedTotal,0.5)

        setServoAngle(self.kit, 90, self.slam) 

        if (self.pidController.setpoint==0):
            self.kit.servo[3].angle=90
        else:
            if (output>0):
                self.kit.servo[3].angle = 110 + output
            else:
                self.kit.servo[3].angle = 80 + output

        if timeLeft < 0.1:
            self.kit.servo[3].angle = 90
            self.startTimeDrive = 5000
            return True
        else:
            return False
    
    def crashRecovery(self):
        self.kit.servo[3].angle = 70
        setServoAngle(self.kit,90,self.slam)
        time.sleep(1)
        self.kit.servo[3].angle = 90
        self.slam.crash = 0
        self.slam.errorDriveList.clear()
    
    def driveToY(self, y, zielwinkel, speed, brake):
        self.pidController.setpoint = speed
        
        if speed > 0:
            speedTotal = self.slam.speed
        else:
            speedTotal = -self.slam.speed

        distenceLeft = abs(y - self.slam.ypos)
        # print("distenceLeft: ", distenceLeft)

        if (distenceLeft < 30) and (brake == 1):
            if (speed>0):
                self.pidController.setpoint = 0.1
            else:
                self.pidController.setpoint = -0.1

        if (distenceLeft < 10) and (brake == 1):
            self.pidController.setpoint = 0
        

        output = self.pidController.compute(speedTotal,0.5)

        fehlerwinkel = -zielwinkel + self.slam.angle
        while fehlerwinkel > 180:
            fehlerwinkel -= 360
        while fehlerwinkel < -180:
            fehlerwinkel += 360
        
        outputSteer = -self.pidSteer.compute(fehlerwinkel,1)
        if (outputSteer>55):
            outputSteer = 55
        if (outputSteer<-55):
            outputSteer = -55
        setServoAngle(self.kit,90 + outputSteer,self.slam)
        self.kit.servo[3].angle = 99 + output

        # if (self.pidController.setpoint==0):
        #     self.kit.servo[3].angle=90
        # else:
        #     if (output>0):
        #         self.kit.servo[3].angle = 110 + output
        #     else:
        #         self.kit.servo[3].angle = 80 + output
        
        if (distenceLeft<10) and ((speedTotal<0.05) or (brake == 0)):
            self.kit.servo[3].angle = 90
            return True
        else:
            return False

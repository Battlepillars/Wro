from slam import *
from drawBoard import *



class PIDController:
    def __init__(self, Kp, Ki, Kd, setpoint, min, max):
        self.Kp = Kp
        self.Ki = Ki
        self.Kd = Kd
        self.setpoint = setpoint
        self.previous_error = 0
        self.integral = 0
        self.min = min
        self.max = max

    def compute(self, process_variable, dt):
            # Calculate error
            error = self.setpoint - process_variable
            
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

    def __init__(self, slam, kit):
        self.slam = slam
        self.kit = kit
        if slam.eventType == slam.ER:
            self.pidController = PIDController(Kp=20, Ki=5, Kd=1.00, setpoint=1, min=-30, max=80)
            self.pidSteer = PIDController(Kp=3, Ki=0, Kd=0, setpoint=0, min=-90, max=90)
        else:
            self.pidController = PIDController(Kp=20, Ki=5, Kd=1.00, setpoint=1, min=-30, max=40)
            self.pidSteer = PIDController(Kp=5, Ki=0, Kd=0, setpoint=0, min=-90, max=90)

    def driveTo(self, x, y, speed, brake):
        self.pidController.setpoint = speed
        
        distance = math.sqrt(math.pow((self.slam.xpos - x),2) + math.pow((self.slam.ypos - y),2))
        zielwinkel = -(math.atan2(self.slam.ypos - y, self.slam.xpos - x) / math.pi * 180)
        
        
        fehlerwinkel = -zielwinkel + self.slam.angle
        while fehlerwinkel > 180:
            fehlerwinkel -= 360
        while fehlerwinkel < -180:
            fehlerwinkel += 360
        
        if self.zielWinkel == 5000:
            self.zielWinkel = zielwinkel
        
        distanceLine = distance * math.cos((self.zielWinkel - zielwinkel) / 180 * math.pi)
        
        if (abs(distanceLine) < 200) and (brake == 1):
            self.pidController.setpoint = speed * distanceLine / 200
        
        outputSteer = self.pidSteer.compute(fehlerwinkel,1)
        
        output = self.pidController.compute(self.slam.speed,0.5)
        
        
        setServoAngle(self.kit,90 + outputSteer,self.slam)
        self.kit.servo[3].angle = 99 + output
        
        if distanceLine < 30:
            self.zielWinkel = 5000
            self.kit.servo[3].angle = 90
            return True
        else:
            return False

    def drivekürvchen(self, dist, angli, speed, brake):
        self.pidController.setpoint = speed
        speedTotal = self.slam.speed

        self.distanci = self.distanci + speedTotal * 10
        distenceLeft= dist - self.distanci

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
            if (output>0):
                self.kit.servo[3].angle = 110 + output
            else:
                self.kit.servo[3].angle = 80 + output
        #print("distenceLeft: ",math.floor(distenceLeft)," setpoint: ",self.pidController.setpoint," speedTotal: ",speedTotal, " output: ", math.floor(output))
        if (distenceLeft<10) and ((speedTotal<0.05) or (brake == 0)):
            self.distanci = 0
            self.kit.servo[3].angle = 90
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

        if (abs(fehlerwinkel) < 10) and (brake == 1):
            self.pidController.setpoint = speed * abs(fehlerwinkel) / 10
        if (dir==0):
            if fehlerwinkel < 0:
                outputSteer = 90
            else:
                outputSteer = -90
        elif (dir==100):               # CW 100=orders.CW
            outputSteer = -90
        else:
            outputSteer = 90           #CCW

        speedTotal = self.slam.speed
        output = self.pidController.compute(speedTotal, 0.5)

        #print(" head: ", math.floor(self.slam.angle), "zielwinkel: ", math.floor(zielwinkel), "Fehlerwinkel: ", fehlerwinkel)

        setServoAngle(self.kit, 90 + outputSteer,self.slam)
        self.kit.servo[3].angle = 99 + output

        if abs(fehlerwinkel) < 5:
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
    
    def driveTime(self, timeDrive, speed, startTime):
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
from slam import *

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

class DriveBase:
    slam:Slam
    kit:ServoKit
    zielWinkel = 5000
    distanci = 0

    def __init__(self, slam, kit):
        self.slam = slam
        self.kit = kit
        self.pidController = PIDController(Kp=20, Ki=5, Kd=1.00, setpoint=1, min=-80, max=80)
        self.pidSteer = PIDController(Kp=7, Ki=0, Kd=0, setpoint=0, min=-90, max=90)

    def driveTo(self, x, y, speed, brake):
        self.pidController.setpoint = speed

        distance = math.sqrt(math.pow((self.slam.xpos - x),2) + math.pow((self.slam.ypos - y),2))
        angle = -(math.atan2(self.slam.ypos - y, self.slam.xpos - x) / math.pi * 180)

        #if distance < 200:
        #   self.pidController.setpoint = 0

        blb = angle
        angle = -angle + self.slam.angle
        while angle > 180:
            angle -= 360
        while angle < -180:
            angle += 360

        if self.zielWinkel == 5000:
            self.zielWinkel = blb

        distanceLine = distance * math.cos(self.zielWinkel / 180 * math.pi)

        if (distanceLine < 200) and (brake == 1):
            self.pidController.setpoint = speed * distanceLine / 200

        outputSteer = self.pidSteer.compute(angle,1)


        speedTotal = self.slam.speed
        output = self.pidController.compute(speedTotal,0.5)


        if abs(distanceLine) < 30:
            xcl = 1
        else:
            xcl = 0


        print(math.floor(distanceLine), math.floor(self.slam.angle), math.floor(blb),x,y,xcl)
        self.kit.servo[0].angle = 90 + outputSteer
        self.kit.servo[3].angle = 99 + output

        if abs(distanceLine) < 30:
            self.zielWinkel = 5000
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

        print(math.floor(self.distanci),math.floor(distenceLeft), speedTotal,output)
        self.kit.servo[0].angle = 90+angli

        if (self.pidController.setpoint==0):
            self.kit.servo[3].angle=90
        else:
            if (output>0):
                self.kit.servo[3].angle = 110 + output
            else:
                self.kit.servo[3].angle = 80 + output

        if (distenceLeft<10) and ((speedTotal<0.05) or (brake == 0)):
            self.distanci = 0
            return True
        else:
            return False
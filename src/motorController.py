import statistics
from slam import *
from drawBoard import *

# Track min/max of raw input angles passed to setServoAngle
_servo_angle_min = None
_servo_angle_max = None



class PIDController:
    def __init__(self, Kp, Ki, Kd, setpoint, min, max, drive = 0):
        """@brief Initialize a PID controller instance.

        @param Kp float Proportional gain.
        @param Ki float Integral gain.
        @param Kd float Derivative gain.
        @param setpoint float Target value the controller drives toward.
        @param min float Minimum output clamp.
        @param max float Maximum output clamp.
        @param drive int Optional flag (1 if used for drive motor diagnostics).
        """
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
        """@brief Reset accumulated integral and derivative history.

        Call when direction changes or large setpoint jump occurs to avoid
        stale integral causing windup.
        @return None
        """
        self.previous_error = 0
        self.integral = 0
        

        def compute(self, process_variable, dt, slam=None):
            """@brief Compute PID output for current process variable.

            Applies anti-windup clamping for integral term then combines P,I,D.
            @param process_variable float Current measured value.
            @param dt float Elapsed time (seconds) since last compute.
            @param slam Slam|None Optional slam object for extended diagnostics.
            @return float Controller output within [min,max].
            """
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
    """@brief Set steering servo to requested logical steering angle.

    Converts logical angle (0..180 with 90 center) to physical servo channel
    angle applying center offset and travel limits. Optionally records wheel
    angle in slam state for visualization.

    @param kit ServoKit ServoKit instance controlling PWM outputs.
    @param angle float Logical desired angle (0 left lock .. 180 right lock, 90 straight).
    @param slam Slam|None Optional slam object to store normalized wheelAngle.
    @return None
    """
    # global _servo_angle_min, _servo_angle_max

    # # Update min/max tracking for raw input angle
    # if _servo_angle_min is None or angle < _servo_angle_min:
    #     _servo_angle_min = angle
    # if _servo_angle_max is None or angle > _servo_angle_max:
    #     _servo_angle_max = angle
    if ((slam is None) or (not slam.finalMove)):
        if (angle<25):
            angle=25
        if (angle>170):
            angle=170
    # if (slam != None) and (slam.finalMove):
    #     slam.logger.warn("Final Move - setServoAngle called with angle: {}".format(angle))

    #print(f"[setServoAngle] raw angle: {angle:.2f}  min: {_servo_angle_min:.2f}  max: {_servo_angle_max:.2f}")
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
        """@brief Construct drive base providing high-level motion primitives.

        @param slam Slam Shared SLAM/pose object.
        @param kit ServoKit Servo controller instance for motor + steering.
        Initializes speed & steering PID controllers with tuned gains.
        @return None
        """
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
        """@brief Drive toward absolute (x,y) field coordinate.

        Implements heading error correction + progressive braking as distance
        shrinks. Uses dual PID (speed & steering).
        @param x float Target X (mm).
        @param y float Target Y (mm).
        @param speed float Desired linear speed (m/s) sign indicates direction.
        @param brake int 1 enables distance-proportional slowdown; 0 disables.
        @return bool True when within 30 mm projected distance, else False.
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
        """@brief Drive a short arc maintaining fixed steering angle (angli).

        Tracks cumulative distance and applies staged braking near end.
        @param dist float Target travel distance
        @param angli float Steering offset (degrees added to center 90).
        @param speed float Target linear speed (m/s, sign for direction).
        @param brake int Enable progressive brake logic if 1.
        @return bool True when finished; False otherwise.
        """
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
        """@brief Rotate robot to target heading (zielwinkel) while moving.

        Chooses steering saturation based on direction hint (dir) and applies
        speed PID for motion. Braking reduces target speed near completion.
        @param zielwinkel float Target heading in degrees.
        @param speed float Desired translational speed (m/s).
        @param brake int Enables slowdown as |error| < 50 if 1.
        @param dir int Direction code (0 auto, 100 CW, else CCW).
        @return bool True when heading error < 4°, else False.\n+        """
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
        """@brief Drive toward (x,y) for a fixed duration then stop.

        Similar to driveTo but terminates based on elapsed time not distance.
        @param x float Target X (mm) used for heading only.
        @param y float Target Y (mm) used for heading only.
        @param speed float Desired speed (m/s).
        @param timeDrive float Duration (s) to sustain motion.
        @param startTime float Program start reference for timing.
        @return bool True when remaining time < 0.1s; else False.
        """
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
        """@brief Apply raw servo speed (PWM angle) for fixed duration.

        Bypasses PID; directly sets motor channel to provided speed angle.
        @param timeDrive float Duration (s).
        @param speed int Servo angle (approx PWM) for motor channel.
        @param startTime float Program start reference.
        @return bool True when finished else False.
        """
        

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
        """@brief Maintain target speed for fixed time using PID.

        @param timeDrive float Duration (s) to drive.
        @param speed float Desired speed (m/s) sign = direction.
        @return bool True when elapsed >= timeDrive threshold.
        """
        self.pidController.setpoint = speed
        speedTotal = self.slam.speed
        startTime = 0 ###

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
        """@brief Simple reverse + straighten sequence to recover from stall.

        This function is unfinished and currently not used
        @return None
        """
        self.kit.servo[3].angle = 70
        setServoAngle(self.kit,90,self.slam)
        time.sleep(1)
        self.kit.servo[3].angle = 90
        self.slam.crash = 0
        self.slam.errorDriveList.clear()
    
    def driveToY(self, y, zielwinkel, speed, brake):
        """@brief Drive along Y axis toward target Y maintaining heading.

        Applies progressive braking as remaining |Y - current| shrinks.
        @param y float Target Y coordinate (mm).
        @param zielwinkel float Desired heading angle (deg) while translating.
        @param speed float Desired linear speed (m/s).
        @param brake int Enable slowdown near target (1 yes, 0 no).
        @return bool True when within 10 mm (and slowed/stopped) else False.
        """
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
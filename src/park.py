import time

from slam import Hindernisse
import pygame

def waitForKeyPress():
    """Wait for any key to be pressed"""
    print("Press any key to continue...")
    waiting = True
    while waiting:
        for event in pygame.event.get():
            if event.type == pygame.KEYDOWN:
                waiting = False
                break
        time.sleep(0.05)

def doReposition(orders, Order, waitCompleteOrders, angleCheck):
    if not waitCompleteOrders():
        return
    time.sleep(0.3)
    orders.append(Order(angleCheckOverwrite=angleCheck,type=Order.REPOSITION))
    if not waitCompleteOrders():
        return
    time.sleep(0.3)

def doReposition2(orders, Order, waitCompleteOrders, direction):
    if direction == Order.CW:
        angleCheck = 0
    else:
        angleCheck = -90
    
    if not waitCompleteOrders():
        return
    time.sleep(0.3)
    orders.append(Order(angleCheckOverwrite=angleCheck,type=Order.REPOSITION))
    if not waitCompleteOrders():
        return
    time.sleep(0.3)

def wallScan(slam,waitCompleteOrders):
    if not waitCompleteOrders():
        return
    time.sleep(0.3)
    # print("X:", slam.xpos, "Y:", slam.ypos, "Angle:", slam.angle, "average:", average, "average3:", 3000 - average)
    slam.logger.warn('-----------------------------------------------------------------------------------------')
    slam.logger.warning('Park Wall Repostion x: %i y: %i angle: %i',slam.xpos,slam.ypos,slam.angle)
    print("Park Wall Repostion")
    averageL = 1625 + slam.scan[90]
    averageR = 2000 - slam.scan[-90]
    average = (averageL + averageR) / 2
    print(f"Wall Scan - Left: {averageL}, Right: {averageR}, Average: {average} Old: {slam.xpos}")
    
    slam.setPostion(average, slam.ypos)
    slam.logger.warning('x-> %i ',average)

def park(orders,Order, waitCompleteOrders, checkForColor, direction, scanStart, slam):
    speedi = 0.5
    
    if direction == Order.CW:
        if (checkForColor(Hindernisse.GREEN, scanStart, scanStart+6) and not checkForColor(Hindernisse.RED, scanStart+2, scanStart+6)) and checkForColor(Hindernisse.RED, scanStart+6, scanStart+7):
            # rot nach rot
            print("CW Rot nach Rot")
            orders.append(Order(x=2600, y=2200,speed=speedi,brake=0,type=Order.DESTINATION,num=33))
            orders.append(Order(zielwinkel=0, speed=0.5, brake=1, type=Order.WINKEL))
            doReposition(orders, Order, waitCompleteOrders, 0)
        
        if (checkForColor(Hindernisse.GREEN, scanStart, scanStart+6) and not checkForColor(Hindernisse.RED, scanStart+2, scanStart+6)) and not checkForColor(Hindernisse.RED, scanStart+6, scanStart+7):
            print("CW Rot nach Grün oder nichts ")
            #rot nach grün oder nichts
            # orders.append(Order(x=2550, y=2450,speed=speedi,brake=0,type=Order.DESTINATION,num=371))
            orders.append(Order(x=2700, y=2450,speed=speedi,brake=1,type=Order.DESTINATION,num=371))
            orders.append(Order(zielwinkel=0, speed=0.5, brake=1, type=Order.WINKEL))
            if not waitCompleteOrders():
                return
            time.sleep(0.3)
            orders.append(Order(angleCheckOverwrite=0,type=Order.REPOSITION))
            if not waitCompleteOrders():
                return
            time.sleep(0.3)
        if (checkForColor(Hindernisse.RED, scanStart, scanStart+6) and not checkForColor(Hindernisse.GREEN, scanStart+4, scanStart+6)):
            print("CW Variante 3")
            if not checkForColor(Hindernisse.RED, scanStart+6, scanStart+7):
                orders.append(Order(x=2300, y=2300,speed=speedi,brake=0,type=Order.DESTINATION,num=34))
        
        if checkForColor(Hindernisse.RED, scanStart+6, scanStart+7):
            print("CW Variante 4")
            orders.append(Order(x=2000, y=2200,speed=speedi,brake=0,type=Order.DESTINATION,num=35))
            orders.append(Order(x=1600, y=2200,speed=speedi,brake=1,type=Order.DESTINATION,num=36))
            time.sleep(3)
            orders.append(Order(zielwinkel=-90, speed=-0.2, brake=1, type=Order.WINKEL))
            doReposition(orders, Order, waitCompleteOrders, 0)
        else:
            print("CW Variante 5")
            #waitForKeyPress()
            doReposition(orders, Order, waitCompleteOrders, 0)
            orders.append(Order(x=2000, y=2600,speed=speedi,brake=0,type=Order.DESTINATION,num=30))
            orders.append(Order(x=1880, y=2600,speed=speedi,brake=1,type=Order.DESTINATION,num=31))
            orders.append(Order(zielwinkel=-90, speed=0.2, brake=1, type=Order.WINKEL))
            # orders.append(Order(x=1745, y=2275,speed=0.2,brake=1,type=Order.DESTINATION,num=32))
            # orders.append(Order(zielwinkel=-90, speed=0.2, brake=1, type=Order.WINKEL))
            # doReposition(orders, Order, waitCompleteOrders, 0)
            #waitForKeyPress()
    
    else:           # CCW
        if (checkForColor(Hindernisse.RED, scanStart, scanStart-6) and not checkForColor(Hindernisse.GREEN, scanStart-2, scanStart-6)) and checkForColor(Hindernisse.GREEN, scanStart-6, scanStart-7):
            orders.append(Order(x=400, y=2200,speed=speedi,brake=0,type=Order.DESTINATION,num=38))
        
        if (checkForColor(Hindernisse.GREEN, scanStart, scanStart-6) and not checkForColor(Hindernisse.RED, scanStart-4, scanStart-6)):
            if not checkForColor(Hindernisse.RED, scanStart-6, scanStart-7):
                orders.append(Order(x=700, y=2300,speed=speedi,brake=0,type=Order.DESTINATION,num=34))
        
        if checkForColor(Hindernisse.GREEN, scanStart-12, scanStart-6):
            orders.append(Order(x=1000, y=2200,speed=speedi,brake=0,type=Order.DESTINATION,num=39))
            orders.append(Order(x=1700, y=2200,speed=speedi,brake=1,type=Order.DESTINATION,num=40))
            orders.append(Order(x=1850, y=2200,speed=0.2,brake=1,type=Order.DESTINATION,num=40))
            time.sleep(3)
            orders.append(Order(zielwinkel=-90, speed=-0.2, brake=1, type=Order.WINKEL))
            doReposition(orders, Order, waitCompleteOrders, -90)
        else:
            orders.append(Order(x=1000, y=2600,speed=speedi,brake=0,type=Order.DESTINATION,num=41))
            orders.append(Order(x=1676, y=2600,speed=speedi,brake=1,type=Order.DESTINATION,num=42))
            orders.append(Order(zielwinkel=-90, speed=0.2, brake=1, type=Order.WINKEL))
            orders.append(Order(x=1705, y=2275,speed=0.2,brake=1,type=Order.DESTINATION,num=43))
            orders.append(Order(zielwinkel=-90, speed=0.2, brake=1, type=Order.WINKEL))
            doReposition(orders, Order, waitCompleteOrders, -90)


    optimalX = 2000-220#1745 # (1795|2685) - Optimale Position zum Einparken
    optimalY = 2655
    # adjustedX = optimalX
    # if slam.xpos < optimalX - 10:
    #     adjustedX += 10
    # elif slam.xpos > optimalX + 10:
    #     adjustedX -= 10
    
    if not waitCompleteOrders():
        return
    time.sleep(0.3)
    
    slam.repositionOneDirFront(90)
    orders.append(Order(y=2815, zielwinkel=-90, speed=-0.2, brake=1, type=Order.DRIVETOY))
    orders.append(Order(zielwinkel=-90, speed=0.2, brake=1, type=Order.WINKEL))
    #doReposition2(orders, Order, waitCompleteOrders, direction)
    wallScan(slam,waitCompleteOrders)
    loops = 0

    print("Starting parking alignment loop")
    #waitForKeyPress()
    
    while ((slam.xpos < (optimalX - 10) or slam.xpos > (optimalX + 10)) and (loops < 3)) or (loops == 0):
        loops += 1
        print("loop ", loops)
        adjustedX = optimalX            # move waypoint left or right to account for movement caused by turning
        if slam.xpos < optimalX:
            adjustedX += 10
            print("adjusting right")
        elif slam.xpos > optimalX:
            adjustedX -= 10
            print("adjusting left")
        orders.append(Order(x=adjustedX, y=2550, speed=0.2, brake=1, type=Order.DESTINATION, num=372))
        orders.append(Order(zielwinkel=-90, speed=0.2, brake=1, type=Order.WINKEL))
        orders.append(Order(y=2815, zielwinkel=-90, speed=-0.2, brake=1, type=Order.DRIVETOY))

        wallScan(slam,waitCompleteOrders)
        print("2")    
        #waitForKeyPress()
    print("Done, Final move")
    #waitForKeyPress()   
    orders.append(Order(x=optimalX, y=optimalY, speed=0.2, brake=1, type=Order.DESTINATION, num=373))
    orders.append(Order(zielwinkel=0, speed=-0.2, brake=1, type=Order.WINKEL))
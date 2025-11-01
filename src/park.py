import time
from slam import Hindernisse

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

def park(orders,Order, waitCompleteOrders, checkForColor, direction, scanStart, slam):
    speedi = 0.5
    
    if direction == Order.CW:
        if (checkForColor(Hindernisse.GREEN, scanStart, scanStart+6) and not checkForColor(Hindernisse.RED, scanStart+2, scanStart+6)) and checkForColor(Hindernisse.RED, scanStart+6, scanStart+7):
            orders.append(Order(x=2600, y=2200,speed=speedi,brake=0,type=Order.DESTINATION,num=33))
        
        if (checkForColor(Hindernisse.RED, scanStart, scanStart+6) and not checkForColor(Hindernisse.GREEN, scanStart+4, scanStart+6)):
            if not checkForColor(Hindernisse.RED, scanStart+6, scanStart+7):
                orders.append(Order(x=2300, y=2300,speed=speedi,brake=0,type=Order.DESTINATION,num=34))
        
        if checkForColor(Hindernisse.RED, scanStart+6, scanStart+7):
            orders.append(Order(x=2000, y=2200,speed=speedi,brake=0,type=Order.DESTINATION,num=35))
            orders.append(Order(x=1600, y=2200,speed=speedi,brake=1,type=Order.DESTINATION,num=36))
            time.sleep(3)
            orders.append(Order(zielwinkel=-90, speed=-0.2, brake=1, type=Order.WINKEL))
            doReposition(orders, Order, waitCompleteOrders, 0)
        else:
            orders.append(Order(x=2000, y=2600,speed=speedi,brake=0,type=Order.DESTINATION,num=30))
            orders.append(Order(x=1800, y=2600,speed=speedi,brake=1,type=Order.DESTINATION,num=31))
            orders.append(Order(zielwinkel=-90, speed=0.2, brake=1, type=Order.WINKEL))
            orders.append(Order(x=1745, y=2275,speed=0.2,brake=1,type=Order.DESTINATION,num=32))
            orders.append(Order(zielwinkel=-90, speed=0.2, brake=1, type=Order.WINKEL))
            doReposition(orders, Order, waitCompleteOrders, 0)
    
    else:
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


    optimalX = 1745 # (1795|2685) - Optimale Position zum Einparken
    optimalY = 2655
    adjustedX = optimalX
    if slam.xpos < optimalX - 10:
        adjustedX += 10
    elif slam.xpos > optimalX + 10:
        adjustedX -= 10
    
    orders.append(Order(y=optimalY, zielwinkel=-90, speed=-0.2, brake=1, type=Order.DRIVETOY))
    orders.append(Order(zielwinkel=-90, speed=0.2, brake=1, type=Order.WINKEL))
    doReposition2(orders, Order, waitCompleteOrders, direction)
    loops = 0
    while (slam.xpos < (optimalX - 10) or slam.xpos > (optimalX + 10)) and (loops < 3):
        loops += 1
        adjustedX = optimalX            # move waypoint left or right to account for movement caused by turning
        if slam.xpos < optimalX:
            adjustedX += 10
            print("adjusting right")
        elif slam.xpos > optimalX:
            adjustedX -= 10
            print("adjusting left")
        orders.append(Order(x=adjustedX, y=2200, speed=0.2, brake=1, type=Order.DESTINATION, num=37))
        orders.append(Order(zielwinkel=-90, speed=0.2, brake=1, type=Order.WINKEL))
        doReposition2(orders, Order, waitCompleteOrders, direction)
        orders.append(Order(y=optimalY, zielwinkel=-90, speed=-0.2, brake=1, type=Order.DRIVETOY))
        doReposition2(orders, Order, waitCompleteOrders, direction)
    orders.append(Order(zielwinkel=0, speed=-0.2, brake=1, type=Order.WINKEL))
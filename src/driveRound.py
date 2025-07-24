import time
from slam import Hindernisse

def doReposition(orders, Order, waitCompleteOrders, rotation, angleCheck):
    if not waitCompleteOrders():
        return
    time.sleep(0.3)
    orders.append(Order(angleCheckOverwrite=angleCheck,type=Order.REPOSITION, rotation=rotation))
    if not waitCompleteOrders():
        return
    time.sleep(0.3)
    
def driveRound(orders,Order, waitCompleteOrders, checkForColor, rotation, scanStart):
    if (rotation > 1000):
        direction = Order.CCW
        outer=Hindernisse.RED
        inner=Hindernisse.GREEN
    else:
        direction = Order.CW
        outer=Hindernisse.GREEN
        inner=Hindernisse.RED
    
    speedi = 0.5


    if checkForColor(Hindernisse.RED, scanStart, scanStart+4) or (not checkForColor(Hindernisse.GREEN, scanStart, scanStart+4) and checkForColor(Hindernisse.RED, scanStart+2, scanStart+6)):
        orders.append(Order(x=750, y=2000,speed=speedi,brake=0,type=Order.DESTINATION,num=14, rotation=rotation))
        orders.append(Order(x=800, y=1750,speed=speedi,brake=0,type=Order.DESTINATION,num=15, rotation=rotation))
    else:
        if rotation != 90 and rotation != 1090:
            orders.append(Order(x=250, y=2000,speed=speedi,brake=0,type=Order.DESTINATION,num=16, rotation=rotation))
            orders.append(Order(x=200, y=1750,speed=speedi,brake=0,type=Order.DESTINATION,num=17, rotation=rotation))
        else:
            orders.append(Order(x=400, y=2000,speed=speedi,brake=0,type=Order.DESTINATION,num=22, rotation=rotation))
            orders.append(Order(x=400, y=1750,speed=speedi,brake=0,type=Order.DESTINATION,num=23, rotation=rotation))

    if checkForColor(Hindernisse.RED, scanStart+2, scanStart+6) or (not checkForColor(Hindernisse.GREEN, scanStart+2, scanStart+6) and checkForColor(Hindernisse.RED, scanStart, scanStart+4)):
        orders.append(Order(x=800, y=1000,speed=speedi,brake=0,type=Order.DESTINATION,num=18, rotation=rotation))
        if rotation != 90 and rotation != 1090:
            pass
        else:
            orders.append(Order(x=400, y=700,speed=speedi,brake=0,type=Order.DESTINATION,num=19, rotation=rotation))
    else:
        if rotation != 90 and rotation != 1090:
            orders.append(Order(x=200, y=1000,speed=speedi,brake=0,type=Order.DESTINATION,num=20, rotation=rotation))
        else:
            orders.append(Order(x=400, y=1000,speed=speedi,brake=0,type=Order.DESTINATION,num=24, rotation=rotation))
            orders.append(Order(x=400, y=500,speed=speedi,brake=0,type=Order.DESTINATION,num=25, rotation=rotation))


    if rotation != 90 and rotation != 1090:
        if checkForColor(Hindernisse.RED, scanStart+2, scanStart+6) or (not checkForColor(Hindernisse.GREEN, scanStart+2, scanStart+6) and checkForColor(Hindernisse.RED, scanStart, scanStart+4)):
            if checkForColor(Hindernisse.RED, scanStart+6, scanStart+10) or (not checkForColor(Hindernisse.GREEN, scanStart+6, scanStart+10) and checkForColor(Hindernisse.RED, scanStart+4, scanStart+8)):
                pass
            else:
                orders.append(Order(x=600, y=500,speed=speedi,brake=0,type=Order.DESTINATION,num=26, rotation=rotation))
        else:
            if checkForColor(Hindernisse.RED, scanStart+6, scanStart+10) or (not checkForColor(Hindernisse.GREEN, scanStart+6, scanStart+10) and checkForColor(Hindernisse.RED, scanStart+4, scanStart+8)):
                orders.append(Order(x=400, y=800,speed=speedi,brake=0,type=Order.DESTINATION,num=27, rotation=rotation))
            else:
                pass
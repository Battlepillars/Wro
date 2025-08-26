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
    
def park(orders,Order, waitCompleteOrders, checkForColor, rotation, scanStart):
    if (rotation > 1000):
        direction = Order.CCW
        outer=Hindernisse.RED
        inner=Hindernisse.GREEN
    else:
        direction = Order.CW
        outer=Hindernisse.GREEN
        inner=Hindernisse.RED
    
    speedi = 0.5
    
    if (checkForColor(Hindernisse.GREEN, scanStart, scanStart+6) and not checkForColor(Hindernisse.RED, scanStart+2, scanStart+6)) and checkForColor(Hindernisse.RED, scanStart+6, scanStart+7):
        orders.append(Order(x=2600, y=2200,speed=speedi,brake=0,type=Order.DESTINATION,num=33, rotation=rotation))
    
    if (checkForColor(Hindernisse.RED, scanStart, scanStart+6) and not checkForColor(Hindernisse.GREEN, scanStart+4, scanStart+6)):
        if not checkForColor(Hindernisse.RED, scanStart+6, scanStart+7):
            orders.append(Order(x=2400, y=2500,speed=speedi,brake=0,type=Order.DESTINATION,num=34, rotation=rotation))
    
    if checkForColor(Hindernisse.RED, scanStart+6, scanStart+7):
        orders.append(Order(x=2000, y=2200,speed=speedi,brake=0,type=Order.DESTINATION,num=35, rotation=rotation))
        orders.append(Order(x=1700, y=2200,speed=speedi,brake=1,type=Order.DESTINATION,num=35, rotation=rotation))
        orders.append(Order(zielwinkel=-90, speed=-0.2, brake=1, type=Order.WINKEL))
        
        # orders.append(Order(x=1775, y=2275,speed=0.2,brake=1,type=Order.DESTINATION,num=32, rotation=rotation))
        # orders.append(Order(zielwinkel=-90, speed=0.2, brake=1, type=Order.WINKEL))
        # doReposition(orders, Order, waitCompleteOrders, rotation, 0)
    else:
        orders.append(Order(x=2000, y=2600,speed=speedi,brake=0,type=Order.DESTINATION,num=30, rotation=rotation))
        orders.append(Order(x=1870, y=2600,speed=speedi,brake=1,type=Order.DESTINATION,num=31, rotation=rotation))
        orders.append(Order(zielwinkel=-90, speed=0.2, brake=1, type=Order.WINKEL))
        orders.append(Order(x=1775, y=2275,speed=0.2,brake=1,type=Order.DESTINATION,num=32, rotation=rotation))
        orders.append(Order(zielwinkel=-90, speed=0.2, brake=1, type=Order.WINKEL))
        doReposition(orders, Order, waitCompleteOrders, rotation, 0)
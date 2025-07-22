import time
from slam import Hindernisse

def scan(orders,Order, waitCompleteOrders, checkForColor):
    speedi = 0.5

    if not waitCompleteOrders():
        return
    time.sleep(0.3)
    orders.append(Order(angleCheckOverwrite=-90,type=Order.REPOSITION))
    if not waitCompleteOrders():
        return
    time.sleep(0.3)
    
    orders.append(Order(zielwinkel=-90, speed=0.2, brake=1, dir=Order.CW, type=Order.WINKEL))
    
    if not waitCompleteOrders():
        return
    time.sleep(0.3)
    orders.append(Order(angleCheckOverwrite=-90,type=Order.REPOSITION))
    if not waitCompleteOrders():
        return
    time.sleep(0.3)
    
    orders.append(Order(steer=0, dist=100, speed=-speedi, brake=1, type=Order.KURVE))
    if not waitCompleteOrders():
        return
    time.sleep(0.3)
    orders.append(Order(x=500, y=2250,speed=0.5,brake=1,type=Order.DESTINATION,num=13))
    orders.append(Order(zielwinkel=-90, speed=0.2, brake=1, type=Order.WINKEL))
    if not waitCompleteOrders():
        return
    time.sleep(0.3)
    orders.append(Order(toScan=[6,7],checkHeightNear=True,type=Order.SCAN))
    if not waitCompleteOrders():
        return
    time.sleep(0.3)
    orders.append(Order(toScan=[8,9,10,11],type=Order.SCAN))
    if not waitCompleteOrders():
        return
    time.sleep(0.3)
    
    orders.append(Order(steer=0, dist=100, speed=-speedi, brake=1, type=Order.KURVE))
    

    if checkForColor(Hindernisse.RED, 6, 10) or (not checkForColor(Hindernisse.GREEN, 6, 10) and checkForColor(Hindernisse.RED, 8, 12)):
        orders.append(Order(x=750, y=2000,speed=speedi,brake=0,type=Order.DESTINATION,num=14))
        orders.append(Order(x=800, y=1750,speed=speedi,brake=0,type=Order.DESTINATION,num=15))
    else:
        orders.append(Order(x=250, y=2000,speed=speedi,brake=0,type=Order.DESTINATION,num=16))
        orders.append(Order(x=200, y=1750,speed=speedi,brake=0,type=Order.DESTINATION,num=17))

    if checkForColor(Hindernisse.RED, 8, 12) or (not checkForColor(Hindernisse.GREEN, 8, 12) and checkForColor(Hindernisse.RED, 6, 10)):
        orders.append(Order(x=800, y=1000,speed=speedi,brake=0,type=Order.DESTINATION,num=18))
        orders.append(Order(x=400, y=700,speed=speedi,brake=0,type=Order.DESTINATION,num=19))
    else:
        orders.append(Order(x=200, y=1000,speed=speedi,brake=0,type=Order.DESTINATION,num=20))
        orders.append(Order(x=350, y=500,speed=speedi,brake=0,type=Order.DESTINATION,num=21))

    orders.append(Order(zielwinkel=-180, speed=0.2, brake=1, dir=Order.CW, type=Order.WINKEL))
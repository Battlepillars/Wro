import time
from slam import Hindernisse

def scan(toscan, orders, Order, waitCompleteOrders):
    if not waitCompleteOrders():
        return
    time.sleep(0.3)
    orders.append(Order(toScan=toscan,type=Order.SCAN))
    if not waitCompleteOrders():
        return
    time.sleep(0.3)

def unparkCW(orders,Order, waitCompleteOrders, checkForColor):
    speedi = 0.5
    
    orders.append(Order(steer=-90, dist=175, speed=0.2, brake=1, type=Order.KURVE))
    
    if not waitCompleteOrders():
        return
    time.sleep(0.3)
    orders.append(Order(toScan=[2],type=Order.SCAN))
    if not waitCompleteOrders():
        return
    time.sleep(0.3)
    
    if checkForColor(Hindernisse.RED, 2, 3):
        print("red")
        orders.append(Order(x=1750, y=2450,speed=speedi,brake=0,type=Order.DESTINATION,num=1))
        orders.append(Order(x=1500, y=2200,speed=speedi,brake=0,type=Order.DESTINATION,num=2))
        orders.append(Order(x=1000, y=2500,speed=speedi,brake=0,type=Order.DESTINATION,num=3))
        orders.append(Order(x=700, y=2650,speed=speedi,brake=0,type=Order.DESTINATION,num=4))
    elif checkForColor(Hindernisse.GREEN, 2, 3):
        orders.append(Order(x=1500, y=2600,speed=speedi,brake=0,type=Order.DESTINATION,num=5))
        orders.append(Order(x=1000, y=2500,speed=speedi,brake=0,type=Order.DESTINATION,num=6))
        orders.append(Order(x=700, y=2650,speed=speedi,brake=0,type=Order.DESTINATION,num=7))
    else:
        orders.append(Order(x=1500, y=2500,speed=speedi,brake=0,type=Order.DESTINATION,num=8))
        orders.append(Order(zielwinkel=0, speed=0.2, brake=1, type=Order.WINKEL))
        scan([4, 5], orders, Order, waitCompleteOrders)
        if checkForColor(Hindernisse.RED, 4, 5):
            orders.append(Order(x=1000, y=2200,speed=speedi,brake=0,type=Order.DESTINATION,num=9))
            orders.append(Order(x=700, y=2550,speed=speedi,brake=0,type=Order.DESTINATION,num=10))
        else:
            orders.append(Order(x=1000, y=2700,speed=speedi,brake=0,type=Order.DESTINATION,num=11))
            orders.append(Order(x=600, y=2650,speed=speedi,brake=0,type=Order.DESTINATION,num=12))
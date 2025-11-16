import time
from slam import Hindernisse

def scanRound(orders,Order, waitCompleteOrders, checkForColor, rotation, scanStart):
    if (rotation >= 1000):
        direction = Order.CCW
        scan1=[scanStart+4, scanStart+5]
        scan2=[scanStart, scanStart+1, scanStart+2, scanStart+3]
        scan3=(scanStart+4, scanStart+6)
        scan4=(scanStart, scanStart+4)
        outer=Hindernisse.RED
        inner=Hindernisse.GREEN
    else:
        direction = Order.CW
        scan1=[scanStart, scanStart+1]
        scan2=[scanStart+2, scanStart+3, scanStart+4, scanStart+5]
        scan3=(scanStart, scanStart+4)
        scan4=(scanStart+4, scanStart+6)
        outer=Hindernisse.GREEN
        inner=Hindernisse.RED
    
    

    speedi = 0.5
    
    orders.append(Order(zielwinkel=-90, speed=0.4, brake=1, dir=direction, type=Order.WINKEL, rotation=rotation))
    
    if not waitCompleteOrders():
        return
    time.sleep(0.3)
    orders.append(Order(angleCheckOverwrite=-90,type=Order.REPOSITION, rotation=rotation))
    if not waitCompleteOrders():
        return
    time.sleep(0.3)
    
    orders.append(Order(steer=0, dist=150, speed=-speedi, brake=1, type=Order.KURVE, rotation=rotation))
    if not waitCompleteOrders():
        return
    time.sleep(0.3)
    #orders.append(Order(x=500, y=2250,speed=0.5,brake=1,type=Order.DESTINATION,num=13, rotation=rotation))
    orders.append(Order(x=500, y=2450,speed=0.5,brake=1,type=Order.DESTINATION,num=13, rotation=rotation))
    orders.append(Order(zielwinkel=-90, speed=0.2, brake=1, type=Order.WINKEL, rotation=rotation))
    #orders.append(Order(x=500, y=2350,speed=0.5,brake=1,type=Order.DESTINATION,num=13, rotation=rotation))
    if not waitCompleteOrders():
        return
    time.sleep(0.3)
    orders.append(Order(toScan=scan1,checkHeightNear=True,type=Order.SCAN))
    if not waitCompleteOrders():
        return
    time.sleep(0.3)
    orders.append(Order(toScan=scan2,type=Order.SCAN))
    if not waitCompleteOrders():
        return
    time.sleep(0.3)
    
    orders.append(Order(steer=0, dist=100, speed=-speedi, brake=1, type=Order.KURVE))
    
    
    if checkForColor(inner, scan3[0], scan3[1]) or (not checkForColor(outer, scan3[0], scan3[1]) and checkForColor(inner, scan4[0], scan4[1])):
        orders.append(Order(x=750, y=2000,speed=speedi,brake=0,type=Order.DESTINATION,num=14, rotation=rotation))
        orders.append(Order(x=800, y=1750,speed=speedi,brake=0,type=Order.DESTINATION,num=15, rotation=rotation))
    else:
        if rotation != 90 and rotation != 1500:
            orders.append(Order(x=250, y=2000,speed=speedi,brake=0,type=Order.DESTINATION,num=16, rotation=rotation))
            orders.append(Order(x=200, y=1750,speed=speedi,brake=0,type=Order.DESTINATION,num=17, rotation=rotation))
        else:
            orders.append(Order(x=400, y=2000,speed=speedi,brake=0,type=Order.DESTINATION,num=22, rotation=rotation))
            orders.append(Order(x=400, y=1750,speed=speedi,brake=0,type=Order.DESTINATION,num=23, rotation=rotation))

    if checkForColor(inner, scan4[0], scan4[1]) or (not checkForColor(outer, scan4[0], scan4[1]) and checkForColor(inner, scan3[0], scan3[1])):
        #orders.append(Order(x=800, y=1000,speed=speedi,brake=1,type=Order.DESTINATION,num=18, rotation=rotation))#knapp
        orders.append(Order(x=780, y=1100,speed=speedi,brake=1,type=Order.DESTINATION,num=18, rotation=rotation))
        orders.append(Order(zielwinkel=-70, speed=0.4, brake=0, type=Order.WINKEL, rotation=rotation))
        orders.append(Order(x=400, y=700,speed=speedi,brake=0,type=Order.DESTINATION,num=19, rotation=rotation))
    else:
        if rotation != 90 and rotation != 1500:
            #orders.append(Order(x=200, y=1000,speed=speedi,brake=0,type=Order.DESTINATION,num=20, rotation=rotation))   #immer knapp
            orders.append(Order(x=220, y=1100,speed=speedi,brake=1,type=Order.DESTINATION,num=20, rotation=rotation))
            orders.append(Order(x=350, y=500,speed=speedi,brake=0,type=Order.DESTINATION,num=21, rotation=rotation))
        else:
            orders.append(Order(x=400, y=1000,speed=speedi,brake=0,type=Order.DESTINATION,num=24, rotation=rotation))
            orders.append(Order(x=400, y=500,speed=speedi,brake=0,type=Order.DESTINATION,num=25, rotation=rotation))
            
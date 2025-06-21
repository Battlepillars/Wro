import time
from slam import Hindernisse


def scan_inner_tour(orders, speedScan, rotation, scanStart, Order, waitCompleteOrders, checkForColor):
    """
    Perform inner tour scanning for obstacles.
    
    Args:
        orders: List of robot orders/commands
        speedScan: Speed for scanning movement
        rotation: Rotation angle for coordinate transformation
        scanStart: Starting index for scanning
        Order: Order class for creating movement commands
        waitCompleteOrders: Function to wait for order completion
        checkForColor: Function to check for color in obstacle range
    """
    if (rotation > 1000):
        direction = Order.CCW
        scan1=[scanStart+4, scanStart+5]
        scan2=[scanStart+0,scanStart+1, scanStart+2, scanStart+3]
        outer=Hindernisse.RED
        inner=Hindernisse.GREEN
    else:
        direction = Order.CW
        scan1=[scanStart, scanStart+1]
        scan2=[scanStart+2, scanStart+3, scanStart+4, scanStart+5]
        outer=Hindernisse.GREEN
        inner=Hindernisse.RED


    orders.append(Order(x=1000, y=2207, speed=speedScan, brake=1, type=Order.DESTINATION, num=301, rotation=rotation))  # erster scan von 6 7 bei der innentour
    orders.append(Order(x=850, y=2207, speed=speedScan, brake=1, type=Order.DESTINATION, num=302, rotation=rotation))

    if not waitCompleteOrders():
        return
    time.sleep(0.5)
    orders.append(Order(type=Order.REPOSITION, angleCheckOverwrite=-90, rotation=rotation))
    
    if not waitCompleteOrders():
        return
    time.sleep(1)
    
    orders.append(Order(zielwinkel=-30, speed=0.2, brake=1, dir=direction, type=Order.WINKEL, rotation=rotation))
    
    if not waitCompleteOrders():
        return
    time.sleep(1)
    
    orders.append(Order(toScan=scan1, type=Order.SCAN))
    time.sleep(0.5)
    if not waitCompleteOrders():
        return

    if checkForColor(inner, scanStart, scanStart+6):
        # print("red")
        orders.append(Order(x=823, y=2008, speed=speedScan, brake=1, type=Order.DESTINATION, num=114, rotation=rotation))
        # orders.append(Order(x=829, y=988, speed=speedScan, brake=1, type=Order.DESTINATION, num=115, rotation=rotation))
        # orders.append(Order(x=244, y=641, speed=speedScan, brake=1, type=Order.DESTINATION, num=116, rotation=rotation))  # exit innen-innen
    elif checkForColor(outer, scanStart, scanStart+6):
        # print("green")
        # orders.append(Order(x=450, y=2400, speed=speedScan, brake=1, type=Order.DESTINATION, num=200, rotation=rotation))
        orders.append(Order(zielwinkel=45, speed=0.2, brake=1, type=Order.WINKEL, rotation=rotation))
        orders.append(Order(steer=0, dist=55, speed=0.2, brake=1, type=Order.KURVE,num=424)) 
        orders.append(Order(zielwinkel=-45, speed=0.2, brake=1, type=Order.WINKEL, rotation=rotation))
        orders.append(Order(x=200, y=2000, speed=speedScan, brake=1, type=Order.DESTINATION, num=201, rotation=rotation))
        # orders.append(Order(x=200, y=1000, speed=speedScan, brake=1, type=Order.DESTINATION, num=117, rotation=rotation))
        # orders.append(Order(x=235, y=616, speed=speedScan, brake=1, type=Order.DESTINATION, num=118, rotation=rotation))  # exit innen-außen
    else:
        orders.append(Order(x=750, y=2100, speed=speedScan, brake=1, type=Order.DESTINATION, num=118, rotation=rotation))  # Nachscannen innentour
        orders.append(Order(zielwinkel=-60, speed=0.2, brake=1, dir=direction, type=Order.WINKEL, rotation=rotation))
        
        if not waitCompleteOrders():
            return
        time.sleep(0.5)
        
        orders.append(Order(toScan=scan2, type=Order.SCAN, rotation=rotation))
        
        time.sleep(0.5)
        if not waitCompleteOrders():
            return

        if checkForColor(inner, scanStart, scanStart+6):  # rot in bereich 2
            # print("red")
            orders.append(Order(x=800, y=1500, speed=speedScan, brake=1, type=Order.DESTINATION, num=114, rotation=rotation))
            # orders.append(Order(x=829, y=988, speed=speedScan, brake=1, type=Order.DESTINATION, num=115, rotation=rotation))
            # orders.append(Order(x=244, y=641, speed=speedScan, brake=1, type=Order.DESTINATION, num=116, rotation=rotation))  # exit innen-innen nachscannen
        elif checkForColor(outer, scanStart, scanStart+6):
            # print("green")
            if not rotation == 1500:        # Beim scannen im süden ccw muss dieser teil weg weil er sonst den Parkplatz rammt
                orders.append(Order(x=200, y=1500, speed=speedScan, brake=1, type=Order.DESTINATION, num=114, rotation=rotation))
                orders.append(Order(x=200, y=1050, speed=speedScan, brake=1, type=Order.DESTINATION, num=112, rotation=rotation))
            # orders.append(Order(x=235, y=616, speed=speedScan, brake=1, type=Order.DESTINATION, num=118, rotation=rotation))  # exit innen-außen nachscannen


def scan_outer_tour(orders, speedScan, rotation, scanstart, Order, waitCompleteOrders, checkForColor):
    """
    Perform outer tour scanning for obstacles.
    
    Args:
        orders: List of robot orders/commands
        speedScan: Speed for scanning movement
        rotation: Rotation angle for coordinate transformation
        scanstart: Starting index for scanning
        Order: Order class for creating movement commands
        waitCompleteOrders: Function to wait for order completion
        checkForColor: Function to check for color in obstacle range
    """
    if (rotation > 1000):
        direction = Order.CCW
        scan2=[scanstart+0, scanstart+1]
        scan1=[scanstart+2, scanstart+3, scanstart+4, scanstart+5]
        outer=Hindernisse.RED
        inner=Hindernisse.GREEN
    else:
        direction = Order.CW
        scan2=[scanstart+4, scanstart+5]
        scan1=[scanstart, scanstart+1, scanstart+2, scanstart+3]
        outer=Hindernisse.GREEN
        inner=Hindernisse.RED

    orders.append(Order(x=750, y=2800, speed=speedScan, brake=1, type=Order.DESTINATION, num=113, rotation=rotation))  # erster check aussentour

    orders.append(Order(zielwinkel=-90, speed=0.2, brake=1, dir=direction, type=Order.WINKEL, rotation=rotation))
    if not waitCompleteOrders():
        return
    time.sleep(0.5)
    orders.append(Order(type=Order.REPOSITION))
    orders.append(Order(toScan=scan1, type=Order.SCAN))
    time.sleep(0.5)
    if not waitCompleteOrders():
        return

    if checkForColor(inner, scanstart, scanstart+6):
        # print("red")
        orders.append(Order(x=823, y=2008, speed=speedScan, brake=1, type=Order.DESTINATION, num=114, rotation=rotation))  # exit außen-innen
        # orders.append(Order(x=829, y=988, speed=speedScan, brake=1, type=Order.DESTINATION, num=115, rotation=rotation))
        # orders.append(Order(x=244, y=641, speed=speedScan, brake=1, type=Order.DESTINATION, num=116, rotation=rotation))
    elif checkForColor(outer, scanstart, scanstart+6):
        # print("green")
        orders.append(Order(x=250, y=2049, speed=speedScan, brake=1, type=Order.DESTINATION, num=202, rotation=rotation))  # exit außen-außen
        # orders.append(Order(x=235, y=616, speed=speedScan, brake=1, type=Order.DESTINATION, num=118, rotation=rotation))
    else:  # nichts gefunden in bereich 2, nachscannen
        orders.append(Order(x=500, y=1830, speed=speedScan, brake=1, type=Order.DESTINATION, num=119, rotation=rotation))
        orders.append(Order(zielwinkel=-90, speed=0.2, brake=1, dir=direction, type=Order.WINKEL, rotation=rotation))
        if not waitCompleteOrders():
            return
        time.sleep(0.5)
        orders.append(Order(toScan=scan2, type=Order.SCAN))
        time.sleep(0.5)
        if not waitCompleteOrders():
            return
        if checkForColor(inner, scanstart, scanstart+6):
            pass
            # print("red")
            # orders.append(Order(x=829, y=988, speed=speedScan, brake=1, type=Order.DESTINATION, num=120, rotation=rotation))  # exit außen-innen nachscannen
            # orders.append(Order(x=244, y=641, speed=speedScan, brake=1, type=Order.DESTINATION, num=121, rotation=rotation))
        else:
            # print("green")
            orders.append(Order(x=200, y=1000, speed=speedScan, brake=1, type=Order.DESTINATION, num=122, rotation=rotation))  # exit außen-außen nachscannen
            # orders.append(Order(x=235, y=616, speed=speedScan, brake=1, type=Order.DESTINATION, num=123, rotation=rotation))

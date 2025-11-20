import time
from slam import Hindernisse

def scan(toscan, orders, Order, waitCompleteOrders):
    """@brief Queue a scan order for specified obstacle indices.

    Ensures previous orders completed before and after queuing to avoid
    unstable sensor readings.

    @param toscan list[int]: Obstacle indices to scan.
    @param orders list: Mutable command queue.
    @param Order type: Factory/class for constructing an order.
    @param waitCompleteOrders callable: Returns True when queue idle; aborts if False.
    @return None
    """
    if not waitCompleteOrders():
        return
    time.sleep(0.3)
    orders.append(Order(toScan=toscan,type=Order.SCAN))
    if not waitCompleteOrders():
        return
    time.sleep(0.3)


def unparkCCW(orders,Order, waitCompleteOrders, checkForColor):
    """@brief Counter‑clockwise unparking sequence with initial scan and branching.

    Rotates out of start zone, performs near-height scan of first obstacle slot
    then selects waypoint pattern based on GREEN vs RED detection. Defaults to
    RED path if no GREEN found.

    @param orders list: Command queue to append orders.
    @param Order type: Order factory/class.
    @param waitCompleteOrders callable: Synchronization helper; abort if returns False.
    @param checkForColor callable: Predicate (color, startIdx, endIdx) -> bool.
    @return None
    """
    speedi = 0.5
    
    #orders.append(Order(steer=90, dist=100, speed=0.2, brake=1, type=Order.KURVE))
    orders.append(Order(zielwinkel=-115, speed=0.5, brake=1, type=Order.WINKEL,dir=Order.CCW))
    if not waitCompleteOrders():
        return
    time.sleep(0.3)
    orders.append(Order(toScan=[0],checkHeightNear=True,type=Order.SCAN))
    if not waitCompleteOrders():
        return
    time.sleep(0.3)
    
    if checkForColor(Hindernisse.GREEN, 0, 1):
        orders.append(Order(x=1825, y=2350,speed=speedi,brake=0,type=Order.DESTINATION,num=1))
        orders.append(Order(zielwinkel=-180, speed=0.4, brake=0, type=Order.WINKEL))
        orders.append(Order(x=2050, y=2250,speed=speedi,brake=1,type=Order.DESTINATION,num=2))
        orders.append(Order(x=2300, y=2650,speed=speedi,brake=0,type=Order.DESTINATION,num=4))
    else: # Red 
        orders.append(Order(x=2000, y=2600,speed=speedi,brake=0,type=Order.DESTINATION,num=5))
        orders.append(Order(x=2300, y=2650,speed=speedi,brake=0,type=Order.DESTINATION,num=7))


def unparkCW(orders,Order, waitCompleteOrders, checkForColor):
    """@brief Clockwise unparking maneuver with obstacle color dependent routing.

    Performs initial heading adjustment, short curve, scans middle slot, then
    chooses waypoint sets for RED, GREEN, or performs an extended scan when
    neither color is conclusively detected.

    @param orders list: Command queue.
    @param Order type: Order factory/class.
    @param waitCompleteOrders callable: Wait for queue to finish between steps.
    @param checkForColor callable: Color presence test (color, startIdx, endIdx).
    @return None
    """
    speedi = 0.5
    
    #orders.append(Order(steer=-90, dist=175, speed=0.2, brake=1, type=Order.KURVE))
    orders.append(Order(zielwinkel=-55, speed=0.5, brake=1, type=Order.WINKEL,dir=Order.CW))
    orders.append(Order(steer=0, dist=40, speed=0.2, brake=1, type=Order.KURVE))
    if not waitCompleteOrders():
        return
    time.sleep(0.3)
    orders.append(Order(toScan=[2],checkHeightNear=True,type=Order.SCAN))
    if not waitCompleteOrders():
        return
    time.sleep(0.3)
    
    if checkForColor(Hindernisse.RED, 2, 3):
        orders.append(Order(x=1750, y=2400,speed=speedi,brake=0,type=Order.DESTINATION,num=1))
        orders.append(Order(zielwinkel=0, speed=0.2, brake=0, type=Order.WINKEL))
        orders.append(Order(x=1350, y=2200,speed=speedi,brake=0,type=Order.DESTINATION,num=2))
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
            orders.append(Order(x=1050, y=2200,speed=speedi,brake=1,type=Order.DESTINATION,num=9))
            orders.append(Order(zielwinkel=30, speed=0.4, brake=0, type=Order.WINKEL))
            orders.append(Order(x=700, y=2550,speed=speedi,brake=0,type=Order.DESTINATION,num=10))
        else:
            orders.append(Order(x=1000, y=2700,speed=speedi,brake=0,type=Order.DESTINATION,num=11))
            orders.append(Order(x=600, y=2650,speed=speedi,brake=0,type=Order.DESTINATION,num=12))
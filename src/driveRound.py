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
    
def driveRound(orders,Order, waitCompleteOrders, checkForColor, rotation, scanStart, last = False):
    if (rotation >= 1000):
        direction = Order.CCW
        scan1=(scanStart+8-12, scanStart+12-12)
        scan2=(scanStart+6-12, scanStart+10-12)
        scan3=(scanStart+2, scanStart+6)
        scan4=(scanStart, scanStart+4)
        outer=Hindernisse.RED
        inner=Hindernisse.GREEN
    else:
        direction = Order.CW
        scan1=(scanStart+6, scanStart+10)
        scan2=(scanStart+8, scanStart+12)
        scan3=(scanStart, scanStart+4)
        scan4=(scanStart+2, scanStart+6)
        outer=Hindernisse.GREEN
        inner=Hindernisse.RED
    
    speedi = 0.5


    if checkForColor(inner, scan3[0], scan3[1]) or (not checkForColor(outer, scan3[0], scan3[1]) and checkForColor(inner, scan4[0], scan4[1])):
        orders.append(Order(x=800, y=2000,speed=speedi,brake=0,type=Order.DESTINATION,num=14, rotation=rotation))
        orders.append(Order(x=800, y=1750,speed=speedi,brake=0,type=Order.DESTINATION,num=15, rotation=rotation))
    else:
        if rotation != 90 and rotation != 1500:
            orders.append(Order(x=200, y=2000,speed=speedi,brake=0,type=Order.DESTINATION,num=16, rotation=rotation))
            orders.append(Order(x=200, y=1750,speed=speedi,brake=0,type=Order.DESTINATION,num=17, rotation=rotation))
        else:
            orders.append(Order(x=400, y=2000,speed=speedi,brake=0,type=Order.DESTINATION,num=22, rotation=rotation))
            orders.append(Order(x=400, y=1750,speed=speedi,brake=0,type=Order.DESTINATION,num=23, rotation=rotation))

    if checkForColor(inner, scan4[0], scan4[1]) or (not checkForColor(outer, scan4[0], scan4[1]) and checkForColor(inner, scan3[0], scan3[1])):
        orders.append(Order(x=800, y=1000,speed=speedi,brake=0,type=Order.DESTINATION,num=18, rotation=rotation))
        if rotation != 90 and rotation != 1500:
            pass
        # else:
        #     orders.append(Order(x=400, y=700,speed=speedi,brake=0,type=Order.DESTINATION,num=19, rotation=rotation))
    else:
        if rotation != 90 and rotation != 1500:
            orders.append(Order(x=200, y=1100,speed=speedi,brake=0,type=Order.DESTINATION,num=20, rotation=rotation))
        else:
            orders.append(Order(x=400, y=1000,speed=speedi,brake=0,type=Order.DESTINATION,num=24, rotation=rotation))
            # orders.append(Order(x=400, y=500,speed=speedi,brake=0,type=Order.DESTINATION,num=25, rotation=rotation))


    # print("Last:",last)
    # print("RED 2,6:",checkForColor(inner, scan4[0], scan4[1]) )
    # print("GREEN 2,6:",checkForColor(outer, scan4[0], scan4[1]) )
    # print("RED 0,4:",checkForColor(inner, scanStart+0, scanStart+4) )

    # print("RED 6,10:",checkForColor(inner, scanStart+6, scanStart+10) )
    # print("GREEN 6,10:",checkForColor(outer, scanStart+6, scanStart+10) )
    # print("RED 8,12:",checkForColor(inner, scanStart+8, scanStart+12) )
    

    
    
    if not last:
        sinside= checkForColor(inner, scan4[0], scan4[1])  or ((not checkForColor(outer, scan4[0], scan4[1])) and checkForColor(inner, scan3[0], scan3[1]))
        dinside= checkForColor(inner, scan1[0], scan1[1])  or ((not checkForColor(outer, scan1[0], scan1[1])) and checkForColor(inner, scan2[0], scan2[1]))
        print("Rotation: ",rotation, "  sinside: " ,sinside, "   dinside: ",dinside)
        
        if rotation != 180 and rotation != 1180:
            if ( sinside and not  dinside):
                orders.append(Order(x=600, y=550,speed=speedi,brake=0,type=Order.DESTINATION,num=26, rotation=rotation))
            if ( not sinside and dinside):
                orders.append(Order(x=400, y=800,speed=speedi,brake=0,type=Order.DESTINATION,num=27, rotation=rotation))
            if ( not sinside and  not dinside):
                orders.append(Order(x=400, y=500,speed=speedi,brake=0,type=Order.DESTINATION,num=28, rotation=rotation))
        else:
            if ( sinside and not  dinside):
                orders.append(Order(x=700, y=700,speed=speedi,brake=0,type=Order.DESTINATION,num=261, rotation=rotation))
            if ( not sinside and dinside):
                orders.append(Order(x=400, y=800,speed=speedi,brake=0,type=Order.DESTINATION,num=272, rotation=rotation))
            if ( not sinside and  not dinside):
                orders.append(Order(x=450, y=550,speed=speedi,brake=0,type=Order.DESTINATION,num=283, rotation=rotation))
        # if (
        #     checkForColor(inner, scan4[0], scan4[1])                # source inner
        #     or ((not checkForColor(outer, scan4[0], scan4[1])) and checkForColor(inner, scan3[0], scan3[1]))
        # ):
        #     if(
        #         checkForColor(inner, scanStart+6, scanStart+10) 
        #         or ((not checkForColor(outer, scanStart+6, scanStart+10)) and checkForColor(inner, scanStart+8, scanStart+12))
        #     ):
        #         pass
        #     else:
        #         orders.append(Order(x=600, y=500,speed=speedi,brake=0,type=Order.DESTINATION,num=526, rotation=rotation))

        # else:
        #     if checkForColor(inner, scanStart+6, scanStart+10) or (not checkForColor(outer, scanStart+6, scanStart+10) and checkForColor(inner, scanStart+4, scanStart+8)):
        #         orders.append(Order(x=400, y=800,speed=speedi,brake=0,type=Order.DESTINATION,num=27, rotation=rotation))
        #     else:
        #         orders.append(Order(x=400, y=500,speed=speedi,brake=0,type=Order.DESTINATION,num=28, rotation=rotation))
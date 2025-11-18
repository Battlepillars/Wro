import time
from slam import Hindernisse
import slam

def doReposition(orders, Order, waitCompleteOrders, rotation, angleCheck):
    """
    Perform a position correction using LiDAR wall measurements.
    
    This function uses the robot's LiDAR to measure distances to walls and corrects
    the robot's position estimate based on known wall locations. The reposition
    command adjusts both x,y coordinates and heading angle.
    
    Args:
        orders: Command queue for robot navigation
        Order: Order class for creating navigation commands
        waitCompleteOrders: Function to wait for command queue completion
        rotation: Current rotation/direction identifier (0-999=CW, 1000+=CCW)
        angleCheck: Angle to use for repositioning calculation (overrides default)
    """
    # Wait for any pending commands to complete
    if not waitCompleteOrders():
        return
    time.sleep(0.3)
    orders.append(Order(angleCheckOverwrite=angleCheck,type=Order.REPOSITION, rotation=rotation))
    
    # Wait for reposition to complete
    if not waitCompleteOrders():
        return
    time.sleep(0.3)  # Allow position to settle after correction
    
def driveRound(orders,Order, waitCompleteOrders, checkForColor, rotation, scanStart, slam, last = False):
    """
    Generate adaptive waypoints for navigating one section of the obstacle challenge course.
    This function analyzes detected obstacles and generates appropriate waypoints to navigate around them
    while staying on the correct side of the field based on obstacle colors (red/green).

    Args:
        orders: Command queue for robot navigation (list of Order objects)
        Order: Order class for creating navigation commands
        waitCompleteOrders: Function to wait for command queue completion
        checkForColor: Function to check if specific color obstacle exists in range
                        checkForColor(color, startIdx, endIdx) -> bool
        rotation: Direction identifier (0-999=CW, 1000+=CCW)
                Specific values: 0=CW-0°, 90=CW-90°, 180=CW-180°, 270=CW-270°
                                1000=CCW-0°, 1090=CCW-90°, 
        scanStart: Starting index for obstacle scanning 
                    Identifies which of 3 sections we're currently navigating
        slam: Slam instance for accessing repostionEnable and other properties
        last: Boolean flag indicating if this is the last section before parking
    
    """
    
    # Print all hindernisse values
    print("=== All Hindernisse ===")
    for idx, h in enumerate(slam.hindernisse):
        print(f"Hinderniss {idx}: x={h.x}, y={h.y}, farbe={h.farbe}")
    print("======================")
    
    # Step 1: Determine direction and configure obstacle colors
    if (rotation >= 1000):
        spaceFix=20
        # Counter-clockwise direction (rotation IDs 1000-1999)
        direction = Order.CCW
        # Adjust scan indices for CCW (wrap around with -12 offset for negative indices)
        scan1=(scanStart+8-12, scanStart+12-12)  # Destination area obstacles (far pair)
        scan2=(scanStart+6-12, scanStart+10-12)  # Destination area obstacles (near pair)
        scan3=(scanStart+4, scanStart+6)         # Source area obstacles (near pair)
        scan4=(scanStart, scanStart+4)           # Source area obstacles (close pair)
        scan5=(scanStart, scanStart+6)           # Source area obstacles (all)
        outer=Hindernisse.RED    # Outer obstacles (toward walls) are RED in CCW
        inner=Hindernisse.GREEN  # Inner obstacles (toward center) are GREEN in CCW
    else:
        spaceFix=-15
        # Clockwise direction (rotation IDs 0-999)
        direction = Order.CW
        scan1=(scanStart+6, scanStart+10)   # Destination area obstacles (near pair)
        scan2=(scanStart+8, scanStart+12)   # Destination area obstacles (far pair)
        scan3=(scanStart, scanStart+4)      # Source area obstacles (near pair)
        scan4=(scanStart+4, scanStart+6)    # Source area obstacles (far pair)
        scan5=(scanStart, scanStart+6)    # Source area obstacles (all)
        outer=Hindernisse.GREEN  # Outer obstacles (toward walls) are GREEN in CW
        inner=Hindernisse.RED    # Inner obstacles (toward center) are RED in CW
    
    speedi = 0.5  # Target speed in m/s (constant throughout section)


    sinside= checkForColor(inner, scan4[0], scan4[1])  or ((not checkForColor(outer, scan4[0], scan4[1])) and checkForColor(inner, scan3[0], scan3[1]))
    dinside= checkForColor(inner, scan1[0], scan1[1])  or ((not checkForColor(outer, scan1[0], scan1[1])) and checkForColor(inner, scan2[0], scan2[1]))
    

    if checkForColor(inner, scan3[0], scan3[1]) or (not checkForColor(outer, scan3[0], scan3[1]) and checkForColor(inner, scan4[0], scan4[1])):
        # cw rot   oder rot-grün
        orders.append(Order(x=800, y=2000,speed=speedi,brake=0,type=Order.DESTINATION,num=14, rotation=rotation))
        orders.append(Order(x=800, y=1750,speed=speedi,brake=0,type=Order.DESTINATION,num=15, rotation=rotation))
        if checkForColor(inner, scan5[0], scan5[1])  and (not checkForColor(outer, scan5[0], scan5[1])):
            # cw rot
            orders.append(Order(x=800, y=1050,speed=speedi,brake=0,type=Order.DESTINATION,num=18, rotation=rotation))
    else:
        # cw grün oder grün-rot
        if rotation != 90 and rotation != 1500:
            # Standard tight path at x=200mm (most sections)
            orders.append(Order(x=200, y=2000,speed=speedi,brake=0,type=Order.DESTINATION,num=16, rotation=rotation))
            orders.append(Order(x=200, y=1750,speed=speedi,brake=0,type=Order.DESTINATION,num=17, rotation=rotation))
            # orders.append(Order(zielwinkel=-90, speed=0.5, brake=1, type=Order.WINKEL, rotation=rotation))
            # doReposition(orders, Order, waitCompleteOrders, rotation, -90)
        else:
            # Special case for 90-degree rotations - slightly wider at x=400mm
            # These rotations need more clearance due to approach angle
            orders.append(Order(x=400, y=2000,speed=speedi,brake=0,type=Order.DESTINATION,num=22, rotation=rotation))
            orders.append(Order(x=400, y=1750,speed=speedi,brake=0,type=Order.DESTINATION,num=23, rotation=rotation))

    if checkForColor(inner, scan4[0], scan4[1]) or (not checkForColor(outer, scan4[0], scan4[1]) and checkForColor(inner, scan3[0], scan3[1])): 
        # x - x - rot                                                  x - x- !g                         r - r - x
        # cw grün-rot oder rot
        
        if (checkForColor(outer, scan3[0], scan3[1])) and (checkForColor(inner, scan4[0], scan4[1])):
            #  cw grün-rot
            if False: #rotation != 90 and rotation != 1500:
                orders.append(Order(x=672, y=1600,speed=speedi,brake=1,type=Order.DESTINATION,num=2031, rotation=rotation))
                orders.append(Order(zielwinkel=-90, speed=speedi*0.6, brake=1, type=Order.WINKEL, rotation=rotation))
                if not waitCompleteOrders():
                    return
                time.sleep(0.3)
                orders.append(Order(x=800, y=1050,speed=speedi,brake=0,type=Order.DESTINATION,num=18, rotation=rotation))
            else:
                #orders.append(Order(x=700, y=1600,speed=speedi,brake=1,type=Order.DESTINATION,num=2032, rotation=rotation))
                orders.append(Order(x=800+spaceFix, y=1150,speed=speedi,brake=1,type=Order.DESTINATION,num=181, rotation=rotation))
                orders.append(Order(zielwinkel=-90, speed=0.4, brake=1, type=Order.WINKEL, rotation=rotation))
                if not waitCompleteOrders():
                    return
                time.sleep(0.5)
                slam.lastQuadrant=slam.getQuadrant(1300)
                slam.logger.warning("Manual Repostion Front 0 from driveRound 1") 
                orders.append(Order(angleCheckOverwrite=-90,type=Order.REPOSITIONSINGLE, rotation=rotation))
                time.sleep(0.2)
                #slam.repositionOneDirFront(-90, rotation=rotation)
                #orders.append(Order(x=800, y=1050,speed=speedi,brake=0,type=Order.DESTINATION,num=182, rotation=rotation))

    else:
        #rot-grün oder grün
        if rotation != 90 and rotation != 1500:
            # Standard tight path continues at x=200mm
            # y=1100mm provides clearance when approaching destination area
            if (checkForColor(inner, scan3[0], scan3[1])) and (checkForColor(outer, scan4[0], scan4[1])):   
                # Grün Rot
                # orders.append(Order(x=350, y=1600,speed=speedi,brake=1,type=Order.DESTINATION,num=201, rotation=rotation))
                # orders.append(Order(zielwinkel=-90, speed=speedi*0.6, brake=1, type=Order.WINKEL, rotation=rotation))
                # if not waitCompleteOrders():
                #     return
                # time.sleep(0.3)
                
                # orders.append(Order(x=800, y=1150,speed=speedi,brake=1,type=Order.DESTINATION,num=181, rotation=rotation))
                orders.append(Order(x=200+spaceFix, y=1150,speed=speedi,brake=1,type=Order.DESTINATION,num=241, rotation=rotation))
                
                orders.append(Order(zielwinkel=-90, speed=0.4, brake=1, type=Order.WINKEL, rotation=rotation))
                if not waitCompleteOrders():
                    return
                time.sleep(0.5)
                slam.lastQuadrant=slam.getQuadrant(1300)
                slam.logger.warning("Manual Repostion Front 0 from driveRound 2") 
                orders.append(Order(angleCheckOverwrite=-90,type=Order.REPOSITIONSINGLE, rotation=rotation))
                time.sleep(0.2)
                #slam.repositionOneDirFront(-90, rotation=rotation)
                # orders.append(Order(x=800, y=1050,speed=speedi,brake=0,type=Order.DESTINATION,num=182, rotation=rotation))
                
                
            else:    
                orders.append(Order(x=200, y=1100,speed=speedi,brake=0,type=Order.DESTINATION,num=202, rotation=rotation))
        else:
            # Special 90-degree rotations continue at x=400mm
            orders.append(Order(x=400, y=1000,speed=speedi,brake=0,type=Order.DESTINATION,num=24, rotation=rotation))

    # Step 5: Generate corner waypoint for section transition (if not last section)
    # The corner waypoint positions the robot for the next section
    # Skip if this is the last section - robot will proceed to parking instead
    if not last:
        # Re-evaluate obstacle configuration for more precise corner placement
        # This is necessary as we need final source/destination assessment
        sinside= checkForColor(inner, scan4[0], scan4[1])  or ((not checkForColor(outer, scan4[0], scan4[1])) and checkForColor(inner, scan3[0], scan3[1]))
        dinside= checkForColor(inner, scan1[0], scan1[1])  or ((not checkForColor(outer, scan1[0], scan1[1])) and checkForColor(inner, scan2[0], scan2[1]))
        
        # Debug output to verify obstacle detection logic
        print("Rotation: ",rotation, "  sinside: " ,sinside, "   dinside: ",dinside)
        
        # Choose corner waypoint based on combined source/destination obstacle configuration
        # Different corners needed for different rotation angles (standard vs 180-degree)
        if rotation != 180 and rotation != 1180:
            # Standard corner positions (most rotations: 0°, 90°, 270°)
            if ( sinside and not  dinside):
                # Source has inner obstacles, destination is outer-only
                # Use moderate corner at (600, 550) - wider x to clear source obstacles
                orders.append(Order(x=600, y=550,speed=speedi,brake=0,type=Order.DESTINATION,num=26, rotation=rotation))
            if ( not sinside and dinside):
                # Source is outer-only, destination has inner obstacles
                # Use higher corner at (400, 800) - extra y clearance for destination
                orders.append(Order(x=300, y=700,speed=speedi,brake=0,type=Order.DESTINATION,num=27, rotation=rotation))
                orders.append(Order(zielwinkel=-180, speed=speedi*0.75, brake=1, type=Order.WINKEL, rotation=rotation))
                if not waitCompleteOrders():
                    return
                time.sleep(0.3)
                orders.append(Order(angleCheckOverwrite=-180,type=Order.REPOSITION, rotation=rotation))
                if not waitCompleteOrders():
                    return
                time.sleep(0.3)
            
    
    
            if ( not sinside and  not dinside):
                # Both areas have outer obstacles only - tightest safe corner
                # Use tight corner at (400, 500) for most efficient path
                orders.append(Order(x=400, y=500,speed=speedi,brake=0,type=Order.DESTINATION,num=28, rotation=rotation))
        else:
            # Special corner positions due to parking space being in the way
            if ( sinside and not  dinside):
                # Source inner, destination outer
                orders.append(Order(x=700, y=700,speed=speedi,brake=0,type=Order.DESTINATION,num=261, rotation=rotation))
            if ( not sinside and dinside):
                # Source outer, destination inner
                orders.append(Order(x=300, y=700,speed=speedi,brake=1,type=Order.DESTINATION,num=272, rotation=rotation))
                orders.append(Order(zielwinkel=-180, speed=speedi*0.75, brake=1, type=Order.WINKEL, rotation=rotation))
                if not waitCompleteOrders():
                    return
                time.sleep(0.3)
                orders.append(Order(angleCheckOverwrite=-180,type=Order.REPOSITION, rotation=rotation))
                if not waitCompleteOrders():
                    return
                time.sleep(0.3)
            if ( not sinside and  not dinside):
                # Both outer
                orders.append(Order(x=450, y=550,speed=speedi,brake=0,type=Order.DESTINATION,num=283, rotation=rotation))

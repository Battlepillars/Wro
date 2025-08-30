# THE TEAM

<img width="600" height="289" alt="battlepillars_schriftzug Kopie" src="https://github.com/user-attachments/assets/b1e74876-8f35-4747-abe6-3c268d19bde8" />
<img width="500" height="262" alt="raupe Kopie" src="https://github.com/user-attachments/assets/5048b443-22c2-430e-9be0-1adfdb5afe0f" />

In this repository, you’ll find the documentation for the robot created by the "Battlepillars" for the 2025 World Robot Olympiad Future Engineers competition. The robot was the result of a collaborative effort by three students.

aus den Regeln: Pictures of the team and robot must be provided. The pictures of the robot must cover all sides of the robot, must be clear, in focus and show aspects of the mobility, power and sense, and obstacle management. Reference in the discussion sections 1, 2 and 3 can be made to these pictures. Team photo is necessary for judges to relate and identify the team during the local and international competitions. 

Fotos und kurze Beschreibung

<br><br><br>

# Mobility Management
aus den Regeln: Mobility management discussion should cover how the vehicle movements are managed. What motors are selected, how they are selected and implemented. A brief discussion regarding the vehicle chassis design /selection can be provided as well as the mounting of all components to the vehicle chassis/structure. The discussion may include engineering principles such as speed, torque, power etc. usage. Building or assembly instructions can be provided together with 3D CAD files to 3D print parts. 

Die Diskussion zur Bewegungssteuerung sollte beschreiben, wie die Bewegungen des Fahrzeugs gesteuert werden. Dabei sollte erläutert werden, welche Motoren ausgewählt wurden, nach welchen Kriterien sie ausgewählt wurden und wie sie im System implementiert sind.
Auch eine kurze Beschreibung des Designs oder der Auswahl des Fahrzeugchassis kann enthalten sein, ebenso wie Informationen zur Befestigung aller Komponenten am Chassis bzw. an der Fahrzeugstruktur.
Die Diskussion kann ingenieurwissenschaftliche Prinzipien wie Geschwindigkeit, Drehmoment, Leistung usw. einbeziehen.
Bauanleitungen oder Montagehinweise können zusammen mit 3D-CAD-Dateien bereitgestellt werden, um Bauteile im 3D-Druck herzustellen.

In diesem Kapitel “Mobility Management” werden wir den Motor, das Servo den Fahrtenregler und den Antriebsstrang des Modellautos näher vorstellen und erläutern, ob wir das jeweilige Bauteil übernommen haben oder ob wir es gegen eine Alternative ausgetauscht haben.

A coordinated system consisting of the chassis, steering mechanism, and powertrain is responsible for the robot's mobility, allowing it to move with both precision and efficiency.

## Chassis
Wir hatten die Idee, unser Auto kürzer als 20cm zu bauen, damit wir am Ende der drei Runden des Hindernisrennens einfach geradeaus einparken können. Dies war nach den regionalen deutschen Regeln zulässig. Kein Modellauto hat ein passendes Maß. Somit war uns bewusst, dass wir ein Auto werden umbauen müssen. Die meisten Modellautos sind um die 30cm lang. Wir trauten uns nicht zu, solch ein langes Auto auf 20cm zu kür-zen. Andere Modellautos sind nur um die 10cm lang. In diesen war kein Platz für unsere ganzen Komponenten. Nur ein einziges Modellauto hatte 22cm. Bei diesem sahen wir die Möglichkeit, es auf 20 cm zu kürzen. Dieses haben wir dann als Basis für unser selbstfahrendes Auto ausgesucht: LaTrax Rally.

<table>
  <tr>
    <th width=500>LaTrax Rally</th>
    <th width=500>Specifications</th>
  </tr>
  <tr>
    <td><img src="https://github.com/Battlepillars/Wro/blob/main/auto1.jpg"><br><img src="https://github.com/Battlepillars/Wro/blob/main/auto2.jpg"> </td>
    <td><li>Motorart:	Elektro</li>
<li>Antrieb:	4WD</li>
<li>Maßstab:	1:18</li>
<li>Ausführung:	RTR - READY TO RUN</li>
<li>Drive / Bau:	11</li>
</td>
   </tr>
</table>

Where to buy the car: https://traxxas.com/75054-5-118-latrax-rally

<br><br>

## Powertrain

### Drivetrain
Folgende Antriebsarten gibt es bei Autos: 

- Allradantrieb: Alle Räder werden angetrieben. 
- Frontantrieb: Nur die vorderen Räder werden angetrieben. 
- Heckantrieb: Nur die hinteren Räder werden angetrieben. 

Das vorhandene Chassis hatte einen Allradantrieb eingebaut, der für den Wettbewerb in Ordnung gewesen wäre. Allerdings war mit der vorhandenen Lenkung kein großer Radeinschlag möglich. Wir konnten z.B. bei der Parkchallenge nicht in einem Zug ausparken. Somit haben wir überlegt, wie wir den Lenkausschlag erhöhen können. Dies haben wir erreicht, indem wir eine komplett neue Vorderachse konstruiert haben. Beim Umbau war es nicht möglich, den Antrieb der Vorderachse zu übernehmen, da die Kardangelenke diesen starken Einschlag nicht mitgemacht haben. Deshalb benutzen wir nur noch den Hinterradantrieb. 

Für den Bau der neuen Vorderachse haben wir vorab eine Konzeptzeichnung erstellt: 

### Motor
Den bereits vorhandenen Brushed Motor haben wir anderen Motorarten gegenübergestellt, über deren Vor- und Nachteile wir uns im Internet informiert haben. Unsere Recherche hat ergeben, dass es neben dem Brushed Motor noch einen Brushless Motor und einen Schrittmotor gibt.

- Brushless Motor: Dieser hätte mehr Leistung als der Motor, der im Modellauto verbaut war, was für den Wettbewerb jedoch nicht nötig ist. Außerdem sind diese Motoren bei niedrigen Geschwindigkeiten schwierig zu steuern, was ungünstig ist, wenn wir langsam die Hindernisse umfahren möchten.
- Schrittmotor: Diese Motoren sind sehr genau zu steuern, aber aufwendig in der Ansteuerung. Außerdem brauchen sie viel Strom, sie sind groß und eher langsam.
  
=> Wir haben uns dafür entschieden, den bereits im Modellauto vorhandenen Brushed Motor zu verwenden.

<table>
  <tr>
    <th width=500>Motor</th>
    <th width=500>Specifications</th>
  </tr>
  <tr>
    <td><img src="https://github.com/Battlepillars/Wro/blob/main/motor.jpg"> </td>
    <td>23-turn brushed 370-size LaTrax® motor with bullet connectors
</td>
   </tr>
</table>

Where to buy the motor: [https://traxxas.com/75054-5-118-latrax-rally](https://traxxas.com/7575r-23-turn-brushed-370-size-motor)

### Motor Driver (= Fahrtenregler)
Der Fahrtenregler sitzt zwischen der Batterie und dem Motor und ist zuständig für die Steuerung der Drehzahl des Motors. In unseren Experimenten hat sich gezeigt, dass der mitgelieferte Fahrtenregler für schnelles Fahren ausgelegt ist. Im langsamen Bereich lässt er sich nicht feinfühlig regeln. 

Nach weiterführender und intensiver Recherche haben wir herausgefunden, dass einige Modellautos für das Fahren auf hügeligen und rauen Böden optimiert sind. Diese Autos nennen sich “Crawler”. Die Eigenschaften der Fahrtenregler von Crawlern entsprechen der Anforderung, die wir haben, nämlich das präzise Fahren bei langsamen Geschwindigkeiten.

=> Wegen dieser spezifischen Vorteile haben wir uns für einen neuen den Fahrtenregler entschieden, den Quicrun WP 1080–G2.

<table>
  <tr>
    <th width=500>Motor Driver</th>
    <th width=500>Specifications</th>
  </tr>
  <tr>
    <td><img src="https://github.com/Battlepillars/Wro/blob/main/fahrtenregler.jpg"> </td>
    <td><li>Application: 1/10th Rock Crawler</li>
<li>Motor Type: Brushed Motor (540 / 555 size motors)</li>
<li>Cont./Peak Current: 80A/400A</li>
<li>Input Voltage: 2-3S LiPo/5-9S Cell NiMH</li>
<li>BEC Output: 6V / 7.4V / 8.4V @ 4A (Switch-mode)</li>
<li>Wires & Connectors: Black-14AWG-200mm / Red-14AWG-200mm</li>
<li>Programming device: LED program box</li>
</td>
   </tr>
</table>

Where to buy the motor: [https://traxxas.com/75054-5-118-latrax-rally](https://traxxas.com/7575r-23-turn-brushed-370-size-motor)
  
<br><br>

## Steering
- Erläuterung (auch Ackermann!)

### Servo Motor
- Bild + Spezifikationen



<br><br><br>

# Power and Sense Management
aus den Regeln: Power and Sense management discussion should cover the power source for the vehicle as well as the sensors required to provide the vehicle with information to negotiate the different challenges. The discussion can include the reasons for selecting various sensors and how they are being used on the vehicle together with power consumption. The discussion could include a wiring diagram with BOM for the vehicle that includes all aspects of professional wiring diagrams. 
<br><br>
Die Diskussion zum Energie- und Sensorsystem sollte sowohl die Stromquelle des Fahrzeugs als auch die Sensoren abdecken, die benötigt werden, um dem Fahrzeug Informationen zur Bewältigung der verschiedenen Herausforderungen bereitzustellen. Die Diskussion kann die Gründe für die Auswahl verschiedener Sensoren sowie deren Einsatz am Fahrzeug und den damit verbundenen Energieverbrauch beinhalten. Es kann zudem ein Schaltplan mit Stückliste (BOM) für das Fahrzeug enthalten sein, der alle Aspekte professioneller Verdrahtungspläne berücksichtigt.

Kurzer Satz was in dem Kapitel alles benannt werden wird.

<br><br>

## Sensoren
  
### Li-Po Battery
- Bild + Spezifikationen

### LiDAR
- Bild + Spezifikationen

### Kamera
- Bild + Spezifikationen

### Odometrie Sensor
- Bild + Spezifikationen
- Verbesserungsvorschlag: Einen dritten Sensor einbauen, damit echte Mehrheitsentscheidung, was der richtige Messwert ist

<br><br>

## Schaltplan der Bauteile
- Schaltplan
  
<br><br><br>

# Code für alle Komponenten
- wird von Nils gefüllt

<br><br><br>

# Obstacle Management

Dieses Kapitel schreibt Nils
Die Diskussion zum Hindernismanagement sollte die Strategie des Fahrzeugs zur Bewältigung des Hindernisparcours in Bezug auf alle Herausforderungen beinhalten. Dies kann Flussdiagramme, Pseudocode sowie Quellcode mit ausführlichen Kommentaren umfassen.
<br><br>
## Initial location aqusition 

At the beginning of the program, the robot detects the starting direction in which the car must drive on the track, based on its position on the mat.

For the Open Challenge, there are four different positions where we can place the robot, which allow it to recognize how it must drive. These four options result from the fact that there are two possible starting sections and two directions of travel.

In the Obstacle Challenge, two different positions are possible. Here as well, the robot uses the LiDAR to detect its position and then knows which direction it needs to drive.

![WhatsApp Image 2025-08-30 at 15 24 43](https://github.com/user-attachments/assets/1f603c1c-980e-4192-8997-ed8e1bf1f1e4)


 <br><br>
## Position updates during driving 

### optical tracking sensor function 
For continuous position tracking, we use two optical tracking sensors. A downward-facing camera inside the sensor captures 20,000 images per second. Based on changes in the images, the sensor detects movement across the surface. Additionally, the sensor has a built-in gyroscope. Using data from the gyroscope and the movement across the ground, the sensor automatically calculates the current coordinates.

### sensor failure detection / health status 
Two optical tracking sensors were installed to increase redundancy. If one sensor fails, for example due to dust on the lens, the robot can still accurately determine its position. A sensor is recognized by the program as “not healthy” under the following conditions:

- One of the two sensors is at least 0.15 m/s slower than the other. Dust on the lens can prevent the sensor from accurately detecting changes in the ground, causing its reported speed to decrease. The slower sensor is then deactivated as “not healthy”.

- If one sensor reports a speed greater than 2 m/s, it is also deactivated as “not healthy”.

- If the sensor reports a position outside the playing field, it is likewise deactivated as “not healthy”.

![WhatsApp Image 2025-08-30 at 15 24 42](https://github.com/user-attachments/assets/6de3a1ca-4f9a-47d4-8c87-d71443b53063)


## position corrections 
Position tracking using the optical tracking sensor leads to inaccuracies of 2–5 cm per meter when the robot drives straight. After turns, the inaccuracy increases. These deviations are not acceptable in the Obstacle Challenge, as they may cause the robot to drive into a wall or hit an obstacle. Therefore, the program implements a position reset using the LiDAR:

- When the robot is stationary, it repositions itself based on the two outer walls. The LiDAR detects the distance to the walls and thus determines the robot's position.

- While driving, the LiDAR measures the distance to the wall in front and repositions the robot accordingly. The issue is that the LiDAR responds to the program's position request with a delay of 100–200 ms because it rotates, making repositioning less accurate while the robot is moving.

## Obstacle Recognition 
This function detects and stores obstacles within each section of the course using the LiDAR and the camera. The process is divided into two parts:

### Determining the position of an obstacle within a course section

Five scan points were defined (see Appendix 4: Scan Point Diagram), at which the LiDAR determines which of the six possible positions within the section in front of the robot the obstacle is located. The environment is not scanned continuously, but only at specific, predefined points that the robot passes during the first lap of the obstacle course. If no obstacle is detected at a scan point, the robot moves forward 50 cm and scans again.

A list of coordinates was created for all possible obstacle positions. The LiDAR checks whether something is detected near (within a radius of 100 mm) any of these coordinates. If an obstacle is detected, the position is stored in a list.

### Determining the color of the obstacle

The camera is then used to identify the color of the obstacle. For image recognition, information from the WRO support document (WRO Future Engineers Getting Started) was used. Based on the camera image, the robot determines the pixel coordinates of the detected obstacles. These coordinates are converted into an angle. For visualization, this angle is drawn on the map.

![Programmausgabe Kopie](https://github.com/user-attachments/assets/9f9b5f2e-5cb8-4573-8a63-38dcde1bda16)

 
<br><br><br><br>


 


lidar obstacle recognition 

camera obstacle recognition 

lidar/camera sensor fusion sample pseudo code 

 

command loop / control loop / display loop explanation why 3 threads short description of each thread flow diagram for each thread 

 

description of commands available to command loop (driveTo.... ) 

 

navigation strategy open challenge 

simple fixed waypoints 

 

navigation strategy obstacle challenge -scan round drive to scan point flow diagram what happens depending on obstacle setup (dive to second scan point) 

description of rotation for second scanpoint 

second/third round 

parking strategy 

9 possible imüprovements - crash recovery - wegpunkte optimieren - open challenge kürzere strecke je nach wand - obstacle challenge momentan umfahren wir mögliche blöcke die vielleicht nicht da sind. wir könnten die strecke verkürzen, würden aber viel zusätzliche komplexibilität hinzufügen 

- speed improvement by using different drive speeds (faster speed on streight ways for example) 
 
- update of heading by measuring the wall angle 
     
- more contunuous position updates by lidar 
 

<br><br><br>


Engineering materials
====

This repository contains engineering materials of a self-driven vehicle's model participating in the WRO Future Engineers competition in the season 2022.

## Content

* `t-photos` contains 2 photos of the team (an official one and one funny photo with all team members)
* `v-photos` contains 6 photos of the vehicle (from every side, from top and bottom)
* `video` contains the video.md file with the link to a video where driving demonstration exists
* `schemes` contains one or several schematic diagrams in form of JPEG, PNG or PDF of the electromechanical components illustrating all the elements (electronic components and motors) used in the vehicle and how they connect to each other.
* `src` contains code of control software for all components which were programmed to participate in the competition
* `models` is for the files for models used by 3D printers, laser cutting machines and CNC machines to produce the vehicle elements. If there is nothing to add to this location, the directory can be removed.
* `other` is for other files which can be used to understand how to prepare the vehicle for the competition. It may include documentation how to connect to a SBC/SBM and upload files there, datasets, hardware specifications, communication protocols descriptions etc. If there is nothing to add to this location, the directory can be removed.

## Introduction

_This part must be filled by participants with the technical clarifications about the code: which modules the code consists of, how they are related to the electromechanical components of the vehicle, and what is the process to build/compile/upload the code to the vehicle’s controllers._

## How to prepare the repo based on the template

_Remove this section before the first commit to the repository_

1. Clone this repo by using the `git clone` functionality.
2. Remove `.git` directory
3. [Initialize a new public repository on GitHub](https://github.com/new) by following instructions from "create a new repository on the command line" section (appeared after pressing "Create repository" button).

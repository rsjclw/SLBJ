from PyQt5.QtCore import QObject, pyqtSignal
import numpy as np
from utils import Globe, Control
from datetime import datetime
from serial import Serial
from threading import Thread, Lock
from TCPClient import TCPClient
from time import sleep, time
import random

class Boat(QObject):
    updateJkt = pyqtSignal(dict)
    updateBoat = pyqtSignal(tuple)
    updateDest = pyqtSignal(tuple)
    updateStatus = pyqtSignal(str)
    running = 0
    def __init__(self, boatID_, globeMap, serialName=None, serverIP=None, serverPort=None, jktSerialName=None):
        super(Boat, self).__init__()
        self.globe = Globe(globeMap)
        self.boatID = boatID_
        self.serialConnected = False
        self.jktSerialConnected = False
        self.tcpConn = TCPClient()
        if serialName != None:
            self.serialConnected = True
            try: self.serialConn = Serial(serialName, 115200, timeout=0)
            except Exception as e: self.serialConnected = False
        if jktSerialName != None :
            self.jktSerialConnected = True
            try: self.jktSerialConn = Serial(serialName, 115200, timeout=0)
            except Exception as e: self.jktSerialConnected = False
        if serverIP != None and serverPort != None: self.tcpConn.connect(serverIP, serverPort)
        if not self.serialConnected: print("Cannot connect to serial port")
        if not self.jktSerialConnected: print("Cannot connect to Lifejacket Server")
        self.on = False
        self.status = 1 # 1: picking up jackets, 2: going to land, 3: going to ship, 4: custom input
        self.lat = 0
        self.lon = 0
        self.saverLat = 0
        self.saverLon = 0
        self.destLat = None
        self.destLon = None
        self.heading = 0
        self.serialData = ""
        self.jktSerialData = ""
        self.serialDataStartFlag = False
        self.jktSerialDataStartFlag = False
        self.nearestJkt = None
        self.nearestJktTemp = None
        self.nearestJktDistance = 20020001
        self.mtxJkt = Lock()
        self.msg0 = "$BOAT"+str(self.boatID)+";0"
        self.jktLen = 0
        self.jktDictTemp = {}
        self.control = Control([1,0,1,4], [1,0,1,4], 1.5)
        self.rescuePlan = 2
        self.searchingJackets = True
        self.maxRange = 999
        self.wait = False
        self.changeStatusTime = 20
        self.newStatus = 0
        self.paused = False
        self.customInputPos = (0, 0)
        self.lastShipMsg = 0
        self.jktTime = 0
        self.jktDataTimestamp = 0
        self.worldMapFlag = False
        t = Thread(target=self.__tcpRun)
        t.daemon = True
        t.start()
    
    def stop(self):
        self.on = False
        self.globe.stop()
        while self.running > 0: sleep(0.001)
        self.serialSend("$00#")
    
    def pause(self):
        self.paused = True

    def resume(self):
        self.paused = False

    def getNearestJkt(self):
        self.mtxJkt.acquire()
        ret = self.nearestJkt
        self.mtxJkt.release()
        return ret
    
    def setWorldMapFlag(self, flag):
        self.worldMapFlag = flag
    
    def __tcpRun(self):
        self.on = True
        self.running += 1
        ts = time()
        while self.on:
            if self.tcpConn.isConnected(): self.__tcpHandler()
            if self.jktSerialConnected: self.__serialJktHandler()
            if self.serialConnected: self.__serialHandler()
            if time()-ts > 0.5:
                self.tcpConn.send("$BOAT{};{};{};{}{}".format(self.boatID, self.lat, self.lon, self.status, self.maxRange))
                ts = time()
            sleep(0.001)
        self.running -= 1

    def __tcpHandler(self):
        data = self.tcpConn.read()
        if not self.status == 3 or data is None: return
        if data == "$!!":
            self.setDest((None, None))
            self.saverLat = 0
            self.saverLon = 0
            self.updateStatus.emit("Ship not found")
            return
        data = data.split(";")
        if time()-self.lastShipMsg > self.changeStatusTime:
            self.setDest((None, None))
            self.saverLat = 0
            self.saverLon = 0
            self.setNewStatusGotoLand()
        if len(data) != 3: return
        self.lastShipMsg = time()
        self.saverLat = float(data[1])
        self.saverLon = float(data[2])
        if self.wait:
            self.setGotoShip()

    def __serialJktHandler(self):
        if time()-self.jktDataTimestamp > 5:
            self.jktDictTemp = {}
            self.updateJkt.emit(self.jktDictTemp)
            self.jktLen = 0
        jktSerialData = self.jktSerialConn.read(self.jktSerialConn.in_waiting)
        # jktSerialData = "$-54.607303;13.620126#".encode('ascii')
        if len(jktSerialData) == 0: return
        try: jktSerialData = jktSerialData.decode('ascii')
        except: return
        # print(jktSerialData)
        startIdx = 0
        idxA = -1
        if self.jktSerialDataStartFlag == False:
            idxA = jktSerialData.find('$')
            if idxA != -1:
                startIdx = idxA+1
                self.jktSerialData = ""
                self.jktSerialDataStartFlag = True
        if self.jktSerialDataStartFlag == True:
            idxB = jktSerialData.find('#', startIdx)
            if idxB != -1:
                self.jktSerialData += jktSerialData[startIdx: idxB]
                self.jktSerialDataStartFlag = False
                self.jktSerialData = self.jktSerialData.split(';')
                if len(self.jktSerialData) == 2:
                    # print(self.jktSerialData)
                    try: lat = float(self.jktSerialData[0])
                    except: return
                    try: lon = float(self.jktSerialData[1])
                    except: return
                    if self.worldMapFlag: self.jktDictTemp[0] = (self.globe.latToIndex(lat), self.globe.lonToIndex(lon))
                    else: self.jktDictTemp[0] = (lat, lon)
                    self.updateJkt.emit(self.jktDictTemp)
                    self.mtxJkt.acquire()
                    self.nearestJkt = (0, lat, lon)
                    self.mtxJkt.release()
                    self.jktLen = len(self.jktDictTemp)
                    self.jktDictTemp = {}
            else:
                self.jktSerialData += jktSerialData[startIdx:]

    def __serialHandler(self):
        serialData = self.serialConn.read(self.serialConn.in_waiting)
        # serialData = "$-54.603021;13.619758;69#".encode('ascii')
        if len(serialData) == 0: return
        try: serialData = serialData.decode('ascii')
        except: return
        # print(serialData)
        startIdx = 0
        idxA = -1
        if self.serialDataStartFlag == False:
            idxA = serialData.find('$')
            if idxA != -1:
                startIdx = idxA+1
                self.serialData = ""
                self.serialDataStartFlag = True
        if self.serialDataStartFlag == True:
            idxB = serialData.find('#', startIdx)
            if idxB != -1:
                self.serialData += serialData[startIdx: idxB]
                self.serialDataStartFlag = False
                self.serialData = self.serialData.split(';')
                if len(self.serialData) == 3:
                    # print(self.serialData)
                    try: tempLat = float(self.serialData[0])
                    except: tempLat = self.lat
                    try: tempLon = float(self.serialData[1])
                    except: tempLon = self.lon
                    try: tempHeading = float(self.serialData[2])
                    except: tempHeading = self.heading
                    self.setBoatPos(tempLat, tempLon)
                    self.heading = tempHeading
            else:
                self.serialData += serialData[startIdx]

    def serialSend(self, message):
        if self.serialConnected: return self.serialConn.write(message.encode('ascii'))
        return -7
    
    def isReady(self):
        if self.lat == 0 and self.lon == 0 and self.heading == 0: return False
        return True
    
    def setDest(self, pos):
        self.destLat = pos[0]
        self.destLon = pos[1]
        if pos == (None, None): self.updateDest.emit((-10000, -10000))
        else: self.updateDest.emit((self.globe.latToIndex(pos[0]), self.globe.lonToIndex(pos[1])))
    
    def requestShip(self):
        self.saverLat = 0
        self.saverLon = 0
        self.updateStatus.emit("Requesting ship")
        self.status = 3
        self.wait = True
        self.tcpConn.send("$BOAT{};{};{};3{}".format(self.boatID, self.lat, self.lon, self.maxRange))
        self.lastShipMsg = time()
    
    def setGotoLand(self):
        self.searchingJackets = False
        self.updateStatus.emit("Searching land")
        self.rescuePlan = 2
        self.status = 2
        dest = self.globe.search_land(self.lat, self.lon, self.maxRange*1000)
        self.setDest(dest)
        self.control.setControlPoint(self.lat, self.lon, self.destLat, self.destLon)
        if dest != (None, None): self.updateStatus.emit("Going to land")
        else: self.updateStatus.emit("Land not found")

    def setGotoShip(self):
        self.searchingJackets = False
        self.setDest((self.saverLat, self.saverLon))
        self.control.setControlPoint(self.lat, self.lon, self.destLat, self.destLon)
        self.rescuePlan = 3
        self.updateStatus.emit("Going to ship")
        self.lastShipMsg = time()
    
    def setPickupJacket(self):
        self.searchingJackets = True
        self.updateStatus.emit("Picking up lifejackets")
        self.status = 1
    
    def setBoatPos(self, lat, lon):
        self.lat = lat
        self.lon = lon
        if self.worldMapFlag: self.updateBoat.emit((self.globe.latToIndex(lat), self.globe.lonToIndex(lon)))
        else: self.updateBoat.emit((lat, lon))
    
    def customInput(self):
        self.setDest(self.customInputPos)
        self.control.setControlPoint(self.lat, self.lon, self.destLat, self.destLon)
        self.updateStatus.emit("Going to custom input")
        self.status = 5
    
    def changeStatus(self):
        if self.newStatus != 0:
            if self.newStatus == 1: self.setPickupJacket()
            elif self.newStatus == 2: self.setGotoLand()
            elif self.newStatus == 3: self.setGotoShip()
            elif self.newStatus == 4: self.requestShip()
            elif self.newStatus == 5: self.customInput()
            self.newStatus = 0
            return
        if self.rescuePlan == 2: self.setGotoLand()
        elif self.rescuePlan == 3: self.setGotoShip()
    
    def setNewStatusPickupJacket(self):
        self.globe.stop()
        self.newStatus = 1

    def setNewStatusGotoLand(self):
        self.globe.stop()
        self.newStatus = 2

    def setNewStatusGotoShip(self):
        self.globe.stop()
        self.newStatus = 3

    def setNewStatusRequestShip(self):
        self.globe.stop()
        self.newStatus = 4
    
    def setNewStatusGotoCustom(self, lat, lon):
        self.globe.stop()
        self.newStatus = 5
        self.customInputPos = (lat, lon)

    def main_(self):
        self.on = True
        self.running += 1
        # self.setBoatPos(random.uniform(-7.287302, -7.286075), random.uniform(112.795609, 112.796427))
        # while not self.isReady() and self.on: sleep(0.01)
        sleep(2)
        at = time()
        wt = 0
        arrived = False
        while self.on:
            if self.newStatus != 0: self.changeStatus()
            # self.setBoatPos(-54.603021, 13.619758)
            # self.setBoatPos(-13.288855, 114.539096)
            # self.setBoatPos(-57.852749, 76.813443)
            # self.setBoatPos(random.uniform(-7.287302, -7.286075), random.uniform(112.795609, 112.796427))
            # self.lat = random.uniform(-7.287302, -7.286075) # random.uniform(-90.0, 90.0) # -7.287106
            # self.lon = random.uniform(112.795609, 112.796427) # random.uniform(-180.0, 180.0) # 112.796112
            # self.heading = random.uniform(-180.0, 180.0)
            if self.searchingJackets and self.jktLen > 0: self.setPickupJacket()
            if self.status == 1: # picking up jackets
                if self.jktLen > 0:
                    self.setDest((self.getNearestJkt())[1:])
                    self.control.setControlPoint(self.lat, self.lon, self.destLat, self.destLon)
                    if self.control.isArrived():
                        if time()-at > 0.5: self.tcpConn.send("$BOAT{};1;{}".format(self.boatID, (self.getNearestJkt())[0]))
                else:
                    if time()-wt > self.changeStatusTime:
                        wt = time()
                        self.changeStatus()
                        self.searchingJackets = True

            elif self.status == 2: # going to land
                if self.destLat is None and self.destLon is None:
                    if time()-wt > self.changeStatusTime:
                        wt = time()
                        self.requestShip()
                        self.searchingJackets = True
                controlOutput = self.control.control(self.lat, self.lon, self.heading)

            elif self.status == 3: # going to ship
                if self.saverLat == 0 and self.saverLon == 0:
                    if time()-wt > self.changeStatusTime:
                        wt = time()
                        self.setGotoLand()
                        self.searchingJackets = True
                else: controlOutput = self.control.control(self.lat, self.lon, self.heading)

            elif self.status == 4: # going to custom input
                controlOutput = self.control.control(self.lat, self.lon, self.heading)

            if self.control.isArrived():
                if not arrived: at = time()
                arrived = True
                message = "$0, 0#"
            elif self.wait or self.paused:
                message = "$0, 0#"
            else: message = "${} {}#".format(200, int(self.control.control(self.lat, self.lon, self.heading)))
            self.serialSend(message)
            sleep(0.01)
        self.running -= 1
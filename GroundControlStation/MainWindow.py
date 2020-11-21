from PyQt5 import uic
from PyQt5.QtWidgets import QMainWindow
from PyQt5.QtCore import pyqtSignal, QThread
from time import sleep
from utils import Globe
from datetime import datetime
from TCPClient import TCPClient
from copy import copy

class MainWindow(QMainWindow):
    startTCP = pyqtSignal()
    stopTCP = pyqtSignal()
    def __init__(self, parent=None):
        super(MainWindow, self).__init__()
        uic.loadUi("MainWindow.ui", self)
        self.globe = Globe("danau8map.npz")
        self.tcpThread = QThread()
        self.tcp = TCPClient("GCSt00", "10.181.15.202", 6969)
        self.tcp.moveToThread(self.tcpThread)
        self.tcpThread.start()

        self.initUIConnection()
        self.selectedBoatID = ""
        self.boatsTemp = {}
    
    def switchTCP(self):
        if self.tcp.isConnected():
            self.pushButton_switchConnection.setText("Connect")
            self.tcp.stopConnection()
        else:
            self.pushButton_switchConnection.setText("Disconnect")
            self.startTCP.emit()
    
    def __updatePos(self, boatID, lat, lon, saverLat, saverLon, status):
        if boatID == "$!!":
            self.widget_Map.updatePos(self.boatsTemp)
            self.boatsTemp = {}
        else:
            self.boatsTemp[boatID] = (self.globe.latToIndex(lat), self.globe.lonToIndex(lon), self.globe.latToIndex(saverLat), self.globe.lonToIndex(saverLon))
        if boatID == self.selectedBoatID:
            self.lineEdit_boatID.setText(boatID[1:])
            self.lineEdit_boatLat.setText(str(lat))
            self.lineEdit_boatLon.setText(str(lon))
            #1 picking up jackets, 2: going to land, 3: going to ship 4: request ship for help
            if status == '1': self.lineEdit_boatMission.setText("Picking up jackets")
            if status == '2': self.lineEdit_boatMission.setText("Going to land")
            if status == '3': self.lineEdit_boatMission.setText("Going to ship")
            if status == '4': self.lineEdit_boatMission.setText("Requesting for help")
    
    def __refreshBoat(self):
        boats = self.widget_Map.getBoats()
        self.listWidget.clear()
        for k in boats:
            self.listWidget.addItem(k[1:])
    
    def listWidgetBoatItemClicked(self, item):
        self.selectedBoatID = "$"+item.data(0)

    def initUIConnection(self):
        self.pushButton_switchConnection.clicked.connect(self.switchTCP)
        self.startTCP.connect(self.tcp.startConnection)
        self.tcp.setPos.connect(self.__updatePos)

        self.pushButton_refreshBoat.clicked.connect(self.__refreshBoat)

        self.listWidget.itemClicked.connect(self.listWidgetBoatItemClicked)
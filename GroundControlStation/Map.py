from PyQt5 import QtCore, QtWidgets
from PyQt5.QtCore import Qt, QPoint
from PyQt5.QtWidgets import QWidget
from PyQt5.QtGui import QPainter, QBrush, QColor
from PyQt5.QtCore import pyqtSignal, QThread, QTimer
from utils import convertToQPixmap, Globe
from cv2 import imread
import random

class Map(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.background = convertToQPixmap(imread("danau8.jpg"))
        self.timer = QTimer()
        self.timer.timeout.connect(self.__update)
        self.timer.start(50)
        self.globe = Globe("danau8map.npz")
        self.boats = []
        self.boatsTemp = []

    def __update(self):
        self.update()
    
    def paintEvent(self, e):
        self.painter = QPainter(self)
        self.painter.drawPixmap(0,0,self.background)
        self.painter.setPen(QColor("green"))
        self.painter.setBrush(QColor("green"))
        for boat in self.boats:
            self.painter.drawEllipse(QPoint(boat[2], boat[1]), 5, 5)
        self.painter.drawEllipse(QPoint(int(random.uniform(0, 415)), int(random.uniform(0, 631))), 2, 2)
        self.painter.end()
    
    def updatePos(self, boatID, lat, lon, saverLat, saverLon):
        if boatID == "$!!":
            self.boats = self.boatsTemp
            self.boatsTemp = []
        else:
            self.boatsTemp.append((boatID, self.globe.latToIndex(lat), self.globe.lonToIndex(lon), self.globe.latToIndex(saverLat), self.globe.lonToIndex(saverLon)))
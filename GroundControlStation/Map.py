from PyQt5 import QtCore, QtWidgets
from PyQt5.QtCore import Qt, QPoint
from PyQt5.QtWidgets import QWidget
from PyQt5.QtGui import QPainter, QBrush, QColor
from PyQt5.QtCore import pyqtSignal, QThread, QTimer
from utils import convertToQPixmap
from cv2 import imread
from copy import copy
import random

class Map(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.background = convertToQPixmap(imread("danau8.jpg"))
        self.timer = QTimer()
        self.timer.timeout.connect(self.__update)
        self.timer.start(50)
        self.boats = {}
        self.selectedBoat = ""

    def __update(self):
        self.update()
    
    def paintEvent(self, e):
        self.painter = QPainter(self)
        self.painter.drawPixmap(0,0,self.background)
        self.painter.setPen(QColor("green"))
        self.painter.setBrush(QColor("green"))
        for boat in self.boats:
            if self.boats[boat][0] == self.selectedBoat:
                self.painter.setBrush(QColor("blue"))
                self.painter.drawEllipse(QPoint(self.boats[boat][1], self.boats[boat][0]), 7, 7)
                self.painter.setBrush(QColor("green"))
            else: self.painter.drawEllipse(QPoint(self.boats[boat][1], self.boats[boat][0]), 5, 5)
        self.painter.drawEllipse(QPoint(int(random.uniform(0, 415)), int(random.uniform(0, 631))), 2, 2)
        self.painter.end()
    
    def updatePos(self, boats):
        self.boats = copy(boats)
    
    def selectBoat(self, boatID):
        self.selectedBoat = boatID
    
    def getBoats(self):
        return self.boats
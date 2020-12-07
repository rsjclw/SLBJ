from PyQt5 import QtWidgets
from MainWindow import MainWindow
from signal import SIGINT
from os import kill
from subprocess import Popen
from time import sleep

if __name__ == '__main__':
    app = QtWidgets.QApplication([])
    main = MainWindow()
    main.show()
    app.exec()
from PyQt5 import QtWidgets
from MainWindow import MainWindow
from signal import SIGINT
from os import kill
from subprocess import Popen
from time import sleep

if __name__ == '__main__':
    # p = Popen("./m.exe")
    app = QtWidgets.QApplication([])
    main = MainWindow()
    main.show()
    app.exec()
    # kill(p.pid, SIGINT)
    # p.wait()
from PyQt5 import QtWidgets
from MainWindow import MainWindow

if __name__ == '__main__':
    app = QtWidgets.QApplication([])
    main = MainWindow()
    main.show()
    app.exec()
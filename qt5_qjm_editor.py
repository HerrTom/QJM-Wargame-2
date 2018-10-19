import os
import sys

from PyQt5 import QtCore, QtGui, QtWidgets
import ui.breeze_resources

import qjm_data
import qt5_qjm_equips
import qt5_qjm_weaps

class MainGui(QtWidgets.QWidget):
    def __init__(self,parent=None):
        super().__init__(parent)
        self.initDB()
        self.initGUI()
        
    def initDB(self):
        self.db = qjm_data.database()
        
    def initGUI(self):
        mainLayout = QtWidgets.QVBoxLayout()
        self.tabWidget = QtWidgets.QTabWidget()
        mainLayout.addWidget(self.tabWidget)
        
        self.weapTab = qt5_qjm_weaps.WeaponGui(self,self.db)
        self.equipTab = qt5_qjm_equips.EquipmentGui(self,self.db)
        
        self.tabWidget.addTab(self.equipTab,"Equipment")
        self.tabWidget.addTab(self.weapTab,"Weapons")
        
        self.setLayout(mainLayout)
        self.setMinimumSize(700, 400)
        self.show()
        
def main():
    import qdarkstyle
    app = QtWidgets.QApplication(sys.argv)
    
    # file = QtCore.QFile(":/dark.qss")
    # file.open(QtCore.QFile.ReadOnly | QtCore.QFile.Text)
    # stream = QtCore.QTextStream(file)
    # app.setStyleSheet(stream.readAll())
    
    # app.setStyleSheet(qdarkstyle.load_stylesheet_pyqt5())
    
    app.setStyle(QtWidgets.QStyleFactory.create("Fusion"))
    palette = QtGui.QPalette()
    palette.setColor(QtGui.QPalette.Window, QtGui.QColor(53, 53, 53))
    palette.setColor(QtGui.QPalette.WindowText, QtCore.Qt.white)

    palette.setColor(QtGui.QPalette.Base, QtGui.QColor(15, 15, 15))
    palette.setColor(QtGui.QPalette.AlternateBase, QtGui.QColor(53, 53, 53))
    palette.setColor(QtGui.QPalette.ToolTipBase, QtCore.Qt.white)
    palette.setColor(QtGui.QPalette.ToolTipText, QtCore.Qt.white)
    palette.setColor(QtGui.QPalette.Text, QtCore.Qt.white)
    palette.setColor(QtGui.QPalette.Button, QtGui.QColor(53, 53, 53))
    palette.setColor(QtGui.QPalette.ButtonText, QtCore.Qt.white)
    palette.setColor(QtGui.QPalette.BrightText, QtCore.Qt.red)
    palette.setColor(QtGui.QPalette.Highlight, QtGui.QColor(0, 24, 193).lighter())
    palette.setColor(QtGui.QPalette.HighlightedText, QtCore.Qt.black)
    palette.setColor(QtGui.QPalette.Disabled, QtGui.QPalette.Text, QtCore.Qt.darkGray)
    palette.setColor(QtGui.QPalette.Disabled, QtGui.QPalette.ButtonText, QtCore.Qt.darkGray)

    app.setPalette(palette)

    ex = MainGui()
    app.exec_()
    # sys.exit(app.exec_())


if __name__ == '__main__':
    abspath = os.path.abspath(__file__)
    dname = os.path.dirname(abspath)
    os.chdir(dname)
    main()


import os
import sys
from collections import OrderedDict

from PyQt5 import QtCore, QtGui, QtWidgets
import breeze_resources

import qjm_data

equipTypes  = ["Infantry","Antitank","Artillery","SP Antitank","SP Artillery","APC","IFV","Tank","Air Defence","SP Air Defence","Aircraft","Helicopter"]
armourList  = ["Steel","Aluminum","Early Composite","Composite","Reactive","Modern Reactive"]
LLCFList    = ["Minimum","Active IR","Passive IR","Thermal","Advanced Thermal"]
RgFFList    = ["Stadiametric","Coincident","Ranging Rifle","Laser"]
weaponTypesList = ["Gun","ATGM","Bomb","AAM"]

guidanceList = ['MCLOS','SACLOS wire day', 'SACLOS wire day/night', 'SACLOS radio','LOSLBR','F&F']
guidanceListAAM = ['Optical','BR','IR','SARH','ARH']

class WeaponGui(QtWidgets.QWidget):
    
    def __init__(self,parent=None,db=None):
        super().__init__(parent)
        
        self.initDB(db=db)
        self.initUI()
        
    def initDB(self,db=None):
        if db is None:
            self.db = qjm_data.database()
        else:
            self.db = db
        
    def initUI(self):
        
        self.setGeometry(300, 300, 250, 150)
        self.setWindowTitle('QT QJM Weapon Editor')
        self.setWindowIcon(QtGui.QIcon('web.png'))        
        
        mainLayout = QtWidgets.QGridLayout()
        
        
        ### LIST DATA ##########################
        listWidget = QtWidgets.QWidget()
        listLayout = QtWidgets.QVBoxLayout()
        
        self.weapList = QtWidgets.QListWidget()
        weapData = self.db.getWeapNames()
        for eq in weapData:
            self.weapList.addItem(eq)
        
        self.weapNew = QtWidgets.QPushButton("New")
        self.weapSave = QtWidgets.QPushButton("Save")
        
        listLayout.addWidget(self.weapList)
        listLayout.addWidget(self.weapNew)
        listLayout.addWidget(self.weapSave)
        
        listWidget.setLayout(listLayout)
        
        # bindings for the weapment data list
        self.weapList.itemDoubleClicked.connect(self.OnWeapSelected)
        self.weapSave.clicked.connect(self.OnSaveWeap)
        
        ### weapMENT DATA #####################
        scrollWidget = QtWidgets.QScrollArea()
        weapWidget = QtWidgets.QWidget()
        scrollWidget.setWidget(weapWidget)
        scrollWidget.setWidgetResizable(True)
        
        weapLayout = QtWidgets.QVBoxLayout()
        weapWidget.setLayout(weapLayout)
        
        weapDataBox = QtWidgets.QGroupBox("Weapon:")
        weapDataLayout = QtWidgets.QGridLayout()
        weapDataLayout.setSpacing(5)
        weapDataBox.setLayout(weapDataLayout)
        
        # name
        nameLabel = QtWidgets.QLabel("Name:")
        self.name = QtWidgets.QLineEdit()
        weapDataLayout.addWidget(nameLabel,0,0)
        weapDataLayout.addWidget(self.name,0,1)
        
        # type
        typeLabel = QtWidgets.QLabel("Type:")
        self.type = QtWidgets.QComboBox()
        self.type.addItems(weaponTypesList)
        weapDataLayout.addWidget(typeLabel,1,0)
        weapDataLayout.addWidget(self.type,1,1)
        
        self.type.currentIndexChanged.connect(self.DisableByType)
        
        # range
        rangeLabel = QtWidgets.QLabel("Range:")
        self.range = QtWidgets.QLineEdit()
        weapDataLayout.addWidget(rangeLabel,2,0)
        weapDataLayout.addWidget(self.range,2,1)
        
        # rate of fire
        rofLabel = QtWidgets.QLabel("Rate of Fire:")
        self.rof = QtWidgets.QLineEdit()
        weapDataLayout.addWidget(rofLabel,3,0)
        weapDataLayout.addWidget(self.rof,3,1)
        
        # calibre
        calibreLabel = QtWidgets.QLabel("Calibre:")
        self.calibre = QtWidgets.QLineEdit()
        weapDataLayout.addWidget(calibreLabel,4,0)
        weapDataLayout.addWidget(self.calibre,4,1)
        
        # muzzle velocity
        muzzleVelLabel = QtWidgets.QLabel("Muzzle Velocity:")
        self.muzzleVel = QtWidgets.QLineEdit()
        weapDataLayout.addWidget(muzzleVelLabel,5,0)
        weapDataLayout.addWidget(self.muzzleVel,5,1)
        
        # accuracy
        accuracyLabel = QtWidgets.QLabel("Accuracy:")
        self.accuracy = QtWidgets.QDoubleSpinBox()
        self.accuracy.setMinimum(0.00)
        self.accuracy.setMaximum(1.00)
        self.accuracy.setSingleStep(0.01)
        weapDataLayout.addWidget(accuracyLabel,6,0)
        weapDataLayout.addWidget(self.accuracy,6,1)
        
        # barrels:
        barrelsLabel = QtWidgets.QLabel("Barrels:")
        self.barrels = QtWidgets.QSpinBox()
        self.barrels.setMinimum(0)
        self.barrels.setMaximum(999)
        self.barrels.setSingleStep(1)
        weapDataLayout.addWidget(barrelsLabel,7,0)
        weapDataLayout.addWidget(self.barrels,7,1)
        
        # crewed
        self.crewed = QtWidgets.QCheckBox("Crewed")
        weapDataLayout.addWidget(self.crewed,8,0,1,2)
        
        # atgms
        ATGMGroup = QtWidgets.QGroupBox("ATGM")
        ATGMLayout = QtWidgets.QGridLayout()
        ATGMGroup.setLayout(ATGMLayout)
        weapDataLayout.addWidget(ATGMGroup,9,0,1,2)
        
        # guidance
        guidanceLabel = QtWidgets.QLabel("Guidance:")
        self.guidance = QtWidgets.QComboBox()
        self.guidance.addItems(guidanceList)
        ATGMLayout.addWidget(guidanceLabel,0,0)
        ATGMLayout.addWidget(self.guidance,0,1)
        
        # min range
        minRangeLabel = QtWidgets.QLabel("Minimum Range:")
        self.minRange = QtWidgets.QLineEdit()
        ATGMLayout.addWidget(minRangeLabel,1,0)
        ATGMLayout.addWidget(self.minRange,1,1)
        
        # penetration
        penetrationLabel = QtWidgets.QLabel("Penetration:")
        self.penetration = QtWidgets.QLineEdit()
        ATGMLayout.addWidget(penetrationLabel,2,0)
        ATGMLayout.addWidget(self.penetration,2,1)
        
        # enhancement
        enhancementLabel = QtWidgets.QLabel("ATGM Enhancement:")
        self.enhancement = QtWidgets.QLineEdit()
        ATGMLayout.addWidget(enhancementLabel,3,0)
        ATGMLayout.addWidget(self.enhancement,3,1)
        
        
        # range: 3200
        # rateOfFire: 300
        # calibre: 30
        # muzzleVel: 970
        # accuracy: 0.7
        # barrels: 1
        # crew: true
        # guidance: null
        # atgmMinRange: null
        # atgmPenetration: null
        # atgmMinRange: null
        # atgmEnhancement: null
        
        weapLayout.addWidget(weapDataBox)
        
        weapLayout.addStretch(1)
        
        ### WRAP UP GUI ########################
        mainLayout.addWidget(listWidget,0,0)
        # mainLayout.addWidget(equipWidget,0,1)
        mainLayout.addWidget(scrollWidget,0,1)
        mainLayout.setColumnStretch(1,1)
        
        self.setLayout(mainLayout)
        self.setMinimumSize(700, 400)
        # self.setGeometry(300, 300, 650, 500)

        self.show()
        
    def OnWeapSelected(self):
        index = self.weapList.currentRow()
        weap = self.db.getWeapon(index)
        print("Populating {}...".format(weap.name))
        self.PopulateWeapon(weap)
    
    def PopulateWeapon(self,weap):
        self.name.setText(weap.name)
        idxType = self.type.findText(weap.type)
        if idxType != -1:
            self.type.setCurrentIndex(idxType)
        self.range.setText(str(weap.range))
        self.rof.setText(str(weap.ROF))
        self.calibre.setText(str(weap.calibre))
        self.muzzleVel.setText(str(weap.muzzleVel))
        self.accuracy.setValue(weap.accuracy)
        self.barrels.setValue(weap.barrels)
        self.crewed.setCheckState(weap.crew)
        guidanceType = self.guidance.findText(weap.guidance)
        if idxType != -1:
            self.guidance.setCurrentIndex(guidanceType)
        self.penetration.setText(str(weap.atgmPen))
        self.minRange.setText(str(weap.atgmMinRng))
        self.enhancement.setText(str(weap.atgmEn))
    
    def OnSaveWeap(self):
        weap = OrderedDict()
        weap["name"] = self.name.text()
        weap["type"] = self.type.currentText()
        weap["range"] = self.range.text()
        weap["rateOfFire"] = self.rof.text()
        weap["calibre"] = self.calibre.text()
        weap["muzzleVel"] = self.muzzleVel.text()
        weap["accuracy"] = self.accuracy.value()
        weap["barrels"] = self.barrels.value()
        weap["crew"] = self.crewed.isChecked()
        weap["guidance"] = self.guidance.currentText()
        weap["atgmPenetration"] = self.penetration.text()
        weap["atgmMinRange"] = self.minRange.text()
        weap["atgmEnhancement"] = self.enhancement.text()
        self.db.saveWeapon(weap)
        self.ReloadWeapons()
        
    def ReloadWeapons(self):
        current = self.weapList.currentItem().text()
        self.db.loadWeaps() # refresh the equipment list
        self.weapList.clear()
        self.weapList.addItems(self.db.getWeapNames())
        item = self.weapList.findItems(current,QtCore.Qt.MatchExactly)[0]
        self.weapList.setCurrentRow(self.weapList.row(item))
    
    def DisableByType(self):
        self.guidance.clear()
        if self.type.currentText() == "ATGM":
            self.guidance.addItems(guidanceList)
            self.guidance.setEnabled(True)
            self.minRange.setEnabled(True)
            self.penetration.setEnabled(True)
            self.enhancement.setEnabled(True)
            # disable others
            self.accuracy.setEnabled(False)
        elif self.type.currentText() == "AAM":
            self.guidance.addItems(guidanceListAAM)
            self.guidance.setEnabled(True)
            self.minRange.setEnabled(True)
            self.penetration.setEnabled(True)
            self.enhancement.setEnabled(True)
            # disable others
            self.accuracy.setEnabled(False)
        else:
            self.guidance.setEnabled(False)
            self.minRange.setEnabled(False)
            self.penetration.setEnabled(False)
            self.enhancement.setEnabled(False)
            # enable others
            self.accuracy.setEnabled(True)
        
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

    ex = WeaponGui()
    app.exec_()
    # sys.exit(app.exec_())


if __name__ == '__main__':
    abspath = os.path.abspath(__file__)
    dname = os.path.dirname(abspath)
    os.chdir(dname)
    main()

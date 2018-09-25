import os
import sys
from PyQt4 import QtGui

import qjm_data

weaponsList = ["","2A42","9K113 Konkurs","PKT"]
armourList  = ["Steel","Aluminum","Early Composite","Composite","Reactive","Modern Reactive"]
LLCFList    = ["Minimum","Active IR","Passive IR","Thermal","Advanced Thermal"]
RgFFList    = ["Stadiametric","Coincident","Ranging Rifle","Laser"]

class EquipmentGui(QtGui.QWidget):
    
    def __init__(self):
        super().__init__()
        
        self.initDB()
        self.initUI()
        
    def initDB(self):
        self.db = qjm_data.database()
        
    def initUI(self):
        
        self.setGeometry(300, 300, 250, 150)
        self.setWindowTitle('QT QJM Equipment Editor')
        self.setWindowIcon(QtGui.QIcon('web.png'))        
        
        mainLayout = QtGui.QGridLayout()
        
        
        ### LIST DATA ##########################
        listWidget = QtGui.QWidget()
        listLayout = QtGui.QVBoxLayout()
        
        self.equipList = QtGui.QListWidget()
        for i in range(10):
            self.equipList.addItem("Item {}".format(i+1))
        
        self.equipNew = QtGui.QPushButton("New")
        self.equipSave = QtGui.QPushButton("Save")
        
        listLayout.addWidget(self.equipList)
        listLayout.addWidget(self.equipNew)
        listLayout.addWidget(self.equipSave)
        
        listWidget.setLayout(listLayout)
        
        
        ### EQUIPMENT DATA #####################
        scrollWidget = QtGui.QScrollArea()
        equipWidget = QtGui.QWidget()
        scrollWidget.setWidget(equipWidget)
        scrollWidget.setWidgetResizable(True)
        
        equipLayout = QtGui.QVBoxLayout()
        
        ### Name data ##########################
        nameBox = QtGui.QGroupBox("Equipment:")
        nameLayout = QtGui.QGridLayout()
        nameLayout.setSpacing(5)
        
        # name
        nameLabel = QtGui.QLabel("Name:")
        self.name = QtGui.QLineEdit()
        nameLayout.addWidget(nameLabel,0,0)
        nameLayout.addWidget(self.name,0,1)
        
        # nation
        nationLabel = QtGui.QLabel("Nationality:")
        self.nation = QtGui.QLineEdit()
        nameLayout.addWidget(nationLabel,1,0)
        nameLayout.addWidget(self.nation,1,1)
        
        nameBox.setLayout(nameLayout)
        
        
        ### WEAPONS ############################
        weapBox = QtGui.QGroupBox("Weapons:")
        self.weapTable = QtGui.QTableWidget()
        
        weapLayout = QtGui.QVBoxLayout()
        weapLayout.addWidget(self.weapTable)
        weapBox.setLayout(weapLayout)
        
        nWeaps = 10 # maximum number of weapons to add
        
        # deal with the table headers
        self.weapTable.setColumnCount(2)
        self.weapTable.setHorizontalHeaderLabels(["Weapon:","Ammo:      "])
        self.weapTable.setRowCount(nWeaps)
        self.weapTable.setMinimumHeight(120)
        header = self.weapTable.horizontalHeader()
        header.setResizeMode(0, QtGui.QHeaderView.Stretch)
        header.setResizeMode(1, QtGui.QHeaderView.ResizeToContents)
        
        self.weapTable.verticalHeader().setResizeMode(QtGui.QHeaderView.ResizeToContents)
        
        self.weapCombos = []
        for row in range(nWeaps):
            weapCombo = QtGui.QComboBox()
            # weapCombo.addItems(weaponsList)
            weapCombo.addItems([""]+self.db.getWeapNames())
            self.weapCombos.append(weapCombo)
            self.weapTable.setCellWidget(row,0, self.weapCombos[-1])
        
        
        ### MOBILITY ###########################
        mobBox = QtGui.QGroupBox("Mobility:")
        mobLayout = QtGui.QGridLayout()
        mobLayout.setSpacing(5)
        # Road speed
        roadSpeedLabel = QtGui.QLabel("Road Speed:")
        roadSpeedUnits = QtGui.QLabel("km/h")
        self.roadSpeed = QtGui.QLineEdit()
        mobLayout.addWidget(roadSpeedLabel,0,0)
        mobLayout.addWidget(self.roadSpeed,0,1)
        mobLayout.addWidget(roadSpeedUnits,0,2)
        
        roadSpeedLabel.setFixedWidth(120) # to line things up nicely
        roadSpeedUnits.setFixedWidth(60)

        # Horsepower
        horsepowerLabel = QtGui.QLabel("Horsepower:")
        horsepowerUnits = QtGui.QLabel("hp")
        self.horsepower = QtGui.QLineEdit()
        mobLayout.addWidget(horsepowerLabel,1,0)
        mobLayout.addWidget(self.horsepower,1,1)
        mobLayout.addWidget(horsepowerUnits,1,2)
        
        # Ground Pressure
        groundPressureLabel = QtGui.QLabel("Ground Pressure:")
        groundPressureUnits = QtGui.QLabel("kg/cm²")
        self.groundPressure = QtGui.QLineEdit()
        mobLayout.addWidget(groundPressureLabel,2,0)
        mobLayout.addWidget(self.groundPressure,2,1)
        mobLayout.addWidget(groundPressureUnits,2,2)
        
        # Radius of Action
        radiusOfActionLabel = QtGui.QLabel("Radius of Action:")
        radiusOfActionUnits = QtGui.QLabel("km")
        self.radiusOfAction = QtGui.QLineEdit()
        mobLayout.addWidget(radiusOfActionLabel,3,0)
        mobLayout.addWidget(self.radiusOfAction,3,1)
        mobLayout.addWidget(radiusOfActionUnits,3,2)
        
        mobBox.setLayout(mobLayout)
        
        armBox = QtGui.QGroupBox("Armour:")
        armLayout = QtGui.QGridLayout()
        armLayout.setSpacing(5)
        # Weight
        weightLabel = QtGui.QLabel("Weight:")
        weightUnits = QtGui.QLabel("tonnes")
        self.weight = QtGui.QLineEdit()
        armLayout.addWidget(weightLabel,0,0)
        armLayout.addWidget(self.weight,0,1)
        armLayout.addWidget(weightUnits,0,2)
        
        weightLabel.setFixedWidth(120) # to line things up nicely
        weightUnits.setFixedWidth(60)
        
        # Length
        lengthLabel = QtGui.QLabel("Length:")
        lengthUnits = QtGui.QLabel("meters")
        self.length = QtGui.QLineEdit()
        armLayout.addWidget(lengthLabel,1,0)
        armLayout.addWidget(self.length,1,1)
        armLayout.addWidget(lengthUnits,1,2)
        
        # height
        heightLabel = QtGui.QLabel("Height:")
        heightUnits = QtGui.QLabel("meters")
        self.height = QtGui.QLineEdit()
        armLayout.addWidget(heightLabel,2,0)
        armLayout.addWidget(self.height,2,1)
        armLayout.addWidget(heightUnits,2,2)
        
        # Armour type
        armourLabel = QtGui.QLabel("Armour type:")
        self.armour = QtGui.QComboBox()
        self.armour.addItems(armourList)
        armLayout.addWidget(armourLabel,3,0)
        armLayout.addWidget(self.armour,3,1)

        armBox.setLayout(armLayout)
        
        ## FIRE CONTROL ##################
        fcBox = QtGui.QGroupBox("Fire Control:")
        fcLayout = QtGui.QGridLayout()
        fcLayout.setSpacing(5)
        
        # VisF - Open or not
        self.visf = QtGui.QCheckBox("Enclosed Vehicle")
        fcLayout.addWidget(self.visf,0,0)
        
        # Traverse factor
        self.travf = QtGui.QCheckBox("Powered traverse")
        fcLayout.addWidget(self.travf,0,1)
        
        # LLCF type
        LLCFLabel = QtGui.QLabel("LLCF type:")
        self.LLCF = QtGui.QComboBox()
        self.LLCF.addItems(LLCFList)
        fcLayout.addWidget(LLCFLabel,1,0)
        fcLayout.addWidget(self.LLCF,1,1)
        
        # RgFF type
        RgFFLabel = QtGui.QLabel("Rangefinder type:")
        self.RgFF = QtGui.QComboBox()
        self.RgFF.addItems(RgFFList)
        fcLayout.addWidget(RgFFLabel,2,0)
        fcLayout.addWidget(self.RgFF,2,1)
        
        # FCCF
        # cant correction
        self.FCCFCant = QtGui.QCheckBox("Cant correction")
        fcLayout.addWidget(self.FCCFCant,3,0)
        
        # ammo type correction
        self.FCCFAmmo = QtGui.QCheckBox("Ammo correction")
        fcLayout.addWidget(self.FCCFAmmo,3,1)
        
        # crosswind correction
        self.FCCFCrosswind = QtGui.QCheckBox("Crosswind correction")
        fcLayout.addWidget(self.FCCFCrosswind,4,0)
        
        # barrel correction
        self.FCCFBarrel = QtGui.QCheckBox("Barrel correction")
        fcLayout.addWidget(self.FCCFBarrel,4,1)
        
        fcBox.setLayout(fcLayout)
        
        ## MISC ####
        miscBox = QtGui.QGroupBox("Miscelleneous:")
        miscLayout = QtGui.QGridLayout()
        miscLayout.setSpacing(5)
        
        # Amphibious
        self.amphibious = QtGui.QCheckBox("Amphibious")
        miscLayout.addWidget(self.amphibious,0,0)
        
        miscBox.setLayout(miscLayout)
        
        equipLayout.addWidget(nameBox)
        equipLayout.addWidget(weapBox)
        equipLayout.addWidget(mobBox)
        equipLayout.addWidget(armBox)
        equipLayout.addWidget(fcBox)
        equipLayout.addWidget(miscBox)
        
        equipWidget.setLayout(equipLayout)
        
        ### WRAP UP GUI ########################
        mainLayout.addWidget(listWidget,0,0)
        # mainLayout.addWidget(equipWidget,0,1)
        mainLayout.addWidget(scrollWidget,0,1)
        mainLayout.setColumnStretch(1,1)
        
        self.setLayout(mainLayout)
        self.setMinimumSize(700, 400)
        # self.setGeometry(300, 300, 650, 500)

        self.show()
        
        
def main():
    
    app = QtGui.QApplication(sys.argv)
    ex = EquipmentGui()
    sys.exit(app.exec_())


if __name__ == '__main__':
    abspath = os.path.abspath(__file__)
    dname = os.path.dirname(abspath)
    os.chdir(dname)
    main()
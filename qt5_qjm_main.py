import os
import sys
from collections import OrderedDict

from PyQt5 import QtCore, QtGui, QtWidgets
import breeze_resources

import qt5_qjm_weaps
import qjm_data

print(QtWidgets.QStyleFactory.keys())

equipTypes  = ["Infantry","Antitank","Artillery","SP Antitank","SP Artillery","APC","IFV","Tank","Air Defence","SP Air Defence","Aircraft","Helicopter"]
armourList  = ["Steel","Aluminum","Early Composite","Composite","Reactive","Modern Reactive"]
LLCFList    = ["Minimum","Active IR","Passive IR","Thermal","Advanced Thermal"]
RgFFList    = ["Stadiametric","Coincident","Ranging Rifle","Laser"]

class EquipmentGui(QtWidgets.QWidget):
    
    def __init__(self,parent=None):
        super().__init__(parent)
        
        self.initDB()
        self.initUI()
        
    def initDB(self):
        self.db = qjm_data.database()
        
    def initUI(self):
        
        self.setGeometry(300, 300, 250, 150)
        self.setWindowTitle('QT QJM Equipment Editor')
        self.setWindowIcon(QtGui.QIcon('web.png'))        
        
        mainLayout = QtWidgets.QGridLayout()
        
        
        ### LIST DATA ##########################
        listWidget = QtWidgets.QWidget()
        listLayout = QtWidgets.QVBoxLayout()
        
        self.FilterButton = QtWidgets.QPushButton("Filter")
        self.MakeFilterMenu()
        
        self.equipList = QtWidgets.QListWidget()
        equipData = self.db.getEquipNames()
        for eq in equipData:
            self.equipList.addItem(eq)
        
        self.equipNew = QtWidgets.QPushButton("New")
        self.equipSave = QtWidgets.QPushButton("Save")
        
        listLayout.addWidget(self.FilterButton)
        listLayout.addWidget(self.equipList)
        listLayout.addWidget(self.equipNew)
        listLayout.addWidget(self.equipSave)
        
        listWidget.setLayout(listLayout)
        
        # bindings for the equipment data list
        self.equipList.itemDoubleClicked.connect(self.OnEquipSelected)
        self.equipNew.clicked.connect(self.OnNewEquipment)
        self.equipSave.clicked.connect(self.OnSaveEquipment)
        
        ### EQUIPMENT DATA #####################
        scrollWidget = QtWidgets.QScrollArea()
        equipWidget = QtWidgets.QWidget()
        scrollWidget.setWidget(equipWidget)
        scrollWidget.setWidgetResizable(True)
        
        equipLayout = QtWidgets.QVBoxLayout()
        
        ### Name data ##########################
        nameBox = QtWidgets.QGroupBox("Equipment:")
        nameLayout = QtWidgets.QGridLayout()
        nameLayout.setSpacing(5)
        
        # name
        nameLabel = QtWidgets.QLabel("Name:")
        self.name = QtWidgets.QLineEdit()
        nameLayout.addWidget(nameLabel,0,0)
        nameLayout.addWidget(self.name,0,1)
        
        # nation
        nationLabel = QtWidgets.QLabel("Nationality:")
        self.nation = QtWidgets.QLineEdit()
        nameLayout.addWidget(nationLabel,1,0)
        nameLayout.addWidget(self.nation,1,1)
        
        # type
        typeLabel   = QtWidgets.QLabel("Type:")
        self.type   = QtWidgets.QComboBox()
        self.type.addItems(equipTypes)
        nameLayout.addWidget(typeLabel,2,0)
        nameLayout.addWidget(self.type,2,1)
        
        # Operational Lethality Index
        OLILabel = QtWidgets.QLabel("OLI:")
        self.OLI = QtWidgets.QLineEdit()
        self.OLI.setReadOnly(True)
        nameLayout.addWidget(OLILabel,3,0)
        nameLayout.addWidget(self.OLI,3,1)
        
        self.OLI.setStyleSheet("color: rgb(128,128,128);")
        
        nameBox.setLayout(nameLayout)
        
        
        ### WEAPONS ############################
        weapBox = QtWidgets.QGroupBox("Weapons:")
        self.weapTable = QtWidgets.QTableWidget()
        
        weapLayout = QtWidgets.QVBoxLayout()
        weapLayout.addWidget(self.weapTable)
        weapBox.setLayout(weapLayout)
        
        nWeaps = 10 # maximum number of weapons to add
        
        # deal with the table headers
        self.weapTable.setColumnCount(2)
        self.weapTable.setHorizontalHeaderLabels(["Weapon:","Ammo:      "])
        self.weapTable.setRowCount(nWeaps)
        self.weapTable.setMinimumHeight(120)
        header = self.weapTable.horizontalHeader()
        header.setSectionResizeMode(0, QtWidgets.QHeaderView.Stretch)
        header.setSectionResizeMode(1, QtWidgets.QHeaderView.ResizeToContents)
        
        self.weapTable.verticalHeader().setSectionResizeMode(QtWidgets.QHeaderView.ResizeToContents)
        
        self.weapCombos = []
        for row in range(nWeaps):
            weapCombo = QtWidgets.QComboBox()
            # weapCombo.addItems(weaponsList)
            weapCombo.addItems([""]+self.db.getWeapNames())
            self.weapCombos.append(weapCombo)
            self.weapTable.setCellWidget(row,0, self.weapCombos[-1])
            ammoCount = QtWidgets.QLineEdit()
            ammoCount.setValidator(QtGui.QIntValidator())
            self.weapTable.setCellWidget(row,1, ammoCount)
        
        self.weapEditBtn = QtWidgets.QPushButton("Edit Weapons")
        self.weapEditBtn.clicked.connect(self.OnEditWeaps)
        
        weapLayout.addWidget(self.weapEditBtn)
        
        ### MOBILITY ###########################
        mobBox = QtWidgets.QGroupBox("Mobility:")
        mobLayout = QtWidgets.QGridLayout()
        mobLayout.setSpacing(5)
        # Road speed
        roadSpeedLabel = QtWidgets.QLabel("Road Speed:")
        roadSpeedUnits = QtWidgets.QLabel("km/h")
        self.roadSpeed = QtWidgets.QLineEdit()
        mobLayout.addWidget(roadSpeedLabel,0,0)
        mobLayout.addWidget(self.roadSpeed,0,1)
        mobLayout.addWidget(roadSpeedUnits,0,2)
        
        roadSpeedLabel.setFixedWidth(120) # to line things up nicely
        roadSpeedUnits.setFixedWidth(60)

        # Horsepower
        horsepowerLabel = QtWidgets.QLabel("Horsepower:")
        horsepowerUnits = QtWidgets.QLabel("hp")
        self.horsepower = QtWidgets.QLineEdit()
        mobLayout.addWidget(horsepowerLabel,1,0)
        mobLayout.addWidget(self.horsepower,1,1)
        mobLayout.addWidget(horsepowerUnits,1,2)
        
        # Ground Pressure
        groundPressureLabel = QtWidgets.QLabel("Ground Pressure:")
        groundPressureUnits = QtWidgets.QLabel("kg/cm²")
        self.groundPressure = QtWidgets.QLineEdit()
        mobLayout.addWidget(groundPressureLabel,2,0)
        mobLayout.addWidget(self.groundPressure,2,1)
        mobLayout.addWidget(groundPressureUnits,2,2)
        
        # Radius of Action
        radiusOfActionLabel = QtWidgets.QLabel("Radius of Action:")
        radiusOfActionUnits = QtWidgets.QLabel("km")
        self.radiusOfAction = QtWidgets.QLineEdit()
        mobLayout.addWidget(radiusOfActionLabel,3,0)
        mobLayout.addWidget(self.radiusOfAction,3,1)
        mobLayout.addWidget(radiusOfActionUnits,3,2)
        
        mobBox.setLayout(mobLayout)
        
        armBox = QtWidgets.QGroupBox("Armour:")
        armLayout = QtWidgets.QGridLayout()
        armLayout.setSpacing(5)
        # Weight
        weightLabel = QtWidgets.QLabel("Weight:")
        weightUnits = QtWidgets.QLabel("tonnes")
        self.weight = QtWidgets.QLineEdit()
        armLayout.addWidget(weightLabel,0,0)
        armLayout.addWidget(self.weight,0,1)
        armLayout.addWidget(weightUnits,0,2)
        
        weightLabel.setFixedWidth(120) # to line things up nicely
        weightUnits.setFixedWidth(60)
        
        # Length
        lengthLabel = QtWidgets.QLabel("Length:")
        lengthUnits = QtWidgets.QLabel("meters")
        self.length = QtWidgets.QLineEdit()
        armLayout.addWidget(lengthLabel,1,0)
        armLayout.addWidget(self.length,1,1)
        armLayout.addWidget(lengthUnits,1,2)
        
        # height
        heightLabel = QtWidgets.QLabel("Height:")
        heightUnits = QtWidgets.QLabel("meters")
        self.height = QtWidgets.QLineEdit()
        armLayout.addWidget(heightLabel,2,0)
        armLayout.addWidget(self.height,2,1)
        armLayout.addWidget(heightUnits,2,2)
        
        # Armour type
        armourLabel = QtWidgets.QLabel("Armour type:")
        self.armour = QtWidgets.QComboBox()
        self.armour.addItems(armourList)
        armLayout.addWidget(armourLabel,3,0)
        armLayout.addWidget(self.armour,3,1)

        armBox.setLayout(armLayout)
        
        ## FIRE CONTROL ##################
        fcBox = QtWidgets.QGroupBox("Fire Control:")
        fcLayout = QtWidgets.QGridLayout()
        fcLayout.setSpacing(5)
        
        # VisF - Open or not
        self.visf = QtWidgets.QCheckBox("Enclosed Vehicle")
        fcLayout.addWidget(self.visf,0,0)
        
        # Traverse factor
        self.travf = QtWidgets.QCheckBox("Powered traverse")
        fcLayout.addWidget(self.travf,0,1)
        
        # LLCF type
        LLCFLabel = QtWidgets.QLabel("LLCF type:")
        self.LLCF = QtWidgets.QComboBox()
        self.LLCF.addItems(LLCFList)
        fcLayout.addWidget(LLCFLabel,1,0)
        fcLayout.addWidget(self.LLCF,1,1)
        
        # RgFF type
        RgFFLabel = QtWidgets.QLabel("Rangefinder type:")
        self.RgFF = QtWidgets.QComboBox()
        self.RgFF.addItems(RgFFList)
        fcLayout.addWidget(RgFFLabel,2,0)
        fcLayout.addWidget(self.RgFF,2,1)
        
        # FCCF
        # cant correction
        self.FCCFCant = QtWidgets.QCheckBox("Cant correction")
        fcLayout.addWidget(self.FCCFCant,3,0)
        
        # ammo type correction
        self.FCCFAmmo = QtWidgets.QCheckBox("Ammo correction")
        fcLayout.addWidget(self.FCCFAmmo,3,1)
        
        # crosswind correction
        self.FCCFCrosswind = QtWidgets.QCheckBox("Crosswind correction")
        fcLayout.addWidget(self.FCCFCrosswind,4,0)
        
        # barrel correction
        self.FCCFBarrel = QtWidgets.QCheckBox("Barrel correction")
        fcLayout.addWidget(self.FCCFBarrel,4,1)
        
        # stabilized
        self.stabilised = QtWidgets.QCheckBox("Stabilised")
        fcLayout.addWidget(self.stabilised,5,0)
        
        fcBox.setLayout(fcLayout)
        
        ## MISC ####
        miscBox = QtWidgets.QGroupBox("Miscelleneous:")
        miscLayout = QtWidgets.QGridLayout()
        miscLayout.setSpacing(5)
        
        # Amphibious
        self.amphibious = QtWidgets.QCheckBox("Amphibious")
        miscLayout.addWidget(self.amphibious,0,0,1,5)
        
        crewLabel = QtWidgets.QLabel("Crew:")
        self.crew = QtWidgets.QSpinBox()
        miscLayout.addWidget(crewLabel,1,0)
        miscLayout.addWidget(self.crew,1,1)
        
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
        
    def MakeFilterMenu(self):
        self.FilterMenu = QtWidgets.QMenu(self)
        self.FilterTypeMenu = QtWidgets.QMenu("Equipment Type")
        self.FilterNationMenu = QtWidgets.QMenu("Equipment Nation")
        
        # clear the menu items
        self.FilterTypeMenu.clear()
        self.FilterNationMenu.clear()
        
        self.typeFilters = []
        typeFilterStrings = self.db.getAllTypes()
        for tp in typeFilterStrings:
            self.typeFilters.append(QtWidgets.QAction(tp,checkable=True))
            self.typeFilters[-1].triggered.connect(self.ApplyFilter)
        self.FilterTypeMenu.addActions(self.typeFilters)
        
        self.nationFilters = []
        nationFilterStrings = self.db.getAllNations()
        for tp in nationFilterStrings:
            self.nationFilters.append(QtWidgets.QAction(tp,checkable=True))
        self.FilterNationMenu.addActions(self.nationFilters)
        
        self.FilterMenu.addMenu(self.FilterTypeMenu)
        self.FilterMenu.addMenu(self.FilterNationMenu)
        self.FilterButton.setMenu(self.FilterMenu)
        
    def ApplyFilter(self):
        typeFilters = []
        nationFilters = []
        for action in self.typeFilters:
            if action.isChecked():
                typeFilters.append(action.text())
            # print(action.text(),action.isChecked())
        for action in self.nationFilters:
            if action.isChecked():
                nationFilters.append(action.text())
        if typeFilters == []:
            typeFilters = None
        if nationFilters == []:
            nationFilters = None
        
        print(nationFilters,typeFilters)
            
        self.ReloadEquipmentList(typeFilter=typeFilters,nationFilter=None)
        
    def OnEquipSelected(self):
        index = self.equipList.currentItem().text()
        # index = self.equipList.currentRow()
        equip = self.db.getEquipmentByName(index)
        print("Populating {}...".format(equip.name))
        self.PopulateEquipment(equip)
        
    def PopulateEquipment(self,equip):
        self.name.setText(str(equip.name))
        self.nation.setText(str(equip.nation))
        
        self.OLI.setText("{:,.1f}".format(equip.OLI))
        
        idxType = self.type.findText(equip.type)
        if idxType != -1:
            self.type.setCurrentIndex(idxType)
        # add the weapons to the list
        self.ClearWeapons()
        if equip.weapons is not None:
            idx = 0
            for weap,ammo in equip.weapons.items():
                weapItem = self.weapTable.cellWidget(idx,0).findText(weap,QtCore.Qt.MatchExactly)
                self.weapTable.cellWidget(idx,0).setCurrentIndex(weapItem)
                self.weapTable.cellWidget(idx,1).setText(ammo)
                idx += 1
        self.roadSpeed.setText(str(equip.roadSpeed))
        self.horsepower.setText(str(equip.horsepower))
        self.groundPressure.setText(str(equip.groundPress))
        self.radiusOfAction.setText(str(equip.radiusOfAction))
        self.weight.setText(str(equip.weight))
        self.length.setText(str(equip.length))
        self.height.setText(str(equip.height))
        idxArmour = self.armour.findText(equip.armour)
        if idxArmour != -1:
            self.armour.setCurrentIndex(idxArmour)
        
        # fire control
        self.visf.setChecked(equip.enclosed)
        self.travf.setChecked(equip.traverse)
        
        idxLLCF = self.LLCF.findText(equip.lowLight)
        if idxLLCF != -1:
            self.LLCF.setCurrentIndex(idxLLCF)
        idxRangefinder = self.RgFF.findText(equip.rangefinder)
        if idxRangefinder != -1:
            self.RgFF.setCurrentIndex(idxRangefinder)
        self.FCCFCant.setChecked(equip.fcCant)
        self.FCCFAmmo.setChecked(equip.fcAmmo)
        self.FCCFCrosswind.setChecked(equip.fcWind)
        self.FCCFBarrel.setChecked(equip.fcBarrel)
        self.stabilised.setChecked(equip.stab)
        
        self.amphibious.setChecked(equip.amphibious)
        self.crew.setValue(equip.crew)

        
    def ReloadEquipmentList(self,typeFilter=None,nationFilter=None):
        if self.equipList.currentItem() is None:
            current = None
        else:
            current = self.equipList.currentItem().text()
        self.db.loadEquip() # refresh the equipment list
        self.equipList.clear()
        eqNames = self.db.getEquipNames(typeFilter,nationFilter)
        self.equipList.addItems(eqNames)
        if current is not None and current in eqNames:
            item = self.equipList.findItems(current,QtCore.Qt.MatchExactly)[0]
            self.equipList.setCurrentRow(self.equipList.row(item))
    
    def ClearWeapons(self):
        # clears the weapons list
        self.db.loadWeaps()
        weapNames = [""] + self.db.getWeapNames()
        count = self.weapTable.rowCount()
        for idx in range(count):
            # print(self.weapTable.cellWidget(idx,0), self.weapTable.item(idx,1))
            self.weapTable.cellWidget(idx,0).clear()
            self.weapTable.cellWidget(idx,0).addItems(weapNames)
            self.weapTable.cellWidget(idx,0).setCurrentIndex(0)
            self.weapTable.cellWidget(idx,1).setText("")
    
    def OnSaveEquipment(self):
        weaps = dict()
        count = self.weapTable.rowCount()
        for idx in range(count):
            # if the entry ammo count is none
            if self.weapTable.cellWidget(idx,1).text() != "":
                weaps.update({self.weapTable.cellWidget(idx,0).currentText():
                                self.weapTable.cellWidget(idx,1).text()})
    
        equip = OrderedDict()
        equip['name']            = self.name.text()
        equip['nation']          = self.nation.text()
        equip['type']            = self.type.currentText()
        equip['weapons']         = weaps
        equip['roadSpeed']       = self.roadSpeed.text()
        equip['horsepower']      = self.horsepower.text()
        equip['groundPress']     = self.groundPressure.text()
        equip['radiusOfAction']  = self.radiusOfAction.text()
        equip['weight']          = self.weight.text()
        equip['length']          = self.length.text()
        equip['height']          = self.height.text()
        equip['armour']          = self.armour.currentText()
        equip['enclosed']        = self.visf.isChecked()
        equip['traverse']        = self.travf.isChecked()
        equip['lowLight']        = self.LLCF.currentText()
        equip['rangefinder']     = self.RgFF.currentText()
        equip['fcCant']          = self.FCCFCant.isChecked()
        equip['fcAmmo']          = self.FCCFAmmo.isChecked()
        equip['fcWind']          = self.FCCFCrosswind.isChecked()
        equip['fcBarrel']        = self.FCCFBarrel.isChecked()
        equip['stabilised']      = self.stabilised.isChecked()
        equip['amphibious']      = self.amphibious.isChecked()
        equip['crew']            = self.crew.value()
        
        self.db.saveEquipment(equip)

        # finally, reload the equipment list
        self.ReloadEquipmentList()
        
    def OnNewEquipment(self):
        equip = qjm_data.equipment()
        self.PopulateEquipment(equip)
        
    def OnEditWeaps(self):
        self.WeapWindow = qt5_qjm_weaps.WeaponGui()
        self.WeapWindow.show()
        
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

    ex = EquipmentGui()
    app.exec_()
    # sys.exit(app.exec_())


if __name__ == '__main__':
    abspath = os.path.abspath(__file__)
    dname = os.path.dirname(abspath)
    os.chdir(dname)
    main()

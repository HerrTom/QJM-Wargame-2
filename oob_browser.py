import os
import sys
import glob

from PyQt5 import QtCore, QtGui, QtWidgets
import ui.breeze_resources
from PIL.ImageQt import ImageQt

import qjm_data

# nation colours

nationColour = {"DDR": (145,80,71), "USSR": (219,26,0), "UK": (255,218,218), "BRD": (177,177,177),
                "VRN": (255,218,218), "BRN": (255,255,218), "NK": (224,255,218), "NDR": (244,218,255),
                }

def gen_OOB_dict(db):
    relations = []
    for formation in db.formations:
        parent = formation.hq
        id = formation.shortname
        relations.append((parent,id))
    
    parents, children = map(set, zip(*relations))
    OOB = {p: get_children(p, relations) for p in (parents - children)}
    
    return OOB

def ColourIcon(pixmap,colour):
    colour = QtGui.QColor(colour[0],colour[1],colour[2],)
    mask = pixmap.createMaskFromColor(QtGui.QColor(128,224,255),QtCore.Qt.MaskOutColor)
    painter = QtGui.QPainter(pixmap)
    painter.setPen(colour)
    painter.drawPixmap(pixmap.rect(),mask,mask.rect())
    painter.end()
    
    return pixmap

def get_children(parent, relations):
    children = (r[1] for r in relations if r[0] == parent)
    return {c: get_children(c, relations) for c in children}
    
def get_icons(path):
    icons = {}
    files = glob.glob(path)
    for f in files:
        SIDC = os.path.basename(f).strip(".png")
        icons[SIDC] = f
    return icons

def MakePixmap(image):
        im = image.copy()
        # im = im.convert("RGB")
        # data = im.tobytes("raw","RGB")
        # qim = QtGui.QImage(data, im.size[0], im.size[1], QtGui.QImage.Format_RGB888)
        qim = ImageQt(im)
        qtim = QtGui.QImage(qim)
        pix = QtGui.QPixmap.fromImage(qtim)
        pix.detach()
        return pix

class MapLabel(QtWidgets.QLabel):
    RightClickSignal = QtCore.pyqtSignal([list])
    def __init__(self,*args,**kwargs):
        QtWidgets.QLabel.__init__(self,*args,**kwargs)
    
    def mousePressEvent(self, event):
        if event.button() == QtCore.Qt.RightButton:
            
            x = self.mapFromGlobal(QtGui.QCursor.pos()).x()
            y = self.mapFromGlobal(QtGui.QCursor.pos()).y()
            self.RightClickSignal.emit([x,y])

            
class UnitIcon(QtWidgets.QLabel):
    LeftClickSignal = QtCore.pyqtSignal(str)
    RightClickSignal = QtCore.pyqtSignal(str)
    def __init__(self, *args, **kwargs):
        QtWidgets.QLabel.__init__(self, *args, **kwargs)
        self.QJMName = None
    
    def mousePressEvent(self, event):
        if event.button() == QtCore.Qt.LeftButton:
            self.LeftClickSignal.emit(self.QJMName)
        elif event.button() == QtCore.Qt.RightButton:
            self.RightClickSignal.emit(self.QJMName)
        
class StretchedLabel(QtWidgets.QLabel):
    def __init__(self, *args, **kwargs):
        QtWidgets.QLabel.__init__(self, *args, **kwargs)
        self.setSizePolicy(QtWidgets.QSizePolicy.Ignored, QtWidgets.QSizePolicy.Ignored)

    def resizeEvent(self, evt):
        font = self.font()
        font.setPixelSize(self.height() * 0.8)
        self.setFont(font)


class MainGui(QtWidgets.QMainWindow):
    def __init__(self,parent=None,database=None):
        super().__init__(parent)
        mainWidget = QtWidgets.QWidget(self)
        self.setCentralWidget(mainWidget)
        
        self.db = database
        
        # menu items
        file = QtWidgets.QMenu("File",self)
        self.load = QtWidgets.QAction("Load Definition",self)
        file.addAction(self.load)
        self.save = QtWidgets.QAction("Save Definition",self)
        file.addAction(self.save)
        self.export = QtWidgets.QAction("Export Definition",self)
        file.addAction(self.export)
        self.simulate = QtWidgets.QAction("Simulate",self)
        file.addAction(self.simulate)
        view = QtWidgets.QMenu("View",self)
        self.ag = QtWidgets.QActionGroup(self,exclusive=True)
        self.Territory = self.ag.addAction(QtWidgets.QAction("Territory",self,checkable=True))
        view.addAction(self.Territory)
        self.Roughness = self.ag.addAction(QtWidgets.QAction("Terrain Roughness",self,checkable=True))
        view.addAction(self.Roughness)
        self.Cover = self.ag.addAction(QtWidgets.QAction("Terrain Cover",self,checkable=True))
        view.addAction(self.Cover)
        self.Water = self.ag.addAction(QtWidgets.QAction("Terrain Water",self,checkable=True))
        view.addAction(self.Water)
        self.BLUSupply = self.ag.addAction(QtWidgets.QAction("BLUFOR traffic",self,checkable=True))
        view.addAction(self.BLUSupply)
        self.REDSupply = self.ag.addAction(QtWidgets.QAction("REDFOR traffic",self,checkable=True))
        view.addAction(self.REDSupply)
        self.Water.setChecked(True)
        view.addSeparator()
        self.viewUnits = QtWidgets.QAction("Show all units",checkable=True)
        self.viewUnits.triggered.connect(self.ShowAllUnits)
        self.viewUnits.setChecked(True)
        view.addAction(self.viewUnits)
        info = QtWidgets.QMenu("Info",self)
        self.infoLoss = QtWidgets.QAction("Losses",self)
        info.addAction(self.infoLoss)
        
        # connect actions
        self.simulate.triggered.connect(self.OnSimulate)
        
        self.ag.triggered.connect(self.OnView)
        
        self.export.triggered.connect(self.OnExportData)
        
        self.infoLoss.triggered.connect(self.OnInfoLoss)
        
        menubar = self.menuBar()
        menubar.addMenu(file)
        menubar.addMenu(view)
        menubar.addMenu(info)
        
        
        layout = QtWidgets.QGridLayout()
        mainWidget.setLayout(layout)
        
        # mapImg= ImageQt(self.db.frontline.TerrainWater)
        self.map = MakePixmap(self.db.frontline.TerrainWater)
        # self.map = QtGui.QPixmap("./data/nirgendwola/maps/nirgendwola_water.bmp")
        
        # scroll area
        mapview = QtWidgets.QScrollArea(self)
        mapview.setWidgetResizable(True)
        mapview.setMinimumHeight(600)
        QtWidgets.QScroller.grabGesture(mapview.viewport(),QtWidgets.QScroller.LeftMouseButtonGesture)
        
        layout.addWidget(mapview,0,0,2,2)
        # self.maplbl = QtWidgets.QGraphicsView(mapview)
        self.maplbl = MapLabel(parent=mapview)
        self.maplbl.RightClickSignal.connect(self.OnMapClick)
        # self.maplbl = QtWidgets.QLabel(mapview)
        mapview.setWidget(self.maplbl)
        mapview.setAlignment(QtCore.Qt.AlignTop)
        # mapviewLayout = QtWidgets.QHBoxLayout(mapview)
        # mapviewLayout.setAlignment(QtCore.Qt.AlignTop)
        
        self.maplbl.setPixmap(self.map)
        # self.maplbl.setAlignment(QtCore.Qt.AlignCenter)
        # self.maplbl.setScaledContents(True)
        # mapviewLayout.addStretch()
        # mapviewLayout.addWidget(self.maplbl)
        # mapviewLayout.addStretch()
        # layout.addWidget(self.maplbl,0,0,2,2)
        
        # unit name label
        self.unitLabel = QtWidgets.QLabel(" "*18,parent=self.maplbl)
        self.unitLabel.setAlignment(QtCore.Qt.AlignBottom)
        
        # SIDC label
        self.SIDCLabel = StretchedLabel("     ",parent=self.maplbl)
        self.SIDCLabel.setAlignment(QtCore.Qt.AlignCenter)
        self.SIDCLabel.setScaledContents(True)
        
        # waypoint label
        self.wpLabel = StretchedLabel("X",parent=self.maplbl)
        self.wpLabel.setAlignment(QtCore.Qt.AlignRight)
        
        # OOB tree
        self.OOBTree = QtWidgets.QTreeView(self)
        self.OOBModel = QtGui.QStandardItemModel(self)
        self.OOBModel.setHorizontalHeaderLabels(["Order of Battle"])
        self.OOBTree.setModel(self.OOBModel)
        self.OOBTree.setUniformRowHeights(True)
        layout.addWidget(self.OOBTree,2,0,2,1)
        
        self.OOBTree.clicked.connect(self.GetFormationData)
        
        
        OOB = gen_OOB_dict(self.db)
        self.icons = get_icons("./data/_sidc/*.png")
        self.PopulateOOBTree(OOB,self.OOBModel.invisibleRootItem())
        
        # details box
        fixed_font = QtGui.QFont("monospace")
        fixed_font.setStyleHint(QtGui.QFont.Monospace)
        self.detailsBox = QtWidgets.QTextEdit(self)
        self.detailsBox.setFont(fixed_font)
        layout.addWidget(self.detailsBox,2,1,1,1)
        
        # equipment table
        self.eqTable = QtWidgets.QTreeView(self)
        layout.addWidget(self.eqTable,3,1,1,1)
        eqModel = QtGui.QStandardItemModel(self)
        self.eqTable.setModel(eqModel)
        self.eqTable.header().setSectionResizeMode(3) #resize to contents
        # self.eqTable.verticalHeader().hide()
        
        # list for all units labels
        self.GenUnitIcons()
        self.ShowAllUnits(None)
        
        
        self.show()
        
    def GetFormationData(self):
        # find the formation
        name = self.OOBTree.currentIndex().data()
        form = self.db.getFormationByName(name)
        if form is not None:
            info, states = form.GetStatus()
            self.detailsBox.setText(info)
            self.PopulateEqTable(states)
            x,y = form.xy
            
            form.PrintStrength()
            
            self.unitLabel.setText(". {}".format(form.shortname))
            size = self.unitLabel.size()
            self.unitLabel.move(x+10,y-size.height()+8) # 4 is offset for text
            
            # SIDC = form.SIDC
            # try:
                # self.SIDCLabel.setPixmap(QtGui.QPixmap(self.icons[SIDC]))
            # except:
                # print("SIDC {} not available".format(SIDC))
                # self.SIDCLabel.setPixmap(QtGui.QPixmap(self.icons["SFGPU-------"]))
            # self.SIDCLabel.move(x,y)
            
            
            
            if form.waypoint is not None:
                self.wpLabel.move(form.waypoint[0],form.waypoint[1])
            else:
                self.wpLabel.move(-100,-100)
            
            
    def PopulateEqTable(self,states):
        self.eqTable.model().clear()
        names = states["Intact"].keys()
        for eq in names:
            nm = QtGui.QStandardItem(eq)
            ok = QtGui.QStandardItem("{:,}".format(states["Intact"][eq]))
            dm = QtGui.QStandardItem("{:,}".format(states["Damaged"][eq]))
            da = QtGui.QStandardItem("{:,}".format(states["Destroyed"][eq]))
            datum = [nm, ok, dm, da]
            self.eqTable.model().appendRow(datum)
        self.eqTable.model().setHorizontalHeaderLabels(["Type","OK","DAM","DES"])
            
    
    def PopulateOOBTree(self,children,parent):
        for child in sorted(children):
            form = self.db.getFormationByShortName(child)
            if form is not None:
                long_name = form.name
                SIDC = form.SIDC
            else:
                long_name = child
                SIDC = "SFGPU-------"
            child_item = QtGui.QStandardItem(long_name)
            try:
                child_item.setIcon(QtGui.QIcon(self.icons[SIDC]))
            except:
                print("SIDC {} not available".format(SIDC))
                child_item.setIcon(QtGui.QIcon(self.icons["SFGPU-------"]))
            child_item.setEditable(False)
            parent.appendRow(child_item)
            self.PopulateOOBTree(children[child], child_item)
    
    def GenUnitIcons(self):
        self.units = []
        for form in self.db.formations:
            if form is not None:
                try:
                    colour = nationColour[form.nation]
                except:
                    colour = (128,224,255)
                SIDC = form.SIDC
                formLabel = UnitIcon("     ",parent=self.maplbl)
                # formLabel = QtWidgets.QLabel("     ",parent=self.maplbl)
                self.units.append(formLabel)
                formLabel.QJMName = form.name
                
                formLabel.LeftClickSignal.connect(self.OnUnitLeftClick)
                
                try:
                    formLabel.setPixmap(ColourIcon(QtGui.QPixmap(self.icons[SIDC]),colour))
                except:
                    print("SIDC {} not available".format(SIDC))
                    formLabel.setPixmap(QtGui.QPixmap(self.icons["SFGPU-------"]))
                formLabel.setAlignment(QtCore.Qt.AlignCenter)
                formLabel.setScaledContents(True)
                formLabel.setGeometry(QtCore.QRect(form.x, form.y, 20, 20))
    
    def ShowAllUnits(self,event):
        # delete and recreate self.units
        for x in self.units:
            x.hide()
            
        # quit here if unchecked
        if not self.viewUnits.isChecked():
            return
        
        for formLabel in self.units:
            form = self.db.getFormationByName(formLabel.QJMName)
            formLabel.setGeometry(QtCore.QRect(form.x-10, form.y-10, 20, 20))
            formLabel.show()
    
    def OnUnitLeftClick(self,event):
        # event contains the name of the unit clicked
        model = self.OOBTree.model()
        idx = model.match(model.index(0,0), 0, event,flags=QtCore.Qt.MatchExactly|QtCore.Qt.MatchRecursive)[0] # [0] makes sure we only select the first item
        self.OOBTree.setCurrentIndex(idx)
        
        # trigger formation data collection
        self.GetFormationData()
    
    def OnSimulate(self,event):
        self.db.Simulate()
        # update the view
        self.ShowAllUnits(None)
        self.OnView(None)
        
    def OnOOBClick(self,event):
        self.GetFormationData(self)
        
    def OnInfoLoss(self,event):
        print(self.db.LossesBySide())
        
    def OnExportData(self,event):
        self.db.dumpFormations()
        
    def OnView(self,event):
        if self.ag.checkedAction() is self.Water:
            self.maplbl.setPixmap(MakePixmap(self.db.frontline.TerrainWater))
        elif self.ag.checkedAction() is self.Territory:
            self.maplbl.setPixmap(MakePixmap(self.db.frontline.Territory))
        elif self.ag.checkedAction() is self.Cover:
            self.maplbl.setPixmap(MakePixmap(self.db.frontline.TerrainCover))
        elif self.ag.checkedAction() is self.BLUSupply:
            self.maplbl.setPixmap(MakePixmap(self.db.frontline.TrafficBLU))
        elif self.ag.checkedAction() is self.REDSupply:
            self.maplbl.setPixmap(MakePixmap(self.db.frontline.TrafficRED))
        else:
            self.maplbl.setPixmap(MakePixmap(self.db.frontline.TerrainType))
            
    def OnMapClick(self,coords):
        name = self.OOBTree.currentIndex().data()
        form = self.db.getFormationByName(name)
        if form is not None:
            form.waypoint = coords
            print(form.shortname,coords)
            self.wpLabel.setGeometry(coords[0]-5,coords[1]-5,10,10)
            # self.wpLabel.move(coords[0],coords[1])
        
def main():
    # import qdarkstyle
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

    # app.setPalette(palette)

    # gameName = "germany83"
    gameName = "nirgendwola"
    path = "./data/"+gameName+"/"
    configName = gameName + ".yml"
    formationPath = path + "formations/"
    mapPath = path + "maps/" + configName
    db = qjm_data.database()
    db.loadFormations(formationPath)
    db.loadFrontline(mapPath)
    
    ex = MainGui(database=db)
    app.exec_()
    # sys.exit(app.exec_())


if __name__ == '__main__':
    abspath = os.path.abspath(__file__)
    dname = os.path.dirname(abspath)
    os.chdir(dname)
    
    
    
    main()
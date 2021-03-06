import os
import sys
import glob

from PyQt5 import QtCore, QtGui, QtWidgets
import ui.breeze_resources
from PIL.ImageQt import ImageQt

import qjm_data

# nation colours

nationColour = {"DDR": (145,80,71), "USSR": (219,26,0), "UK": (255,218,218), "BRD": (177,177,177),
                "NL": (255,120,30), "BEL": (255,238,0),
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
    def __init__(self,parent=None,*args,**kwargs):
        QtWidgets.QLabel.__init__(self,parent=parent,*args,**kwargs)
        self.parent = parent

    def mousePressEvent(self, event):
        if event.button() == QtCore.Qt.RightButton:
            #x = self.mapFromGlobal(QtGui.QCursor.pos()).x()
            #y = self.mapFromGlobal(QtGui.QCursor.pos()).y()
            x = event.x()
            y = event.y()
            print(x,y)
            self.RightClickSignal.emit([x,y])
        super().mousePressEvent(event)


class ZoomGraphicsView(QtWidgets.QGraphicsView):
    def __init__ (self, parent=None):
        super().__init__ (parent)
        self.setDragMode(QtWidgets.QGraphicsView.ScrollHandDrag)

    def wheelEvent(self, event):
        # Zoom Factor
        zoomInFactor = 1.1
        zoomOutFactor = 1 / zoomInFactor

        # Set Anchors
        self.setTransformationAnchor(QtWidgets.QGraphicsView.NoAnchor)
        self.setResizeAnchor(QtWidgets.QGraphicsView.NoAnchor)

        # Save the scene pos
        oldPos = self.mapToScene(event.pos())

        # Zoom
        if event.angleDelta().y() > 0:
            zoomFactor = zoomInFactor
        else:
            zoomFactor = zoomOutFactor
        self.scale(zoomFactor, zoomFactor)

        # Get the new position
        newPos = self.mapToScene(event.pos())

        # Move scene to old position
        delta = newPos - oldPos
        self.translate(delta.x(), delta.y())
            
class UnitIcon(QtWidgets.QLabel):
    LeftClickSignal = QtCore.pyqtSignal(list)
    RightClickSignal = QtCore.pyqtSignal(list)
    def __init__(self, *args, **kwargs):
        QtWidgets.QLabel.__init__(self, *args, **kwargs)
        self.QJMName = None
        self.SIDC = None
        self.BaseColour = None
        self.Icon = None
        self.formation = qjm_data.formation()
    
    def ResetIcon(self,brighten=None):
        colour = self.BaseColour
        if brighten is not None:
            colour = [min(x+brighten,255) for x in colour]
        try:
            self.setPixmap(ColourIcon(QtGui.QPixmap(self.Icon),colour))
        except:
            pass

    def mousePressEvent(self, event):
        if event.button() == QtCore.Qt.LeftButton:
            self.LeftClickSignal.emit([self, self.QJMName])
        elif event.button() == QtCore.Qt.RightButton:
            self.RightClickSignal.emit([self, self.QJMName])
            # create context menu:
            self.cMenu = QtWidgets.QMenu(self)
            stance = QtWidgets.QActionGroup(self)
            stanceDefending = QtWidgets.QAction("Defending",checkable=True)
            stanceDefending.setChecked(2)
            stanceAttacking = QtWidgets.QAction("Attacking",checkable=True)
            stance.addAction(stanceDefending)
            self.cMenu.addAction(stanceDefending)
            self.cMenu.addAction(stanceAttacking)
            self.cMenu.exec_(self.mapToGlobal(event.pos()))
        
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
        self.load = QtWidgets.QAction("Load Definition",self,triggered=self.LoadDefinition)
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
        self.Roads = self.ag.addAction(QtWidgets.QAction("Terrain Roads",self,checkable=True))
        view.addAction(self.Roads)
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

        debugMenu = QtWidgets.QMenu("Debug",self)
        self.debugDoSupply = QtWidgets.QAction("Run Supply",self,checkable=True)
        self.debugDoSupply.setChecked(True)
        debugMenu.addAction(self.debugDoSupply)
        
        # connect actions
        self.simulate.triggered.connect(self.OnSimulate)
        
        self.ag.triggered.connect(self.OnView)
        
        self.export.triggered.connect(self.OnExportData)
        
        self.infoLoss.triggered.connect(self.OnInfoLoss)
        
        menubar = self.menuBar()
        menubar.addMenu(file)
        menubar.addMenu(view)
        menubar.addMenu(info)
        menubar.addMenu(debugMenu)
        
        
        layout = QtWidgets.QGridLayout()
        mainWidget.setLayout(layout)
        
        # mapImg= ImageQt(self.db.frontline.TerrainWater)
        self.map = MakePixmap(self.db.frontline.TerrainWater)
        # self.map = QtGui.QPixmap("./data/nirgendwola/maps/nirgendwola_water.bmp")
        
        # scroll area
        # mapview = QtWidgets.QScrollArea(self)
        mapview = ZoomGraphicsView(self)
        #mapview.setWidgetResizable(True)
        mapview.setMinimumHeight(600)
        #QtWidgets.QScroller.grabGesture(mapview.viewport(),QtWidgets.QScroller.LeftMouseButtonGesture)
        self._scene = QtWidgets.QGraphicsScene(mapview)
        mapview.setScene(self._scene)

        layout.addWidget(mapview,0,0,2,2)
        # self.maplbl = QtWidgets.QGraphicsView(mapview)
        self.maplbl = MapLabel()
        self.maplbl.RightClickSignal.connect(self.OnMapClick)
        self.maplbl.setAlignment(QtCore.Qt.AlignTop)
        # self.maplbl = QtWidgets.QLabel(mapview)
        self._scene.addWidget(self.maplbl)
        #mapview.setWidget(self.maplbl)
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
        self.unitLabel.setStyleSheet("QLabel {color: black;}")
        self.unitLabel.show()
        
        
        # OOB tree
        self.OOBTree = QtWidgets.QTreeView(self)
        self.OOBModel = QtGui.QStandardItemModel(self)
        self.OOBModel.setHorizontalHeaderLabels(["Order of Battle"])
        self.OOBTree.setModel(self.OOBModel)
        self.OOBTree.setUniformRowHeights(True)
        layout.addWidget(self.OOBTree,2,0,2,1)
        
        self.OOBTree.selectionModel().selectionChanged.connect(self.GetFormationData)
        
        
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
        self.units = []
        self.GenUnitIcons()
        self.ShowAllUnits(None)

        # SIDC label
        #self.SIDCLabel = UnitIcon("     ",parent=self.maplbl)
        #self.SIDCLabel.setAlignment(QtCore.Qt.AlignCenter)
        #self.SIDCLabel.setScaledContents(True)
        #self.SIDCLabel.show()
        
        # waypoint label
        self.otherIcons = get_icons("./data/_icons/*.png")
        self.wpLabel = UnitIcon(" X ",parent=self.maplbl)
        self.wpLabel.setAlignment(QtCore.Qt.AlignCenter)
        self.wpLabel.setPixmap(QtGui.QPixmap(self.otherIcons["waypoint"]))
        self.wpLabel.show()
        self.MoveWaypoint(-100,-100)

        self.show()
        
    def MoveWaypoint(self,x,y):
        self.wpLabel.setScaledContents(True)
        self.wpLabel.setGeometry(QtCore.QRect(x-4,y-4, 8, 8))
        


    def GetFormationData(self,event=None):
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
                # get location of parent

                #self.wpLabel.move(form.waypoint[0],form.waypoint[1])
                self.MoveWaypoint(form.waypoint[0],form.waypoint[1])
            else:
                #self.wpLabel.move(-100,-100)
                self.MoveWaypoint(-500,-500)
            
            
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
    
    def ClearUnitIcons(self):
        for unit in self.units:
            unit.deleteLater()
            unit = None
        self.units = []


    def GenUnitIcons(self):
        self.ClearUnitIcons()
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
                formLabel.BaseColour = colour
                formLabel.SIDC = SIDC
                
                formLabel.LeftClickSignal.connect(self.OnUnitLeftClick)
                
                try:
                    formLabel.setPixmap(ColourIcon(QtGui.QPixmap(self.icons[SIDC]),colour))
                    formLabel.Icon = self.icons[SIDC]
                except:
                    print("SIDC {} not available".format(SIDC))
                    formLabel.setPixmap(QtGui.QPixmap(self.icons["SFGPU-------"]))
                    formLabel.icon = self.icons["SFGPU-------"]
                formLabel.setAlignment(QtCore.Qt.AlignCenter)
                formLabel.setScaledContents(True)
                formLabel.setGeometry(QtCore.QRect(form.x, form.y, 20, 20))
        self.ShowAllUnits()
    
    def ShowAllUnits(self,event=None):
        # hide everything
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
        idx = model.match(model.index(0,0), 0, event[1],flags=QtCore.Qt.MatchExactly|QtCore.Qt.MatchRecursive)[0] # [0] makes sure we only select the first item
        self.OOBTree.setCurrentIndex(idx)

        # reset the colours of all units
        for icon in self.units:
            icon.ResetIcon()
        # set the selected unit's color brighter
        event[0].ResetIcon(brighten=20)


        # trigger formation data collection
        self.GetFormationData()
    
    def OnSimulate(self,event):
        # get the state of the supply debug flag
        self.db.setDebugSupplyFlag(self.debugDoSupply.isChecked())
        self.db.Simulate()
        # update the view
        self.ShowAllUnits(None)
        self.OnView(None)
        
    def OnInfoLoss(self,event):
        print(self.db.LossesBySide())
        
    def OnExportData(self,event):
        self.db.dumpFormations()
        import yaml_to_geojson as conv
        conv.convert('./convert/yaml_in/*.yml')

        
    def OnView(self,event):
        if self.ag.checkedAction() is self.Water:
            self.maplbl.setPixmap(MakePixmap(self.db.frontline.TerrainWater))
        elif self.ag.checkedAction() is self.Territory:
            self.maplbl.setPixmap(MakePixmap(self.db.frontline.Territory))
        elif self.ag.checkedAction() is self.Cover:
            self.maplbl.setPixmap(MakePixmap(self.db.frontline.TerrainCover))
        elif self.ag.checkedAction() is self.Roads:
            self.maplbl.setPixmap(MakePixmap(self.db.frontline.Roads))
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
            self.MoveWaypoint(coords[0], coords[1])
            #self.wpLabel.setGeometry(coords[0]-5,coords[1]-5,10,10)
            # self.wpLabel.move(coords[0],coords[1])

    def LoadDefinition(self,event):
        configpath = QtWidgets.QFileDialog.getOpenFileName(self,"Config File","./data/",filter="Config Files (*.yml)")
        configpath = configpath[0]
        if configpath != "":
            formationpath =  os.path.dirname(os.path.dirname(configpath)) + "/formations/"
            print(formationpath)
            db = qjm_data.database()
            db.loadFormations(formationpath)
            db.loadFrontline(configpath)
            self.db = db
            self.OOBModel.clear()
            self.PopulateOOBTree(gen_OOB_dict(self.db),self.OOBModel.invisibleRootItem())
            self.OnView(None)
            self.GenUnitIcons()
            self.maplbl.repaint()
            self.update()
        
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

    # gameName = "demo"
    gameName = "germany83"
    #gameName = "nirgendwola"
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
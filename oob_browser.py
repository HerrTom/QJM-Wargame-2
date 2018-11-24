import os
import sys
import glob

from PyQt5 import QtCore, QtGui, QtWidgets
import ui.breeze_resources
from PIL.ImageQt import ImageQt

import qjm_data

def gen_OOB_dict(db):
    relations = []
    for formation in db.formations:
        parent = formation.hq
        id = formation.shortname
        relations.append((parent,id))
    
    parents, children = map(set, zip(*relations))
    OOB = {p: get_children(p, relations) for p in (parents - children)}
    
    return OOB


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
        im = im.convert("RGB")
        data = im.tobytes("raw","RGB")
        qim = QtGui.QImage(data, im.size[0], im.size[1], QtGui.QImage.Format_RGB888)
        # qim = ImageQt(im)
        return QtGui.QPixmap.fromImage(qim)

class MapLabel(QtWidgets.QLabel):
    RightClickSignal = QtCore.pyqtSignal([list])
    def __init__(self,*args,**kwargs):
        QtWidgets.QLabel.__init__(self,*args,**kwargs)
    
    def mousePressEvent(self, event):
        if event.button() == QtCore.Qt.RightButton:
            
            x = self.mapFromGlobal(QtGui.QCursor.pos()).x()
            y = self.mapFromGlobal(QtGui.QCursor.pos()).y()
            self.RightClickSignal.emit([x,y])
    
        
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
        self.Water.setChecked(True)
        
        # connect actions
        self.simulate.triggered.connect(self.OnSimulate)
        
        self.ag.triggered.connect(self.OnView)
        # self.Water.triggered.connect(self.OnView)
        # self.Roughness.triggered.connect(self.OnView)
        
        menubar = self.menuBar()
        menubar.addMenu(file)
        menubar.addMenu(view)
        
        
        layout = QtWidgets.QGridLayout()
        mainWidget.setLayout(layout)
        
        # mapImg= ImageQt(self.db.frontline.TerrainWater)
        self.map = MakePixmap(self.db.frontline.TerrainWater)
        # self.map = QtGui.QPixmap("./data/nirgendwola/maps/nirgendwola_water.bmp")
        
        mapview = QtWidgets.QScrollArea(self)
        mapview.setWidgetResizable(True)
        # mapview.setMinimumHeight(300)
        layout.addWidget(mapview,0,0,2,2)
        # self.maplbl = QtWidgets.QGraphicsView(mapview)
        self.maplbl = MapLabel(parent=mapview)
        self.maplbl.RightClickSignal.connect(self.onMapClick)
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
        
        self.unitLabel = StretchedLabel(" "*18,parent=self.maplbl)
        # self.unitLabel = QtWidgets.QLabel("X",parent=self.maplbl)
        self.unitLabel.setAlignment(QtCore.Qt.AlignBottom)
        
        self.wpLabel = StretchedLabel("X",parent=self.maplbl)
        self.wpLabel.setAlignment(QtCore.Qt.AlignRight)
        
        # OOB tree
        self.OOBTree = QtWidgets.QTreeView(self)
        self.OOBModel = QtGui.QStandardItemModel(self)
        self.OOBModel.setHorizontalHeaderLabels(["Order of Battle"])
        self.OOBTree.setModel(self.OOBModel)
        self.OOBTree.setUniformRowHeights(True)
        layout.addWidget(self.OOBTree,2,0,2,1)
        
        self.OOBTree.clicked.connect(self.get_formation_data)
        
        
        OOB = gen_OOB_dict(self.db)
        self.icons = get_icons("./data/_sidc/*.png")
        self.populate_OOBTree(OOB,self.OOBModel.invisibleRootItem())
        
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
        
        
        self.show()
        
    def get_formation_data(self,event):
        # find the formation
        name = self.OOBTree.currentIndex().data()
        form = self.db.getFormationByName(name)
        if form is not None:
            info, states = form.GetStatus()
            self.detailsBox.setText(info)
            self.populate_eqTable(states)
            x,y = form.xy
            
            self.unitLabel.setText(". {}".format(form.shortname))
            size = self.unitLabel.size()
            pos = self.maplbl.pos()
            self.unitLabel.move(x,y-size.height()+8) # 4 is offset for text
            if form.waypoint is not None:
                self.wpLabel.move(form.waypoint[0],form.waypoint[1])
            
    def populate_eqTable(self,states):
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
            
    
    def populate_OOBTree(self,children,parent):
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
            self.populate_OOBTree(children[child], child_item)
    
    def OnSimulate(self,event):
        self.db.Simulate()
        
    def OnView(self,event):
        if self.ag.checkedAction() is self.Water:
            self.maplbl.setPixmap(MakePixmap(self.db.frontline.TerrainWater))
        elif self.ag.checkedAction() is self.Territory:
            self.maplbl.setPixmap(MakePixmap(self.db.frontline.Territory))
        elif self.ag.checkedAction() is self.Cover:
            self.maplbl.setPixmap(MakePixmap(self.db.frontline.TerrainCover))
        else:
            self.maplbl.setPixmap(MakePixmap(self.db.frontline.TerrainType))
            
    def onMapClick(self,coords):
        name = self.OOBTree.currentIndex().data()
        form = self.db.getFormationByName(name)
        if form is not None:
            form.waypoint = coords
            print(form.shortname,coords)
            self.wpLabel.move(coords[0],coords[1])
        
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
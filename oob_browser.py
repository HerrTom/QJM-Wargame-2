import os
import sys
import glob

from PyQt5 import QtCore, QtGui, QtWidgets
import ui.breeze_resources

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
    

class MainGui(QtWidgets.QWidget):
    def __init__(self,parent=None,database=None):
        super().__init__(parent)
        
        self.db = database
        
        layout = QtWidgets.QGridLayout(self)
        
        # OOB tree
        self.OOBTree = QtWidgets.QTreeView(self)
        self.OOBModel = QtGui.QStandardItemModel(self)
        self.OOBModel.setHorizontalHeaderLabels(["Order of Battle"])
        self.OOBTree.setModel(self.OOBModel)
        self.OOBTree.setUniformRowHeights(True)
        layout.addWidget(self.OOBTree,0,0)
        
        self.OOBTree.clicked.connect(self.get_formation_data)
        
        OOB = gen_OOB_dict(self.db)
        self.icons = get_icons("./data/_sidc/*.png")
        self.populate_OOBTree(OOB,self.OOBModel.invisibleRootItem())
        
        # details box
        fixed_font = QtGui.QFont("monospace")
        fixed_font.setStyleHint(QtGui.QFont.Monospace)
        self.detailsBox = QtWidgets.QTextEdit(self)
        self.detailsBox.setFont(fixed_font)
        layout.addWidget(self.detailsBox,0,1)
        
        self.show()
        
    def get_formation_data(self,event):
        # find the formation
        name = self.OOBTree.currentIndex().data()
        form = self.db.getFormationByName(name)
        if form is not None:
            info = form.GetStatus()
            self.detailsBox.setText(info)
        
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

        
    # formationPath = "./data/germany83/formations/"
    formationPath = "./data/nirgendwola/formations/"
    db = qjm_data.database()
    db.loadFormations(formationPath)
    
    ex = MainGui(database=db)
    app.exec_()
    # sys.exit(app.exec_())


if __name__ == '__main__':
    abspath = os.path.abspath(__file__)
    dname = os.path.dirname(abspath)
    os.chdir(dname)
    
    
    
    main()
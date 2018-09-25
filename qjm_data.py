import glob
from collections import OrderedDict, Counter

import yaml
import pathvalidate as pv

import interps


global Di
Di = 5000

# for debug only
global missing
missing = []

weap_types = ["gun","atgm","aam","bomb"]
equipTypes  = ["Infantry","Antitank","Artillery","SP Antitank","SP Artillery",
            "APC","IFV","Tank","Air Defence","SP Air Defence","Aircraft","Helicopter"]


def represent_ordereddict(dumper, data):
    value = []

    for item_key, item_value in data.items():
        node_key = dumper.represent_data(item_key)
        node_value = dumper.represent_data(item_value)

        value.append((node_key, node_value))

    return yaml.nodes.MappingNode(u'tag:yaml.org,2002:map', value)
## handle ordered dicts nicely
yaml.add_representer(OrderedDict, represent_ordereddict)

def signed_sqrt(x):
    if x >= 0:
        return x**0.5
    else:
        return -(-x) ** 0.5


class weapon():
    def __init__(self,data=None):
    
        self.TLI = 0
        
        if data is None:
            self.name       =  None
            self.type       =  None
            self.range      =  None
            self.ROF        =  None
            self.calibre    =  None
            self.muzzleVel  =  None
            self.accuracy   =  None
            self.barrels    =  None
            self.crew       =  None
            self.guidance   =  None
            self.atgmPen    =  None
            self.atgmEn     =  None
            
        else:
            self.name       = data['name']
            self.type       = data['type']
            self.range      = data['range']
            self.ROF        = data['rateOfFire']
            self.calibre    = data['calibre']
            self.muzzleVel  = data['muzzleVel']
            self.accuracy   = data['accuracy']
            self.barrels    = data['barrels']
            self.crew       = data['crew']
            self.guidance   = data['guidance']
            self.atgmPen    = data['atgmPenetration']
            self.atgmMinRng = data['atgmMinRange']
            self.atgmEn     = data['atgmEnhancement']
  
    def CalculateTLI(self):
        # generic TLI calculation that has special handling of types
        
        # RF rate of fire factor
        if self.ROF is None or self.ROF == "" or self.ROF == "None":
            RF = interps.RF_From_Calibre(self.calibre)
        else:
            RF = float(self.ROF)
        
        if self.crew:
            RF = RF * 2
        self.RF = RF
        # PTS potential targets per strike
        PTS = interps.PTS_From_Calibre(self.calibre)
        # RIE relative incapacitation effect (usually 1)
        RIE = interps.RIE_From_Calibre(self.calibre)
        # RN range factor
        RN_Range        = 1 + (0.001 * float(self.range))**0.5
        RN_MuzzleVel    = 0.007 * float(self.muzzleVel) * 0.1 * (float(self.calibre) **0.5)
        if RN_MuzzleVel > RN_Range:
            RN = RN_MuzzleVel
        else:
            RN = (RN_Range + RN_MuzzleVel)
        # A accuracy
        A = float(self.accuracy)
        # RL reliability - ignoring for now
        RL = 1
        
        # SME, MCE, and AE are ignored for now
        SME = 1
        MCE = 1
        AE  = 1
        
        # MBE multiple barrel effect
        MBE = interps.MBE(self.barrels)
        
        # ATGM effects - Guidance, Velocity, Min Range, Penetration, Enhancement
        GE = 1
        VEL = 1
        MRN = 1
        PEN = 1
        EN = 1
        
        # special handling for ATGMS:
        if self.type == "ATGM":
            A = interps.GuidanceAccuracy(self.guidance)
            GE = 2
            VEL = 1 + 0.001 * (float(self.muzzleVel) - 400)
            MRN = 1 - 0.190 * ((float(self.atgmMinRng) - 100) /100)
            PEN = 1 + 0.010 * signed_sqrt(float(self.atgmPen) - 500)
            EN = float(self.atgmEn)
            self.RF = RF / 2 # to increase impact of ATGM
        
        self.TLI = RF * PTS * RIE * RN * A * RL * \
                    SME * MCE * AE * MBE * MRN * PEN * VEL * EN * GE
        
class equipment():
    def __init__(self,data=None):
    
        self.OLI            = 0
        self.weapObj        = None
        
        if data is None:
            self.name           = ""
            self.nation         = ""
            self.type           = ""
            self.weapons        = []
            self.roadSpeed      = ""
            self.horsepower     = ""
            self.groundPress    = ""
            self.radiusOfAction = ""
            self.weight         = ""
            self.length         = ""
            self.height         = ""
            self.armour         = ""
            self.enclosed       = False
            self.traverse       = False
            self.lowLight       = None
            self.rangefinder    = None
            self.fcCant         = False
            self.fcAmmo         = False
            self.fcWind         = False
            self.fcBarrel       = False
            self.stab           = False
            self.amphibious     = False
            self.crew           = 0
              
        else:
            self.name           = data['name']
            self.nation         = data['nation']
            self.type           = data['type']
            self.weapons        = data['weapons']
            self.roadSpeed      = data['roadSpeed']
            self.horsepower     = data['horsepower']
            self.groundPress    = data['groundPress']
            self.radiusOfAction = data['radiusOfAction']
            self.weight         = data['weight']
            self.length         = data['length']
            self.height         = data['height']
            self.armour         = data['armour']
            self.enclosed       = data['enclosed']
            self.traverse       = data['traverse']
            self.lowLight       = data['lowLight']
            self.rangefinder    = data['rangefinder']
            self.fcCant         = data['fcCant']
            self.fcAmmo         = data['fcAmmo']
            self.fcWind         = data['fcWind']
            self.fcBarrel       = data['fcBarrel']
            self.stab           = data['stabilised']
            self.amphibious     = data['amphibious']
            self.crew           = data['crew']
            
    
    def AddWeapons(self,weapList):
        # adds weapon objects to the unit
        self.weapObj = weapList
    
    def CalculateOLI(self):
        
        WEAP = 0
        for wp in self.weapObj:
            ammoRatio = float(self.weapons[wp.name]) / float(wp.RF)
            ASE = interps.AmmoSupplyEffect(ammoRatio)
            WEAP += wp.TLI * ASE
            # print(wp.name,wp.TLI/Di,ASE)
            
        if self.type in ["Infantry","Antitank","Artillery","Air Defence"]:
            self.OLI = WEAP / Di
            return
        
        # Aircraft aren't handled...
        
        # PF punishment factor
        ARMF = interps.ARMF(self.armour)
        PF = 1.2 * ARMF * float(self.weight) / (2 * float(self.length) * float(self.height))
        
        # FCF is combined fire control factor
        if self.fcCant:
            FCCFCant = 1.05
        else:
            FCCFCant = 1.00
            
        if self.fcAmmo:
            FCCFAmmo = 1.05
        else:
            FCCFAmmo = 1.00
        
        if self.fcWind:
            FCCFCrosswind = 1.05
        else:
            FCCFCrosswind = 1.00
        
        if self.fcAmmo:
            FCCFAmmo = 1.05
        else:
            FCCFAmmo = 1.00
            
        if self.fcBarrel:
            FCCFBarrel = 1.05
        else:
            FCCFBarrel = 1.00
        
        if self.enclosed:
            VisF = 0.90
        else:
            VisF = 1.00
         
        LLCF = interps.LLCF(self.lowLight)
        
        if self.traverse:
            TravF = 1.10
        else:
            TravF = 1.00
            
        if self.stab:
            SGF = 1.10
        else:
            SGF = 1.00
            
        RgFF = interps.RgFF(self.rangefinder)
        
        FCF = (FCCFCant * FCCFAmmo * FCCFCrosswind * FCCFBarrel * VisF * LLCF * TravF * SGF * RgFF)**0.5
        
        if self.amphibious:
            AME = 1.10
        else:
            AME = 1.00
            
        VMF = 0.04 * (float(self.horsepower)/float(self.weight) * float(self.roadSpeed)/float(self.groundPress))**0.5
        
        RA = 0.08 * (float(self.radiusOfAction))**0.5
        
        self.OLI = (WEAP / Di) * FCF * AME * VMF * RA * PF
        
        # note that if OLI is smaller than the weapons individually, I modified it to be weapons * (1+total factor)
        if self.OLI < (WEAP / Di):
            self.OLI = (WEAP / Di) * (1+ FCF * AME * VMF * RA * PF)
        
class database():
    def __init__(self):
        self.loadWeaps()
        self.loadEquip()
        self.loadFormations()
        
    def loadWeaps(self):
        self.weaps = []
        files = glob.glob("./data/weapons/*.yml")
        print(files)
        for fid in files:
            with open(fid) as f:
                data = yaml.load(f)
            self.weaps.append(weapon(data=data))
            self.weaps[-1].CalculateTLI()
    
    def loadEquip(self):
        self.equip = []
        files = glob.glob("./data/equipment/*.yml")
        print(files)
        for fid in files:
            with open(fid) as f:
                data = yaml.load(f)
            self.equip.append(equipment(data=data))
            # gather all the weapons this equipment should use
            weapList = []
            if self.equip[-1].weapons is not None:
                for weap in self.equip[-1].weapons.keys():
                    weapIdx = self.getWeapNames().index(weap)
                    weapList.append(self.weaps[weapIdx])
            self.equip[-1].AddWeapons(weapList)
            self.equip[-1].CalculateOLI()
        
    def getEquipment(self,index):
        return self.equip[index]
        
    def getEquipmentByName(self,name):
        for eq in self.equip:
            if eq.name == name:
                return eq
        # If the loop runs out, this equipment is not in the list
        if name not in missing:
            missing.append(name)
        return None
        
    def getWeapon(self,index):
        return self.weaps[index]
        
    def saveEquipment(self,data):
        filename = "./data/equipment/{}.yml".format(pv.sanitize_filename(data["name"]))
        # sanitize the data such that '' turns into None and 'None' turns into None
        for key, value in data.items():
            if value == "" or value == "None":
                data[key] = None
        with open(filename, "w+") as f:
            f.write(yaml.dump(data, default_flow_style=False))
    
    def saveWeapon(self,data):
        filename = "./data/weapons/{}.yml".format(pv.sanitize_filename(data["name"]))
        with open(filename, "w+") as f:
            f.write(yaml.dump(data, default_flow_style=False))
    
    def getWeapNames(self):
        names = []
        for n in self.weaps:
            names.append(n.name)
        return names
    
    def getEquipNames(self,types=None,nations=None):
        names = []
        for n in self.equip:
            if types is None:
                typePass = True
            elif n.type in types:
                typePass = True
            else:
                typePass = False
                
            if nations is None:
                nationPass = True
            elif n.nation in nations:
                nationPass = True
            else:
                nationPass = False

            if typePass and nationPass:
                names.append(n.name)
            
        return names
        
    def getAllTypes(self):
        equipTypes = set()
        for n in self.equip:
            equipTypes.add(n.type)
        equipTypes = list(equipTypes)
        return equipTypes
        
    def getAllNations(self):
        equipNations = set()
        for n in self.equip:
            equipNations.add(n.nation)
        equipNations = list(equipNations)
        return equipNations
        
    def loadFormations(self):
        self.formations = []
        files = glob.glob("./data/formations/*.yml")
        print(files)
        for fid in files:
            with open(fid) as f:
                data = yaml.load(f)
            self.formations.append(formation(data=data))
            needs = self.formations[-1].GetEquipmentNeeds()
            for eq in needs:
                self.formations[-1].AddEquipment(self.getEquipmentByName(eq))
            self.formations[-1].GenStrength()
        
# Formations contain equipment objects
class formation():
    def __init__(self,data=None):
        self.Strength = None
        self.name = ""
        self.equipment = []
        self.data = data
        if data is not None:
            self.name = data["name"]
        
    def GetEquipmentNeeds(self):
        needs = []
        for key, val in self.data["equipment"].items():
            for n in range(val):
                needs.append(key)
        return needs
        
    def AddEquipment(self,equipment):
        # adds equipment in a list to the formation
        self.equipment.append(equipment)
        
    def GenStrength(self):
        self.Strength = OrderedDict({"Infantry": 0, "AFV": 0, "Antitank": 0, "Artillery": 0,
                                "Air Defence": 0, "Aircraft": 0})
        # strength values are in the followin categories:
        # infantry, afv, antitank, arty, air defence and air
        for eq in self.equipment:
            if eq is not None:
                # check the type of equipment
                if eq.type in ["Infantry","APC"]:
                    self.Strength["Infantry"] += eq.OLI
                elif eq.type in ["IFV","Tank"]:
                    self.Strength["AFV"] += eq.OLI
                elif eq.type in ["Antitank","SP Antitank"]:
                    self.Strength["Antitank"] += eq.OLI
                elif eq.type in ["Artillery","SP Artillery"]:
                    self.Strength["Artillery"] += eq.OLI
                elif eq.type in ["Air Defence","SP Air Defence"]:
                    self.Strength["Air Defence"] += eq.OLI
                elif eq.type in ["Helicopter","Aircraft"]:
                    self.Strength["Aircraft"] += eq.OLI
        
    def PrintStrength(self):
        total = 0
        print("*"*50)
        print("**** FORMATION: {:^30s}****".format(self.name))
        for key, val in self.Strength.items():
            print("{:>15s} strength: {:10,.0f}".format(key,val))
            total += val
        print("{:*>15s} strength: {:10,.0f}**************".format("Total",total))
        print("*"*50)
        
        
if __name__ == '__main__':
    import os
    abspath = os.path.abspath(__file__)
    dname = os.path.dirname(abspath)
    os.chdir(dname)
    
    db = database()
    for form in db.formations:
        form.PrintStrength()
    
    print(missing)
    
    
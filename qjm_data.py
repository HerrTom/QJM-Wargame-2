import glob
from collections import OrderedDict, Counter

from copy import copy

import yaml
import pathvalidate as pv
from PIL import Image
from tqdm import tqdm

import interps


global Di
Di = 5000

# for debug only
global missing
missing = []

weap_types = ["gun","atgm","aam","bomb"]
equipTypes  = ["Infantry","Antitank","Artillery","SP Antitank","SP Artillery",
            "APC","IFV","Tank","Air Defence","SP Air Defence","Aircraft","Helicopter"]

REDFOR = ["USSR","DDR","POL","CZE"]
BLUFOR = ["USA","BRD","NL","BEL","UK","DAN"]
            

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
        
def make_unit(vec):
    # turns an (x,y) vector into a unit vector
    magnitude = (vec[0]**2 + vec[1]**2)**.5
    return [vec[0]/magnitude, vec[1]/magnitude]
    
def multiply_dict(A,B):
    # multiplies keys in dict A by equivalent keys in BEL
    for key, val in A.items():
        A[key] == val * B[key]
        
    return A
    
def linspace(val,num):
    # generates a linearly spaced vector from 0 to val
    vec = []
    for i in range(num):
        vec.append(i*val/num)
    return vec


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
            
    def loadFrontline(self):
        # load in a map
        with open("./data/maps/germany83.yml") as f:
            mapdata = yaml.load(f)
        self.frontline = Frontline(mapdata)
        
# Formations contain equipment objects
class formation():
    def __init__(self,data=None):
        self.Strength = None
        self.name = ""
        self.equipment = []
        self.nation = ""
        self.waypoint = None
        self.personnel = 0
        self.stance = ""
        
        self.data = data
        self.NumPoints = 0 # this factor determines how many battles this unit is involved in
        if data is not None:
            self.name   = data["name"]
            self.nation = data["nation"]
            self.waypoint = data["waypoints"]
            self.personnel = data["personnel"]
            self.stance = data["stance"]
            
            self.xy     = data["location"]
            self.x      = self.xy[0]
            self.y      = self.xy[1]
            
            
    def __repr__(self):
        return "formation({})".format(self.name)
        
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
        self.Strength = {"Infantry": 0, "AFV": 0, "Antitank": 0, "Artillery": 0,
                                "Air Defence": 0, "Aircraft": 0}
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
    
    def GetVehicles(self):
        # returns the number of vehicles in this unit
        vehicles = 0
        for eq in self.equipment:
            if eq is not None:
                if eq.type not in ["Infantry","Antitank","Artillery","Air Defence"]:
                    vehicles += 1
        return vehicles
    
    def PrintStrength(self):
        total = 0
        print("*"*50)
        print("**** FORMATION: {:^30s}****".format(self.name))
        for key, val in self.Strength.items():
            print("{:>15s} strength: {:10,.0f}".format(key,val))
            total += val
        print("{:*>15s} strength: {:10,.0f}**************".format("Total",total))
        print("*"*50)
        
        
class Frontline():
    blue    = (0,30,255)
    red     = (255,0,0)
    
    def __init__(self,mapdata):
        self.name           = mapdata["mapName"]
        self.desc           = mapdata["mapDesc"]
        self.scale          = mapdata["mapPixelsPerKM"]
        self.TerrainCover   = Image.open("./data/maps/{}".format(mapdata["mapTerrainCover"]))
        self.TerrainType    = Image.open("./data/maps/{}".format(mapdata["mapTerrainType"]))
        self.Territory      = Image.open("./data/maps/{}".format(mapdata["mapTerritory"]))
        
        self.weather        = mapdata["weather"]
        self.season         = mapdata["season"]
        
        self.FrontlinePoints = []
        self.FrontlineCoords = []
        
        self.FindFL()
        
        
    def FindFL(self):
        # march through image from L to R, and drop a FrontlinePoint on each type
        size = self.Territory.size
        px = self.Territory.load()
        pxType = self.TerrainType.load()
        pxCover = self.TerrainCover.load()
        
        # check horizontally
        print("Horizontal Frontline check")
        x = 0
        for y in tqdm(range(size[1])):
            # set initial pixel colour
            colour = px[x,y]
            for x in range(size[0]):
                newcolour = px[x,y]
                if colour != newcolour and not self.InFrontlineList(x,y) and (255,255,255) not in [newcolour, colour]:
                    self.FrontlinePoints.append(FrontlinePoint(self,(x,y),pxCover[x,y],pxType[x,y]))
                colour = newcolour
        # repeat the check vertically
        print("Vertical Frontline check")
        y = 0
        for x in tqdm(range(size[0])):
            # set initial pixel colour
            colour = px[x,y]
            for y in range(size[1]):
                newcolour = px[x,y]
                if colour != newcolour and not self.InFrontlineList(x,y) and (255,255,255) not in [newcolour, colour]:
                    self.FrontlinePoints.append(FrontlinePoint(self,(x,y),pxCover[x,y],pxType[x,y]))
                colour = newcolour
                        
    def InFrontlineList(self,x,y):
        if self.FrontlineCoords == []:
            # generate the frontline coords
            for pt in self.FrontlinePoints:
                self.FrontlineCoords.append(pt.xy)
        xy = (x,y)
        if xy in self.FrontlineCoords:
            return True
        else:
            return False
        
    def DrawFrontline(self):
        tempterr = copy(self.Territory)
        px = tempterr.load()
        for pt in self.FrontlinePoints:
            px[pt.x,pt.y] = (0,0,0)
        tempterr.show()
        
    def AssociateUnits(self,units):
        # runs through each frontline point and attaches units to it
        unitrange = 60 # units can affect the frontline from within this many km
        maxrad = unitrange / self.scale * 2
        
        # first determine how many points are in range
        print("Associating Formations with the Frontline")
        for unit in tqdm(units):
            unit.NumPoints = 0 # this value determines how many battles the unit is in
            points = 0
            for pt in self.FrontlinePoints:
                dist = ((pt.x-unit.x)**2 + (pt.y-unit.y)**2)**0.5
                if dist < maxrad:
                    if dist < maxrad/2:
                        influence = 1
                    else:
                        influence = 2 - dist/(maxrad/2)
                    pt.AddUnit(unit,influence)
                    unit.NumPoints+=1
                    
    def RunCombat(self):
        for pt in self.FrontlinePoints:
            pt.Combat()
                    
    def Advance(self):
        px = self.Territory.load()
        # iterates through all the frontline points and advances them per their property
        for pt in self.FrontlinePoints:
            idx = 0
            for attacker in pt.attackers:
                wp  = attacker.waypoint
                dir = make_unit([wp[0] - pt.x, wp[1]-pt.y])
                n = 100 # number of samples to take
                advance = pt.advance[idx]
                
                # draw pixels for advances
                for i in linspace(advance,n):
                    x = round(pt.x + dir[0] * i,0)
                    y = round(pt.y + dir[1] * i,0)
                    px[x,y] = (0,255,0)
                    
        self.Territory.show()
                   
        
class FrontlinePoint():
    def __init__(self,parent,xy,terrcover,terrtype):
        self.x = xy[0]
        self.y = xy[1]
        self.xy = xy
        self.units = []
        self.unitinfl = [] # vector with influence of unit applied to point (reduces advance rate for far points)
        self.advance = [] # advance rate
        
        self.terrainCover = terrcover
        self.terrainType = terrtype
        
        self.parent = parent
        
        self.attackers = []
        
        
    def AddUnit(self,unit,influence):
        # print("Adding {}".format(unit.name))
        self.units.append(unit)
        self.unitinfl.append(influence)
        
    def Combat(self):
		# need to determine the attacker and defender.
		#	if both are attacking - side with fewer personnel is defending
        self.attackers = []
        self.defenders = []
        attackersRED = 0
        attackersBLU = 0
        for unit in self.units:
            if unit.stance == "attacking":
                self.attackers.append(unit)
                if unit.nation in REDFOR:
                    # print(unit.name, unit.stance)
                    attackersRED += unit.personnel
                else:
                    attackersBLU += unit.personnel
            else:
                self.defenders.append(unit)
        # determine which side is attacking
        # quit here if there are no self.attackers
        if self.attackers == []:
            return
        # print(self.attackers)
        self.attackers = []
        self.defenders = []
        # combat strengths are a Counter dict, so we can just update them with the units
        attackerStr = Counter({"Infantry": 0, "AFV": 0, "Antitank": 0, "Artillery": 0,
                                "Air Defence": 0, "Aircraft": 0})
        defenderStr = Counter({"Infantry": 0, "AFV": 0, "Antitank": 0, "Artillery": 0,
                                "Air Defence": 0, "Aircraft": 0})
        
        if attackersRED > attackersBLU:
            # redo the attacker list without BLUFOR
            for unit in self.units:
                if unit.stance == "attacking" and unit.nation in REDFOR:
                    self.attackers.append(unit)
                    # print(attackerStr)
                elif unit.nation in BLUFOR:
                    self.defenders.append(unit)
        else:
            # redo the attacker list without REDFOR
            for unit in self.units:
                if unit.stance == "attacking" and unit.nation in BLUFOR:
                    self.attackers.append(unit)
                elif unit.nation in REDFOR:
                    self.defenders.append(unit)
        # splitting out the strength calculation so we only have to code it once (I know it's inefficient -Tom)
        for unit in self.attackers:
            attackerStr += unit.Strength
        # stance precendence means all units will use the first in the list
        stancePrecedence = ["fortified","prepared","delay","hasty","attacking"]
        defenderStance = stancePrecedence[-1]
        for unit in self.defenders:
            defenderStr += unit.Strength
            if stancePrecedence.index(unit.stance) < stancePrecedence.index(defenderStance):
                defenderStance = unit.stance

        if self.units != []:
            # This finds the advance rate and sets the casualty rates
            
            # Units apply full combat power at every point in influence
            #   Not ideal solution, but NumPoints will divide casualties
            
            # N is the number of personnel, J is the number of vehicles
            #       involved in this combat
            N_attacker = sum([j.personnel for j in self.attackers])
            J_attacker = sum([j.GetVehicles() for j in self.attackers])
            N_defender = sum([j.personnel for j in self.defenders])
            J_defender = sum([j.GetVehicles() for j in self.defenders])
            
            # HANDLE TERRAIN ###############################
            # types of terrain are:
            # ["rugged, heavily wooded","rugged, mixed","rugged, bare",
            # "rolling, heavily wooded","rolling, mixed","rolling, bare",
            # "flat, heavily wooded","flat, mixed","flat, bare, hard",
            # "flat, desert","desert, sandy dunes","swamp, jungled",
            # "swamp, mixed or open", "urban"]
            roughDict = {(216,0,255): "urban", (208,192,82): "rolling",
                        (208,144,82): "rugged", (255,255,255): "flat",}
            coverDict = {(26,113,0): "heavily wooded",
                        (229,247,107): "mixed", (255,255,255): "bare",}
            
            if roughDict[self.terrainType] == "urban":
                terrain = "urban"
            else:
                terrain = roughDict[self.terrainType] + ", " + coverDict[self.terrainCover]
          
            
            for unit in self.attackers:
                if self.defenders == []:
                    # no defenders, maximum advance rate
                    self.advance.append(100)
                else:
                    self.advance.append(40)
        
        

        
if __name__ == '__main__':
    import os
    abspath = os.path.abspath(__file__)
    dname = os.path.dirname(abspath)
    os.chdir(dname)
    
    db = database()
    for form in db.formations:
        form.PrintStrength()
    
    db.loadFrontline()
    
    # db.frontline.DrawFrontline()
    
    # associate the units to the frontline
    db.frontline.AssociateUnits(db.formations)
    db.frontline.RunCombat()
    db.frontline.Advance()
        
    print("MISSING OBJECTS:", missing)
    
    
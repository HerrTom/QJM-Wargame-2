import os
import glob
import pprint
from collections import OrderedDict, Counter
from statistics import mean
from random import random
from copy import copy

import numpy as np
import yaml
import pathvalidate as pv
from PIL import Image
from tqdm import tqdm

import interps
import supply_network

global Di
Di = 5000

global simTime
simDuration = 1 # days
simSteps    = 6
simTime = simDuration / simSteps

# for debug only
global missing
missing = []

weap_types = ["gun","atgm","aam","bomb"]
equipTypes  = ["Infantry","Antitank","Artillery","SP Antitank","SP Artillery",
            "APC","IFV","Tank","Air Defence","SP Air Defence","Aircraft","Helicopter"]

# REDFOR = ["USSR","DDR","POL","CZE"]
# BLUFOR = ["USA","BRD","NL","BEL","UK","DAN"]
global REDFOR
global BLUFOR

REDFOR = []
BLUFOR = []

global FLAG_RUN_SUPPLY
FLAG_RUN_SUPPLY = False

global SUPPLY_RATE
SUPPLY_RATE = 1 / 5 # default is 5 days of supply per unit

RED = (255,0,0)
BLU = (6,0,255)

roughDict = {(172,35,167): "urban", (254,230,154): "rolling",
            (186,134,43): "rugged", (255,255,255): "flat",}
coverDict = {(46,104,8): "heavily wooded",
            (215,236,130): "mixed", (255,255,255): "bare",}
waterColour = (37,98,129)
riverColour = (210,238,252)
waterDict = {riverColour: "river", waterColour: "water",
            (255,255,255): "land"}


def print_losses(losses,cols = 3, quiet=False):
    idx = 0
    lossStr = ""
    for key, val in losses.items():
        lossStr += "{:4,.0f} {:<20}".format(val,key)
        idx += 1
        if idx == cols:
            idx = 0
            lossStr += "\n"
    if quiet:
        return lossStr
    else:
        print(lossStr)
            
def represent_ordereddict(dumper, data):
    value = []

    for item_key, item_value in data.items():
        node_key = dumper.represent_data(item_key)
        node_value = dumper.represent_data(item_value)

        value.append((node_key, node_value))

    return yaml.nodes.MappingNode(u'tag:yaml.org,2002:map', value)
## handle ordered dicts nicely
yaml.add_representer(OrderedDict, represent_ordereddict)

def normalize_matrix(x):
    if x.max() != 0:
        return x / x.max() * 255
    else:
        return x*255
        
def signed_sqrt(x):
    if x >= 0:
        return x**0.5
    else:
        return -(-x) ** 0.5
        
def make_unit(vec):
    # turns an (x,y) vector into a unit vector
    magnitude = (vec[0]**2 + vec[1]**2)**.5
    if magnitude == 0:
        return [0,0]
    else:
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

def overmatch(oli,limit_oli,cap=100):
    # does the 1/2 factor overmatching
    if oli > limit_oli:
        overmatch_oli = oli - limit_oli
        new_oli = limit_oli + overmatch_oli/2
        if new_oli > cap*limit_oli:
            new_oli = cap*limit_oli
    else:
        new_oli = oli
    return new_oli
    
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
        self.state          = "Intact"
        
        if data is None:
            self.name           = ""
            self.nation         = ""
            self.type           = ""
            self.weapons        = {}
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
            # aircraft special effects
            self.ceiling        = 0
              
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
            # optional aircraft data
            try:
                self.ceiling    = data['ceiling']
            except:
                self.ceiling    = 0
            
    
    def AddWeapons(self,weapList):
        # adds weapon objects to the unit
        self.weapObj = weapList
    
    def Kill(self):
        # equipment has an x percent chance of being destroyed
        saveChance = 0.5
        roll = random()
        
        if roll > saveChance:
            self.state = "Destroyed"
        else:
            self.state = "Damaged"
    
    def CalculateOLI(self):
        
        WEAP = 0
        for wp in self.weapObj:
            ammoRatio = float(self.weapons[wp.name]) / float(wp.RF)
            if self.type in ["Infantry","Antitank","Artillery"]:
                ASE = 1 # ASE does not apply to foot-mobile equipment
            elif self.type in ["Aircraft","Helicopter"]:
                ASE = 0.25
            else:
                ASE = interps.AmmoSupplyEffect(ammoRatio)
            WEAP += wp.TLI * ASE
            # print(self.name,wp.name,wp.TLI/Di,ASE)
            
        if self.type in ["Infantry","Antitank","Artillery","Air Defence"]:
            self.OLI = WEAP / Di
            return
        
        # Aircraft aren't handled...
        
        # PF punishment factor
        ARMF = interps.ARMF(self.armour)
        if self.type in ["Aircraft", "Helicopter"]:
            PF = float(self.weight) / 8 * (2* float(self.weight))**0.5
        elif self.type in ["APC"]:
            # APCs get a bonus to their PF
            PF = ARMF * float(self.weight) / 16 * (float(self.weight) * 2)**.5
        else:
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
        
        if self.type in ["Aircraft", "Helicopter"]:
            s = int(self.roadSpeed)
            if s <= 500:
                A = s
                B = 0
                C = 0
            elif s <= 1500:
                A = 500
                B = s-500
                C = 0
            else:
                A = 500
                B = 1500
                C = s-1500
            VMF = 0.15 * (A + 0.1*B + 0.01*C)**0.5
        else:
            VMF = 0.04 * (float(self.horsepower)/float(self.weight) * float(self.roadSpeed)/float(self.groundPress))**0.5
        
        RA = 0.08 * (float(self.radiusOfAction))**0.5
        
        # aircraft values
        if self.type == "Helicopter":
            CL = 0.6
        elif self.type == "Aircraft":
            if self.ceiling >= 9000:
                CL = 1 + 0.02 * (self.ceiling-9000)/300
            else:
                CL = 1 - 0.005 * (self.ceiling-9000)/300
        else:
            CL = 1
        
        self.OLI = (WEAP / Di) * FCF * AME * VMF * RA * PF * CL
        
        # note that if OLI is smaller than the weapons individually, I modified it to be weapons * (1+total factor)
        if self.OLI < (WEAP / Di):
            self.OLI = (WEAP / Di) * (1+ FCF * AME * VMF * RA * PF * CL)
        
class database():
    def __init__(self):
        self.loadWeaps()
        self.loadEquip()
        
    def Simulate(self):
        
        # dev stuff to visiualize front
        # im = copy(db.frontline.TerrainWater)
        # db.frontline.DrawFrontline(im,(100,100,100))
        
        # associate the units to the frontline
        # db.frontline.AssociateUnits(db.formations)
        # run combat for 6 turns
        print("Running combat...")
        for x in tqdm(range(simSteps)):
            self.frontline.FindFL()
            self.TurnAdmin()
            self.frontline.AssociateUnits()
            self.frontline.RunCombat()
            self.frontline.Advance()
            self.MoveIdleUnits()
            
            self.frontline.GetSupplySources()
            self.frontline.GetSupplyStatus()
            
            # db.frontline.DrawFrontline(im,(190,190,190))
            
        # db.frontline.Territory.show()
        
        # for form in db.formations:
            # form.PrintStrength()
        
        # show units on the map
        # db.frontline.DrawFrontline(im,(0,0,0))
        # db.frontline.DrawUnits(im)
        # im.show()
        
    def loadWeaps(self):
        self.weaps = []
        files = glob.glob("./data/weapons/*.yml")
        for fid in files:
            with open(fid) as f:
                data = yaml.load(f)
            self.weaps.append(weapon(data=data))
            self.weaps[-1].CalculateTLI()
    
    def loadEquip(self):
        self.equip = []
        files = glob.glob("./data/equipment/*.yml")
        # print(files)
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
        
    def loadFormations(self,path="./data/formations/"):
        self.formations = []
        files = glob.glob("{}*.yml".format(path))
        # print(files)
        for fid in files:
            with open(fid) as f:
                data = yaml.load(f)
            self.formations.append(formation(data=data))
            needs = self.formations[-1].GetEquipmentNeeds()
            for eq in needs:
                self.formations[-1].AddEquipment(self.getEquipmentByName(eq))
            self.formations[-1].GenStrength()
        print("MISSING OBJECTS:", missing)
    
    def getFormationByShortName(self,name):
        for f in self.formations:
            if f.shortname == name:
                return f
        # If the loop runs out, this equipment is not in the list
        return None

    def getFormationByName(self,name):
        for f in self.formations:
            if f.name == name:
                return f
        # If the loop runs out, this equipment is not in the list
        return None
    
    def dumpFormations(self):
        # this function will dump formation data back out as YAML
        for f in self.formations:
            filename = "./convert/yaml_in/{}.yml".format(pv.sanitize_filename(f.name))
            f.WriteYaml(filename)

    
    def loadFrontline(self,path):
        # load in a map
        dir, file = os.path.split(path)
        with open(path) as f:
            mapdata = yaml.load(f)
        self.frontline = Frontline(self,mapdata,dir)
        
    def MoveIdleUnits(self):
        # moves all units that don't see combat
        for unit in self.formations:
            if unit.NumPoints == 0 and unit.waypoint is not None:
                unit.Move(60 * simTime)
                
    def TurnAdmin(self):
        # runs the admin part of turn resolution - destroy encircled units, change stances, check supply
        entrench_chance = 0.3
        entrench_odds = 1-(1 - entrench_chance)**simTime
        
        # run through each formation and check if it has a waypoint. If yes, set stance to attakcing
        for form in self.formations:
            # make a roll to see if this formation can raise its entrenchment level
            entrench_roll = random()
            if entrench_roll <= entrench_odds:
                entrench = True
            else:
                entrench = False
            if form.waypoint is not None:
                form.stance = "attacking"
            elif form.waypoint is None and form.stance == "attacking": # if this unit was attacking but no longer
                form.stance = "delay"
            elif form.waypoint is None and form.stance == "delay" and entrench:
                form.stance = "hasty"
            elif form.waypoint is None and form.stance == "hasty" and entrench:
                form.stance = "prepared"
            elif form.waypoint is None and form.stance == "prepared" and entrench:
                form.stance = "fortified"
            
            curr = self.frontline.GetOwner(form.x,form.y)
            # check if units are on unfriendly territory and correct
            maxRad = form.personnel / 200
            form.NumPoints = 1 # for this purpose, casualties need to occur at once
            if form.nation in REDFOR:
                if curr == "BLU":
                    xy, dist = self.frontline.NearestFriendly(form.x,form.y,RED,maxRad)
                    tqdm.write("RED on BLU! Range: {}".format(dist))
                    form.x = xy[0] 
                    form.y = xy[1]
                    form.xy = xy
                    # inflict casualties at rate given by distance
                    form.Casualties(dist,dist)
            else:
                if curr == "RED":
                    xy, dist = self.frontline.NearestFriendly(form.x,form.y,BLU,maxRad)
                    tqdm.write("BLU on RED! Range: {}".format(dist))
                    form.x = xy[0] 
                    form.y = xy[1]
                    form.xy = xy
                    # inflict casualties at rate given by distance
                    form.Casualties(dist,dist)
        
                
    def TotalCasualties(self):
        casualties = Counter()
        for unit in self.formations:
            casualties += unit.casualties
        print("Total casualties this turn: {:5,.0f} KIA, {:5,.0f} WIA".format(casualties["Killed"],casualties["Wounded"]))
    
    def LossesBySide(self):
        sides = [BLUFOR, REDFOR]
        lossStr = ""
        for factions in sides:
            losses = Counter()
            casualties = Counter()
            for unit in self.formations:
                if unit.nation in factions:
                    casualties += unit.casualties
                    losses += unit.losses
            lossStr += "\n## Total losses for {} ##\n".format(factions)
            lossStr += "Casualties: {:5,.0f} KIA, {:5,.0f} WIA\n".format(casualties["Killed"],casualties["Wounded"])
            
            lossStr += print_losses(losses,quiet=True)
        return lossStr
        
    
# Formations contain equipment objects
class formation():
    def __init__(self,data=None):
        self.Strength = None
        self.name = ""
        self.shortname = ""
        self.equipment = []
        self.nation = ""
        self.type = ""
        self.waypoint = None
        self.personnel = 0
        self.proficiency = 0
        self.stance = ""
        self.hq = None
        self.SIDC = "SFGPU-------"
        
        self.supply = 1 # default is fully supplied
        
        self.losses = Counter()
        self.casualties = Counter({"Killed": 0, "Wounded": 0})
        
        self.data = data
        self.NumPoints = 0 # this factor determines how many battles this unit is involved in
        
        self.advance = []
        
        if data is not None:
            self.name   = data["name"]
            self.shortname   = data["shortname"]
            self.nation = data["nation"]
            self.type   = data["type"]
            self.waypoint = data["waypoints"]
            self.personnel = data["personnel"]
            self.proficiency = data["proficiency"]
            self.hq         = data["hq"]
            self.SIDC       = data["SIDC"]
            self.stance = data["stance"]
            
            self.xy     = [int(data["location"][0]), int(data["location"][1])]
            self.x      = self.xy[0]
            self.y      = self.xy[1]
            
            
    def __repr__(self):
        return "formation({})".format(self.name)
    
    def WriteYaml(self,file):
        self.data["location"] = self.xy
        self.data["personnel"] = self.personnel
        eqDict = Counter()
        for eq in self.equipment:
            if eq is not None:
                if eq.state == "Intact":
                    eqDict.update({eq.name: 1})
        self.data["equipment"] = dict(eqDict)
        
        with open(file,'w+') as f:
            d = yaml.dump(self.data,default_flow_style=False)
            f.write(d)
    
    def GetEquipmentNeeds(self):
        needs = []
        for key, val in self.data["equipment"].items():
            for n in range(val):
                needs.append(key)
        return needs
        
    def AddEquipment(self,equipment):
        # adds equipment in a list to the formation
        self.equipment.append(copy(equipment)) # equipments need to be COPIES to work
        
    def GenStrength(self):
        # TODO remove infantry bonus for testing
        self.Strength = {"Infantry": 1, "AFV": 0, "Antitank": 0, "Artillery": 0,
                                "Air Defence": 0, "Aircraft": 0}
        # strength values are in the followin categories:
        # infantry, afv, antitank, arty, air defence and air
        for eq in self.equipment:
            if eq is not None:
                if eq.state == "Intact": # equipment must alive
                    # check the type of equipment
                    if eq.type in ["Infantry","APC"]:
                        self.Strength["Infantry"] += eq.OLI * self.proficiency
                    elif eq.type in ["IFV","Tank"]:
                        self.Strength["AFV"] += eq.OLI * self.proficiency
                    elif eq.type in ["Antitank","SP Antitank"]:
                        self.Strength["Antitank"] += eq.OLI * self.proficiency
                    elif eq.type in ["Artillery","SP Artillery"]:
                        self.Strength["Artillery"] += eq.OLI * self.proficiency
                    elif eq.type in ["Air Defence","SP Air Defence"]:
                        self.Strength["Air Defence"] += eq.OLI * self.proficiency
                    elif eq.type in ["Helicopter","Aircraft"]:
                        self.Strength["Aircraft"] += eq.OLI * self.proficiency
    
    def Casualties(self,rate_pers,rate_arm):
        # casualty rate should be applied on a per-unit basis instead of a per-frontline point basis?
        # casualty categories
        casualty_arm = ["Tank","IFV","APC"]
        casualty_support = ["Antitank","Artillery","Air Defence"]
        casualty_sp = ["SP Artillery","SP Air Defence"]
        
        
        # deal with multiple combat points
        rate_pers = 1-(1-rate_pers)**(1/self.NumPoints)
        rate_arm = 1-(1-rate_arm)**(1/self.NumPoints)
        tqdm.write("Armour rate: {}".format(rate_arm))
        
        # deal with simulation time
        rate_pers = 1-(1 - rate_pers)**simTime
        rate_arm = 1-(1 - rate_arm)**simTime
        
        for eq in self.equipment:
            if eq is not None:
                roll = random()
                if eq.type in casualty_arm:
                    cas = rate_arm
                elif eq.type in casualty_support:
                    cas = 0.1 * rate_pers
                elif eq.type in casualty_sp:
                    cas = 0.3 * rate_pers
                else: # is infantry casualty rate
                    cas = rate_pers
                
                if roll <= cas:
                    eq.Kill()
                    # add to the losses dictionary
                    self.losses.update({eq.name: 1})
                    # deal with crew losses
                    for x in range(eq.crew):
                        roll = random()
                        if roll >= .25:
                            self.casualties.update({"Wounded": 1})
                        else:
                            self.casualties.update({"Killed": 1})    
        
        self.GenStrength()
                
        
    def GetVehicles(self):
        # returns the number of vehicles in this unit
        vehicles = 0
        for eq in self.equipment:
            if eq is not None:
                if eq.type not in ["Infantry","Antitank","Artillery","Air Defence"]:
                    vehicles += 1
        return vehicles
        
    def Move(self,advance,wp = None):
        # advances unit by advance amount
        if wp is None:
            # if waypoint parameter is blank, use this unit's waypoint
            wp = self.waypoint
        
        # TODO handle if distance is zero
        dir = make_unit([wp[0] - self.x, wp[1]-self.y])
        self.x = int(self.x + dir[0] * advance)
        self.y = int(self.y + dir[1] * advance)
        self.xy = [self.x, self.y]
    
    def PrintStrength(self):
        total = 0
        print("*"*50)
        print("**** FORMATION: {:^40s}****".format(self.name))
        print("Location: {}".format(self.xy))
        for key, val in self.Strength.items():
            print("{:>15s} strength: {:10,.0f}".format(key,val))
            total += val
        print("{:*>15s} strength: {:10,.0f}**************".format("Total",total))
        print("Casualties: {:5,.0f} KIA, {:5,.0f} WIA".format(self.casualties["Killed"],self.casualties["Wounded"]))
        print_losses(self.losses)
        # print("Losses: {}".format(self.losses))
        print("*"*60)
    
    def GetStatus(self):
        losses = "{} wounded, {} killed".format(self.casualties["Wounded"],self.casualties["Killed"])
        
        eqIntact    = Counter()
        eqDamaged   = Counter()
        eqDestroyed = Counter()
        
        for eq in self.equipment:
            if eq is not None:
                # this adds the entry to each, regardless of its state
                eqIntact.update({eq.name: 0})
                eqDamaged.update({eq.name: 0})
                eqDestroyed.update({eq.name: 0})
                
                if eq.state == "Intact":
                    eqIntact.update({eq.name: 1})
                elif eq.state == "Damaged":
                    eqDamaged.update({eq.name: 1})
                else:
                    eqDestroyed.update({eq.name: 1})
        
        data = "{}\n{}\n  Losses: {}\nSupply: {}\n".format(self.name,"*"*len(self.name),losses,self.supply)
        states = {"Intact": eqIntact, "Damaged": eqDamaged, "Destroyed": eqDestroyed}
        return data, states
        
    def UseSupply(self,amount):
        if FLAG_RUN_SUPPLY:
            self.supply = self.supply - amount / self.NumPoints * simTime
        
class Frontline():
    
    def __init__(self,parent,mapdata,directory):
        self.name           = mapdata["mapName"]
        self.desc           = mapdata["mapDesc"]
        self.scale          = mapdata["mapPixelsPerKM"]
        self.TerrainCover   = Image.open("{}/{}".format(directory,mapdata["mapTerrainCover"]))
        self.TerrainType    = Image.open("{}/{}".format(directory,mapdata["mapTerrainType"]))
        self.Territory      = Image.open("{}/{}".format(directory,mapdata["mapTerritory"]))
        self.TerrainWater   = Image.open("{}/{}".format(directory,mapdata["mapWater"]))
        self.Roads          = Image.open("{}/{}".format(directory,mapdata["mapRoads"]))
        
        self.weather        = mapdata["weather"]
        self.season         = mapdata["season"]
        
        # Set the GLOBAL redfor/blufor variables from the file
        global REDFOR
        global BLUFOR
        REDFOR = mapdata["REDFOR"]
        BLUFOR = mapdata["BLUFOR"]
        
        self.parent = parent
        
        self.FrontlinePoints = []
        self.FrontlineCoords = []
        
        self.FindFL()
        
        self.GetSupplySources()
        self.GetSupplyStatus()
        
        
    def FindFL(self):
        # march through image from L to R, and drop a FrontlinePoint on each type
        size = self.Territory.size
        px = self.Territory.load()
        pxType = self.TerrainType.load()
        pxCover = self.TerrainCover.load()
        pxWater = self.TerrainWater.load()
        
        # clear out the frontline
        self.FrontlinePoints = []
        self.FrontlineCoords = []
        
        # check horizontally
        # print("Horizontal Frontline check")
        x = 0
        for y in range(size[1]):
            # set initial pixel colour
            colour = px[x,y]
            for x in range(size[0]):
                newcolour = px[x,y]
                if colour != newcolour and not self.InFrontlineList(x,y) and (255,255,255) not in [newcolour, colour]:
                    self.FrontlinePoints.append(FrontlinePoint(self,(x,y),pxCover[x,y],pxType[x,y],pxWater[x,y]))
                colour = newcolour
        # repeat the check vertically
        # print("Vertical Frontline check")
        y = 0
        for x in range(size[0]):
            # set initial pixel colour
            colour = px[x,y]
            for y in range(size[1]):
                newcolour = px[x,y]
                if colour != newcolour and not self.InFrontlineList(x,y) and (255,255,255) not in [newcolour, colour]:
                    self.FrontlinePoints.append(FrontlinePoint(self,(x,y),pxCover[x,y],pxType[x,y],pxWater[x,y]))
                colour = newcolour
    
    def GetSupplySources(self):
        if FLAG_RUN_SUPPLY:
            self.SupplySources = []
            for form in self.parent.formations:
                if form.type == "supply":
                    self.SupplySources.append((form.x,form.y)) # supply can't cross ownership so we can do all of them
            tqdm.write("Creating BLU supply network")
            self.SupplyGraphBLUFOR = supply_network.generate_weighted_graph(self.Roads,self.TerrainWater,self.TerrainType,self.Territory,BLU)
            tqdm.write("Creating RED supply network")
            self.SupplyGraphREDFOR = supply_network.generate_weighted_graph(self.Roads,self.TerrainWater,self.TerrainType,self.Territory,RED)
        
        
    def GetSupplyStatus(self):
        if FLAG_RUN_SUPPLY:
            size = self.Territory.size
            
            REDFOR_pos = []
            BLUFOR_pos = []
            
            REDFOR_load = []
            BLUFOR_load = []
            
            for form in self.parent.formations:
                if form.nation in BLUFOR:
                    BLUFOR_pos.append((form.x,form.y))
                    BLUFOR_load.append(form.personnel / 10)
                else:
                    REDFOR_pos.append((form.x,form.y))
                    REDFOR_load.append(form.personnel / 10)
            tqdm.write("Running BLU supply")
            SupplyBLU, TrafficBLU = supply_network.get_supply(self.SupplySources,BLUFOR_pos,BLUFOR_load,self.SupplyGraphBLUFOR,size)
            tqdm.write("Running RED supply")
            SupplyRED, TrafficRED = supply_network.get_supply(self.SupplySources,REDFOR_pos,REDFOR_load,self.SupplyGraphREDFOR,size)
            
            # convert the traffic maps to images
            self.TrafficBLU = Image.fromarray(255-(normalize_matrix(TrafficBLU)).astype('uint8')).rotate(-90).transpose(Image.FLIP_LEFT_RIGHT)
            self.TrafficRED = Image.fromarray(255-(normalize_matrix(TrafficRED)).astype('uint8')).rotate(-90).transpose(Image.FLIP_LEFT_RIGHT)
        
        
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
        
    def DrawFrontline(self,im,colour = (0,0,0)):
        px = im.load()
        for pt in self.FrontlinePoints:
            px[pt.x,pt.y] = colour
        
    def DrawUnits(self,im):
        px = im.load()
        for unit in self.parent.formations:
            if unit.nation in REDFOR:
                px[unit.x,unit.y] = (255,0,0)
            else:
                px[unit.x,unit.y] = (0,0,255)
        
    def AssociateUnits(self):
        # runs through each frontline point and attaches units to it
        # first determine how many points are in range
        # print("Associating Formations with the Frontline")
        units = self.parent.formations
        for unit in units:
            unitrange = unit.personnel / 200  # units can affect the frontline from within this many km
            
            # calibrated so 1200 men affect 10 km frontage
            # handle min ranges
            # attacking units use lower frontage
            if unit.stance == "attacking":
                unitrange = unitrange/2
            if unitrange <= 2:
                unitrange = 2
            maxrad = unitrange / self.scale * 2
            
            unit.maxrange = maxrad
            
            unit.NumPoints = 0 # this value determines how many battles the unit is in
            points = 0
            for pt in self.FrontlinePoints:
                dist = ((pt.x-unit.x)**2 + (pt.y-unit.y)**2)**0.5
                if dist < maxrad:
                    # if dist < maxrad/2:
                        # influence = 1
                    # else:
                        # influence = 2 - dist/(maxrad/2)
                    influence = 1/(1+np.exp(-8*(dist/maxrad - 0.5)))
                    pt.AddUnit(unit,influence)
                    unit.NumPoints+=1
        
    def GetOwner(self,x,y):
        px = self.Territory.load()
        if px[x,y] == RED:
            return "RED"
        else:
            return "BLU"
            
    def NearestFriendly(self,x,y,colour,maxrad):
        # finds the nearest friendly pixel and returns an (x,y) pair and % of maxrad
        px = self.Territory.load()
        size = self.Territory.size
        
        xBound = (max(0,x-maxrad), min(x+maxrad,size[0]))
        yBound = (max(0,y-maxrad), min(y+maxrad,size[1]))
        
        points  = []
        rng     = []
        
        for xp in np.arange(xBound[0],xBound[1]):
            for yp in np.arange(yBound[0],yBound[1]):
                dist = ((xp-x)**2 + (yp-y)**2)**0.5 
                if dist <= maxrad:
                    # only if point is within the circle do we want to do something
                    if px[xp,yp] == colour:
                        points.append((int(xp),int(yp)))
                        rng.append(dist)
                        
        # find the minimum distance and return point
        if rng != []:
            idx = rng.index(min(rng))
            return points[idx], rng[idx]/maxrad
        else:
            xy = (0,0)
            return xy, 1
        
    
    def RunCombat(self):
        for pt in self.FrontlinePoints:
            pt.Combat()
                    
    def Advance(self):
        px = self.Territory.load()
        waterPx = self.TerrainWater.load()
        
        # tqdm.write("Advance called.")
        
        # iterates through all the frontline points and advances them per their property
        for pt in self.FrontlinePoints:
            idx = 0
            for attacker in pt.attackers:
                if attacker.nation in REDFOR:
                    colour = RED
                else:
                    colour = BLU
                wp  = attacker.waypoint
                dir = make_unit([wp[0] - attacker.x, wp[1]-attacker.y])
                n = 300 # number of samples to take
                
                range = ((pt.x - attacker.x)**2 + (pt.y - attacker.y)**2)**.5 # range from attacker to this point
                
                advance = pt.advance[idx] / len(pt.attackers) * simTime # scale advance rates by SimTime
                
                # draw pixels for advances
                adv = True
                for i in linspace(advance,n):
                    x = round(pt.x + dir[0] * i,0)
                    y = round(pt.y + dir[1] * i,0)
                    
                    if waterPx[x,y] == waterColour:
                        # stop the advance if we hit water
                        adv = True
                        moveAmount = i
                        # adv = False
                    elif adv:
                        px[x,y] = colour
                        moveAmount = i
                # move the unit by advance / NumPoints
                
                # tqdm.write("Advance {:.1}@{}, {}, {}".format(advance,pt.unitinfl,pt.attackers,pt.defenders))
                
                # attacker.Move(moveAmount/attacker.NumPoints)
                attacker.advance.append(moveAmount)
                # retreat
                for defender in pt.defenders:
                    defender.Move(moveAmount/attacker.NumPoints,wp = attacker.waypoint)
        
        # move attackers by average advance
        for form in self.parent.formations:
            if form.advance != []:
                form.Move(mean(form.advance))
            # reset the "advance" parameter after moving
            form.advance = []
        
class FrontlinePoint():
    def __init__(self,parent,xy,terrcover,terrtype,terrwater):
        self.x = xy[0]
        self.y = xy[1]
        self.xy = xy
        self.units = []
        self.unitinfl = [] # vector with influence of unit applied to point (reduces advance rate for far points)
        self.advance = [] # advance rate
        
        self.terrainCover = terrcover
        self.terrainType = terrtype
        self.terrainWater = terrwater
        
        self.parent = parent
        
        self.attackers = []
        self.defenders = []
        
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
        # print(self.attackers)
        if self.attackers == []:
            return
        
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
       
        
        if self.defenders != []:
            # This finds the advance rate and sets the casualty rates
            
            
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

            
            if roughDict[self.terrainType] == "urban":
                terrain = "urban"
            else:
                terrain = roughDict[self.terrainType] + ", " + coverDict[self.terrainCover]
            
            water = waterDict[self.terrainWater]
            
            weather = self.parent.weather
            season  = self.parent.season
            
            # attacker weapon strengths
            Wain = 0
            Waat = 0
            Watn = 0
            Waar = 0
            Waad = 0
            Waai = 0
            
            # defender weapon strengths
            Wdin = 0
            Wdat = 0
            Wdtn = 0
            Wdar = 0
            Wdad = 0
            Wdai = 0
            
            # get weapon strengths, divide by NumPoints so that concentration is applied
            for unit in self.attackers:
                Wain += unit.Strength["Infantry"] / unit.NumPoints 
                Waat += unit.Strength["Antitank"] / unit.NumPoints 
                Watn += unit.Strength["AFV"] / unit.NumPoints 
                Waar += unit.Strength["Artillery"] / unit.NumPoints 
                Waad += unit.Strength["Air Defence"] / unit.NumPoints 
                Waai += unit.Strength["Aircraft"] / unit.NumPoints 
                
            for unit in self.defenders:
                Wdin += unit.Strength["Infantry"] / unit.NumPoints 
                Wdat += unit.Strength["Antitank"] / unit.NumPoints 
                Wdtn += unit.Strength["AFV"] / unit.NumPoints 
                Wdar += unit.Strength["Artillery"] / unit.NumPoints 
                Wdad += unit.Strength["Air Defence"] / unit.NumPoints 
                Wdai += unit.Strength["Aircraft"] / unit.NumPoints 
            
            # deal with the overmatches in AT and AD combat power
            Waat = overmatch(Waat,Wdtn)
            Wdat = overmatch(Wdat,Watn)
            Waad = overmatch(Waad,Wdai,cap=3)
            Wdad = overmatch(Wdad,Waai,cap=3)
            
            # constants
            # terrain effectiveness (r) and weather effectiveness (h)
            #       and season effectiveness (z)
            rn      = interps.terrain(terrain,'inf')
            # artillery & air defence
            rwg     = interps.terrain(terrain,'arty')
            hwg     = interps.weather(weather,'arty')
            zwg     = interps.season(season,'arty')
            # tanks
            rwi     = interps.terrain(terrain,'tank')
            hwi     = interps.weather(weather,'tank')
            # aircraft
            rwy     = interps.terrain(terrain,'air')
            hwy     = interps.weather(weather,'air')
            zwy     = interps.season(season,'air')
            
            # air superiority (constant for now)
            wyg = 1
            wyy = 1
            
            # other factors
            Faj = 1 # judgement degrading factor for attacker
            Fdj = 1 # judgement degrading factor for defender
            uas = interps.stren_posture_factor('attacking') # posture for attacker
            uds = interps.stren_posture_factor(defenderStance) # posture for defender
            rau = 1 # terrain for attacker - attacker is always 1
            rdu = interps.terrain(terrain,'defpos') # terrain for defender - uses terrain defpos
            hau = interps.weather(weather,'attack') # weather for attacker
            hdu = 1 # weather for defender - defender is always 1
            zau = interps.season(season,'attack') # season for attacker
            zdu = 1 # season for defender - defender is always 1
            
            # get the side strengths
            S_attacker = (Wain + Waat)*rn + (Waar+Waad*wyg)*rwg*hwg*zwg + \
                            Watn*rwi*hwi + Waai*rwy*hwy*zwy*wyy
            S_defender = (Wdin + Wdat)*rn + (Wdar+Wdad*wyg)*rwg*hwg*zwg + \
                            Wdtn*rwi*hwi + Wdai*rwy*hwy*zwy*wyy
            
            # mobility factors
            road_quality = 1 # TODO - use new map to calculate this
            road_density = 1 # TODO - use new map to calculate this
            rma = interps.terrain(terrain,'mobility')
            hma = interps.weather(weather,'mobility')
            mya = 1 # don't know what this factor is
            myd = 1 # don't know what this factor is either
            # mobility calculation
            MFactor = 12 # 20 for WWII
            M_attacker = (((N_attacker + MFactor * J_attacker + Waar) * mya / N_attacker) /
                            ((N_defender + MFactor*J_defender + Wdar) * myd / N_defender))**0.5
            M_defender = 1 # always 1
            
            ma_operational = M_attacker - (1-rma*hma)*(M_attacker-1)
            md_operational = M_defender

            # vulnerability factors
            uav = interps.vuln_posture_factor('attacking')
            udv = interps.vuln_posture_factor(defenderStance)
            vay = 1 # air superiority vulnerability
            vdy = 1 # air superiority vulnerability
            var = 1 # shoreline vulnerability
            vdr = 1 # shoreline vulnerability
            
            # vulnerability
            Vuln_attacker = N_attacker * uav / rau * (S_defender/S_attacker)**0.5 * vay * var
            Vuln_defender = N_defender * udv / rdu * (S_attacker/S_defender)**0.5 * vdy * vdr
            va_operational = (1-Vuln_attacker/S_attacker)
            vd_operational = (1-Vuln_defender/S_defender)
            
            if va_operational > 0.8:
                va_operational = 0.8
            elif va_operational > 0.3:
                va_operational = 0.3 + 0.1 * (va_operational-0.3)
            else:
                va_operational = 0.3
            if vd_operational > 0.8:
                vd_operational = 0.8
            elif vd_operational > 0.3:
                vd_operational = 0.3 + 0.1 * (vd_operational-0.3)
            else:
                vd_operational = 0.3
            
            # note that the CEV is already contained in the OLI output
            Op_attacker = Faj * uas*rau*hau*zau
            Op_defender = Fdj * uds*rdu*hdu*zdu
            
            P_attacker = S_attacker * ma_operational * Op_attacker * va_operational
            P_defender = S_defender * md_operational * Op_defender * vd_operational
            P_ratio = P_attacker / P_defender
            
            # if self.defenders != []:
                # print("Combat at {}".format(P_ratio))
            
            # determine the advance rate for each attacker
            attackerNames = [x.name for x in self.attackers]
            for unit in self.attackers:
                adv_base = interps.advance_rate_base(P_ratio,unit.type,defenderStance)
                # adv_roads = interps.advance_rate_road(road_quality,road_density)
                adv_roads = 1
                if unit.type == "armoured":
                    advType = "advanceArm"
                else:
                    advType = "advance"
                adv_terr = interps.terrain(terrain,advType)
                if self.terrainWater == riverColour:
                    adv_river = 0.5
                else:
                    adv_river = 1
                adv_rate = adv_base * adv_roads * adv_terr * adv_river
                
                # add the advance rate for this unit
                idx = attackerNames.index(unit.name)
                self.advance.append(adv_rate * self.unitinfl[idx])
                
                # calculate loss rate
                casualty_base_attack = .028
                factor_size = interps.strength_size_factor(N_attacker)
                factor_opposition = interps.opposition_factor(P_ratio)
                casualty_rate = casualty_base_attack * factor_size * factor_opposition
                
                
                # tanks
                factor_tank_size = interps.tank_size_factor(J_attacker)
                casualty_tank = casualty_rate * 3 * factor_tank_size
                
                # inflict casualties
                unit.Casualties(casualty_rate,casualty_tank)
                unit.UseSupply(SUPPLY_RATE)
                
                
            for unit in self.defenders:
                # calculate defender loss rate
                casualty_base_defend = .015
                factor_size = interps.strength_size_factor(N_defender)
                factor_opposition = interps.opposition_factor(1/P_ratio)
                casualty_rate = casualty_base_defend * factor_size * factor_opposition
                # tanks
                factor_tank_size = interps.tank_size_factor(J_defender)
                casualty_tank = casualty_rate * 3 * factor_tank_size
                
                unit.Casualties(casualty_rate,casualty_tank)
                unit.UseSupply(SUPPLY_RATE)

        else:
            # if there are no defenders, we have maximum advance rate
            for unit in self.attackers:
                self.advance.append(60)
            
        
        

        
if __name__ == '__main__':
    import os
    abspath = os.path.abspath(__file__)
    dname = os.path.dirname(abspath)
    os.chdir(dname)
    
    
    mapname = "nirgendwola"
    # mapname = "germany1983"
    dbconfig = "./data/{}/".format(mapname)
    dbforms = "{}formations/".format(dbconfig)
    mapconfig = "{}maps/{}.yml".format(dbconfig,mapname)
    
    db = database()
    db.loadFormations(dbforms)
    # for form in db.formations:
        # form.PrintStrength()
        
    # dump equipment data
    with open("equipment_dump.txt","w+") as f:
        for equip in db.equip:
            f.write("{}\t{}\n".format(equip.name,equip.OLI))
    
    ans = input("Run simulation? (y/n) > ")
    if ans.lower == "y":
        db.loadFrontline(mapconfig)
        db.Simulate()
        
        db.TotalCasualties()
        
        db.LossesBySide()
        
        db.dumpFormations()
        # print("MISSING OBJECTS:", missing)
    
    
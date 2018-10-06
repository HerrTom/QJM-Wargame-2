from scipy.interpolate import pchip_interpolate, interp1d
from numpy import loadtxt

def dict_from_csv(file):
    # loads in a csv file as a dictionary
    result = {}
    reader = csv.reader(open(file))
    # next(reader) # skips the first row as a header
    n = 0
    for row in reader:
        if n == 0:
            headers = row[1:]
        else:
            key = row[0]
            result[key] = float(row[1:])
        n += 1
    return result, headers

# interpolations for QJM model

def RF_From_Calibre(calibre):
    data = loadtxt("./data/lookups/rf_from_calibre.csv",delimiter=',',
        skiprows=1)
    calibre_pts = data[:,0]
    RF_pts = data[:,1]
    rf_interp = interp1d(calibre_pts,RF_pts,'slinear',fill_value='extrapolate')
    return rf_interp(calibre)
    
def PTS_From_Calibre(calibre):
    data = loadtxt("./data/lookups/pts_from_calibre.csv",delimiter=',',
        skiprows=1)
    calibre_pts = data[:,0]
    PTS_pts = data[:,1]
    pts_interp = interp1d(calibre_pts,PTS_pts,'slinear',fill_value='extrapolate')
    return pts_interp(calibre)
 
def RIE_From_Calibre(calibre):
    data = loadtxt("./data/lookups/rie_from_calibre.csv",delimiter=',',
        skiprows=1)
    calibre_pts = data[:,0]
    RIE_pts = data[:,1]
    rie_interp = interp1d(calibre_pts,RIE_pts,'slinear',fill_value='extrapolate')
    return rie_interp(calibre)

def AmmoSupplyEffect(ammo_ratio):
    data = loadtxt("./data/lookups/ASE.csv",delimiter=',',
        skiprows=1)
    ammo_pts = data[:,0]
    ASE_pts = data[:,1]
    ase_interp = interp1d(ammo_pts,ASE_pts,'slinear',fill_value='extrapolate')
    return ase_interp(ammo_ratio)
    
def MBE(barrels):
    MBEDict = { 1: 1,
                2: 1.5,
                3: 1.83,
                4: 2.08,
                5: 2.28,
                6: 2.47,
                7: 2.65,
                8: 2.82,
                9: 2.98,
                10: 3.13,
                11: 3.27,
                12: 3.4,
                13: 3.52,
                14: 3.63,
                15: 3.73,
                16: 3.82,
                17: 3.9,
                18: 3.97,
                19: 4.03,
                20: 4.08,
                21: 4.12,
                22: 4.15,
                23: 4.17,
                24: 4.18}
    if barrels < 25:
        return MBEDict[barrels]
    else:
        return 4.18
        
        
def LLCF(lowLightOptics):
    mapping = {"Minimum": 1.0,
                "Active IR": 1.05,
                "Passive IR": 1.1,
                "Thermal": 1.3,
                "Advanced Thermal": 1.4,
            }
    return mapping[lowLightOptics]
    
def RgFF(rangefinder):
    mapping = {"Stadiametric": 1.00,
                "Coincident": 1.05,
                "Ranging Rifle": 1.10,
                "Laser": 1.20,
            }
    return mapping[rangefinder]  
    
def ARMF(armour):
    mapping = {"Steel": 1.00,
                "Aluminum": 0.70,
                "Early Composite": 1.10,
                "Composite": 1.20,
                "Reactive": 1.275,
                "Modern Reactive": 1.3025,
            }
    return mapping[armour] 
    
    
def GuidanceAccuracy(guidance):
    mapping = {'SACLOS wire day': 1.6,
               'SACLOS wire day/night': 1.7,
               'SACLOS radio': 1.7,
               'LOSLBR': 1.8,
               'F&F': 1.9}
    return mapping[guidance] 

def terrain(terrainType,factor):
    terrainDict, headers = dict_from_csv("./data/lookups/terrain.csv")
    
# advance rate
def advance_rate_base(ratio,unittype,deftype):
    pratio_pts = [1, 1.1, 1.25, 1.45, 1.75, 2.25, 3.0, 4.25, 6.0]
    advance = {
    "armoured": {"hasty": [4,5,6,9,12,16,20,40,60],
            "attack": [4,5,6,9,12,16,20,40,60],
            "delay": [4,5,6,9,12,16,20,40,60],
            "prepared": [2,2.25,2.5,4,6,8,10,20,30],
            "fortified": [1,1.85,1.5,2,3,4,5,10,30],},
    "mechanised": {"hasty": [4,4.5,5,7.5,10,13,16,30,48],
             "attack": [4,4.5,5,7.5,10,13,16,30,48],
             "delay": [4,4.5,5,7.5,10,13,16,30,48],
             "prepared": [2,2.25,2.8,3.5,5,7,8,16,24],
             "fortified": [1,1.85,1.5,2,2.5,3,4,8,24],},
    "infantry": {"hasty": [4,4.5,5,6.5,8,10,12,18,24],
            "attack": [4,4.5,5,6.5,8,10,12,18,24],
            "delay": [4,4.5,5,6.5,8,10,12,18,24],
            "prepared": [2,2.25,2.5,3,4,5,6,10,12],
            "fortified": [1,1.85,1.5,1.75,2,2.5,3,6,12],},
    }
    if ratio < 1:
        base = 0
    #elif ratio < max(pratio_pts):
    else:
        rate_pts = advance[unittype][deftype]
        rate_interp = interp1d(pratio_pts,rate_pts,'cubic',fill_value=max(rate_pts),bounds_error=False)
        base = float(rate_interp(ratio))
    #else:
    #    base = 60
    return base
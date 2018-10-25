import glob
import yaml
import pathvalidate as pv

# constants
m_lon =  0.01450
b_lon = -0.21810
m_lat = -0.00933
b_lat = 56.48237

typeConvert = {"mech": "mechanised", "armour": "armoured", "inf": "infantry"}

def xy_to_lon_lat(xy):
    x = xy[0]
    y = xy[1]
    
    lon = m_lon * x + b_lon
    lat = m_lat * y + b_lat
    
    return [lon,lat]
    
def lon_lat_to_xy(coords):
    lat = coords[0]
    lon = coords[1]
    
    # x corresponds to longitude
    # y corresponds to latitude
    
    x = round((lon - b_lon) / m_lon,0)
    y = round((lat - b_lat) / m_lat,0)
    
    return [x,y]
    
def convert_file(file):
    with open(file) as f:
        data = yaml.load(f)
    
    # do some conversions
    type = typeConvert[data["type"]]
    loc = lon_lat_to_xy(data["coords"])
    
    # just for testing :)
    if data["faction"] in ["USSR","DDR"]:
        waypoint = [153,809]
        stance = "attacking"
    else:
        waypoint = None
        stance = "hasty"
        
    if data["personnel"] == 0:
        personnel = 500
    else:
        personnel = data["personnel"]
    
    ## MAPPING ##
    new = {"name": data["name"],
            "shortname": data["shortname"],
            "hq": data["command"],
            "nation": data["faction"],
            "type": type,
            "SIDC": data["SIDC"],
            "proficiency": data["CEV"],
            "personnel": personnel,
            "equipment": data["equipment"],
            "location": loc,
            "waypoints": waypoint,
            "stance": stance,
            }
            
    with open("./yaml_out/{}.yml".format(pv.sanitize_filename(data["name"])),'w+') as f:
        f.write(yaml.dump(new, default_flow_style=False))
    
def convert_all(files):
    for f in files:
        convert_file(f)
    
if __name__ == '__main__':
    import os
    abspath = os.path.abspath(__file__)
    dname = os.path.dirname(abspath)
    os.chdir(dname)
    
    files = glob.glob("./web_yaml/*/*.yml")
    
    convert_all(files)
    
import os
from collections import Counter, OrderedDict
import glob
import yaml
from geojson import Feature, Point, FeatureCollection
# import simpletable
from natsort import index_natsorted, order_by_index

from convert_from_old_web import xy_to_lon_lat

# set the working directory to the script location
abspath = os.path.abspath(__file__)
dname = os.path.dirname(abspath)
os.chdir(dname)


# DEFS ####
table_style = "width: 90%, border: 1px solid black"
default_command = "ALL COMMAND"
colourDicts = {"USSR": "rgb(190,30,45)", "DDR": "rgb(153,69,70)", "USA": "rgb(0,174,239)", "BRD": "rgb(167,169,172)", "NL": "rgb(247,148,30)",
                "UK": "rgb(255,204,205)", "BEL": "rgb(255,255,0)", "FRA": "rgb(141,198,63)", "DEFAULT": "rgb(255,255,255)",
                "VRN": "rgb(255,218,218)", "BRN": "rgb(255,255,218)", "NK": "rgb(224,255,218)", "NDR": "rgb(244,218,255)",
                }


# categories:
with open("equip_cats.yml",'r') as f:
    equip_cats = yaml.load(f)

def search_names(data,term,key="shortname"):
    keylist = list()
    for x in data:
        keylist.append(x[key])
    if term in keylist:
        return keylist.index(term)
    else:
        return None

def pretty_unit(unit_list,unit_name):
    idx = search_names(unit_list,unit_name)
    unit = unit_list[idx]
    equip = unit["equipment"]
    tot_equip = unit["total_equipment"]
    print(unit["name"])
    print("Subunits: {}".format(', '.join(unit["children"])))
    print(" Personnel: {:,.0f} ({:,.0f})".format(unit["personnel"],unit["total_pers"]))
    written = []
    for cat in equip_cats.keys():
        print(" {}-------".format(cat))
        for eq in tot_equip.keys():
            if (eq in equip_cats[cat] or equip_cats[cat][0] is None) and eq not in written:
                if eq in equip.keys():
                    equip_entry = equip[eq]
                else:
                    equip_entry = 0
                print("   {:20}: {:8,.0f} ({:8,.0f})".format(eq,equip_entry,tot_equip[eq]))
                written.append(eq)
        
def collect_children(unit_list,unit):
    children = unit["children"]
    unit_idx = search_names(unit_list,unit["shortname"])
    # if children is [] we skip it
    equip = Counter(unit_list[unit_idx]["equipment"])
    pers = unit_list[unit_idx]["personnel"]
    if children != []:
        # print("Collecting {:9} : {}".format(unit["shortname"], children))
        # check if subunit has children
        for subchild in children:
            subchild_idx = search_names(unit_list,subchild)
            subchild_entry = unit_list[subchild_idx]
            # print("     Subchild {}".format(subchild))
            # call this function again
            if subchild_entry["children"] != []:
                # this prevents double counting
                equip_new,pers_new = collect_children(unit_list,subchild_entry)
                equip += equip_new
                pers += pers_new
            # once we've collected, add the child's equipment
            equip += subchild_entry["equipment"]
            pers += subchild_entry["personnel"]
        equip.update()
    return equip,pers
        
        
def html_equipment(equip,name,personnel):
    # takes an equipment dictionary and returns an HTML table
    html_table = """<h2>{}</h2>
    <table>
    <tr>
        <td><i>Personnel</i></td>
        <td style="text-align: right">{:6,.0f}</td>
    </tr>
    <tr>
        <th>Equipment</th>
        <th style="text-align: right">Qty</th>
    </tr>""".format(name,personnel)
    written = [] # list of already written entries
    for cat in equip_cats.keys():
        html_table +="""    <tr>
        <th>{}</th>
        <th></th>
        """.format(cat)
        for eq in equip.keys():
            if (eq in equip_cats[cat] or equip_cats[cat][0] is None) and eq not in written:
                equip_entry = """
    <tr>
        <td>{}:    </td>
        <td style="text-align: right">{:6,.0f}</td>
    </tr>""".format(eq,equip[eq])
                html_table += equip_entry
                # delete the entry when it's entered
                written.append(eq)
    # finish the table with </table>
    html_table += "\n</table>"
    # print(html_table)
    return html_table

def write_geojson(unit_list, filename):
    # writes a geojson file to a given write object
    crs = {"type": "name","properties": {"name": "EPSG:4326"}}
    fl = FeatureCollection(unit_list, crs = crs)
    output = "var situation = " + str(fl)
    # print(output)
    with open(filename, 'w+') as f:
        f.write(output)
        

def gen_unit_feature(coords,sidc,name,fullname,command='default',equip={"None": 0},
                    color='rgb(255,255,255)'):
    # type,geometry{type,coordinates},properties{SIDC,name,fullname,command,color}
    # note coords goes lat,lon but is reversed in geojson
    coords_corr = (float(coords[0]),float(coords[1]))
    return Feature(geometry=Point(coords_corr),properties={"SIDC": sidc, "name": name, 
                                "fullname": fullname, "command": command, "color": color,
                                "equipment": equip})
        


        
# # demo units
# u = [gen_unit_feature([53.5439458,10.9408425],"SFGPUCA----K","1.U","1st Unit","Command A")]
# print(u[0])
# u.append(gen_unit_feature([53.5439458,10.9408425],"SFGPUCA----K","2.U","2nd Unit","Command A"))

units = glob.glob('./yaml_in/*.yml')

# load in all the unit def files
unit_list = list()
for file in units:
    with open(file) as f:
        unit_list.append(yaml.load(f))
    unit_list[-1]["children"] = [] # this initializes the children entry
    # unit_list[-1]["total_equipment"] = None # this initializes equip summary
    # unit_list[-1]["total_pers"] = 0 # this initializes equip summary

# iterate over the untis to add children
new_units = []
new_units_nm = []
for ud in unit_list:
    # look for a parent
    command = ud["hq"]
    cmd_index = search_names(unit_list,command)
    if cmd_index is not None:
        # add this unit as a child
        unit_list[cmd_index]["children"].append(ud["shortname"])
        # print("Command exists: {}".format(command))
    else:
        if command not in new_units_nm:
            print("Command does not exist: {}".format(command))
            new_units.append(
                {"name": command, "shortname": command, "children": [ud["shortname"]], "equipment": {},
                "personnel": 0, "nation": ud["nation"], "hq": default_command, "location": [0,0],
                "SIDC": "SFGP------"}
            )
            new_units_nm.append(command)
        else: # command was previously created but not added to main list
            idx = search_names(new_units,command)
            new_units[idx]["children"].append(ud["shortname"])

for ud in new_units:
    print("new unit", ud)
    unit_list.append(ud)

# naturally sort units
name_list = []
for ud in unit_list:
    name_list.append(ud["shortname"])
index = index_natsorted(name_list)
unit_list = order_by_index(unit_list, index)
    
for idx, ud in enumerate(unit_list):
    # iterate over units for children
     equip, pers = collect_children(unit_list,ud)
     unit_list[idx]["total_equipment"] = equip
     unit_list[idx]["total_pers"] = pers


# iterate over all the units to generate the database entry
u = []
for ud in unit_list:
    # print(ud)
    # create a table
    equipment = html_equipment(ud["total_equipment"],ud["name"],ud["total_pers"])
    # create the color entry from the nation
    try:
        color = colourDicts[ud["nation"]]
    except:
        color = colourDicts["DEFAULT"]
    coords = xy_to_lon_lat(ud["location"])
    u.append(gen_unit_feature(coords,ud["SIDC"],ud["shortname"],ud["name"],ud["hq"],equipment,color))
    
# write the geojson file
write_geojson(u,'./json_out/situation.js')

# write an example unit
# print("-----")
# pretty_unit(unit_list,unit_list[0])
# pretty_unit(unit_list,"GSFG")

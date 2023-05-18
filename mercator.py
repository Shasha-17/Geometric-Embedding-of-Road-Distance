import os
import os.path
import sys
import geocoder
import folium
import webbrowser
import matplotlib.pyplot as plt
import mpld3
import numpy as np
import math as mt
import osmnx as ox
import geopandas as gpd
from shapely.ops import unary_union
from geopy.geocoders import Nominatim
from shapely.geometry import Point
from shapely.geometry.polygon import Polygon

debug = False  # debugging variable
map = False
R = 6371
# Convention : long = x, lat = y


class Location:
    def __init__(self, lon, lat):
        self.lat = lat
        self.lon = lon

# assuming each point in kms unit


### READ INPUT ###

cwd = os.getcwd()
mwd = "{c}\\Vrp-Set-A\\A".format(c=cwd)
owd = "{c}\\Haryana\\mercator\\T".format(c=cwd)
print(mwd)
l = os.listdir(mwd)
lnew = []
for f in l:
    if(debug):
        print(f[-3:])
    if f[-3:] == "vrp":
        lnew.append(f)
for file_name in lnew:
    vehicle_list = []  # neuman dataset defines this as depot_list
    consignment_list = []  # customer
    demand_list = []

    inptfile = open(os.path.join(mwd, file_name), 'r')
    inpt = inptfile.readlines()

    dep_info = inpt[1].split()
    no_of_veh = int(dep_info[8][:-1])
    veh_info = inpt[5].split()
    veh_cap = int(veh_info[2])
    dep_loc = inpt[7].split()
    dep_lat = int(dep_loc[2])
    dep_lon = int(dep_loc[1])

    for i in range(no_of_veh):
        id = i+1
        lat = dep_lat
        lon = dep_lon
        route = []
        consignments = []
        capacity = veh_cap
        curr_capacity = 0
        vehicle_list.append(Location(lon, lat))

    base = 7
    cust_info = inpt[3].split()
    no_of_cust = int(cust_info[2])
    for i in range(no_of_cust):
        cust_info = inpt[base + i]. split()
        id = int(cust_info[0])
        status = 0  # 0 = not allocated, 1 = allocated
        cust_Y = int(cust_info[2])
        cust_X = int(cust_info[1])
        consignment_list.append(Location(cust_X, cust_Y))

    coords = [Location(dep_lon, dep_lat)]
    for x in consignment_list:
        coords.append(x)
    if (debug):
        print("Input read and coords stored")
        print(coords[0].lat)
        print(coords[0].lon)
    base = base + no_of_cust + 1
    for i in range(no_of_cust):
        dem_info = inpt[base + i].split()
        id = int(dem_info[0])
        weight = int(dem_info[1])
        demand_list.append(weight)
    ### INPUT READ ###

    ### Mercator Inverse Projection ###
    lat_lon_list = []
    for i in range(no_of_cust + 1):
        longi = (coords[i].lon/R)
        lati = (2 * np.arctan(mt.exp(coords[i].lat/R))) - mt.pi/2
        lat_lon_list.append(Location(longi, lati))

    if (debug):
        print("x, y converted to lat, lon range")

    ### TRANSLATION ###
    ### Lateral shift - center around the city of interest ###
    currCenter = Location(0, 0)
    miLat = lat_lon_list[0].lat
    miLon = lat_lon_list[0].lon
    maLat = lat_lon_list[0].lat
    maLon = lat_lon_list[0].lon

    for coord in lat_lon_list:
        if (coord.lat < miLat):
            miLat = coord.lat
        if (coord.lat > maLat):
            maLat = coord.lat
        if (coord.lon < miLon):
            miLon = coord.lon
        if (coord.lon > maLon):
            maLon = coord.lon
    currCenter = Location((miLon + maLon)/2, (miLat + maLat)/2)
    if (map):
        mercator_map = folium.Map()
        mercator_map = folium.Map(
            center=[currCenter.lon, currCenter.lat], zoom_start=0.5)
        folium.CircleMarker(location=[currCenter.lon, currCenter.lat],
                            radius=1,
                            weight=5).add_to(mercator_map)
        for c in lat_lon_list:
            folium.CircleMarker(location=[c.lon, c.lat], fill_color='#FF0000',
                                radius=1,
                                weight=5).add_to(mercator_map)
        mercator_map.fit_bounds(mercator_map.get_bounds())
        mercator_map.save("mercator_map.html")
        webbrowser.open("mercator_map.html")

    # calculating "shift"
    geolocator = Nominatim(user_agent="MyApp")
    city_loc = geolocator.geocode("Haryana")
    cityCenter = Location((city_loc.longitude), (city_loc.latitude))
    #cityCenter = Location((80.274696), (13.082258))

    if (debug):
        print("City's coords ", (cityCenter.lat), (cityCenter.lon))
    diffDist = Location((cityCenter.lon - currCenter.lon),
                        (cityCenter.lat - currCenter.lat))
    if (debug):
        print("Shifting distance ", (diffDist.lon), (diffDist.lat))

    # Shifting current center to city center
    # Note : folium takes in loc as (y, x) = (lat, lon)
    city_list = []
    for i in range(no_of_cust + 1):
        lati = lat_lon_list[i].lat + diffDist.lat
        longi = lat_lon_list[i].lon + diffDist.lon
        city_list.append(Location((longi), (lati)))
    if (map):
        shifted_map = folium.Map(
            center=[cityCenter.lat, cityCenter.lon], zoom_start=0.5)
        folium.CircleMarker(location=[cityCenter.lat, cityCenter.lon],
                            radius=1,
                            weight=5).add_to(shifted_map)
        for c in city_list:
            folium.CircleMarker(location=[c.lat, c.lon], fill_color='#43d9de',
                                radius=1,
                                weight=5).add_to(shifted_map)
        shifted_map.fit_bounds(shifted_map.get_bounds())
        shifted_map.save("shifted_map.html")
        webbrowser.open("shifted_map.html")

    ### centered around the desried city ###

    ### CONTRACTION ###
    # taking the mean of lats and lons around center - radially

    # city boundary as a geodataframe
    # shp = ox.geocode_to_gdf("Chennai, TamilNadu, India")
    # Multi = shp.loc[0, 'geometry']

    # boundary coords obtained as a single polygon from the internet
    # chennai_union_poly = Polygon([(80.18, 13.058), (80.186, 13.063), (80.187, 13.079), (80.192, 13.089), (80.192, 13.096), (80.19, 13.099), (80.191, 13.109), (80.195, 13.112), (80.197, 13.116), (80.198, 13.128), (80.2, 13.13), (80.212, 13.135), (80.224, 13.134), (80.228, 13.131), (80.235, 13.131), (80.237, 13.132), (80.236, 13.145), (80.242, 13.149), (80.244, 13.148), (80.244, 13.15), (80.248, 13.151), (80.25, 13.154), (80.26, 13.154), (80.272, 13.151), (80.272, 13.146), (80.27, 13.144), (80.279, 13.146), (80.284, 13.15), (80.302, 13.147), (80.304, 13.145), (80.304, 13.14), (80.302, 13.137), (80.308, 13.135), (
    #    80.309, 13.128), (80.304, 13.122), (80.306, 13.118), (80.306, 13.113), (80.3032, 13.105), (80.308, 13.106), (80.311, 13.103), (80.311, 13.1), (80.307, 13.092), (80.307, 13.088), (80.3, 13.081), (80.295, 13.067), (80.291, 13.061), (80.284, 13.033), (80.282, 13.012), (80.277, 13), (80.272, 12.976), (80.269, 12.971), (80.253, 12.973), (80.249, 12.979), (80.248, 12.977), (80.233, 12.969), (80.225, 12.962), (80.215, 12.964), (80.202, 12.982), (80.207, 13.006), (80.196, 13.014), (80.196, 13.025), (80.193, 13.021), (80.187, 13.019), (80.183, 13.022), (80.183, 13.041), (80.181, 13.053), (80.18, 13.058)])
    union_poly = Polygon ([(74.46,29.73),(74.46,29.82),(74.535,29.865),(74.49,29.895),(74.52,29.97),(74.625,29.925),(74.7,30),(74.79,30.015),(74.94,29.97),(75,29.895),(75.105,29.94),(75.135,29.82),(75.21,29.865),(75.27,29.745),(75.21,29.67),(75.255,29.565),(75.33,29.715),(75.465,29.835),(75.585,29.775),(75.69,29.79),(75.705,29.835),(75.855,29.835),
                           (75.945,29.745),(76.05,29.775),(76.08,29.835),(76.185,29.85),(76.155,29.955),(76.215,30.075),(76.2,30.18),(76.32,30.135),(76.32,30.165),(76.44,30.21),(76.455,30.15),(76.545,30.09),(76.605,30.165),(76.575,30.18),(76.59,30.225),(76.53,30.21),(76.53,30.27),(76.71,30.345),(76.695,30.42),(76.725,30.45),(76.875,30.45),(76.89,30.615),
                           (76.8,30.675),(76.83,30.825),(76.77,30.855),(76.755,30.915),(76.8,30.945),(76.845,30.945),(76.86,30.9),(76.935,30.915),(77.0088139403526,30.809551513782),(77.0100832,30.8102144),(77.0115423,30.8101222),(77.0119929,30.8089428),(77.0117783,30.8072288),(77.0117354,30.8056622),(77.0116802208671,30.8054568273328),(77.04,30.765),
                           (77.1,30.765),(77.19,30.69),(77.170530051143,30.6023852301437),(77.171359,30.6010358),(77.1699413780468,30.5997362012108),(77.16,30.555),(77.235,30.495),(77.4,30.45),(77.46,30.48),(77.49,30.435),(77.535,30.465),(77.625,30.375),(77.61,30.3),(77.445,30.15),(77.445,30.09),(77.295,30.03),(77.2767161966885,30.0007459147015),
                           (77.2771033,29.9953952),(77.2708228112291,29.9913164979666),(77.22,29.91),(77.205,29.805),(77.145,29.76),(77.175,29.685),(77.115,29.52),(77.175,29.445),(77.16,29.1),(77.205,29.055),(77.25,28.875),(77.175,28.815),(77.115,28.845),(76.995,28.815),(76.965,28.62),(76.875,28.575),(76.905,28.53),(76.995,28.56),(77.115,28.53),
                           (77.175,28.425),(77.22,28.44),(77.235,28.5),(77.34,28.545),(77.49,28.44),(77.501048283352,28.373710299888),(77.5045779,28.3696357),(77.5021350362471,28.3671897825177),(77.5026825076133,28.3639049543202),(77.5047496,28.3623475),(77.5033038381011,28.3601769713936),(77.52,28.26),(77.565,28.26),(77.565,28.155),(77.52,28.11),
                           (77.565,28.005),(77.55,27.915),(77.295,27.78),(77.1,27.765),(77.085,27.705),(77.01,27.705),(76.995,27.63),(76.905,27.63),(76.8920635205152,27.6946823974241),(76.8896597,27.6961875),(76.8904582,27.6993266),(76.8910026390727,27.6999868046365),(76.875,27.78),(76.92,27.855),(76.905,27.99),(76.95,28.125),(76.845,28.2),(76.8,28.125),
                           (76.68,28.065),(76.68,27.99),(76.575,27.945),(76.515,27.96),(76.5,28.02),(76.44,28.02),(76.41,28.11),(76.365,28.11),(76.38,28.065),(76.335,27.99),(76.275,28.005),(76.26,28.05),(76.23,28.035),(76.2,27.915),(76.245,27.81),(76.2,27.78),(76.1334518384906,27.8243654410063),(76.1322606,27.8244839),(76.132444776307,27.8250368157953),
                           (76.11,27.84),(75.96,27.825),(75.96,27.9),(75.915,27.9),(75.915,27.945),(75.96,27.96),(75.96,28.065),(75.915,28.095),(76.035,28.2),(75.915,28.35),(75.765,28.38),(75.72,28.47),(75.615,28.53),(75.6,28.59),(75.54,28.605),(75.45,28.905),(75.51,28.995),(75.42,28.995),(75.42,29.04),(75.375,29.04),(75.345,29.145),(75.39,29.205),
                           (75.33,29.205),(75.315,29.265),(75.24,29.205),(75.195,29.235),(75.06,29.205),(75.045,29.265),(74.94,29.265),(74.925,29.355),(74.85,29.385),(74.805,29.34),(74.67,29.355),(74.67,29.31),(74.58,29.31),(74.5381331055083,29.4251339598522),(74.5364692,29.4251831),(74.5358016,29.4283399),(74.5348478,29.4333242),(74.5348478,29.43416855),
                           (74.52,29.475),(74.58,29.49),(74.55,29.595),(74.595,29.73),(74.49,29.73),(74.46,29.73)])
    if (map):
        x, y = union_poly.exterior.xy
        plt.plot(x, y)
        plt.show()

    # compress in factors of 2 until all points fit inside the city completely
    all_in_check = True
    no_of_comp = 0
    temp_city_list = []
    for i in range(no_of_cust + 1):
        lati = city_list[i].lat
        longi = city_list[i].lon
        coord = Point(longi, lati)  # check order of lat, lon
        all_in_check = all_in_check and union_poly.contains(coord)
        if (all_in_check == False):
            break

    if (all_in_check == False):
        temp_city_list = []
        for i in range(no_of_cust + 1):
            lati = (city_list[i].lat + cityCenter.lat)*(0.5)
            longi = (city_list[i].lon + cityCenter.lon)*(0.5)
            temp_city_list.append(Location((longi), (lati)))
        no_of_comp = no_of_comp + 1
        city_list = temp_city_list[:]

    while (all_in_check == False):
        all_in_check = True
        for i in range(no_of_cust + 1):
            lati = city_list[i].lat
            longi = city_list[i].lon
            coord = Point(longi, lati)  # check order of lat, lon
            all_in_check = all_in_check and union_poly.contains(coord)
            if (all_in_check == False):
                break
        if (all_in_check == False):
            temp_city_list = []
            for i in range(no_of_cust + 1):
                lati = (city_list[i].lat + cityCenter.lat) * (0.5)
                longi = (city_list[i].lon + cityCenter.lon) * (0.5)
                temp_city_list.append(Location((longi), (lati)))
            no_of_comp = no_of_comp + 1
            city_list = temp_city_list[:]
    print("Number of times compressed " + str(no_of_comp))
    if (debug):
        print("Compressed to fit")

    if (map):
        final_map = folium.Map(
            center=[cityCenter.lat, cityCenter.lon], zoom_start=0.5)
        for c in city_list:
            folium.CircleMarker(location=[c.lat, c.lon], fill_color='#000000',
                                radius=0.5,
                                weight=5).add_to(final_map)
            # folium.Marker(location = (c.lat, c.lon)).add_to(map)

        final_map.fit_bounds(final_map.get_bounds())
        final_map.save("haryana_final_map.html")
        webbrowser.open("haryana_final_map.html")

    ### Write back transforemd dataset ###
    opfile = open(os.path.join(owd, "T" + file_name), 'w')
    opfile.write("%d\n" % (no_of_veh))
    opfile.write("%d\n" % (no_of_cust))
    # opfile.write(str() + " " + str())
    # x,y = lon,lat
    for i in range(no_of_cust):
        opfile.write(str(i+1) + " " + str(city_list[i].lon) + " " + str(
            city_list[i].lat) + " " + str(demand_list[i]))
        opfile.write("\n")
    for i in range(no_of_cust):
        opfile.write(str(
            i+1) + " " + str(coords[i].lon) + " " + str(coords[i].lat) + " " + str(demand_list[i]))
        opfile.write("\n")

'''
STEPS TO CONVERT X,Y TO LAT,LONG

1. Read input and store x, y coords
2. Find range of x, y
3. Find image height and length
4. Convert x,y to lat, long using formula on 
https://stackoverflow.com/questions/6659208/how-to-find-pixel-coordinates-of-a-city-on-a-world-map-using-longitude-and-latit
5. Find centre of these lat, long (uisng range/2) 
6. Now using chennai/delhi's centre lat long, shift all lat, longs using centre as reference 
'''
'''
STEPS TO RESIZE AND FIT ALL COORDS INSIDE THE CITY

1. Find the smallest rectangle that bounds all these points
2. Using osrm about polygon boundary points for the city
3. Now keep compressing until the rectangle fits completely inside the polygon
   3.1. Algorithm 
'''

import geocoder
import folium
import webbrowser
import matplotlib.pyplot as plt 
import mpld3

debug = False # debugging variable 

# for storing each point as a pair of latitude and longitude 
class Location:
  def __init__(self, lat, lon):
        self.lat = lat
        self.lon = lon

### READ INPUT ###
vehicle_list = [] #neuman dataset defines this as depot_list
consignment_list = [] #customer 

inptfile = open("C1_2_1.txt", 'r')
inpt = inptfile.readlines()

dep_info = inpt[4].split()
no_of_veh = int(dep_info[0])
veh_cap = int(dep_info[1])
temp_loc = inpt[9].split()
dep_lat = int(temp_loc[2])
dep_lon = int(temp_loc[1])

for i in range(no_of_veh):
    id = i+1
    #status = not ("Idle")
    lat = dep_lat
    lon = dep_lon
    route = []
    consignments = []
    capacity = veh_cap
    #volume = float(temp[5])
    curr_capacity = 0
    vehicle_list.append(Location(lat, lon))

base = 10
no_of_cust = 200

for i in range(no_of_cust):
    cust_info = inpt[base + i]. split()
    id = int(cust_info[0])
    status = 0 #0 = not allocated, 1 = allocated
    cust_lat = int(cust_info[2])
for i in range(no_of_cust):
    cust_info = inpt[base + i]. split()
    id = int(cust_info[0])
    status = 0 #0 = not allocated, 1 = allocated
    cust_Y = int(cust_info[2])
    cust_X = int(cust_info[1])
    demand = int(cust_info[3])
    st_time = int(cust_info[4])
    end_time = int(cust_info[5])
    service_time = int(cust_info[6])
    consignment_list.append(Location(cust_Y, cust_X))

### INPUT READ ###

coords = [Location(dep_lat, dep_lon)]
for x in consignment_list:
    coords.append(x)
if (debug):
    print("Input read and coords stored")
    # print(coords[0].lat)
    # print(coords[0].lon)

miX = coords[0].lat
miY = coords[0].lon
maX = coords[0].lat
maY = coords[0].lon

for point in coords :
    # if debug:
    #     print(point.lat, point.lon)
    if(point.lat < miX):
        miX = point.lat
    if(point.lat > maX):
        maX = point.lat
    if(point.lon < miY):
        miY = point.lon
    if(point.lon > maY):
        maY = point.lon
img_ht = abs(maY - miY)
img_wt = abs(maX - miX)
# if (debug):
#     print("minX and maxX")
#     print(miX)
#     print(maX)
#     print("minY and maxY")
#     print(miY)
#     print(maY)

lat_lon_list = []
for i in range(no_of_cust + 1):
    lati = ((coords[i].lat - miY)/(maY - miY))*(maY - miY) + miY
    longi = ((coords[i].lon - miX)/(maX - miX))*(maX - miX) + miX
    lat_lon_list.append(Location(lati, longi))

if (debug):
    print("x, y converted to lat, lon range")
    # print(lat_lon_list[0].lat)
    # print(lat_lon_list[0].lon)


currCenter = Location(0, 0)
miLat = lat_lon_list[0].lat
miLon = lat_lon_list[0].lon
maLat = lat_lon_list[0].lat
maLon = lat_lon_list[0].lon

for coord in lat_lon_list :
    if(coord.lat < miLat):
        miLat = coord.lat
    if(coord.lat > maLat):
        maLat = coord.lat
    if(coord.lon < miLon):
        miLon = coord.lon
    if(coord.lon > maLon):
        maLon = coord.lon
currCenter = Location (int((miLat + maLat)/2), int((miLon + maLon)/2))
if(debug):
    latlon_map = folium.Map()
    latlon_map = folium.Map(center = [currCenter.lat, currCenter.lon], zoom_start = 0.5)
    folium.CircleMarker(location=[currCenter.lat, currCenter.lon],
                        radius=1,
                        weight=5).add_to(latlon_map)
    for c in lat_lon_list:
        folium.CircleMarker(location=[c.lat, c.lon], fill_color='#FF0000',
                        radius=1,
                        weight=5).add_to(latlon_map)
    latlon_map.fit_bounds(latlon_map.get_bounds())
    latlon_map.save("latlon_map.html")
    webbrowser.open("latlon_map.html")
# Import the required library
from geopy.geocoders import Nominatim

# Initialize Nominatim API
geolocator = Nominatim(user_agent="MyApp")
location = geolocator.geocode("Chennai")
cityCenter = Location((location.latitude), (location.longitude))
# g = geocoder.osm("Chennai City")
# cityCenter = Location(int(g.osm['x']), int(g.osm['y']))
if(debug):
    print("city's coords ", (cityCenter.lat), (cityCenter.lon))
diffDist = Location(int(cityCenter.lat - currCenter.lat), int(cityCenter.lon - currCenter.lon))
if (debug):
    print("Shifting distance ", (diffDist.lon), (diffDist.lat))

#Shifting current cneter to city center 
city_list = []
for i in range(no_of_cust + 1):
    lati = lat_lon_list[i].lat + diffDist.lat
    longi = lat_lon_list[i].lon + diffDist.lon
    city_list.append(Location((lati), (longi)))
if(debug):
    shifted_map = folium.Map(center = [cityCenter.lat, cityCenter.lon], zoom_start = 0.5)
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
import osmnx as ox
from shapely.geometry import Point
from shapely.geometry.polygon import Polygon
import geopandas as gpd
from shapely.ops import unary_union

# Get place boundary related to the place name as a geodataframe
shp = ox.geocode_to_gdf("Chennai, TamilNadu, India")
Multi = shp.loc[0, 'geometry']
#poly_list = list(Multi.geoms)
#union_poly = Polygon(unary_union(Multi))
union_poly = Polygon([(80.18,13.058),(80.186,13.063),(80.187,13.079),(80.192,13.089),(80.192,13.096),(80.19,13.099),(80.191,13.109),(80.195,13.112),(80.197,13.116),(80.198,13.128),(80.2,13.13),(80.212,13.135),(80.224,13.134),(80.228,13.131),(80.235,13.131),(80.237,13.132),(80.236,13.145),(80.242,13.149),(80.244,13.148),(80.244,13.15),(80.248,13.151),(80.25,13.154),(80.26,13.154),(80.272,13.151),(80.272,13.146),(80.27,13.144),(80.279,13.146),(80.284,13.15),(80.302,13.147),(80.304,13.145),(80.304,13.14),(80.302,13.137),(80.308,13.135),(80.309,13.128),(80.304,13.122),(80.306,13.118),(80.306,13.113),(80.3032,13.105),(80.308,13.106),(80.311,13.103),(80.311,13.1),(80.307,13.092),(80.307,13.088),(80.3,13.081),(80.295,13.067),(80.291,13.061),(80.284,13.033),(80.282,13.012),(80.277,13),(80.272,12.976),(80.269,12.971),(80.253,12.973),(80.249,12.979),(80.248,12.977),(80.233,12.969),(80.225,12.962),(80.215,12.964),(80.202,12.982),(80.207,13.006),(80.196,13.014),(80.196,13.025),(80.193,13.021),(80.187,13.019),(80.183,13.022),(80.183,13.041),(80.181,13.053),(80.18,13.058)])
if(debug):
        x,y = union_poly.exterior.xy
        plt.plot(x,y)
        plt.show()

# if(debug):
#     for polyg in poly_list:
#         x,y = polyg.exterior.xy
#         plt.plot(x,y)
#         plt.show()

# checks if "pt" lies inside at least one of the polyogns
# RETURNS false - outside every polygon
# def check_all_poly (poly_list, pt):
#   for poly in poly_list:
#       if poly.contains(pt):
#           return True
#   return False
      

# determine if a point is within the city boundary
all_in_check = True
temp_city_list = []
for i in range(no_of_cust + 1):
    lati = city_list[i].lat
    longi = city_list[i].lon
    coords = Point (longi, lati) #check order of lat, lon
    all_in_check = all_in_check and union_poly.contains(coords)
    if (all_in_check == False):
        break

if (all_in_check == False):
    temp_city_list = []
    for i in range(no_of_cust + 1):
        lati = (city_list[i].lat + cityCenter.lat)*(0.5)
        longi = (city_list[i].lon + cityCenter.lon)*(0.5)
        temp_city_list.append(Location((lati), (longi)))
    city_list = temp_city_list[:]  


while(all_in_check == False):
    all_in_check = True
    for i in range(no_of_cust + 1):
        lati = city_list[i].lat
        longi = city_list[i].lon
        coords = Point (longi, lati) #check order of lat, lon
        all_in_check = all_in_check and union_poly.contains(coords)

        if (all_in_check == False): 
            break
    if (all_in_check == False):
        temp_city_list = []
        for i in range(no_of_cust + 1):
            lati = (city_list[i].lat + cityCenter.lat) *(0.5)
            longi = (city_list[i].lon + cityCenter.lon) *(0.5)
            temp_city_list.append(Location((lati), (longi)))
        city_list = temp_city_list[:]
    # if(debug):
    #         print(all_in_check)
    #         comp_map = folium.Map(center = [cityCenter.lat, cityCenter.lon], zoom_start = 0.5)
    #         folium.CircleMarker(location=[cityCenter.lat, cityCenter.lon],
    #                             radius=0.5,
    #                             weight=5).add_to(comp_map)
    #         for c in temp_city_list:
    #             folium.CircleMarker(location=[c.lat, c.lon], fill_color='#43d9de',
    #                             radius=0.5,
    #                             weight=5).add_to(comp_map)
    #         comp_map.fit_bounds(comp_map.get_bounds())
    #         comp_map.save(str(flag) + "_comp_map.html")
    #         webbrowser.open(str(flag) + "_comp_map.html")

print ("Compressed to fit")  


final_map = folium.Map(center = [cityCenter.lat, cityCenter.lon], zoom_start = 0.5)
for c in city_list:
    folium.CircleMarker(location=[c.lat, c.lon], fill_color='#000000',
                        radius=0.5,
                        weight=5).add_to(final_map)
    #folium.Marker(location = (c.lat, c.lon)).add_to(map)

final_map.fit_bounds(final_map.get_bounds())
final_map.save("final_map.html")
webbrowser.open("final_map.html")
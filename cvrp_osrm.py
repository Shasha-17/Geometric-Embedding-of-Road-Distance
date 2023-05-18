import folium
import requests
import pandas as pd
import numpy as np
import math
from pprint import pprint
import os
import os.path

debug = False
H_MAX = 100
W_MAX = 100
w, h = W_MAX, H_MAX
distMat = [[0 for x in range(w)] for y in range(h)]
coords = []


class Location:
    def __init__(self, lat, lon):
        self.lat = lat
        self.lon = lon


class Stop:
    def __init__(self, loc, drop, id):
        self.loc = loc
        self.drop = drop
        self.id = id


class Vehicle:
    # volume, current_volume
    def __init__(self, id, status, loc, route, max_capacity, current_capacity, consignments):
        self.id = id
        self.status = status
        self.loc = loc
        self.route = route
        self.max_capacity = max_capacity
        self.current_capacity = current_capacity
        # self.volume = volume
        # self.current_volume = current_volume
        self.consignments = consignments


class Consignment:
    def __init__(self, id, status, pickup_location, drop_location, pickup_date, drop_date, pickup_time, drop_time, weight):  # volume
        self.id = id
        self.status = status
        self.pickup_location = pickup_location
        self.drop_location = drop_location
        self.pickup_date = pickup_date
        self.drop_date = drop_date
        self.pickup_time = pickup_time
        self.drop_time = drop_time
        self.weight = weight
        # self.volume = volume


class Route:
    def __init__(self, start_point, end_point, sequence_of_points):
        self.start_point = start_point
        self.end_point = end_point
        self.sequence_of_points = sequence_of_points


def osrm_distance_matrix(coords):
    # calculates distance matrix for the given array of coords
    url = 'http://router.project-osrm.org/table/v1/driving/'
    for c in range(len(coords)):
        lng = str(coords[c].lon)
        lat = str(coords[c].lat)
        if c == 0:
            url = url+lng+','+lat
        else:
            url = url + ';'+lng + ',' + lat

    url = url+'?annotations=distance'

    dis_mat = requests.get(url).json()['distances']
    return dis_mat


def replace_none(mat):
    for i in range(len(mat[0])):
        for j in range(len(mat[0])):
            if (mat[i][j] is not None):
                mat[i][j] = mat[i][j]
            else:
                mat[i][j] = float('inf')
    return mat


def get_point_point_dist(a, b):
    # get from distance matrix generated using osrm
    i = 0
    j = 0
    for c in range(len(coords)):
        lng = coords[c].lon  # longitude
        lat = coords[c].lat  # latitude
        if (a.lon == lng and a.lat == lat):
            i = c
        if (b.lon == lng and b.lat == lat):
            j = c
    return distMat[i][j]


def can_be_allocated(consignment, v, vehicle_list):
    if consignment.weight > vehicle_list[v].current_capacity:
        return False
    # if consignment.volume > vehicle_list[v].current_volume:
    #     return False
    return True


def allocate_consignments_to_empty_vehicles(vehicles_list, consignment_list):
    local_consignment_list = consignment_list[:]
    veh_set = list(range(len(vehicles_list)))
    for c in consignment_list:
        c_vehicles = veh_set[:]
        n_veh = c_vehicles[0]
        min_distance = get_point_point_dist(
            c.pickup_location, vehicles_list[n_veh].loc)
        for veh in c_vehicles:
            distance = get_point_point_dist(
                c.pickup_location, vehicles_list[veh].loc)
            if distance < min_distance:
                n_veh = veh
                min_distance = distance
        c_vehicles.remove(n_veh)
        c_allocated = False
        while not c_allocated:
            if can_be_allocated(c, n_veh, vehicle_list):
                c_allocated = True
                local_consignment_list.remove(c)
                vehicle_list[n_veh].consignments.append(c.id)
                vehicle_list[n_veh].current_capacity -= c.weight
                # vehicle_list[n_veh].current_volume -= c.volume
            else:
                if not c_vehicles:
                    break
                n_veh = c_vehicles[0]
                min_distance = get_point_point_dist(
                    c.pickup_location, vehicles_list[n_veh].loc)
                for veh in c_vehicles:
                    distance = get_point_point_dist(
                        c.pickup_location, vehicles_list[veh].loc)
                    if distance < min_distance:
                        n_veh = veh
                        min_distance = distance
                c_vehicles.remove(n_veh)
    return local_consignment_list, vehicles_list


def CVRPhelper(stops, V):

    savingslist = []

    for i in range(len(stops)):
        for j in range(len(stops)):
            savingslist.append([get_point_point_dist(stops[i], V.loc) + get_point_point_dist(
                V.loc, stops[j]) - get_point_point_dist(stops[i], stops[j]), (i, j)])
    savingslist.sort(reverse=True, key=lambda x: x[0])

    all_routes = []
    for i in range(len(stops)):
        all_routes.append(Route(i, i, [i]))


    for l in savingslist:


        i = l[1][0]
        j = l[1][1]

        j_route = 0
        i_route = 0



        for k in all_routes:
            if (i in k.sequence_of_points):
                i_route = 1
                routewith_i = k
                break
        for k in all_routes:
            if (j in k.sequence_of_points):
                j_route = 1
                routewith_j = k
                break

        # case1 no routes assigned for both
        if (not (i_route or j_route)):
            all_routes.append(Route(i, j, [i, j]))
            continue

        # 3
        if (i_route and j_route):
            if routewith_i == routewith_j:
                continue
            if (routewith_i.end_point == i and routewith_j.start_point == j):
                all_routes.append(Route(routewith_i.start_point, routewith_j.end_point,
                                  routewith_i.sequence_of_points + routewith_j.sequence_of_points))

                all_routes.remove(routewith_j)
                all_routes.remove(routewith_i)
            continue

        # case 2
        if (i_route):
            if (routewith_i.end_point == i):
                routewith_i.end_point = j
                routewith_i.sequence_of_points.append(j)

            continue

        if (j_route):
            if (routewith_j.start_point == j):
                routewith_j.start_point = i
                routewith_j.sequence_of_points.insert(0, i)


    return all_routes

# %%


def CVRP(V, consignment_list):  # V - vehicle
    # global consignment_list
    savingslist = []
    pstops = []
    dstops = []
    cons = V.consignments

    for consignment_id in cons:
        for c in consignment_list:
            if c.id == consignment_id:
                pstops.append(c.pickup_location)
                dstops.append(c.drop_location)
                break

    proute = CVRPhelper(pstops, V)
    # print("****************")
    droute = CVRPhelper(dstops, V)

    for route in proute:
        # pprint(vars(route))

        for stop in route.sequence_of_points:
            V.route.append((pstops[stop], cons[stop], 'P'))
    for route in droute:
        for stop in route.sequence_of_points:
            V.route.append((dstops[stop], cons[stop], 'D'))

    return V


def get_shortest(distance_list):
    shortest = min(distance_list, key=lambda x: x[0])
    return shortest[1]


def route_alloc(vehicles_list, consignment_list):
    all_empty = True
    moving_vehicles = []
    unassigned_consignments_list = consignment_list
    for vehicle in vehicles_list:
        if vehicle.consignments:
            all_empty = False
        if vehicle.status == True:
            moving_vehicles.append(vehicle)
    if all_empty and not moving_vehicles:
        unassigned_consignments_list, vehicles_list = allocate_consignments_to_empty_vehicles(
            vehicles_list, consignment_list)
    return unassigned_consignments_list, vehicles_list

### READ INPUT ###
cwd = os.getcwd()
choice = input("Enter lambert or mercator: ")
mwd = "{c}\\haryana\\{ch}\\T".format(c=cwd, ch = choice)
dwd = "{c}\\haryana\\{ch}\\D".format(c=cwd, ch = choice)
owd = "{c}\\haryana\\{ch}".format(c=cwd, ch = choice)
l = os.listdir(mwd)
lnew = []
for f in l:
    if f[-3:] == "vrp":
        lnew.append(f)
osrm_op = open(os.path.join(owd, "osrm_op.txt"), 'w')
for file_name in lnew:
    distmat_op = open(os.path.join(dwd, "D" + file_name ), 'w')
    print(file_name)
    vehicle_list = []
    consignment_list = []

    inptfile = open(os.path.join(mwd, file_name), 'r')
    inpt = inptfile.readlines()

    vn = int(inpt[0])
    cn = int(inpt[1])
    dep_info = inpt[2].split()
    dep_lat = float(dep_info[1])
    dep_lon = float(dep_info[0])

    for i in range(vn):
        # temp = inpt[base + i].split()
        id = i
        status = False
        # not (temp[1].strip() == "Idle")
        lat = float(dep_lat)
        lon = float(dep_lon)
        route = []
        consignments = []
        capacity = 100
        # volume = float(temp[5])
        curr_capacity = 100
        vehicle_list.append(Vehicle(id, status, Location(
            lat, lon), route, capacity, curr_capacity, consignments))  # volume, volume,

    base = 2
    for i in range(cn):
        temp = inpt[base + i].split()
        id = int(temp[0])
        status = False
        plat = float(dep_lat)
        plon = float(dep_lon)
        dlat = float(temp[2])
        dlon = float(temp[1])
        weight = float(temp[3])
        consignment_list.append(Consignment(id, status, Location(
            plat, plon), Location(dlat, dlon), 0, 0, 0, 0, weight))
    # for c in consignment_list:
    #     print(c.weight)
    coords = [Location(dep_lat, dep_lon)]
    # coords.extend([x.pickup_location for x in consignment_list])
    coords.extend([x.drop_location for x in consignment_list])

    # if(debug):
    #     print (coords)

    map = folium.Map()

    for c in coords:
        folium.Marker(location=(c.lat, c.lon)).add_to(map)

    map.fit_bounds(map.get_bounds())

    distMat = osrm_distance_matrix(coords)
    distMat = replace_none(distMat)
    if (debug):
        print(distMat)
    #distance matrix output stored 
    for i in range(len(consignment_list)):
        for j in range(len(consignment_list)):
            distmat_op.write(str(get_point_point_dist(consignment_list[i].drop_location, consignment_list[j].drop_location)))
            distmat_op.write("\n")
    unallocated_cons, vehicle_list = route_alloc(
        vehicle_list, consignment_list)
    # from pprint import pprint
    total_cost = 0
    for v in vehicle_list:
        print("Vehicle ", v.id)
        if not v.consignments:
            print("Vehicle", v.id, " is unassigned")
        else:
            print(len(v.consignments), *v.consignments)
            v1 = CVRP(v, consignment_list)
            for stop in v1.route:
                print(stop[1], stop[2], stop[0].lat, stop[0].lon)
            curr_cost = 0
            for i in range(len(v1.route)-1):
                a = consignment_list[v1.route[i][1] - 1].drop_location
                b = consignment_list[v1.route[i+1][1] - 1].drop_location
                curr_cost += get_point_point_dist(a, b)
            a = consignment_list[v1.route[len(
                v1.route) - 1][1] - 1].drop_location
            b = consignment_list[v1.route[0][1] - 1].drop_location
            curr_cost += get_point_point_dist(a, b)
            total_cost += curr_cost
            print("cost for vehicle ", v.id, "is " + str(curr_cost) + "\n")
    osrm_op.write(file_name + " " + str(total_cost))
    osrm_op.write("\n")
    print("Total osrm_trans cost is " + str(total_cost) + "\n")

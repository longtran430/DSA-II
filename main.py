# Long Tran
# Student ID: 001347132
# B.S. Computer Science (March 1, 2020)
# My Program Mentor: Stephannie Schiro
# 405-586-4589 Central Time
# ltran56@my.wgu.edu

# A nearest neighbor algorithm is used to deliver packages.

# Development Environment
# Programming language: Python 3.10
# IDE: Pycharm Community Edition 2022.1.2
# Operating System: Microsoft Windows 10 Pro version 1903
# AMD Ryzen 7 2700X Eight-core processor 3.7 GHz
# 16 GB RAM

import csv
import re
from datetime import datetime

packageLists = []


# Opens package file, skips first 8 lines and stores each package into a list.
# List is used to count number of packages to set up hash table capacity.
def load_package_list(timeInput):
    with open('WGUPS Package File.csv') as packages:
        packageData = csv.reader(packages, delimiter=',')
        for e in range(8):
            next(packageData)
        # Corrects wrong address for package at 10:20 a.m.
        for line in packageData:
            if 'Wrong address' in line[7] and time_to_hours(timeInput, '10:20:00') > 0:
                line[1] = '410 S State St.'
                line[2] = 'Salt Lake City'
                line[3] = 'UT'
                line[4] = '84111'
            packageLists.append(line)


# Calculates the number of hours since start of workday to inputted time
def time_to_hours(timeString, start):
    if len(timeString) < 7:
        timeString += ':00'
    t = datetime.strptime(timeString, "%H:%M:%S")  # to datetime object
    s = datetime.strptime(start, "%H:%M:%S")
    return (t - s).total_seconds() / 3600  # 3600sec/hr / 18 mi/hr = 200 sec/mi


load_package_list('8:00')


# HashTable class for packages with an insert, search and remove methods.
class PackageTable:
    def __init__(self, cap=len(packageLists)):
        self.table = []
        for j in range(cap):
            self.table.append([])

    def insert(self, key, item):
        bucket = hash(key) % len(self.table)
        bucket_list = self.table[bucket]

        for value in bucket_list:
            if value[0] == key:
                value[1] = item
                return True

        key_value = [key, item]
        bucket_list.append(key_value)
        # bucket_list = self.table[bucket]
        return True

    def search(self, key):
        bucket = hash(key) % len(self.table)
        bucket_list = self.table[bucket]

        for value in bucket_list:
            if value[0] == key:
                return value[1]
        return None

    def remove(self, key):
        bucket = hash(key) % len(self.table)
        bucket_list = self.table[bucket]

        for value in bucket_list:
            if value[0] == key:
                bucket_list.remove([value[0], value[1]])


packageHash = PackageTable()
distanceData = []
truck1set = set()
truck2set = set()
truck3set = set()
group_set1 = set()  # early deadline and grouped packages
group_set2 = set()  # delayed and only truck 2
group_set3 = set()  # remaining
truck1Miles = 0.0
totalMiles = 0.0
maxMiles = 0.0
status = ''
statusHash = {}
notesHash = {}

must_be_with = {}


# Adds mileage for each truck to total mileage for all trucks.
def get_total_miles(miles):
    global totalMiles
    totalMiles += miles
    return totalMiles


# Converts number of miles to elapsed time
def miles_to_time(miles):
    hours = int(miles / 18)
    minutes = int(miles / 18 % 1 * 60)
    seconds = int(miles / 18 * 60 % 1 * 60)
    time_from_miles = '%02d:%02d:%02d' % (hours + 8, minutes, seconds)
    return time_from_miles


# Organizes packages into sets based on priority by reading the notes of each package
# and determining their delays, deadlines, and other delivery requirements.
# High priority sets of packages will be on the first truck to meet deadlines and requirements.
def priority_packages(ID, deadline, notes):
    if 'Must be delivered with' in notes or 'EOD' not in deadline and 'Delayed' not in notes:
        group_set1.add(ID)
        truck1set.add(ID)
        x = re.findall(r"\d\d", notes)  # Match any digit in notes
        for pid in x:
            # print(pid)
            group_set1.add(int(pid))
            truck1set.add(int(pid))
    elif 'truck' in notes or 'Delayed' in notes or 'Wrong address' in notes:
        group_set2.add(ID)
        truck2set.add(ID)
    else:
        group_set3.add(ID)


# Fills remaining, low priority packages into trucks.
def sort_package(ID):
    pStatus = 'At Hub'
    if ID in group_set3:
        if len(truck1set) < 16:
            truck1set.add(ID)
        elif len(truck2set) < 16:
            truck2set.add(ID)
        elif len(truck3set) < 16:
            truck3set.add(ID)
    return pStatus


# Organizes packages into trucks and inserts package data into hash table.
def load_package_hash():
    global status
    status = 'At hub'
    # Time Complexity: O(n), Space Complexity: O(n)
    for package in packageLists:
        priority_packages(int(package[0]), package[5], package[7])  # group priority packages
    # Time Complexity: O(n), Space Complexity: O(n)
    for package in packageLists:
        pID = int(package[0])
        pAddress = package[1]
        pCity = package[2]
        pState = package[3]
        pZip = package[4]
        pDeadline = package[5]
        pMass = package[6] + ' kg'
        notesHash[pID] = package[7]
        pStatus = sort_package(pID)
        p = [pID, pAddress, pCity, pState, pZip, pDeadline, pMass, pStatus]
        packageHash.insert(pID, p)


# Algorithm that determines delivery route for trucks.
# Reads data from WGUPS Distance Table and loads it into a nested list, then goes through
# and determines the next delivery address using a nearest neighbor algorithm (the shortest distance)
# for the most efficient delivery route to keep total mileage under 140 miles for all trucks.
def package_delivery(timeString, file_name, truckSet, truckName, returnToHub, delayMiles):
    location = 'HUB'
    currentRow = 7
    currentColumn = 2
    visited = {'HUB'}
    deliveredLocations = set()
    truckMiles = 0.0
    global totalMiles, distanceData
    # Updates statuses of packages in current truck
    for x in truckSet:
        p = packageHash.search(x)
        p[7] = 'En route - ' + truckName
        packageHash.insert(x, p)
    # Determine max mileage for each truck
    maxPerTruck = time_to_hours(timeString, '8:00:00') * 18 - delayMiles
    nextMiles = 0.0
    packageAmount = len(packageLists)

    # Time Complexity: O(n^2), Space Complexity: O(n^2)
    while packageAmount > 0 and len(truckSet) > 0:
        file = open(file_name)
        distanceData = list(csv.reader(file, delimiter=','))
        # row 27 after first run

        # Reads distance values for each address from the row of the current truck
        # location and comparing each value. Will be used to compare with column
        # values from the next for loop to determine next closest address.
        rowLocationDistance = ['', 0, 0]
        shortestRowDistance = 100.0
        # Time Complexity: O(n), Space Complexity: O(1)
        # go through rows for closest destination starting from 7th row
        for j in range(7, len(distanceData)):
            if distanceData[j][currentColumn] == '':  # if reading empty cell
                pass
            elif shortestRowDistance > float(distanceData[j][currentColumn]) > \
                    0.0 and distanceData[j][1].strip() not in visited:  # addresses in 2nd column
                shortestRowDistance = float(distanceData[j][currentColumn])  # shortest distance
                location = distanceData[j][1].strip()  # closest destination address
                rowLocationDistance = [distanceData[j][1].strip(), j, float(distanceData[j][currentColumn])]
                # address, row, distance

        # Reads distance values for each address from the column of the current truck
        # location and comparing each value. Will be used to compare with row values
        # from the previous for loop to determine next closest address.
        columnLocationDistance = ['', 0, 0]
        shortestColumnDistance = 100.0
        # Time Complexity: O(n), Space Complexity: O(1)
        # go through columns for closest destination starting from 2nd column
        for j in range(2, len(distanceData) - 5):
            if distanceData[currentRow][j] == '':
                pass
            elif shortestColumnDistance > float(distanceData[currentRow][j]) > \
                    0.0 and distanceData[6][j].strip() not in visited:  # addressed in 7th row
                shortestColumnDistance = float(distanceData[currentRow][j])  # shortest distance
                location = distanceData[6][j].strip()  # closest destination
                columnLocationDistance = [distanceData[6][j].strip(), j, float(distanceData[currentRow][j])]

        # Compare the shortest row and shortest column values to determine the next closest address
        # and checks if there is enough mileage to make the trip.
        if truckMiles + rowLocationDistance[2] < maxPerTruck and 0.0 < rowLocationDistance[2] and \
                (rowLocationDistance[2] < columnLocationDistance[2] or shortestColumnDistance == 100.0):  # \
            # and rowLocationDistance[0] in packageHash:
            location = rowLocationDistance[0]
            currentRow = rowLocationDistance[1]
            currentColumn = currentRow - 5
            truckMiles += rowLocationDistance[2]
        elif truckMiles + columnLocationDistance[2] < maxPerTruck and 0.0 < columnLocationDistance[2] and \
                (columnLocationDistance[2] < rowLocationDistance[2] or shortestRowDistance == 100.0):
            location = columnLocationDistance[0]
            currentColumn = columnLocationDistance[1]
            currentRow = currentColumn + 5
            truckMiles += columnLocationDistance[2]

        if 0.0 < rowLocationDistance[2] < columnLocationDistance[2] or \
                0.0 == columnLocationDistance[2] < rowLocationDistance[2]:
            nextMiles = rowLocationDistance[2]
        elif 0.0 < columnLocationDistance[2] < rowLocationDistance[2] or \
                0.0 == rowLocationDistance[2] < columnLocationDistance[2]:
            nextMiles = columnLocationDistance[2]

        visited.add(location.strip())

        # Reads each delivery address and edits addresses to common format for application to work properly.
        # Delivers package to address once the truck is verified to be at the destination address.
        # Time Complexity: O(n), Space Complexity: O(n)
        for x in range(len(packageLists) + 1):
            location1 = re.sub('North', 'N', location[:-8])
            location2 = re.sub('South', 'S', location1)
            location3 = re.sub('East', 'E', location2)
            location4 = re.sub('West', 'W', location3)
            destination1 = re.sub('North', 'N', str(packageHash.search(x)))
            destination2 = re.sub('South', 'S', destination1)
            destination3 = re.sub('East', 'E', destination2)
            destination4 = re.sub('West', 'W', destination3)
            if (location4 in destination4) and (x in truckSet) and (truckMiles < truckMiles + nextMiles < maxPerTruck):
                # compare location to package destination
                '''# Insert packages into hashtable
                p = Package(pID, pDestination, pCity, pState, pZip, pDeadline, pMass, pNotes)
                packageHash.insert(pID, p)'''
                if x != 9 or (x == 9 and time_to_hours(timeString, '10:20:00') > 0):
                    deliveredLocations.add(location.strip())
                    package = packageHash.search(x)
                    t = miles_to_time(truckMiles + delayMiles)
                    package[7] = 'Delivered at ' + t
                    truckSet.remove(x)
        packageAmount -= 1

    totalMiles = get_total_miles(truckMiles)
    if returnToHub:
        global truck1Miles
        truck1Miles = truckMiles + float(distanceData[currentRow][2])


# Start of Program
if __name__ == '__main__':
    print("\nWestern Governors University Parcel Service")
    fileName = 'WGUPS Distance Table with column headers.csv'
    delay = '9:05:00'
    # Loop options menu
    dontExit = True
    while dontExit:
        print("\nView status of package deliveries with 1 or 2, or exit with 3")
        print("1. View status of a package")
        print("2. View status of all packages")
        print("3. Exit")
        choice = input()
        if choice == '1' or choice == "2":
            print("At what time do you want to check the status of the package(s)?")
            print("Please enter a time in 24-hour in HH:MM or HH:MM:SS format after 08:00:00")
            # trucks go 18 mph, max 140 miles, 2 drivers, 70 miles/3.9 hrs per truck driver
            # While loop to retry code block if input is improper format
            retry = True
            while retry:
                try:
                    time = input()
                    totalMiles = 0.0
                    maxMiles = time_to_hours(time, '8:00:00') * 18
                    # Calls package data loading and delivery methods.
                    # Truck 1 begins delivery immediately at start of workday to deliver packages with early deadlines.
                    # Truck 2 begins delivery when all delayed packages arrive to hub.
                    # Truck 3 begins delivery of remaining packages when driver of Truck 1 returns to hub.
                    # trucks go 18 mph, max 140 miles, 2 drivers, 70 miles/3.9 hrs per truck driver

                    # Maximum possible mileage based on time elapsed from start of workday to input time.
                    # maxMiles = time_to_hours(time, '8:00:00') * 18
                    load_package_list(time)
                    load_package_hash()
                    package_delivery(time, fileName, truck1set, 'Truck 1', True, 0)
                    if time_to_hours(time, delay) > 0:
                        package_delivery(time, fileName, truck2set, 'Truck 2', False, 18 * 65 / 60)
                    # need to have truck driver drive back
                    if len(truck1set) == 0:
                        package_delivery(time, fileName, truck3set, 'Truck 3', False, truck1Miles)
                    # Time Complexity: O(n), Space Complexity: O(1)
                    if choice == '1':
                        print('Of which package do you want to check the status?')
                        packageChoice = input()
                        while not 0 < int(packageChoice) < len(packageHash.table) + 1:
                            print('Please enter a package ID of an existing package.')
                            packageChoice = input()
                        print('Package Status')
                        print("Package: {}".format(packageHash.search(int(packageChoice))))
                    elif choice == '2':
                        print('Package Status')
                        for i in range(len(packageHash.table)):
                            print("Package: {}".format(packageHash.search(i + 1)))
                    print('Total miles driven: %.2f' % totalMiles)
                    retry = False
                except ValueError:
                    print("Please enter a proper time in HH:MM:SS format.")
        elif choice == "3":
            print("Exiting...")
            dontExit = False
        else:
            print("Please enter 1 or 2.")


# End of Main

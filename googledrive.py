#!/usr/bin/env python3
"""
Bluetooth temperature server that listen for clients
adds them to a known premade google sheet
"""
import time
import gspread
import datetime
import bluetooth
import subprocess
import Adafruit_DHT

#Set up gpio4 for dht11 temperature sensor
sensor = Adafruit_DHT.DHT11
pin = 4

#Globals
needtorepot = True
togooglelist = ["", "", "", "", "", "", ""]

from oauth2client.service_account import ServiceAccountCredentials

#Used for google drive to know what we want to do on there
scope = ["https://www.googleapis.com/auth/drive"]

#raspberry pi cmd to turn Bluetooth discoverable on
bluediscovercmd = 'sudo hciconfig hci0 piscan'


#random uuid that was auto generated for this Raspberry Pi for Bluetooth interactions
uuid = "f105b946-6cb3-4957-a763-8655bab0e33b"


#Setup Credentials object to get authorized by google
creds = ServiceAccountCredentials.from_json_keyfile_name("picreds.json", scope)

#get access to the google drive
client = gspread.authorize(creds)

#get the google sheet handel to the sheet we want to add to.
log = client.open("TempData").worksheet('Sheet2')
#the front we only want to show the most up to date
front = client.open("TempData").worksheet('Sheet1')
#use sheet3 for error logs
errorlog = client.open("TempData").worksheet('Sheet3')


"""
no arguments get both the date and time in a format I want
"""
def gettime():
    timeobj = datetime.datetime.now()
    timeobj = str(timeobj)
    date = timeobj[5:10]
    tim = timeobj[11:16]
    return date, tim

"""
Get Temperature and Humidity from the DHT11 
"""
def gettemp():
    try:
        gotdata =False

        while not gotdata:
            humidity, temperature_c = Adafruit_DHT.read_retry(sensor, pin)
            if not temperature_c == None:

                gotdata = True


    except RuntimeError as error:
        # Errors happen fairly often, DHT's are hard to read, just keep going
        print(error.args[0])

    #convert to fahrenheit and to a string
    temperature_f = temperature_c * (9 / 5) + 32
    temperature_f = str(round(temperature_f, 2)) + "°F"
    return humidity, temperature_f

"""
Update the front page of the google sheet
"""
def updatefront():
    front.update_cell(2, 1, togooglelist[0])
    front.update_cell(2, 2, togooglelist[1])
    front.update_cell(2, 3, togooglelist[2])
    front.update_cell(2, 4, togooglelist[3])
    front.update_cell(2, 5, togooglelist[4])
    front.update_cell(2, 6, togooglelist[5])
    front.update_cell(2, 7, togooglelist[6])


"""
get the Raspberry pi local data DHT11
"""
def getlocals():
    local_hum, local_temp = gettemp()
    date, tim = gettime()
    togooglelist[0] = date
    togooglelist[1] = tim
    togooglelist[2] = local_temp
    togooglelist[3] = local_hum

"""
"""

def processdata(data):

    data = data.split(';')

    for item in data:
        item = item.split(':')
        if item[0] == "TEMP":
            togooglelist[6] = item[1]
        if item[0] == "DATE":
            togooglelist[4] = item[1]
        if item[0] == "TIME":
            togooglelist[5] = item[1] + ":" + item[2]


#send the cmd for bluetooth discoverable on
subprocess.check_output(bluediscovercmd, shell = True )
print("bluetooth discoverable on")
misseddata = 0

"""
The Main Loop
wait around every 15 minuates
advertise server with uuid
"""
while True:
    #set up a socket for bluetooth
    server_sock = bluetooth.BluetoothSocket(bluetooth.RFCOMM)
    #we dont care what bluetooth port to use just to and open on
    server_sock.bind(("", bluetooth.PORT_ANY))
    server_sock.listen(1)

    #start advetiseing the server with the UUID
    bluetooth.advertise_service(server_sock, "tempserver", service_id=uuid,
                                service_classes=[uuid, bluetooth.SERIAL_PORT_CLASS],
                                profiles=[bluetooth.SERIAL_PORT_PROFILE]
                                )
    #wait until we get a connection or a timeout
    gotconnection = False
    while not gotconnection:
        try:
            client_sock, client_info = server_sock.accept()
            gotconnection = True
        #Log error and move on if we get an error while trying to connect a
        except:
            error_string = [gettime()]
            error_string.append("got an error while trying to accept a connection")
            errorlog.insert_row( error_string, 2)

    try:
        #get local data
        getlocals()

        #get data from the connection it is a blocking call
        data = client_sock.recv(1024)

        if not data:
            #Error while trying to get data from socket log it and move on
            togooglelist[5] = "none"
            togooglelist[6] = "none"
            date, tim = gettime()
            error_string = [date, tim]
            error_string.append("Got an connection with No data")
            errorlog.insert_row( error_string, 2)
        else:
            #data is good so process it
            misseddata = 0
            needtorepot = True
            #data from sock comes in as bytes data type
            data = data.decode("utf-8")
            processdata(data)

        #update the front sheet in the googledrive
        updatefront()
        #log data on sheet 2
        log.insert_row(togooglelist, 2)

    except OSError:
        pass
    #report that we missed client data after a few misses
    misseddata = misseddata + 1
    if misseddata > 4 and needtorepot:
        #reported the error dont need to report again until we get data
        needtorepot = False
        error_string = [gettime()]
        error_string.append("Error Outdoor sensor is missing")
        errorlog.insert_row(error_string, 2)

    #done with connect so close both ends
    client_sock.close()
    server_sock.close()

    time.sleep(60)
    #wait a bit until we look for data again
    # wait right before every 15 mins before starting to broadcasting
    morewait = False
    while morewait:
        date, waittime = gettime()
        waittime = waittime[3:]
        waittime = int(waittime)
        if waittime % 15 == 0:
            morewait = False
        else:
            time.sleep(50)
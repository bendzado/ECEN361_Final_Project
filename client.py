#!/usr/bin/env python3
"""
Client to a Bluetooth server
Looks for a UUID thats being advertised
gets details to the server
connects then send data to the server
wait for a little bit then looks for the server again
"""

import sys
import time
import datetime
import bluetooth

from w1thermsensor import W1ThermSensor

"""
Get the temperature from the DS18B20
"""
def gettemp():
    temp = sensor.get_temperature(2)
    temp = str(round(temp,2))
    temp = temp + "°F"
    return temp


"""
no arguments get both the date and time in a format I want
"""
def gettime():
    timeobj = datetime.datetime.now()
    timeobj = str(timeobj)
    date = timeobj[5:10]
    tim = timeobj[11:16]
    return date, tim

#uuid that the server is boardcasting
uuid = "f105b946-6cb3-4957-a763-8655bab0e33b"
#get the senor handel for the sensor
sensor = W1ThermSensor()

"""
The Main loop
Search for the server then send data to it 
"""
while True:
    try:

        foundserver = False
        #look for the server
        while (not foundserver):
            service_matches = bluetooth.find_service(uuid=uuid)

            #did not find the server look again in a
            if len(service_matches) == 0:
                time.sleep(5)
            else:
                #found the server quit looking for tit
                foundserver = True
        #get the server info
        first_match = service_matches[0]
        port = first_match["port"]
        host = first_match["host"]
        #create the Bluetooth socket
        sock = bluetooth.BluetoothSocket(bluetooth.RFCOMM)
        #Connect to the server
        sock.connect((host, port))
        #packet up date to send
        data = "LOC:OUTSIDE;"
        date, tim = gettime()
        data = data + "TEMP:" + gettemp() + ";DATE:" + date + ";TIME:" + tim + ";"
        #send the data through the socket
        sock.send(data)
        #close the connection
        sock.close()

    #Look for keyboard interrupts so we can stop the program
    except KeyboardInterrupt:
        exit()
    #an error happen but we want to keep running anyway
    except:
        print("an error happened")
    #wait for a little bit before we try and connect again
    time.sleep(60)

    #wait until a 15 minute mark until we send data again
    morewait = False

    while morewait:
        date, waittime = gettime()
        waittime = waittime[3:]
        waittime = int(waittime)
        if waittime % 15 == 0:
            morewait = False
        else:
            time.sleep(50)
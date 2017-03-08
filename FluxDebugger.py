import socket
from threading import Thread
import threading
from datetime import datetime
import time
import json, requests
import os
import sys
import shutil
import struct
import fcntl
import subprocess
import ctypes
import picamera
from PIL import Image
# from PIL import ImageFont
# from PIL import ImageDraw
import numpy as np
# import math
# from numpy.lib.stride_tricks import as_strided
from uuid import getnode

global ver
ver = '0.06'

def restartPi():
    print '#####Restart PI #####'
    command = "sudo shutdown -r now"
    process = subprocess.Popen(command.split(), stdout=subprocess.PIPE)
    output = process.communicate()[0]
    print output

def removeLogs():
    print '#### Remove logs #####'
    baseDir = '/home/pi/FluxPlanet/fluxdebugger'
    fileList = os.listdir(baseDir)
    txtList = []

    for filename in fileList:
        name, ext = os.path.splitext(filename)
        if ext == '.txt':
            txtList.append(filename)

    # remain the last txt file
    txtList.pop(len(txtList) - 1)

    for txtname in txtList:
        fullname = baseDir + '/' + txtname
        os.remove(fullname)

    print 'Log files have been removed!'

def takePhoto(gain, exposure):
    print '##### Take photo #####'
    
    cmd = "/home/pi/FluxPlanet/userland/camera_i2c"
    process = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE)
    process.communicate()

    cmd = "sudo /home/pi/FluxPlanet/fluxdebugger/rpiraw -g %d -e %d -o /var/www/html/fluxd/rpiraw.raw" % (gain, exposure)
    process = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE)
    process.communicate()

def convertImg():
    print "debyaer"
    cmd = "/home/pi/FluxPlanet/fluxdebugger/debayer -s %f -i /var/www/html/fluxd/rpiraw.raw -o /var/www/html/fluxd/rpiraw.ppm" % (0.25, )
    print cmd
    process = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE)
    process.communicate()

    print "PIL"
    # ppm to jpg
    Image.open("/var/www/html/fluxd/rpiraw.ppm").save("/var/www/html/fluxd/rpiraw.jpg")

def get_ip_address(ifname):
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    addressFound = False
    while (addressFound == False):
        try:
            address = socket.inet_ntoa(fcntl.ioctl(
            s.fileno(),
            0x8915,  # SIOCGIFADDR
            struct.pack('256s', ifname[:15])
            )[20:24])
            addressFound = True
        except socket.error, msg:
            print "socket error %s " % msg
            time.sleep(1)
        except IOError as e:
            print "IO Error %s " %e
            time.sleep(1)
    return address



def cmdHandler(data):
    return



global server_found
server_found = False

global server_address

def listenToServer():
    global ver
    global server_address
    global server_found

    # kill pid of port 4123, in case 4123 port is being used
    cmd = "sudo netstat -nap | grep 4123 | grep LISTEN | awk '{split($NF, a, \"/\"); print a[1]}' | xargs sudo kill -s SIGKILL"

    process = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE)
    process.communicate()

    HOST = ''
    PORT = 4123
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    try:
        s.bind((HOST, PORT))
    except socket.error, msg:
        print 'Bind failed. Error code: ' + str(msg[0]) + ' , Error message: ' + msg[1]
        return


    print 'Socket is now waiting for the signal of the server'

    while True:
        s.listen(1)
        print 'Listen..'

        conn, addr = s.accept()
        serverData = conn.recv(1024)
        
        if 'SendAddr' in serverData:
            print 'Received server address: ' + addr[0]
            server_address = addr[0]
            
            jsonString = '{"ACK" : { "MAC" : "' + str(getnode()) + '", "VER" : "' + ver + '"} }'
            conn.send(jsonString)
            server_found = True
        # elif 'sebservice' in serverData:
            # conn.send('ACK')
            # command = "sudo raspistill -n -t 20000 -tl 1000 -o /var/www/html/images/temp_img%04d.jpg"
            # process = subprocess.Popen(command.split(), stdout=subprocess.PIPE)
            # output = process.communicate()
        else: 
            print 'data is not available'
        
        conn.close()
    s.close()    

def sendMsgToServer(msg):
    global server_found
    global server_address

    if not server_found :
        print 'Failed : Server is not found'
        return

    url = 'http://' + server_address + ':3000/ajax/slavemsg'

    resp = requests.post(url=url, data={'msg':msg})
    jData = resp.json()

    if jData["status"] == 'DONE':
        print 'Data sent to server: ' + msg
    else:
        print 'FAILED to send msg to server!'
 

def broadcastReceiver():
    global ver
    global server_found

    if not server_found :
        print 'Failed : master is not found'
        time.sleep(2)
        Thread(target = slaveReady).start()
        return

    print 'start broadcastReceiver'

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    try:
        sock.bind(('', 3228))
    except socket.error, msg:
        print 'Bind failed. Error code: ' + str(msg[0]) + ' , Error message: ' + msg[1]
        return

    while True:

        data, addr = sock.recvfrom(1024)

        if "led" in data:
            cmdHandler(data)
        elif "WakeUp" in data :
            jsonString = '{"RES": "WokeUp", "DATA" : { "MAC" : "' + str(getnode()) + '", "VER" : "' + ver + '"} }'
            sendMsgToServer(jsonString)
        elif "Update" in data :
            jData =  json.loads(data)
            masterIP = jData['Update']['serverip'];
            cmd = "/home/pi/bin/git_fluxdebugger_update.sh %s" % (masterIP, )
            process = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE)
            process.communicate()
            restartPi()
        elif "RmLogs" in data :
            removeLogs()
        elif "Convert" in data :
            print "convert"
            # jData =  json.loads(data)
            # takePhoto(jData['Take']['gain'], jData['Take']['exposure'])
            convertImg()
        elif "Take" in data :
            jData =  json.loads(data)
            takePhoto(jData['Take']['gain'], jData['Take']['exposure'])
        elif data != 'Controller' :
            cmdHandler(data)

def slaveReady():
    global server_found

    time.sleep(3)
    print 'Slave is ready!'


    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
    dev = "eth0" + "\0"
    # sock.setsockopt(socket.SOL_SOCKET, 25, dev)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    
    while True :
        if not server_found :
            print 'Try to find the server...'
            sock.sendto('Ready', ('<broadcast>', 3227))
        else:
            break
        time.sleep(2)

    sock.close()
    print 'End of slaveReady!'

    broadcastReceiver();


# ps -ef | grep FluxDebugger | grep sudo | awk '{print $2}' | xargs sudo kill -9
# sudo netstat -nap | grep 4123 | awk '{split($NF, a, "/"); print a[1]}' | xargs sudo kill -9
    
Thread(target = slaveReady).start()
listenToServer()
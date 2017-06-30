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
import RPi.GPIO as GPIO


global ver
ver = '0.26'

global gpio_dslr_shutter
global gpio_dslr_focus

gpio_dslr_shutter = 22
gpio_dslr_focus = 23

global is_cam
global take_process
global movfile

def initGPIO():
    global gpio_dslr_shutter
    global gpio_dslr_focus

    GPIO.cleanup()
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(gpio_dslr_shutter, GPIO.OUT)
    GPIO.setup(gpio_dslr_focus, GPIO.OUT)
    
    # gpio defaults
    GPIO.output(gpio_dslr_focus, GPIO.LOW)
    GPIO.output(gpio_dslr_shutter, GPIO.LOW)

def killGphoto2():
    print 'Kill gphoto2 process'
    cmd = "ps -A | grep gvfsd-gphoto2 | awk '{print $1}' | xargs sudo kill -s SIGKILL"
    subprocess.Popen(cmd, shell=True)

def detectDSLR():
    cmd = "gphoto2 --auto-detect | grep Canon"
    process = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE)
    cannon = process.communicate()[0]
    cannon = cannon.replace("\n", "")

    return len(cannon)

def rmFilesFromDSLR():
    if not detectDSLR():
        print 'No camera found'
        return

    killGphoto2()
    print 'delete all files from DSLR'
    cmd = 'gphoto2 -DR'
    subprocess.Popen(cmd, shell=True)

def getLastFileFromDSLR():
    global movfile

    if not detectDSLR():
        print 'No camera found'
        return

    print "rm *.MOV files at /home/pi/fluxd/"

    cmd4 = "rm /home/pi/fluxd/*.MOV"
    process4 = subprocess.Popen(cmd4, shell=True, stdout=subprocess.PIPE)
    print process4.communicate()[0]

    cmd = "gphoto2 --list-files | grep application | tail -n 1 | awk '{split($1, a, \"#\"); print a[2]}'"
    process = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE)
    output = process.communicate()[0]

    cmd2 = "gphoto2 --list-files | grep application | tail -n 1 | awk '{print $2}'"
    process2 = subprocess.Popen(cmd2, shell=True, stdout=subprocess.PIPE)
    movfile = process2.communicate()[0]
    movfile = movfile.replace("\n", "")

    cmd3 = "gphoto2 --get-file %d" % (int(output), )
    process3 = subprocess.Popen(cmd3, shell=True, stdout=subprocess.PIPE)
    print process3.communicate()[0]

    print "Got the mov file named %s from DSLR" % (movfile, )

def readyDSLR():
    global gpio_dslr_focus
    killGphoto2()
    GPIO.output(gpio_dslr_focus, GPIO.HIGH)
    print 'DSLR is ready to take video'

    jsonString = '{"RES": "RdyToTake"}'
    sendMsgToServer(jsonString)

def endVideoOfDSLR():
    global gpio_dslr_focus
    time.sleep(3)
    GPIO.output(gpio_dslr_focus, GPIO.HIGH)
    time.sleep(1)
    GPIO.output(gpio_dslr_focus, GPIO.LOW)
    time.sleep(1)

    print 'End of Video of DSLR'

def restartPi():
    print '#####Restart PI #####'
    command = "sudo shutdown -r now"
    process = subprocess.Popen(command.split(), stdout=subprocess.PIPE)
    output = process.communicate()[0]
    print output

def removeLogs():
    print '#### Remove logs #####'
    baseDir = '/home/pi/fluxd'
    fileList = os.listdir(baseDir)
    txtList = []

    for filename in fileList:
        name, ext = os.path.splitext(filename)
        if ext == '.txt':
            txtList.append(name)

    # find last log file
    maxtxt = 0
    for txtname in txtList:
        if(int(txtname) > maxtxt):
            maxtxt = int(txtname)

    for txtname in txtList:
        if(int(txtname) == maxtxt):
            continue

        fullname = baseDir + '/' + txtname + '.txt'
        os.remove(fullname)

    print 'Log files have been removed!'

def detectCamModule():
    global is_cam
    cmd = "vcgencmd get_camera | awk '{split($NF, a, \"=\"); print a[2]}'"
    process = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE)
    output = process.communicate()[0]
    is_cam = int(output)

def readyPhoto(frames, interval, dgain, gain, exposure, manual):
    global take_process
    # print '##### Take photo #####'
    
    cmd = "ps -ef | grep rpiraw | awk '{print $2}' | xargs sudo kill -s SIGKILL"
    subprocess.Popen(cmd, shell=True)

    cmd = "/home/pi/FluxPlanet/userland/camera_i2c"
    process = subprocess.Popen(cmd, shell=True)

    cmd = "sudo /home/pi/fluxd/rpiraw -f %d -i %d -dg %d -g %d -e %d -m %d -o /var/www/html/fluxd/rpiraw.raw" % (int(frames), int(interval), int(dgain), int(gain), int(exposure), int(manual))
    print cmd
    
    take_process = subprocess.Popen(cmd, stdin=subprocess.PIPE, shell=True)

    # take_process = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE)
    # print process.communicate()[0]

    jsonString = '{"RES": "RdyToTake"}'
    sendMsgToServer(jsonString)

def takePhoto():
    global take_process

    take_process.stdin.write('\n')
    print '##### Take photo #####'

    jsonString = '{"RES": "EndOfTake"}'
    sendMsgToServer(jsonString)


def takePhotoWithDSLR():
    global gpio_dslr_focus
    global movfile

    detectDSLR()

    GPIO.output(gpio_dslr_focus, GPIO.LOW)
    print '##### Take video with DSLR #####'
    endVideoOfDSLR()
    getLastFileFromDSLR()

    time.sleep(1)

    if detectDSLR():
        cmd = "/home/pi/bin/ffmpeg -i %s -r 1 mov_%%02d.jpg" % (movfile,)
        process = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE)
        print process.communicate()[0]

    jsonString = '{"RES": "EndOfTake"}'
    sendMsgToServer(jsonString)

def convertImg(index, scale, enhance, do_stretch, stretch, bx, by):
    cmd = "/home/pi/fluxd/debayer -fi %d -bx %f -by %f -sd %d -sv %f -sf 1 -s %f -c %f -i /var/www/html/fluxd/rpiraw.raw -o /var/www/html/fluxd/rpiraw.ppm" % (int(index), float(bx), float(by), int(do_stretch), float(stretch), float(scale), float(enhance))
    print cmd
    process = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE)
    print process.communicate()[0]

    print "PIL: convert ppm to jpg"
    Image.open("/var/www/html/fluxd/rpiraw.ppm").save("/var/www/html/fluxd/rpiraw.jpg")

    jsonString = '{"RES": "EndOfCvt"}'
    sendMsgToServer(jsonString)

def mov2jpg(index):
    offset = int(index) + 1

    cmd = "cp mov_%02d.jpg /var/www/html/fluxd/rpiraw.jpg" %(offset, )
    print cmd
    process = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE)
    print process.communicate()[0]

    jsonString = '{"RES": "EndOfCvt"}'
    sendMsgToServer(jsonString)

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
            print "IO Error %s " % e
            time.sleep(1)
    return address

def cmdHandler(data):
    return

global server_found
server_found = False

global server_address

def listenToServer():
    global is_cam
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
            
            jsonString = '{"ACK" : { "MAC" : "' + str(getnode()) + '", "VER" : "' + ver + '", "CAM" : ' + str(is_cam) + '} }'
            print jsonString
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
    global is_cam
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
            jsonString = '{"RES": "WokeUp", "DATA" : { "MAC" : "' + str(getnode()) + '", "VER" : "' + ver + '", "CAM" : ' + str(is_cam) + '} }'
            sendMsgToServer(jsonString)
        elif "Update" in data :
            jData =  json.loads(data)
            masterIP = jData['Update']['serverip']
            cmd = "/home/pi/bin/fluxdebugger_update.sh %s" % (masterIP, )
            process = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE)
            process.communicate()
            restartPi()
        elif "RmLogs" in data :
            removeLogs()
        elif "RmDSLR" in data :
            if not is_cam:
                rmFilesFromDSLR()
        elif "Convert" in data :
            print "convert"
            
            jData =  json.loads(data)
            if is_cam:
                convertImg(jData['Convert']['index'], jData['Convert']['scale'], jData['Convert']['enhance'], jData['Convert']['do_stretch'], jData['Convert']['stretch'], jData['Convert']['bx'], jData['Convert']['by'])
            else :
                mov2jpg(jData['Convert']['index'])
        elif "Ready" in data :
            if is_cam:      # camera exists
                jData =  json.loads(data)
                readyPhoto(jData['Ready']['frames'], jData['Ready']['interval'], jData['Ready']['dgain'], jData['Ready']['gain'], jData['Ready']['exposure'], jData['Ready']['manual'])
            else :
                readyDSLR()
        elif "Take" in data :
            if is_cam:
                takePhoto()
            else : 
                takePhotoWithDSLR()
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

# start FluxDebugger

# ps -ef | grep FluxDebugger | grep sudo | awk '{print $2}' | xargs sudo kill -9
# sudo netstat -nap | grep 4123 | awk '{split($NF, a, "/"); print a[1]}' | xargs sudo kill -9
detectCamModule()
initGPIO()
Thread(target = slaveReady).start()
listenToServer()

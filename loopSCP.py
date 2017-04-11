import os
import sys
import time
from threading import Thread
from thread import *

import subprocess
import fcntl
import struct

# global serverAddr


def get_ip_address(ifname):
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    return socket.inet_ntoa(fcntl.ioctl(
        s.fileno(),
        0x8915,  # SIOCGIFADDR
        struct.pack('256s', ifname[:15])
    )[20:24])

def myCLI(argv):
    global serverAddr

    startIndex = 0
    endIndex = 0 
    fileIndex = 0 
    for ind, cmd in enumerate(argv):
        if cmd == '-s':
            startIndex = ind
        if cmd == '-e':
            endIndex = ind
        if cmd == '-f':
            fileIndex = ind

    if not startIndex or not endIndex or not fileIndex:
        print "(err) >> python loopPSCP -s number -e number -f file"
        return

    try:
        startNo =  int(argv[startIndex+1]);
    except IndexError:
        print "Error '-s': failed to read start numner"
    except ValueError:
        print "Error '-s': start ip must be an int"
    
    try:
        endNo =  int(argv[endIndex+1]);
    except IndexError:
        print "Error '-e': failed to read end numner"
    except ValueError:
        print "Error '-e': end ip must be an int"
    
    try:
        filename =  argv[fileIndex+1];
    except IndexError:
        print "Error '-f': failed to filename"

    if not os.path.isfile(filename):
        print "Error '-f': is not file!"
    	return 

    # try:
    #     socket.inet_aton(serverAddr)
    # except socket.error:
    #     print "error : invalid ip addr"
    
    for x in range(endNo-startNo+1):

        # cmd = 'pscp -pw raspberry ' + filename + ' pi@192.168.1.' + str(x+startNo) + ":/home/pi/"
        cmd = 'sshpass -p "raspberry" scp -o StrictHostKeyChecking=no ' + filename + ' pi@192.168.1.' + str(x+startNo) + ":/home/pi/"
        print cmd    
        process = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE)
        process.communicate()
            
    print 'End pscp!!'

myCLI(sys.argv)

# print("--- %s seconds ---" % (time.time() - start_time))

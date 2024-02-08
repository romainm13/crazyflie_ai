#%%
import time

import cflib.crtp
from cflib.crazyflie import Crazyflie
from cflib.crazyflie.syncCrazyflie import SyncCrazyflie
from cflib.utils import uri_helper

import logging
logging.basicConfig(level=logging.DEBUG)

"""
The cflib.crtp module is for scanning for Crazyflies instances.
The Crazyflie class is used to easily connect/send/receive data from a Crazyflie.
The synCrazyflie class is a wrapper around the “normal” Crazyflie class. It handles the asynchronous nature of the Crazyflie API and turns it into blocking function.
"""

#%% Scanning for Crazyflies
if __name__ == '__main__':
    cflib.crtp.init_drivers()
    # Get interface status
    print(cflib.crtp.get_interfaces_status())
    # Scan for Crazyflies
    available = cflib.crtp.scan_interfaces()
    print("Crazyflies found:", available)
    for i in available:
        print("Found Crazyflie on URI [%s] with comment [%s]" % (i[0], i[1]))

"""
RESPONSE
INFO:cflib.crtp.prrtdriver:Initialized PRRT driver.
DEBUG:cflib.crtp:Scanning: <class 'cflib.crtp.radiodriver.RadioDriver'>
INFO:cflib.crtp.radiodriver:v0.53 dongle with serial N/A found
{'radio': 'Crazyradio version 0.53', 'UsbCdc': 'No information available', 'udp': None, 'prrt': 'No information available', 'cpx': None}
DEBUG:cflib.crtp:Scanning: <class 'cflib.crtp.usbdriver.UsbDriver'>
INFO:cflib.drivers.cfusb:Looking for devices....
DEBUG:cflib.crtp:Scanning: <class 'cflib.crtp.udpdriver.UdpDriver'>
DEBUG:cflib.crtp:Scanning: <class 'cflib.crtp.prrtdriver.PrrtDriver'>
INFO:cflib.crtp.prrtdriver:Initialized PRRT driver.
DEBUG:cflib.crtp:Scanning: <class 'cflib.crtp.tcpdriver.TcpDriver'>
Crazyflies found: []
""" 

#%%
# URI to the Crazyflie to connect to
"""
All communication links are identified using an URI built up of the following: 
InterfaceType://InterfaceId/InterfaceChannel/InterfaceSpeed

Currently we have radio, serial, usb, debug, udp interfaces. Here are some examples:
radio://0/10/2M : Radio interface, USB dongle number 0, radio channel 10 and radio speed 2 Mbit/s: radio://0/10/2M
debug://0/1 : Debug interface, id 0, channel 1
usb://0 : USB cable to microusb port, id 0
serial://ttyAMA0 : Serial port, id ttyAMA0
tcp://aideck-AABBCCDD.local:5000 : TCP network connection, Name: aideck-AABBCCDD.local, port 5000
"""
uri = uri_helper.uri_from_env(default='radio://0/80/2M/E7E7E7E7E7')

# URI to the Crazyflie to connect to
uri = 'radio://0/80/2M/E7E7E7E7E7'

def simple_connect():
    print("Yeah, I'm connected! :D")
    time.sleep(3)
    print("Now I will disconnect :'(")

if __name__ == '__main__':
    # Initialize the low-level drivers
    cflib.crtp.init_drivers()
    
    with SyncCrazyflie(uri, cf=Crazyflie(rw_cache='./cache')) as scf:
        simple_connect()

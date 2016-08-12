#
# Catroid: An on-device visual programming system for Android devices
# Copyright (C) 2010-2016 The Catrobat Team
# (<http://developer.catrobat.org/credits>)
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# An additional term exception under section 7 of the GNU Affero
# General Public License, version 3, is available at
# http://developer.catrobat.org/license_additional_term
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#

import socket
import sys
from thread import start_new_thread
import time
import subprocess

import RPi.GPIO as GPIO

serviceport   = 10000
interruptport = serviceport + 5

connected = False
pwm_dict = {}

#------------------------------------------------------------------------------
# Zuordnung der GPIO Pins (ggf. anpassen)
DISPLAY_RS = 33
DISPLAY_E  = 40
DISPLAY_DATA4 = 36 
DISPLAY_DATA5 = 35
DISPLAY_DATA6 = 38
DISPLAY_DATA7 = 37
DISPLAY_WIDTH = 24 	# Zeichen je Zeile
DISPLAY_LINE_1 = 0x80 	# Adresse der ersten Display Zeile
DISPLAY_LINE_2 = 0xC0 	# Adresse der zweiten Display Zeile
# (bei 4x20-Displays lauten die Adressen der dritten und vierten Zeile: 0x94 und 0xD4)

DISPLAY_CHR = True
DISPLAY_CMD = False
E_PULSE = 0.0005
E_DELAY = 0.0005

def display_init(line, connection):

        words = line.split(' ')
        if len(words) != 7 or words[0] != "HD4780init":
          print "wrong number of arguments. usage:HD4780init 4, 5, 6, 7, e, rs"
          return

	GPIO.setup(int(words[1]), GPIO.OUT)
	GPIO.setup(int(words[2]), GPIO.OUT)
	GPIO.setup(int(words[3]), GPIO.OUT)
	GPIO.setup(int(words[4]), GPIO.OUT)
	GPIO.setup(int(words[5]), GPIO.OUT)
	GPIO.setup(int(words[6]), GPIO.OUT)

	lcd_byte(0x33,DISPLAY_CMD)
	lcd_byte(0x32,DISPLAY_CMD)
	lcd_byte(0x28,DISPLAY_CMD)
	lcd_byte(0x0C,DISPLAY_CMD)  
	lcd_byte(0x06,DISPLAY_CMD)
	lcd_byte(0x01,DISPLAY_CMD)  

def lcd_write(line, connection):
  words = line.split(' ')
  if len(words) < 3 or words[0] != "HD4780write":
    print "wrong number of arguments. usage:HD4780write line message"
    return

  if(words[1] == '1'):
    lcd_byte(DISPLAY_LINE_1, DISPLAY_CMD)
  elif(words[1] == '2'):
    lcd_byte(DISPLAY_LINE_2, DISPLAY_CMD)

  catstr = "";
  for x in range(2, len(words)):
    if(x != 2):
      catstr += " " + words[x]
    else:
      catstr += words[x]
    
  lcd_string(catstr)
    

def lcd_string(message):
	message = message.ljust(DISPLAY_WIDTH," ")  
	for i in range(DISPLAY_WIDTH):
	  lcd_byte(ord(message[i]),DISPLAY_CHR)

def lcd_byte(bits, mode):
	GPIO.output(DISPLAY_RS, mode)
	GPIO.output(DISPLAY_DATA4, False)
	GPIO.output(DISPLAY_DATA5, False)
	GPIO.output(DISPLAY_DATA6, False)
	GPIO.output(DISPLAY_DATA7, False)
	if bits&0x10==0x10:
	  GPIO.output(DISPLAY_DATA4, True)
	if bits&0x20==0x20:
	  GPIO.output(DISPLAY_DATA5, True)
	if bits&0x40==0x40:
	  GPIO.output(DISPLAY_DATA6, True)
	if bits&0x80==0x80:
	  GPIO.output(DISPLAY_DATA7, True)
	time.sleep(E_DELAY)    
	GPIO.output(DISPLAY_E, True)  
	time.sleep(E_PULSE)
	GPIO.output(DISPLAY_E, False)  
	time.sleep(E_DELAY)      
	GPIO.output(DISPLAY_DATA4, False)
	GPIO.output(DISPLAY_DATA5, False)
	GPIO.output(DISPLAY_DATA6, False)
	GPIO.output(DISPLAY_DATA7, False)
	if bits&0x01==0x01:
	  GPIO.output(DISPLAY_DATA4, True)
	if bits&0x02==0x02:
	  GPIO.output(DISPLAY_DATA5, True)
	if bits&0x04==0x04:
	  GPIO.output(DISPLAY_DATA6, True)
	if bits&0x08==0x08:
	  GPIO.output(DISPLAY_DATA7, True)
	time.sleep(E_DELAY)    
	GPIO.output(DISPLAY_E, True)  
	time.sleep(E_PULSE)
	GPIO.output(DISPLAY_E, False)  
	time.sleep(E_DELAY)   
#------------------------------------------------------------------------------

def findRaspberryVersion():
    return GPIO.RPI_INFO['REVISION']

def disable_pwm(pin):
    if pin in pwm_dict:
        del pwm_dict[pin]
    return

def cmd_read_polling(line, connection):
    words = line.split()
    if len(words) != 2 or words[0] != "read":
        print "wrong number of arguments. usage: read <pin>"
        return

    port = int(words[1])
    disable_pwm(port)

    # TODO: sanity checks
#  try:
#    if GPIO.gpio_function(port) != GPIO.IN:
#      GPIO.setup(port, GPIO.IN)
#  except RuntimeError as e:
#    GPIO.setup(port, GPIO.IN)
    GPIO.setup(port, GPIO.IN)

    if GPIO.input(port) != GPIO.HIGH:
        print "port value is HIGH"
        value = "1"
    else:
        print "port value is LOW"
        value = "0"

    # send response
    answer = "read " + words[1] + " " + value + "\n"
    connection.send(answer)

    return

def cmd_read_interrupt(line, connection):
    words = line.split()
    print "length = " + str(len(words))
    if len(words) != 2 or words[0] != "readint":
        print "wrong number of arguments. usage: readint <pin>"
        return

    pin = int(words[1])
    disable_pwm(pin)

    #start_new_thread(button_handler, (pin,))
    GPIO.setup(pin, GPIO.IN)
    # add rising edge detection on a channel, 
    #ignoring further edges for 100ms for switch bounce handling
    GPIO.add_event_detect(pin, GPIO.BOTH, callback=my_callback_both, bouncetime=25)
    #GPIO.add_event_detect(pin, GPIO.RISING, callback=my_callback_rising)  
    #GPIO.add_event_detect(pin, GPIO.FALLING, callback=my_callback_falling)  


    # send response
    answer = "readint " + words[1] + " activated\n"
    connection.send(answer)

    return

def my_callback_both(channel):
    time.sleep(.03)
    pin_str = str(channel)
    if GPIO.input(channel): 
        print "Rising edge detected on " + pin_str
        mysocket2connection.send("interrupt " + pin_str + " pressed\n")
    else:
        print "Falling edge detected on " + pin_str
        mysocket2connection.send("interrupt " + pin_str + " released\n")

def my_callback_rising(channel):
    pin_str = str(channel)
    print "Rising edge detected on " + pin_str
    mysocket2connection.send("interrupt " + pin_str + " pressed\n")

def my_callback_falling(channel):
    pin_str = str(channel)
    print "Falling edge detected on " + pin_str
    mysocket2connection.send("interrupt " + pin_str + " released\n")

def cmd_setpin(line, connection):
    words = line.split()

    if len(words) != 3 or words[0] != "set":
        print "wrong number of arguments. usage: set <pin> <value>"
        return

    port = int(words[1])
    disable_pwm(port)
    print "port = " + str(port) + " value=" + words[2]
    # TODO: sanity checks
    if words[2] == "1":
        value = GPIO.HIGH
        print "set " + words[1] + " to HIGH"
    elif words[2] == "0":
        value = GPIO.LOW
        print "set " + words[1] + " to LOW"
    else:
        print "wrong value"
        return

    answer = "set " + words[1] + " " + words[2] + "\n"
    connection.send(answer)

#  try:
#    if GPIO.gpio_function(port) != GPIO.OUT:
#      GPIO.setup(port, GPIO.OUT)
#  except RuntimeError as e:
#    GPIO.setup(port, GPIO.OUT)
    GPIO.setup(port, GPIO.OUT)

    GPIO.output(port, value)
    return

def cmd_pwm(line, connection):
    global pwm_dict # maps: pin -> pwm_port_instance
    words = line.split()

    if len(words) != 4 or words[0] != "pwm":
        print "wrong number of arguments. usage: pwm <pin> <frequency> <dutycycle>"
        return

    port = int(words[1])
    frequency = float(words[2])
    dutycycle = float(words[3])

    if dutycycle < 0.0:
        print "Error: dutycycle < 0%, use 0%"
        dutycycle = 0.0

    if dutycycle > 100.0:
        print "Error: dutycycle > 100%, use 100%"
        dutycycle = 100.0


    if not port in pwm_dict:
        GPIO.setup(port, GPIO.OUT)
        pwm_dict[port] = GPIO.PWM(port, frequency)
        pwm_dict[port].start(0)
    # TODO: elif frequency has changed:
    #   pwm_dict[port] = GPIO.PWM(port, frequency)

    pwm_dict[port].ChangeDutyCycle(dutycycle)
    answer = "pwm " + words[1] + " " + words[2] + " " + words[3] + "\n"
    connection.send(answer)
 
    return

def cmd_play(line):
    splitline = line.split()
    file = splitline[1]
    subprocess.Popen(["/usr/bin/mplayer","/home/pi/audio/" + file])
    return

def cmd_receive_audio(line, connection):
    splitline = line.split()
    file = splitline[1]
    size = splitline[2]
    f = open("/home/pi/audio/" + file,'wb')
    print("now receiving " + size)
    amount = int(size)/1024
    rest = int(size)%1024
    i = 0
    while(i < amount):
        l = connection.recv(1024)
        f.write(l)
        i = i + 1
        print("Current: " + str(i))
    l = connection.recv(rest)
    f.write(l)
    print("finished receiving")
    f.close()
    return

def cmd_quit(connection):
    connection.send("quit ack\n")
    print "client sent quit command"
    return True

def handle_command(connection, command):
    if command == "":
        return True

    commandstr = command.decode("utf-8")

    print "received command: " + commandstr + ""

    if commandstr.startswith("readint"):
        cmd_read_interrupt(commandstr, connection)
    elif commandstr.startswith("read"):
        cmd_read_polling(commandstr, connection)
    elif commandstr.startswith("set"):
        cmd_setpin(commandstr, connection)
    elif commandstr.startswith("pwm"):
        cmd_pwm(commandstr, connection)
    elif commandstr.startswith("audiofile"):
        cmd_receive_audio(commandstr, connection)
    elif commandstr.startswith("play"):
        cmd_play(commandstr)
    elif commandstr == "rev":
        print "sending version..."
        connection.send("rev " + findRaspberryVersion() + "\n")
    elif commandstr == "serverport":
        connection.send("serverport " + str(interruptport) + "\n")
    elif commandstr == "quit":
        return cmd_quit(connection)
    elif commandstr.startswith("HD4780init"):
        connection.send(commandstr + "\n")
        display_init(commandstr, connection)
    elif commandstr.startswith("HD4780write"):
        connection.send(commandstr + "\n")
        lcd_write(commandstr, connection)
    else:
        print "Unknown command!"

    return False

def button_handler(pin):
    global connected

    GPIO.setup(pin, GPIO.IN)
    state = 0
    pin_str = str(pin)
    while connected:
        if not(GPIO.input(pin)):
            if(state == 0):
                mysocket2connection.send("interrupt " + pin_str + " pressed\n") # TODO: change to 1
                print "button pressed"
                state = 1
        else:
            if(state == 1):
                mysocket2connection.send(
                    "interrupt " + pin_str + " released\n") # TODO change to 0
                print "button released"
                state = 0
            time.sleep(.01)
    print "close button_handler thread for pin " + str(pin)
    return

def socket1_client_thread(socket1connection, client_address):
    global connected

    try:
        GPIO.setmode(GPIO.BOARD)
        socket1connection.send("hello\n")
        print "socket1connection from ", client_address
        while True:
            data = socket1connection.recv(32)
            if handle_command(socket1connection, data):
                break

    finally:
        socket1connection.close()
        connected = False
        GPIO.cleanup()
        pwm_dict.clear()
        print "socket1connection CLOSED: ", client_address
    return
       
def socket1_handler():
    global connected
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    with open("/etc/RaspberIno/config.cfg") as f:
      content = f.readlines()
      for line in content:
        myconfig = line.split('=')
        if(myconfig[0] == "port"):
          serviceport = int(myconfig[1])
    # Bind the socket to the port
    server_address = ('', serviceport)
    print "starting up on %s port %s" % server_address
    sock.bind(server_address)

    sock.listen(1)
    while True:
        print "waiting for a socket1connection"
        socket1connection, client_address = sock.accept()
        if not connected:
            connected = True
            start_new_thread(socket1_client_thread, (socket1connection, client_address))
        else:
            socket1connection.send("quit busy\n")
            
    return
     
def socket2_handler():
    global mysocket2connection
    global connected

    button_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_address = ('', interruptport)
    button_socket.bind(server_address)
    button_socket.listen(1)

    while True:
        socket2connection, client_address = button_socket.accept()
        mysocket2connection = socket2connection
        try:
            print 'socket2 connection from ', client_address
            while connected:
                time.sleep(.5)
        finally:
            socket2connection.close()

    return

    
#-------------------------------------------------------------------------
# Main Function
#-------------------------------------------------------------------------

start_new_thread(socket2_handler, ())
socket1_handler()
    




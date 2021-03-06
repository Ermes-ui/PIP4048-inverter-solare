import serial, time
import struct, string
import shutil
import os
from ctypes import c_ubyte, c_ushort
from requests import post
import json

#####################################################################
##                                                                 ##
##     CURL                                                        ##
#####################################################################
url = "http://192.168.1.146:8123/api/states/"
token = "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJpc3MiOiIwN2ZmYzI2MDE2NDQ0ZDJlYmU2ODUyMTJkOGI3OWZjMyIsImlhdCI6MTYzODk5ODU3NCwiZXhwIjoxOTU0MzU4NTc0fQ.jJenCS_JOxpaFVhD30KZ78vIm5YX8dqumPTht4wXRbY"

headers = {
    "Authorization": "Bearer " + token,
    "content-type": "application/json",
}

#####################################################################

def CalcoloCRC( str ):

	crc_ta = [ 0x0000, 0x1021, 0x2042, 0x3063, 0x4084, 0x50a5, 0x60c6, 0x70e7, \
                     0x8108, 0x9129, 0xa14a, 0xb16b, 0xc18c, 0xd1ad, 0xe1ce, 0xf1ef ]

	lunghezza = len(str)

	Calcolo = list(str)

	crc = 0

	for idx in range(0,lunghezza):
		da=c_ubyte((c_ubyte(crc>>8).value)>>4).value
		crc = c_ushort(crc << 4).value
		crc = c_ushort(crc ^ crc_ta[da^c_ubyte(c_ubyte(ord(Calcolo[idx])).value >> 4).value]).value
		da = (c_ubyte(crc>>8).value) >> 4
		crc <<= 4
		crc = c_ushort(crc ^ crc_ta[ da ^ ( ord(Calcolo[idx]) & 0x0f )]).value

	bCRCLow = c_ubyte(crc).value
	bCRCHign = c_ubyte(crc>>8).value

	if ( bCRCLow==0x28 or bCRCLow==0x0d or bCRCLow==0x0a ):
		bCRCLow += 1

	if ( bCRCHign==0x28 or bCRCHign==0x0d or bCRCHign==0x0a ):
		bCRCHign += 1

	crc = c_ushort(bCRCHign).value << 8
	crc += bCRCLow;
	return crc

class Inverter:
	def __init__(self,serialport):

		self.ser = serial.Serial()
		self.ser.port = serialport
		self.ser.baudrate = 2400
		self.ser.bytesize = serial.EIGHTBITS    #number of bits per bytes
		self.ser.parity = serial.PARITY_NONE    #set parity check: no parity
		self.ser.stopbits = serial.STOPBITS_ONE #number of stop bits
		self.ser.timeout = 1                    #non-block read
		self.ser.xonxoff = False                #disable software flow control
		self.ser.rtscts = False                 #disable hardware (RTS/CTS) flow control
		self.ser.dsrdtr = False                 #disable hardware (DSR/DTR) flow control
		self.ser.writeTimeout = 2               #timeout for write

		try:
		    self.ser.open()

		except Exception, e:
		    print "error open serial port: " + str(e)
		    exit()

		if self.ser.isOpen():
			try:
				self.ser.flushInput()   #flush input buffer, discarding all its contents
				self.ser.flushOutput()  #flush output buffer, aborting current output
							#and discard all that is in buffer
			except Exception, e1:
				print "error communicating...: " + str(e1)
		else:
			print "cannot open serial port "

	def QueryCMD(self,CMD):

		try:
			self.ser.write(CMD + struct.pack('!H',CalcoloCRC(CMD)) + '\x0D')
			time.sleep(0.2)  #give the serial port sometime to receive the data
			self.response = self.ser.readline()
			self.CRCSENT = ord(self.response[-3]) * 256 + ord(self.response[-2])
			if ( CalcoloCRC(self.response[:-3]) == self.CRCSENT ):
				return self.response[:-3]
			else:
				return -1
		except:
			return -1

	def Update(self):
		CMD = self.QueryCMD("QPIGS")
		if(CMD == -1  or CMD == "(NAK" ):  #CMD == "(NAK" serve per evitare che il programma si blocchi quando l'inverter risponde con una stringa sbagliata
            print "eccolo"
            return -1
		all = string.split(CMD[1:])
		self.grid_voltage = float(all[0])
		self.grid_frequency = float(all[1])
		self.ac_output_voltage = float(all[2])
		self.ac_output_frequency = float(all[3])
		self.ac_output_apparent_power = int(all[4])
		self.ac_output_active_power = int(all[5])
		self.output_load_percent = int(all[6])
		self.bus_voltage = float(all[7])
		self.battery_voltage = float(all[8])
		self.battery_charging_current = int(all[9])
		self.battery_capacity = int(all[10])
		self.heatsink_temperature = int(all[11])
		self.pv_current = int(all[12])
		self.pv_voltage = float(all[13])
		self.battery_voltage_scc = float(all[14])
		self.battery_discharge_current = int(all[15])
		CMD = self.QueryCMD("QMOD")
		if (CMD == -1):
			return -1
		mode = CMD[1:]
		self.isLineMode = 0
		if ( mode == "L" ):
			self.isLineMode = 1
		self.isBatteryMode = 0
		if ( mode == "B" ):
			self.isBatteryMode = 1
		CMD = self.QueryCMD("QPIWS")
		if (CMD == -1):
			return -1
		self.inverter_fault = CMD[1:2]
		self.BusOvervolt = CMD[2:3]
 		self.BusUndervolt = CMD[3:4]
 		self.SoftStartFail = CMD[4:5]
 		self.LineFail = CMD[5:6]
 		self.PvShort = CMD[6:7]
 		self.InvVoltLow = CMD[7:8]
 		self.InvVolrHigh = CMD[8:9]
 		self.OverTemp = CMD[9:10]
 		self.BatteryVoltHigh = CMD[10:11]
		self.BatteryVoltLow = CMD[11:12]
		return 0

#####################################################################
##                                                                 ##
##     MAIN                                                        ##
#####################################################################


sp5000 = Inverter("/dev/ttyUSB0")
while True:
    if (sp5000.Update() == 0):

        mydata = '{"state":' + str(sp5000.grid_voltage) + ', "attributes": {"unit_of_measurement": "V", "friendly_name": "grid_voltage"}}'
        response = post(url + "sensor.solar1", headers=headers,data =mydata)
        mydata = '{"state":' + str(sp5000.grid_frequency) + ', "attributes": {"unit_of_measurement": "Hz", "friendly_name": "grid_frequency"}}'
        response = post(url + "sensor.solar2", headers=headers,data =mydata)
        mydata = '{"state":' + str(sp5000.ac_output_voltage) + ', "attributes": {"unit_of_measurement": "V", "friendly_name": "ac_output_voltage"}}'
        response = post(url + "sensor.solar3", headers=headers,data =mydata)
        mydata = '{"state":' + str(sp5000.ac_output_frequency) + ', "attributes": {"unit_of_measurement": "Hz", "friendly_name": "ac_output_frequency"}}'
        response = post(url + "sensor.solar4", headers=headers,data =mydata)
        mydata = '{"state":' + str(sp5000.ac_output_apparent_power) + ', "attributes": {"unit_of_measurement": "W", "friendly_name": "ac_output_apparent_power"}}'
        response = post(url + "sensor.solar5", headers=headers,data =mydata)
        mydata = '{"state":' + str(sp5000.ac_output_active_power) + ', "attributes": {"unit_of_measurement": "W", "friendly_name": "ac_output_active_power"}}'
        response = post(url + "sensor.solar6", headers=headers,data =mydata)
        mydata = '{"state":' + str(sp5000.output_load_percent) + ', "attributes": {"unit_of_measurement": "%", "friendly_name": "output_load_percent"}}'
        response = post(url + "sensor.solar7", headers=headers,data =mydata)
        mydata = '{"state":' + str(sp5000.bus_voltage) + ', "attributes": {"unit_of_measurement": "V", "friendly_name": "bus_voltage"}}'
        response = post(url + "sensor.solar8", headers=headers,data =mydata)
        mydata = '{"state":' + str(sp5000.battery_voltage) + ', "attributes": {"unit_of_measurement": "V", "friendly_name": "battery_voltage"}}'
        response = post(url + "sensor.solar9", headers=headers,data =mydata)
        mydata = '{"state":' + str(sp5000.battery_charging_current) + ', "attributes": {"unit_of_measurement": "A", "friendly_name": "battery_charging_current"}}'
        response = post(url + "sensor.solar10", headers=headers,data =mydata)
        mydata = '{"state":' + str(sp5000.battery_capacity) + ', "attributes": {"unit_of_measurement": "%", "friendly_name": "battery_capacity"}}'
        response = post(url + "sensor.solar11", headers=headers,data =mydata)
        mydata = '{"state":' + str(sp5000.heatsink_temperature) + ', "attributes": {"unit_of_measurement": + chr(176) + "C", "friendly_name": "heatsink_temperature"}}'
        response = post(url + "sensor.solar12", headers=headers,data =mydata)
        mydata = '{"state":' + str(sp5000.pv_current) + ', "attributes": {"unit_of_measurement": "A", "friendly_name": "pv_current"}}'
        response = post(url + "sensor.solar13", headers=headers,data =mydata)
        mydata = '{"state":' + str(sp5000.pv_voltage) + ', "attributes": {"unit_of_measurement": "V", "friendly_name": "pv_voltage"}}'
        response = post(url + "sensor.solar14", headers=headers,data =mydata)
        mydata = '{"state":' + str(sp5000.battery_voltage_scc) + ', "attributes": {"unit_of_measurement": "V", "friendly_name": "battery_voltage_scc"}}'
        response = post(url + "sensor.solar15", headers=headers,data =mydata)
        mydata = '{"state":' + str(sp5000.battery_discharge_current) + ', "attributes": {"unit_of_measurement": "A", "friendly_name": "battery_discharge_current"}}'
        response = post(url + "sensor.solar16", headers=headers,data =mydata)
        mydata = '{"state":' + str(sp5000.isLineMode) + ', "attributes": {"unit_of_measurement": "", "friendly_name": "isLineMode"}}'
        response = post(url + "sensor.solar17", headers=headers,data =mydata)
        mydata = '{"state":' + str(sp5000.isBatteryMode) + ', "attributes": {"unit_of_measurement": "", "friendly_name": "isBatteryMode"}}'
        response = post(url + "sensor.solar18", headers=headers,data =mydata)
        mydata = '{"state":' + str(sp5000.inverter_fault) + ', "attributes": {"unit_of_measurement": "", "friendly_name": "inverter_fault"}}'
        response = post(url + "sensor.solar19", headers=headers,data =mydata)
        mydata = '{"state":' + str(sp5000.BusOvervolt) + ', "attributes": {"unit_of_measurement": "", "friendly_name": "BusOvervolt"}}'
        response = post(url + "sensor.solar20", headers=headers,data =mydata)
        mydata = '{"state":' + str(sp5000.BusUndervolt) + ', "attributes": {"unit_of_measurement": "", "friendly_name": "BusUndervolt"}}'
        response = post(url + "sensor.solar21", headers=headers,data =mydata)
        mydata = '{"state":' + str(sp5000.SoftStartFail) + ', "attributes": {"unit_of_measurement": "", "friendly_name": "SoftStartFail"}}'
        response = post(url + "sensor.solar22", headers=headers,data =mydata)
        mydata = '{"state":' + str(sp5000.LineFail) + ', "attributes": {"unit_of_measurement": "", "friendly_name": "LineFail"}}'
        response = post(url + "sensor.solar23", headers=headers,data =mydata)
        mydata = '{"state":' + str(sp5000.PvShort) + ', "attributes": {"unit_of_measurement": "", "friendly_name": "PvShort"}}'
        response = post(url + "sensor.solar24", headers=headers,data =mydata)
        mydata = '{"state":' + str(sp5000.InvVoltLow) + ', "attributes": {"unit_of_measurement": "", "friendly_name": "InvVoltLow"}}'
        response = post(url + "sensor.solar25", headers=headers,data =mydata)
        mydata = '{"state":' + str(sp5000.InvVolrHigh) + ', "attributes": {"unit_of_measurement": "", "friendly_name": "InvVolrHigh"}}'
        response = post(url + "sensor.solar26", headers=headers,data =mydata)
        mydata = '{"state":' + str(sp5000.OverTemp) + ', "attributes": {"unit_of_measurement": "", "friendly_name": "OverTemp"}}'
        response = post(url + "sensor.solar27", headers=headers,data =mydata)
        mydata = '{"state":' + str(sp5000.BatteryVoltHigh) + ', "attributes": {"unit_of_measurement": "", "friendly_name": "BatteryVoltHigh"}}'
        response = post(url + "sensor.solar28", headers=headers,data =mydata)
        mydata = '{"state":' + str(sp5000.BatteryVoltLow) + ', "attributes": {"unit_of_measurement": "", "friendly_name": "BatteryVoltLow"}}'
        response = post(url + "sensor.solar29", headers=headers,data =mydata)

        time.sleep(3)

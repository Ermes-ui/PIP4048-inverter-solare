import serial, time
import struct, string
import shutil
import os
from ctypes import c_ubyte, c_ushort

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
		if(CMD == -1):
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
		out_file = open("/tmp/sp5000out_B","w")
		out_file.write("grid_voltage:"+str(sp5000.grid_voltage)+"\n")
		out_file.write("grid_frequency:"+str(sp5000.grid_frequency)+"\n")
		out_file.write("ac_output_voltage:"+str(sp5000.ac_output_voltage)+"\n")
	    out_file.write("ac_output_frequency:"+str(sp5000.ac_output_frequency)+"\n")
		out_file.write("ac_output_apparent_power:"+str(sp5000.ac_output_apparent_power)+"\n")
		out_file.write("ac_output_active_power:"+str(sp5000.ac_output_active_power)+"\n")
		out_file.write("output_load_percent:"+str(sp5000.output_load_percent)+"\n")
		out_file.write("bus_voltage:"+str(sp5000.bus_voltage)+"\n")
		out_file.write("battery_voltage:"+str(sp5000.battery_voltage)+"\n")
		out_file.write("battery_charging_current:"+str(sp5000.battery_charging_current)+"\n")
		out_file.write("battery_capacity:"+str(sp5000.battery_capacity)+"\n")
		out_file.write("heatsink_temperature:"+str(sp5000.heatsink_temperature)+"\n")
		out_file.write("pv_current:"+str(sp5000.pv_current)+"\n")
		out_file.write("pv_voltage:"+str(sp5000.pv_voltage)+"\n")
		out_file.write("battery_voltage_scc:"+str(sp5000.battery_voltage_scc)+"\n")
		out_file.write("battery_discharge_current:"+str(sp5000.battery_discharge_current)+"\n")
		out_file.write("isLineMode:"+str(sp5000.isLineMode)+"\n")
		out_file.write("isBatteryMode:"+str(sp5000.isBatteryMode)+"\n")
		out_file.write("inverter_fault:"+str(sp5000.inverter_fault)+"\n")
		out_file.write("BusOvervolt:"+str(sp5000.BusOvervolt)+"\n")
		out_file.write("BusUndervolt:"+str(sp5000.BusUndervolt)+"\n")
		out_file.write("SoftStartFail:"+str(sp5000.SoftStartFail)+"\n")
		out_file.write("LineFail:"+str(sp5000.LineFail)+"\n")
		out_file.write("PvShort:"+str(sp5000.PvShort)+"\n")
		out_file.write("InvVoltLow:"+str(sp5000.InvVoltLow)+"\n")
		out_file.write("InvVolrHigh:"+str(sp5000.InvVolrHigh)+"\n")
		out_file.write("OverTemp:"+str(sp5000.OverTemp)+"\n")
		out_file.write("BatteryVoltHigh:"+str(sp5000.BatteryVoltHigh)+"\n")
		out_file.write("BatteryVoltLow:"+str(sp5000.BatteryVoltLow)+"\n")
		out_file.close()
		shutil.move("/tmp/sp5000out_B","/tmp/sp5000out")
        if os.path.exists("/etc/zabbix/externalscripts/comandi_tx"):
		if (sp5000.Comandi() == 0):
			os.remove('/etc/zabbix/externalscripts/comandi_tx')

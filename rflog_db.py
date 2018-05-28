#!/usr/bin/env python
#rflog_db.py Interface between RF Module serial interface and AdafruitIO
#---------------------------------------------------------------------------------                                                                               
# J. Evans May 2018
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR 
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, 
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE 
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, 
# WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN 
# CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.                                                       
#                                                                                  
# Revision History                                                                  
# V1.00 - Release
# -----------------------------------------------------------------------------------
#
import MySQLdb 
import serial
import time
from time import sleep
import sys
import thread
Fahrenheit = False
DEBUG = True

def dprint(message):
	if (DEBUG):
		print message

def ProcessMessageThread(value, value2, DevId, type):
	try:
			thread.start_new_thread(ProcessMessage, (value, value2, DevId, type, ) )
	except:
			print "Error: unable to start thread"

def LogTelemetry(devid, type, value):
	# log the temperature to the database
	# open database connection
	db = MySQLdb.connect(
	"localhost",
	"dblogger",
	"password",
	"sensor_logs" )
	
	if (type==3):
		if (Fahrenheit == False):
			uom="C"
		else:
			uom="F"
	else:
		uom=""
	
	# prepare a cursor object using cursor() 
	# method
	cursor = db.cursor()
	
	# build the SQL statement
	sql = "INSERT INTO telemetry_log (device_id, type, value, date, unit_of_measure) VALUES ('%s', %d, '%s', NOW(), '%c')" % (devid, type, value, uom)  
	
	dprint(sql);
	
	# Execute the SQL command
	cursor.execute(sql)
	
	# Commit your changes in the database
	db.commit()
	
	# disconnect from server
	db.close()
	
	dprint("Telemetry "+ str(devid) + ","+ str(type) + "," + str(value) + "," + uom + "," + "logged");
			
def ProcessMessage(value, value2, DevId, type):
# Notify the host that there is new data from a sensor (e.g. door open)
	try:
		dprint("Processing data : DevId="+str(DevId)+",Type="+str(type)+",Value1="+str(value)+",Value2="+str(value2))

		#Send switch sensor value to host
		if type==1:
				value=value[1:]
				if value=='OF' or value=='OFF':
						LogTelemetry(DevId,1,"Open")
				if value=='ON':
						LogTelemetry(DevId,1, "Close")

		#Send battery level to host
		if type==2:
				LogTelemetry(DevId,2, value)

		#Send temperature to host
		if type==3:
				if Fahrenheit:
						value = value*1.8+32
						value = round(value,2)
				
				LogTelemetry(str(DevId),3, str(value))

		#Send humidity to host
		if type==4:
				if Fahrenheit:
						value = value*1.8+32
						value = round(value,2)
				
				LogTelemetry(DevId,3, str(value))
				LogTelemetry(DevId,4, str(value2))
				
	except Exception as e: dprint(e)
	return(0)

def main():
        currvalue=''
        tempvalue=-999;
        
        # loop until the serial buffer is empty

        start_time = time.time()
        
        #try:
        while True:

				# declare to variables, holding the com port we wish to talk to and the speed
				port = '/dev/ttyAMA0'
				baud = 9600

				# open a serial connection using the variables above
				ser = serial.Serial(port=port, baudrate=baud)

				# wait for a moment before doing anything else
				sleep(0.2)        
				while ser.inWaiting():
						# read a single character
						char = ser.read()
						# check we have the start of a LLAP message
						if char == 'a':
								sleep(0.01)
								start_time = time.time()
								
								# start building the full llap message by adding the 'a' we have
								llapMsg = 'a'

								# read in the next 11 characters form the serial buffer
								# into the llap message
								llapMsg += ser.read(11)

								# now we split the llap message apart into devID and data
								devID = llapMsg[1:3]
								data = llapMsg[3:]
								
								dprint(time.strftime("%c")+ " " + llapMsg)
																
								if data.startswith('BUTTON'):
										sensordata=data[5:].strip('-')
										if currvalue<>sensordata or currvalue=='':
												currvalue=sensordata
												ProcessMessage(currvalue, 0, devID,1)

								if data.startswith('BTN'):
										sensordata=data[2:].strip('-')
										if currvalue<>sensordata or currvalue=='':
												currvalue=sensordata
												ProcessMessage(currvalue, 0, devID,1)

								if data.startswith('TMPA'):
										sensordata=str(data[4:].rstrip("-"))								
										currvalue=sensordata
										ProcessMessage(currvalue, 0, devID,3)
								
								if data.startswith('ANAA'):
										sensordata=str(data[4:].rstrip("-"))								
										currvalue=sensordata
										ProcessMessage(currvalue, 0, devID,3)
								
								if data.startswith('ANAB'):
										sensordata=str(data[4:].rstrip("-"))								
										currvalue=sensordata
										ProcessMessage(currvalue, 0, devID,3)
								
								if data.startswith('TMPC'):
										sensordata=str(data[4:].rstrip("-"))								
										currvalue=sensordata
										ProcessMessage(currvalue, 0, devID,3)
								
								if data.startswith('TMPB'): #Temperature followed by humidity
										sensordata=str(data[4:].rstrip("-"))								
										tempbdata=sensordata
																				
								if data.startswith('HUM'):
										sensordata=str(data[3:].rstrip("-"))								
										currvalue=sensordata
										if tempbdata<>"" and sensordata<>"":
											ProcessMessage(tempbdata, sensordata, devID,4)
											tempbdata=''
												
								# check if battery level is being sent axxBATTn.nn-
								if data.startswith('BATT'):
										sensordata=data[4:].strip('-')
										currvalue=sensordata 
										ProcessMessage(currvalue, 0, devID,2)
				elapsed_time = time.time() - start_time
				if (elapsed_time > 2):
						currvalue=""
						sensordata=""
						tempbdata=""
				sleep(0.2)
				#except:
				#        print "Error: unable to start thread"
           
if __name__ == "__main__":
        main()



   
   



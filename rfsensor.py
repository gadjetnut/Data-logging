#!/usr/bin/env python
"""
rfsensor.py v21 PrivateEyePi RF Sensor Interface
---------------------------------------------------------------------------------
 Works conjunction with host at www.privateeyepi.com                              
 Visit projects.privateeyepi.com for full details                                 
                                          
 J. Evans October 2013       
 THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR 
 IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, 
 FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE 
 AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, 
 WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN 
 CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.                                                       
                                          
 Revision History                                                                  
 V1.00 - Release
 V2.00 - Incorporation of rules functionality  
 V3.00 - Incorporated Button B logic
 V3.01 - High CPU utilization fixed
 V9    - Rule release   
 V10   - Added support for the BETA single button power saving wireless switch   
     - Functionality added for wireless temperature and humidity sensor  
 V11   - Fixed a bug with negative readings from a DHT22 sensor
 V13   - Publish temperature to LCD
 V14   - Added auto sensor creation on the server, dropped support for obsolete two button sensors
 V15   - Added token based authentication
 V16   - Removed delay to speed up serial polling
 V17   - Added functionality for Light sensors
 V18   - Fixed bug wireles switch BUTTONON and BUTTONOFF sensing same state
 V20   - Changed STATEON STATEOFF to not trigger rules or log on the server
 V21   - Added support for BME280 Temperature, Humidity and Air Pressure
 -----------------------------------------------------------------------------------
"""

import globals
import time
import sys
from threading import Thread
from alarmfunctionsr import UpdateHostThread
from time import sleep
from bme280 import process_bme_reading
from rf2serial import rf2serial
import rfsettings

def dprint(message):
  if (globals.PrintToScreen):
    print message

def ProcessMessage(value, DevId, PEPFunction):  
  global measure
  
  # Notify the host that there is new data from a sensor (e.g. door open)
 
  hostdata =[]
  hostdata.append(DevId)
  hostdata.append(value)
  if PEPFunction==22: #Battery
      MaxVoltage=3
      for z in range (0,len(globals.VoltageList)):
        if globals.VoltageList[z] == int(DevId):
          MaxVoltage=globals.MaxVoltage[z]
      hostdata.append(MaxVoltage) #MaxVoltage
  if PEPFunction==37: #Temperature or Analog
      hostdata.append(measure)
  rt=UpdateHostThread(PEPFunction,hostdata)
  
  return(0)

def DoFahrenheitConversion(value):
  global measure
  if globals.Farenheit:
    value = float(value)*1.8+32
    value = round(value,2)
    measure = '1'
  else:
    measure='0'
  return(value)
  
def remove_duplicates():
    x=0
    print "sorted deduplified queue:"
    
    #sort the queue by ID
    rfsettings.message_queue = sorted(rfsettings.message_queue, key = lambda x: (x[0]))
        
    x=0    
    while x<len(rfsettings.message_queue)-1:   
        if rfsettings.message_queue[x][0]==rfsettings.message_queue[x+1][0] and \
           rfsettings.message_queue[x][1]==rfsettings.message_queue[x+1][1]:
            #print "duplicate removed:"+rfsettings.message_queue[x][0]+rfsettings.message_queue[x][1]
            #for y in range (0,8):
            #  sys.stdout.write(str(ord(rfsettings.message_queue[x][y]))+",")
            #print ""
            rfsettings.message_queue.pop(x)
        else:
            x=x+1

    for x in range(0,len(rfsettings.message_queue)):
        print rfsettings.message_queue[x][0]+rfsettings.message_queue[x][1]

def queue_processing():
  global measure
  try:
    sensordata=""
    bme_data=""
    bme_messages=0
    start_time = time.time()
    while (True):
        if len(rfsettings.message_queue)>0 and not rfsettings.rf_event.is_set():
            remove_duplicates()
            message = rfsettings.message_queue.pop()
            devID = message[0]
            data = message[1]
            dprint(time.strftime("%c")+ " " + message[0]+message[1])
            if data.startswith('BUTTONON'):
                devID=globals.BUTTONPrefix+devID
                sensordata=0
                PEPFunction=26

            if data.startswith('STATEON'):
                devID=globals.BUTTONPrefix+devID
                sensordata=0
                PEPFunction=38

            if data.startswith('STATEOFF'):
                devID=globals.BUTTONPrefix+devID
                sensordata=1
                PEPFunction=38

            if data.startswith('BUTTONOFF'):
                sensordata=1
                PEPFunction=26

            if data.startswith('TMPA'):
                sensordata=DoFahrenheitConversion(str(data[4:].rstrip("-")))
                PEPFunction=37
            
            if data.startswith('ANAA'):
                sensordata=str(data[4:].rstrip("-"))
                sensordata=(float(sensordata)-1470)/16 #convert it to a reading between 1(light) and 48 (dark)
                sensordata=str(sensordata)
                PEPFunction=37
                measure='2'
            
            if data.startswith('ANAB'):
                devID=globals.ANABPrefix+devID
                sensordata=str(data[4:].rstrip("-"))	
                sensordata=(float(sensordata)-1470)/16 #convert it to a reading between 1(light) and 48 (dark)
                sensordata=str(sensordata)
                measure='2'
                PEPFunction=37
            
            if data.startswith('TMPC'):
                devID=globals.TMPCPrefix+devID
                sensordata=DoFahrenheitConversion(str(data[4:].rstrip("-")))
                PEPFunction=37
            
            if data.startswith('TMPB'): 
                devID=globals.TMPBPrefix+devID
                sensordata=DoFahrenheitConversion(str(data[4:].rstrip("-")))
                PEPFunction=37
                                    
            if data.startswith('HUM'):
                devID=globals.HUMPrefix+devID
                sensordata=str(data[3:].rstrip("-"))								
                PEPFunction=37
                measure='2'
                    
            if data.startswith('BATT'):
                sensordata=data[4:].strip('-')
                PEPFunction=22
         
            if data.startswith('BMP') or (bme_messages>0 and sensordata==''):
              start_time = time.time()
              if bme_messages==0:
                  bme_data=bme_data+data[5:9]
              else:
                  bme_data=bme_data+data[0:9]
              bme_messages=bme_messages+1
              
              
              if bme_messages==5:
                bme280=process_bme_reading(bme_data, devID)
                if bme280.error <> "":
                  dprint(bme280.error)
                else:
                  if bme280.temp_rt == 1:
                    ProcessMessage(DoFahrenheitConversion(round(bme280.temp,2)), devID, 37)
                  if bme280.hum_rt == 1:
                    measure='2'
                    ProcessMessage(round(bme280.hum,2), globals.HUMPrefix+devID, 37)
                  if bme280.hum_rt == 1:
                    measure='2'
                    ProcessMessage(round(bme280.press/100,1), globals.PRESPrefix+devID, 37)
                bme_messages=0;
                bme_data=""
            if sensordata <> "":
                ProcessMessage(sensordata, devID, PEPFunction)
        sensordata=""
        
        if rfsettings.event.is_set():
            break
            
        elapsed_time = time.time() - start_time
        if (elapsed_time > 5):
            start_time = time.time()-120
            bme_messages=0;
            bme_data=""

  except Exception as e: 
      template = "An exception of type {0} occurred. Arguments:\n{1!r}"
      message = template.format(type(e).__name__, e.args)
      print message
      print e
      rfsettings.event.set()
      exit()

def main():
    globals.init()
    rfsettings.init()

    a=Thread(target=rf2serial, args=())
    a.start()
    
    b=Thread(target=queue_processing, args=())
    b.start()
  
    while not rfsettings.event.is_set():
      try:
          sleep(1)
      except KeyboardInterrupt:
          rfsettings.event.set()
          break

if __name__ == "__main__":
    try:
      main()
    except Exception as e: 
      template = "An exception of type {0} occurred. Arguments:\n{1!r}"
      message = template.format(type(e).__name__, e.args)
      print message
      print e
      rfsettings.event.set()
    finally:
      rfsettings.event.set()
      exit()




   
   



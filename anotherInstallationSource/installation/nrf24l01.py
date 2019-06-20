#!/usr/bin/python

import time
import spidev
import RPi.GPIO as GPIO

GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)
GPIO.setup(27,GPIO.OUT)
GPIO.setup(24,GPIO.OUT)
GPIO.setup(19,GPIO.OUT)

spi=spidev.SpiDev()
spi.open(0,0)
spi.max_speed_hz=1000000

def wbreg(addr,data):    #Write register of NRF24L01
    temp=spi.xfer2([addr|0x20,data])
                
def initRF(chan):      #Initialise NRF24L01
    wbreg(0x03,0x02)    #Set 4 byte address
    wbreg(0x05,chan)    #Set RF Channel
    wbreg(0x06,0x26)    #Select 250kBaud 
    wbreg(0x01,0x00)    #Disble auto-ack
    temp=spi.xfer2([0x2A,0x5A,0x69,0xA5,0x96])   #Pipe 0 RX address
    temp=spi.xfer2([0x2B,0x3C,0x69,0xA5,0x96])   #Pipe 1 RX address
    wbreg(0x11,0x08)    #Rx 8 byte messages on pipe 0
    wbreg(0x12,0x08)    #Rx 8 byte messages on pipe 1
    spi.xfer2([0xE2]) #flush recieve buffer
    spi.xfer2([0xE1]) #flush transmit buffer
    
def tx(ser,idNo,code,data1,data2,pipe):
#    print("----tx Sending "+str(idNo)+" "+str(code)+" "+str(data1)+" "+str(data2)+" "+str(pipe))
    spi.xfer2([0xE1]) #flush transmit buffer
    if pipe==0:
        temp=spi.xfer2([0x30,0x5A,0x69,0xA5,0x96])  #Send on pipe 0
    else :
        temp=spi.xfer2([0x30,0x3C,0x69,0xA5,0x96])  #Send on pipe 1
    wbreg(0x00,0x2E)  #Enable CRC, 2-Byte CRC,Power up, Transmit mode,mask TX_DS interrupt?
    time.sleep(0.003)  #Wait for chip to settle
    temp = spi.xfer2([0xA0,ser & 0xFF,(ser >>8)&0xFF,idNo,code, #Load payload
                    (data1 &0xFF),(data1>>8)&0xFF,
                    (data2 &0xFF),(data2>>8)&0xFF])
    time.sleep(0.001)
    GPIO.output(27,GPIO.HIGH)  #Strobe CE to initiate transmission
    time.sleep(0.001)
    GPIO.output(27,GPIO.LOW)
    stat = 0x00
    while (stat & 0x10)==0 :     #Wait for transmission to complete
        stat = spi.xfer2([0x17,0xff])[1]
    spi.xfer2([0xE2]) #flush recieve buffer

def refresh_rx():
    GPIO.output(27,GPIO.LOW)  
    wbreg(0,0x6D)
    time.sleep(0.0001)
    wbreg(0,0x6E)
    time.sleep(0.005)
    wbreg(0,0x6F)
    GPIO.output(27,GPIO.HIGH)  #Initiate reception
    
def rx(mess_handler,exitfunc,refreshrate):
#monitor for recieved messages, calling exitfunc in between polls.  
#exitfunc calls cleanup function if it returns True, indicating this function should itself return
    refresht=time.perf_counter()
    
    while True: 
        wbreg(0x00,0x2F)  #Recieve mode
        GPIO.output(27,GPIO.HIGH)  #Initiate reception
  
        stat = 0
#        print("Entering RX")
        while (stat &0x40)==0x00 :
            if time.perf_counter()-refresht>refreshrate:
                refresh_rx()
                refresht=time.perf_counter()
            elif exitfunc(lambda:GPIO.output(27,GPIO.LOW)):
#                print("Exited RX")
#                GPIO.output(27,GPIO.LOW)  #Disable reception
                return
            stat=spi.xfer2([0xFF])[0]
        
        pipe=(stat&0x0E)>>1
        temp=0
        while (temp&1)==0:  #Process all messages in buffer
            res = spi.xfer2([0x61,0xFF,0xFF,0xFF,0xFF,0xFF,0xFF,0xFF,0xFF])
            wbreg(0x07,0x70);
            GPIO.output(27,GPIO.LOW)
            temp = spi.xfer2([0x17,0xFF])[1]
#            print("----rx recieved "+hex(res[3])+" "+hex(res[4])+" "+hex(res[5]+(res[6]<<8))+" "+hex(res[7]+(res[8]<<8))+" "+str(pipe))
            mess_handler(res[1]+(res[2]<<8),res[3],res[4],res[5]+(res[6]<<8),res[7]+(res[8]<<8),pipe)
    
def mess_handler_template(ser,idNo,code,d1,d2,pipe):
#        print("Handling :"+str(ser)+" "+str(idNo)+" "+str(code)+" "+str(d1)+" "+str(d2)+" "+str(pipe))
#        print("---")
    pass

def exitfunc(ontruereturnfunc):
    return False

def main():
    initRF(0x33)       
    time.sleep(1)
    tx(1234,3,129,1,0,1)
    rx(mess_handler_template,exitfunc,10)
        
if __name__=="__main__":
    main()

#!/usr/bin/python

import smbus
import time
import spidev
import RPi.GPIO as GPIO

code_name={ 2:"Humidity",3:"Virtual",4:"Control" }


config={}
with open("/home/pi/BUBBLnetConfig.bub","r",) as conf:
    for line in conf:
        if line[0:4]=="cfg(":
            cp=line.index(",")
            key=line[4:cp]
            config[key]=line[cp+1:-2]

rfChannel=int(config["RFchannel"])
serialNo=int(config["serial"])
period=int(config["period"])

   
bus = smbus.SMBus(1)    # 1 = /dev/i2c-1 (port I2C1)

GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)
GPIO.setup(27,GPIO.OUT)
GPIO.setup(24,GPIO.OUT)
GPIO.setup(19,GPIO.OUT)

spi=spidev.SpiDev()
spi.open(0,0)
spi.max_speed_hz=1000000

#Low order 4bits of I2C 8-bit port expander connected to HD44780U lcd driver as follows
#bit 0  RS   Data/Command
#bit 1  R/-W Read/Write
#bit 2  E    Strobe
#bit 3  Backlight Enable

addr=0x27

def lcd_byte(byte,lcd_ctl):  #Sends byte as 2 nibbles using 4 bit bus via I2C
    bus.write_byte(addr, (byte & 0xf0) | lcd_ctl)
    bus.write_byte(addr, (byte & 0xf0) | lcd_ctl |4)  #strobe high nibble
    bus.write_byte(addr, (byte & 0xf0) | lcd_ctl)
    bus.write_byte(addr, (byte & 0xf)*16 | lcd_ctl)
    bus.write_byte(addr, (byte & 0xf)*16 | lcd_ctl |4) #strobe low nibble
    bus.write_byte(addr, (byte & 0xf)*16 | lcd_ctl)
   
def lcd_init():
    lcd_ctl=0
    lcd_byte(0x33,lcd_ctl)  #Ensure bus is synchronized in 4 bit mode
    lcd_byte(0x32,lcd_ctl)
    lcd_ctl=8       #Enable Backlight
    time.sleep(0.0041) #Wait 4.1ms
    lcd_byte(0x2C,lcd_ctl)  #Home
    time.sleep(0.0015)
    lcd_byte(0x0F,lcd_ctl)      #Left to right, 2 rows
    time.sleep(0.0015)
    lcd_byte(0x06,lcd_ctl)      #Display on + cursors
    time.sleep(0.0015)
    lcd_byte(0x01,lcd_ctl)
    time.sleep(0.0015)
    
def lcd_num(num,pos,radix,ndig):
    lcd_ctl=8
    pin=pos+ndig
    while ndig>0:
        dig = num % radix
        num = num // radix
        ndig -= 1
        if dig>9:
            dig += 7
        lcd_byte(0x80|(pos+ndig),lcd_ctl)
        lcd_byte(48+dig,lcd_ctl|1)
    lcd_byte(0x80|pin,lcd_ctl)

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
    
def tx(ser,idNo,code,data1,data2,pipe):
    if pipe==0:
        temp=spi.xfer2([0x30,0x5A,0x69,0xA5,0x96])  #Send on pipe 0
    else :
        temp=spi.xfer2([0x30,0x3C,0x69,0xA5,0x96])  #Send on pipe 1
    wbreg(0x00,0x2E)  #Enable CRC, 2-Byte CRC,Power up, Transmit mode,mask TX_DS interrupt?
    time.sleep(0.003)  #Wait for chip to settle
    temp = spi.xfer2([0xA0,ser & 0xFF,(ser >>8)&0xFF,idNo,code, #Load payload
                    data1 &0xFF,(data1>>8)&0xFF,
                    data2 &0xFF,(data2>>8)&0xFF])
    time.sleep(0.001)
    GPIO.output(27,GPIO.HIGH)  #Strobe CE to initiate transmission
    time.sleep(0.001)
    GPIO.output(27,GPIO.LOW)
    stat = 0x00
    while (stat & 0x10)==0 :     #Wait for transmission to complete
        stat = spi.xfer2([0x17,0xff])[1]
       
def rx(mess_handler):
    wbreg(0x00,0x2F)  #Recieve mode
    GPIO.output(27,GPIO.HIGH)  #Initiate reception
    stat = 0
    while (stat &0x40)==0x00 :
        stat=spi.xfer2([0xFF])[0]
        
    pipe=(stat&0x0E)>>1
    temp=0
    while (temp&1)==0:  #Process all messages in buffer
        res = spi.xfer2([0x61,0xFF,0xFF,0xFF,0xFF,0xFF,0xFF,0xFF,0xFF])
        wbreg(0x07,stat);
        temp = spi.xfer2([0x17,0xFF])[1]
        GPIO.output(27,GPIO.LOW)
        mess_handler(res[1]+(res[2]<<8),res[3],res[4],res[5]+(res[6]<<8),res[7]+(res[8]<<8),pipe)
    


def handler(ser,idNo,code,d1,d2,pipe):
    print("Pipe "+str(pipe))
    print("Serial number "+str(ser))
    print("idNo="+str(idNo))
    print("code="+str(code))
    print("d1=%s"%d1)
    print("d2=%s"%d2)
    lcd_num(pipe,0,10,1)
    lcd_num(ser,2,10,5)
    lcd_num(idNo,8,10,3)
    lcd_num(code,13,10,3)
    lcd_num(d1,0x40,10,5)
    lcd_num(d2,0x48,10,5)

    
try :
    lcd_init()
    lcd_byte(0xC0,8)
    lcd_byte(79,9)
    lcd_byte(75,9)
except :
    print("LCD not Conncected")
time.sleep(1)

initRF(rfChannel)
   
count=0
while True:
    print("--- starting ---"+str(count))
    rx(handler)
    count+=1
    

 

#!/usr/bin/python

import smbus
import time
bus = smbus.SMBus(1)    # 1 = /dev/i2c-1 (port I2C1)

#Low order 4bits of I2C 8-bit port expander connected to HD44780U lcd driver as follows
#bit 0  RS   Data/Command
#bit 1  R/-W Read/Write
#bit 2  E    Strobe
#bit 3  Backlight Enable

addr=0x27
lcdOk=[False]

def lcd_byte(byte,lcd_ctl):  #Sends byte as 2 nibbles using 4 bit bus via I2C
    bus.write_byte(addr, (byte & 0xf0) | lcd_ctl)
    bus.write_byte(addr, (byte & 0xf0) | lcd_ctl |4)   #strobe high nibble
    bus.write_byte(addr, (byte & 0xf0) | lcd_ctl)
    bus.write_byte(addr, (byte & 0xf)*16 | lcd_ctl)
    bus.write_byte(addr, (byte & 0xf)*16 | lcd_ctl |4) #strobe low nibble
    bus.write_byte(addr, (byte & 0xf)*16 | lcd_ctl)
   
def lcd_init():
    try:
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
        lcdOk[0]=True
        return True
    except:
        lcdOk[0]=False
        return False
        
def old_lcd_num(num,pos,radix,ndig):
    if not lcdOk[0]:
        if not lcd_init():
            return
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

def num_str(num,radix,ndig):
    res=""
    
    while ndig>0:
        dig = num % radix
        num = num // radix
        ndig -= 1
        if dig>9:
            dig += 7
        res=str(chr(48+dig))+res
    return res
    
def lcd_mess(mess,pos):
    if not lcdOk:
        if not lcd_init():
            return
    lcd_ctl=8
    lcd_byte(0x80|pos,lcd_ctl)
    for c in mess:
        lcd_byte(ord(c),lcd_ctl|1)
    
def lcd_num(num,pos,radix,ndig):
    lcd_mess(numstr(num,radix,ndig),pos)
    


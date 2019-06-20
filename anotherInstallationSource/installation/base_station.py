#!/usr/bin/python3
import time
import sys
import RPi.GPIO as GPIO
import sqlite3
import createBubNetTables
import executeBSM
from executeBSM import BSM
import nrf24l01
from nrf24l01 import tx,rx,initRF
import hd44780u_i2c
from hd44780u_i2c import lcd_init,lcd_num,lcd_mess,num_str

db=createBubNetTables.getdb()
bsmdb=createBubNetTables.getbsmdb();
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
scriptPath=config["scriptPath"]

loglevel=2 #0=Debug 1=comms 2=Info 3=Warning 4=error 5=critical

if len(sys.argv)>1:
    if sys.argv[1][:9]=="loglevel=":
        loglevel=int(sys.argv[1][9:])

for opt in sys.argv[1:] :
    if opt.startswith("loglevel="):
        loglevel=int(opt[9:])

def log(level,mess):
    if level>=1 :
        db.execute("INSERT INTO log values((?),(?));",(time.asctime(time.gmtime()),mess))
        db.commit()
    if level<loglevel:
        return
    print("Log >"+mess)

class dispManager:
    def __init__(self):
        lcd_init()
        lcd_mess("bubblNet ph=?",0)
        lcd_mess("                ",64)
        self.messageQueue=[]
    
    def enqueue(self,item):
        self.messageQueue.insert(0,item)
    
    def dequeue(self):
        if self.messageQueue==[]:
            return None
        return self.messageQueue.pop()
        
    def report(self,mess,ind):
        self.enqueue((mess,ind))
        
    def reportNum(self,num,ind,radix,digits):
        self.report(num_str(num,radix,digits),ind)
        
dm=dispManager()

bsmspec=config["BSMs"].split(",")
testbsmspec=config["TESTBSMs"].split(",")
bsms=[]
testbsms=[]
actionQueue=[]

if bsmspec!="":
    for ms in bsmspec:
        fn=ms.split(";")
        log(0,"Loading bsm:"+str(fn[0])+" from:"+scriptPath+str(fn[1]))
        bsms.append(BSM(fn[0],scriptPath+fn[1],db,dm))

if testbsmspec!="":
    for ms in testbsmspec:
        fn=ms.split(";")
        log(0,"Loading test bsm:"+str(fn[0])+" from:"+scriptPath+str(fn[1]))
        testbsms.append(BSM(fn[0],scriptPath+fn[1],db,dm))

def getPhase():
#Return phase in units of 1/64th Sec
    t=time.time()-0.5
    res=t-period*(int(t/period)) 
    return int(64*res)
       
def getTimeErr(channel) :  #Channel is integral second-number within period
    """ Return the difference between now and Channel's phase in units of 1/64 sec """
    phase=getPhase()
    err=((phase-64*channel+period*96)%(period*64))-period*32
    log(0,"err={}".format(err))
    return err

code_name={ 2:"Humidity",3:"Virtual",128:"Control" }

def getCodeName(key):
    try:
        res=code_name[key]
    except KeyError as e:
        res="Unknown"
    return res

def point_one_percent_negative(x,max):
    no=int(((max-x)*1000.0)/max+0.5)
    return str(no // 10)+"."+str(no % 10)+"%",no
    
def processed(value,code):
    if (code==2) :
        return point_one_percent_negative(value,1023)
    if (code==3) :
        return "Mess.No."+str(value)
    if (code==-1) :
        return ("%.2f"% (value/1000.0))+"V",value
    return str(value),value

def coroutine(func):
    def start(*args,**kwargs):
        cr=func(*args,**kwargs)
        cr.send(None)
        return cr
    return start

class Remote_Sensor:
    def updatedb(self,d1,d2):
        sval,val=processed(d1,self.code)
        sbatt,batt=processed(d2,-1)
        db.execute("UPDATE readings SET svalue=(?),value=(?),batt=(?),sbatt=(?),time=(?) WHERE channel = (?);",(sval,val,batt,sbatt,time.asctime(time.gmtime()),self.idNo))
        db.commit()
        log(1,"Sensor data logged from %s"%(self.idNo))
   
    def __init__(self,idNo,code,repeat,fromdb):
        self.idNo=idNo
        self.code=code
        self.repeat=repeat*64
        self.state=self.syncing
        self.messageTimeout=0  #Cheat to allow control checking
        if not fromdb:
            db.execute("INSERT INTO readings values((?),(?),(?),(?),(?),(?),(?),(?));",
                       (time.asctime(time.gmtime()),idNo,getCodeName(code),'none',code,0,0,"Unknown"))
            db.commit()
                    
    def syncing(self,message):
        if message[0]!="message":
            return
        _,self.code,d1,d2=message
        err=getTimeErr(self.idNo)
        next=self.repeat-err
        tx(serialNo,self.idNo,self.code,next,self.repeat,1)
        self.updatedb(d1,d2)
           
    @coroutine
    def run(self):
        while True:
            event=yield
            self.state(event)
    
class Remote_Control:
    def __init__(self,idNo,code,fromdb):
        self.idNo=idNo
        self.code=code
        self.state=self.quiet
        self.messageTimeout=0
        if not fromdb:
            db.execute("INSERT INTO readings values((?),(?),(?),(?),(?),(?),(?),(?));",
                       (time.asctime(time.gmtime()),idNo,getCodeName(code),'none',code,0,0,"Unknown"))
            db.commit()

    def quiet(self,message):
        log(0,"RC_State=quiet")
        if message[0]=="Action":
            self.retry=message
            self.retries=0
            _,d1,d2=message
            log(0,"queueing control message to %s %s 129 %s %s pipe1"%(serialNo,self.idNo,d1,d2))
#            self.messageTimeout=time.perf_counter()+0.05
            self.state=self.acted
            actionQueue.insert(0,(self,serialNo,int(self.idNo),129,int(d1),int(d2),1))
#            tx(serialNo,int(self.idNo),129,int(d1),int(d2),1)
        elif message[0]=="message":
            _,code,d1,d2=message
            if code==128:
                tx(serialNo,int(self.idNo),128,int(d1),int(d2),1)
                log(0,"Changing control mode (a)")
                
    def acted(self,message):
        log(0,"RC_State=acted")
        if message[0]=="TimedOut":
            _,d1,d2=self.retry
            if self.retries<2:
                log(0,"Resending control message to %s %s 129 %s %s pipe1"%(serialNo,self.idNo,d1,d2))
                self.messageTimeout=time.perf_counter()+0.05
                actionQueue.insert(0,(self,serialNo,int(self.idNo),129,int(d1),int(d2),1))
#                tx(serialNo,int(self.idNo),129,int(d1),int(d2),1)
                self.retries+=1
            else:
                log(2,"Message failed 3 tries: %s %s 129 %s %s pipe1"%(serialNo,self.idNo,d1,d2))
                self.state=self.quiet
        elif message[0]=="message":
            _,code,data,d2=message
            if code==129:
                self.messageTimeout=0
                self.state=self.quiet
                log(0,"Control %s acknowledged d1=%x d2=%x "%(self.idNo,data,d2))
                if (data &1) == 1:
                    sval="a)On"
                else:
                    sval="a)Off"
                if (data &2)== 2:
                    sval=sval+" b)On"
                else:
                    sval=sval+" b)Off"
                sbatt,batt=processed(d2,-1)
                curs=db.cursor()
                curs.execute("UPDATE readings SET svalue=(?),value=(?),batt=(?),sbatt=(?),time=(?) WHERE channel=(?);",(sval,data,batt,sbatt,time.asctime(time.gmtime()),self.idNo))
                 #db.execute("UPDATE readings SET svalue=(?),value=(?),batt=(?),sbatt=(?),time=(?) WHERE channel = (?);",(sval,val,batt,sbatt,time.asctime(time.gmtime()),self.idNo))
                db.commit()
            elif code==128:
                log(0,"Changing control mode (b)")
                tx(serialNo,int(self.idNo),128,0,0,1)
                
        elif message[0]=="Action":
            log(4,"Remote Control %s. New Action required before previous executed"%self.idNo)
        else :
            log(4,"Remote Control %s. Unrecognised Event in Remote_Control.acted:%s"%(self.idNo,repr(message)))
           
    @coroutine
    def run(self):
        while True:
            event=yield
            log(0,"Remote control got message:%s"%repr(event))
            self.state(event)
            
sensors={}  #key is channel No, value is network-node,network-node.run() (=node management object and its handler co-routine)
            
def init_sensors():
    curs=db.cursor()
    curs.execute("SELECT channel,mode FROM readings")
    sns=curs.fetchall()
    for ch in sns:
        if int(ch[1])<128:
            node=Remote_Sensor(ch[0],ch[1],period,True)
        else:
            node=Remote_Control(ch[0],ch[1],True)
        sensors[int(ch[0])]=(node,node.run())
    curs.close()

def handle(ser,idNo,code,d1,d2,pipe):
    log(0,"Handling %s %s %s %s %s %s"%(ser,idNo,code,d1,d2,pipe))
    if ser!=serialNo :
        log(2,"wrong serial number %s"%ser)
        dm.enqueue(("ser??????",64))
    if pipe!=0 :
        return
    if idNo==0xFF :
        log(1,"Un-configured sensor/control.  Run 'sensor_config.py'")
        dm.enqueue(("unconfig.",64))
        return
    if idNo in sensors:
        node,handler=sensors[idNo]
    else:
        if code>=128:
            node=Remote_Control(idNo,code,False)
        else:
            node=Remote_Sensor(idNo,code,period,False)
        handler=node.run()
        sensors[idNo]=node,handler
    dm.enqueue(("Ch"+num_str(idNo,10,2)+" "+num_str(code,10,3)+" "+num_str(d1,16,2)+" "+num_str(d2,16,4),64))
    handler.send(("message",code,d1,d2))  
        
def getOperatingMode(db):
    curs=db.cursor()
    curs.execute("SELECT state FROM system")
    mode=curs.fetchall()
    if mode==[]:
        return "auto"
    return mode[0][0]   #Should be either test or manual
        

def exerciseControl(actionfunc):  
#call actionfunc and return True if control from database acted on,
#otherwise return False 
    log(0,"Exercising control")
    curs=db.cursor()
    curs.execute("SELECT ALL channel,value FROM control")
    conts=curs.fetchall()
    curs.close()
    if conts==[] :
        return False
    actionfunc()
    idNo,data=conts[0]
    if int(idNo) in sensors:
        _,handler=sensors[int(idNo)]
    else :
        node=Remote_Control(int(idNo),128,False)
        handler=node.run()
        sensors[int(idNo)]=node,handler
        log(3,"Unrecognised control activated %s"%idNo)
    data=int(data,0)
    mask=data>>8
    data &=0xFF
    log(2,"exerciseControl Sending action message to control %s 129 %x %x pipe1"%(idNo,data,mask))
    curs=db.cursor()
    curs.execute("DELETE FROM control WHERE channel=(?);",(idNo,))
    db.commit()
    curs.close()
    dm.enqueue(("Co"+num_str(idNo,10,2)+" "+num_str(data,16,4)+" "+num_str(mask,16,4)+"  ",64))
    handler.send(("Action",data,mask))
    return True

def bsmHandler(actionfunc):
    mode=getOperatingMode(db)
    if mode=="auto":
        for bsm in bsms:
    #        log(0,"running bsm events")
            bsm.runEvent()
    elif mode=="test":
        for bsm in testbsms:
    #        log(0,"running test bsm events")
            bsm.runEvent()
    return exerciseControl(actionfunc)   # mode=="manual":
       
class intConsts:
    def __init__(self):
        self.lastSec=0
        self.not0=True
ls=intConsts()


def idle(func):
    tdisp=dm.dequeue()
    if tdisp != None:
        mess,pos=tdisp
        lcd_mess(mess,pos)        
    t=time.perf_counter()
    for ind in sensors:
        node,handler=sensors[ind]
        if node.messageTimeout!=0 and t-node.messageTimeout>0:
            log(0,"TimedOut %s"%ind) 
            node.messageTimeout=0
            func()
            handler.send(("TimedOut",))
            return True
    s=int(t)
    if s==ls.lastSec:
        time.sleep(0.05)
        return False
        
    if (s%5==0):
        if ls.not0:
            func()
            log(1,"Sending network present message")
            log(1,"time=%s"%time.perf_counter())
            tx(serialNo,0,(s % period)//5,0,0,1)  #Send 'network present' message
            time.sleep(0.05)
            ls.not0=False
            return True
        if actionQueue!=[]:
            func()
            cont,ser,i,c,d1,d2,p=actionQueue.pop()
            log(1,"Sending control message to %s"%i)
            log(1,"time=%s"%time.perf_counter())
            cont.messageTimeout=time.perf_counter()+0.05
            tx(ser,i,c,d1,d2,p)
            return True
    dm.enqueue((num_str(s%period,10,3),13))
    ls.lastSec=s
    ls.not0=True        
    return bsmHandler(func)
    
time.sleep(1)

initRF(rfChannel)

count=0
init_sensors()
while True:
    rx(handle,idle,10)
    count+=1
    

 
 

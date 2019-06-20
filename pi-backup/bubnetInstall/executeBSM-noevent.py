#!/usr/bin/python

import time
import sqlite3
import smtplib
from smtplib import SMTP
import sys

gmxmail="BUBBLnet@gmx.com","smtp.gmx.com","pwor4581"


class MyError(Exception):
    def __init__(self,message):
        self.mess=message
    def __str__(self):
        return repr(self.mess)
        
"""
these state machines use database and rtc for all their info
current state is maintained in ram-based database
file format
#comment
variable(Name,Value)
node(State,Test,Actions,Defaults)

Test is expressions:
variables
operators (>, <, >=, <=, <>, =, AND, OR,)
built in variables
    timeofday (0..24*60*60-1 secs)
    hourofday (0..23)
    dayofweek (0..6, Mon to Sun)
    timeout (Seconds since entered state)
    sensor<n>
    button
    <number>
Actions
    control<n>=<number> 
    state=<state-name>
    mailto:<email address>=<message>
    log=<message>
    var<varname>=<expression>   
    
    
e.g.:
# Sprinkler Control Algorithm
#variable(Name,Value)
variable(dryThresh,20)
variable(detectTime,300)
variable(onTime,1800)
variable(offTime,3600)
#node(State,Test,Actions,Defaults)
node(start,1,control3=0x200;state = off,)
node(off,sensor4 < dryThresh,state = detecting,)
node(detecting,sensor4 > dryThresh,state=off,)
node(detecting,timeout > detectTime,control3=0x202;state=on,)
node(on,timeout > onTime,control3=0x200;state=waitOff,)
node(waitOff,timeout > offTime,state=off,)
  
    
"""        
def sendEmail(mail,to,subject_message):
#mail
    subject,message=subject_message
    try:
        smptObj=SMTP(mail[1])
    except Exception as e:
        return repr(e)
    try:
        smptObj.ehlo()
        smptObj.starttls()
        smptObj.login(mail[0],mail[2])
        smptObj.sendmail(mail[0],to,"Subject: "+subject+"\nTo:"+to+"\nFrom:"+mail[0]+"\n\n"+message)
        smptObj.quit()
        return "Ok"
    except Exception as f:
        smptObj.quit()
        return repr(f)

compfuncs={">":(10,lambda x,y:1 if str(x).isdigit() and str(y).isdigit() and x>y else 0),
           "<":(11,lambda x,y:1 if str(x).isdigit() and str(y).isdigit() and x<y else 0),
           ">=":(11,lambda x,y:1 if str(x).isdigit() and str(y).isdigit() and x>=y else 0),
           "<=":(11,lambda x,y:1 if str(x).isdigit() and str(y).isdigit() and x<=y else 0),
           "<>":(11,lambda x,y:1 if x!=y else 0),
           "=":(11,lambda x,y:1 if x==y else 0),
           "OR":(13,lambda x,y:1 if x==1 or y==1 else 0),
           "AND":(12,lambda x,y:1 if x==1 and y==1 else 0),
           "+":(8,lambda x,y: x+y if str(x).isdigit() and str(y).isdigit() else str(x)+"+"+str(y)), 
           "-":(8,lambda x,y: x-y if str(x).isdigit() and str(y).isdigit() else str(x)+"-"+str(y)),
           "*":(6,lambda x,y: x*y if str(x).isdigit() and str(y).isdigit() else str(x)+"*"+str(y)),
           "MOD":(6,lambda x,y: x%y if str(x).isdigit() and str(y).isdigit() else str(x)+"%"+str(y)),
           "/":(6,lambda x,y: x//y if str(x).isdigit() and str(y).isdigit() else str(x)+"/"+str(y))  }


logging=False

loglevel=5
for opt in sys.argv[1:] :
    if opt.startswith("loglevel="):
        loglevel=int(opt[9:])
        
if loglevel<=2:
    logging=True
    
class BSM:
    def log(self,mess):
        if logging:
            print("excuteBSM Log,"+self.name+": >"+mess)

    def __init__(self,name,filename,db,others):
        self.name=name
        self.vars={}
        self.nodes={}    #state:[cond,[actions if cond true],[actions if cond false]]
        self.curs=db.cursor()
        self.others=others
        with open(filename,"r",) as f:
            for line in f:
                if line.startswith("#"):
                    continue
                tokens=line.strip().split(",")
                if len(tokens)<2:
                    continue
                if tokens[0].startswith("variable("):
                    self.vars[tokens[0][9:]]=int(tokens[1].rstrip(")"))
                else :
                    if tokens[0].startswith("node("):
                        if len(tokens)<4:
                            raise MyError("Short line Error in "+filename+":"+line)
                        state=tokens[0][5:]
                        cond=self.evaluator(tokens[1])
                        #self.log("parsing actions")
                        if tokens[2].strip()=="":
                            actions=[]
                        else :
                            actions=[self.action(token.strip()) for token in tokens[2].split(";")]
                        #self.log("parsing defaults")
                        tok3=tokens[3].rstrip(")").strip()
                        if tok3=="":
                            defaultActions=[]
                        else:
                            defaultActions=[ self.action(token.strip()) for token in tok3.split(";")]
                        state=state.strip()
                        #log(actions)
                        #self.log(defaultActions)
                        
                        if state not in self.nodes:
                           self.nodes[state]=[]
                        self.nodes[state].append((cond,actions,defaultActions))
            self.getState()

    def changeState(self,newState):
        self.curs.execute("UPDATE machine SET time=(?),state=(?) WHERE mname = (?);",(int(time.time()),newState,self.name))
        self.curs.connection.commit()
        
    def getState(self): 
#Return time state entered and state
#Force into 'start' if no record existing
        self.curs.execute("SELECT time,state FROM machine WHERE mname=(?)",(self.name,))
        st=self.curs.fetchall()
        if (st==[]):
            stime=int(time.time())
            self.curs.execute("INSERT INTO machine values((?),(?),(?));",(self.name,stime,"start"))
            self.curs.connection.commit()
            return stime,"start"
        return st[0]
    
    def evalVar(self,varname): #Return value of variable
#        self.log("evalvar is evaluating "+varname)
        if (varname.strip().isdigit()):
            return int(varname)
        if varname=="timeofday":
            return int(time.time())%(24*60*60)
        if varname=="hourofday":
            return int(time.time())%(24*60*60)//3600
        if varname=="dayofweek":
            return (int(time.time())//(24*60*60)+3)%7
        if varname=="timeout":
            return int(time.time())-self.getState()[0]
        if varname.startswith("sensor"):
            self.curs.execute("SELECT value FROM readings WHERE channel=(?);",varname[6:])
            sv=self.curs.fetchall()
            if sv==[]:
                return None
            return int(sv[0][0])
        if varname == "button":
            self.curs.execute("SELECT ALL bname from button")
            bs=self.curs.fetchall()
            if bs==[]:
                return None
            self.curs.execute("DELETE ALL from button")
            self.curs.connection.commit()
            return str(bs[0][0])
        if varname in self.vars:
            return self.vars[varname]
        if varname.startswith("machine"):
            mach=varname[7:]
            if mach in self.others:
                return self.others[mach].getState()[1]
        return varname
     
    def evaluator(self,cond): #Effectively a parser for BSM event detection
        parts=cond.split()
        if len(parts)==1:
            return lambda pt=parts[0]:self.evalVar(pt)
        valfuncs=[]
        operators=[]
 #       try :
        if True:
            for part in parts:
                if part not in compfuncs:
                    valfuncs.append(lambda pt=part:self.evalVar(pt))
                else :
                    op=compfuncs[part]
                    prec,func=op
                    
                    while operators!=[] and prec>operators[-1][0]:
                        eop=operators.pop()
                        rv=valfuncs.pop()
                        lv=valfuncs.pop()
                        valfuncs.append(lambda func=eop[1],llv=lv,lrv=rv:func(llv(),lrv()))
                    operators.append(op)
#            self.log("valfuncs[0]="+str(valfuncs[0]()))
#            self.log("valfuncs[1]="+str(valfuncs[1]()))
            while operators !=[] :
                eop=operators.pop()
                rv=valfuncs.pop()
                lv=valfuncs.pop()
                valfuncs.append(lambda func=eop[1],llv=lv,lrv=rv:func(llv(),lrv()))
            return valfuncs[0]        
#        except exception:
#            print(repr(exception))
#            raise MyError("Syntax in expression:"+part)
#            return 0   
        
    def action(self,action):
        dv=action.strip().split("=")
        return dv[0].strip(),dv[1].strip()

    def perform(self,action):
        if action[0].startswith("control"):
            self.log("  inititiating messsage control "+action[0][7:]+" = "+action[1])
            self.curs.execute("INSERT INTO control values((?),(?));",(action[0][7:],action[1]))
            self.curs.connection.commit()
            return None
        if action[0]=="state":
            self.log("Changing state to "+action[1])
            self.changeState(action[1])
            return "newState"
        if action[0].startswith("mailto:"):
            addressee=action[0][7:].strip()
            message=action[1]
            self.log("Sending "+message+" to "+addressee)
            self.log(sendEmail(gmxmail,addressee,("BUBBLnet Report",message)))
            return None    
        if action[0]=="log":
            self.log(action[1])
            return None
        if action[0].startswith("var"):
            self.vars[action[0][3:]]=self.evaluator(action[1])()
            return None
        raise MyError("Unknown action:"+action[0])

    def runEvent(self):
        self.curs.execute("SELECT state FROM system")
        if self.curs.fetchall()!=[]:
            return        #Suspend operations while not in auto
        sttime,state=self.getState()
        clauses=self.nodes[state]   #cond,actions,defaults
        if clauses==None:
            raise(MyError("Unknown state in "+self.name))
        self.log("state="+state)
        for cond,actions,defaults in clauses:
#            self.log("cond="+str(cond()))
            if cond()==1:
#                self.log("cond()=1 -tested. Action="+str(actions))
                for action in actions:
                    self.log("action:"+str(action)+":")
                    if self.perform(action)=="newState":
                        return
            else:
#                self.log("cond() not =1 -tested")
                for action in defaults:
#                    self.log("defaultaction:"+str(action)+":")
                    if self.perform(action)=="newState":
                        return




#db=sqlite3.connect("/tmp/network.db")
#db.execute("CREATE TABLE IF NOT EXISTS readings (time DATETIME, channel INTEGER, mode INTEGER, svalue STRING, value INTEGER)")
#db.execute("CREATE TABLE IF NOT EXISTS machine (mname STRING, time INTEGER, state STRING)")
#db.execute("CREATE TABLE IF NOT EXISTS button (bname)")
#db.execute("CREATE TABLE IF NOT EXISTS control (channel,value)")
#db.commit()

#  
#bsm=BSM("sprinkler","/home/barney/Desktop/bubblNet/rpi-apache-sqlite-stuff/sprinkler.bsm",db)
#bsm.runEvent()

#while True:
#    bsm.runEvent()
#    query=input("query:")
#    try:
#       db.execute(query)
#    except:
#       print("bad query")
#    db.commit()
    
                          

 

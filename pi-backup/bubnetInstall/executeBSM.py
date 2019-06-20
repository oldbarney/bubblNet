#!/usr/bin/python

#executebsm version 1.0
import time
import calendar
import sqlite3
import smtplib
from smtplib import SMTP
import sys
import json

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
node(State,Test,Actions)

Test is expressions:
variables
operators (>, <, >=, <=, <>, =, AND, OR,)
built in variables
    timeofday (0..24*60*60-1 secs)
    hourofday (0..23)
    dayofweek (0..6, Mon to Sun)
    timeout (Seconds since entered state)
    sensor<n>
	sensortime<n>
    battery<n>
    button
    event<name>
    <number>
Actions
    control<n>=<number> 
    state=<state-name>
    mailto:<email address>=<message>
    log=<message>
    var<varname>=<expression> 
    event<eventname>=<expression>  
        
e.g.:
# Sprinkler Control Algorithm
#variable(Name,Value)
variable(dryThresh,20)
variable(detectTime,300)
variable(onTime,1800)
variable(offTime,3600)
#node(State,Test,Actions)
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
           "+":(8,lambda x,y: x+y if str(x).isdigit() and str(y).isdigit() else str(x)+str(y)), 
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
    
import socket
def getIPA():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        # doesn't even have to be reachable
        s.connect(('10.255.255.255', 0))
        IP = s.getsockname()[0]
    except:
        IP = '127.0.0.1'
    finally:
        s.close()
    print(IP)
    return IP


def fronttoken(expr):
#return string split into tuple of first token and rest of string
#token will be:
#   integer,
#   alpha-numeric identifier,
#   non alpha-numeric character or pair of characters,
#
    if expr=="":
        return None,""
    i=0
    while expr[:i+1].isspace():
        i+=1
    j=i+1
    if expr[i:j]=='"':
        while j<len(expr) and expr[j:j+1]!='"':
            j+=1
        return expr[i+1:j],expr[j+1:]
    if expr[i:j].isdigit():
        while expr[j:j+1].isdigit():
            j+=1
        return expr[i:j],expr[j:]
    if expr[i:j].isalpha():
        while expr[j:j+1].isalnum() or expr[j:j+1]=="_":
            j+=1
        return expr[i:j],expr[j:]
    if expr[j:j+1] in ">=":  #for >= <= <>
        j+=1
    return expr[i:j],expr[j:]

def tokenised(expr):
    res=[]
    while expr!="":
        tok,expr=fronttoken(expr)
        res.append(tok)
    return res
   
class BSM:
    ipc_events={}    #this is how machines communicate with each other
    
    sysvars={"timeofday":lambda:int(time.time())%(24*60*60),
             "hourofday":lambda:int(time.time())%(24*60*60)//3600,
             "dayofweek":lambda:(int(time.time())//(24*60*60)+3)%7,
             "ipa1":lambda:int(getIPA().split(".")[0]),
             "ipa2":lambda:int(getIPA().split(".")[1]),
             "ipa3":lambda:int(getIPA().split(".")[2]),
             "ipa4":lambda:int(getIPA().split(".")[3]),
             "ipa":lambda:getIPA()}  #more calendar functions
             
    def log(self,mess):
        if logging:
            print("excuteBSM Log,%s : >%s"%(self.name,mess))

    def __init__(self,name,filename,db,reporter):
        print("new object:"+name)
        self.name=name
        self.vars={}
        self.nodes={}    #state:[cond,[actions if cond true]]
        self.curs=db.cursor()
        self.out=reporter
        self.cursor=0
        self.digits=2
        
        if filename.endswith(".db"):
            bsmdb=sqlite3.connect(filename)
            c=bsmdb.cursor()
            c.execute("SELECT json,mode FROM bsms WHERE name=(?)",(self.name,))
            st=c.fetchall()
            if (st==[]):
                return ""
            js=json.loads(st[0][0])
            #st[0][1] is numerical code bit 0=active, bit 1=active for testing
            for v in js["vars"]:
                self.vars[v[0]]=int(v[1])
            
            for s in js["nodes"]:
                st=s["state"]
                self.nodes[st]=[]
                for cn in s["conds"]:
                    self.nodes[st].append((self.evaluator(cn["cond"].replace("&quot",'"')),[self.action(token.replace("&quot",'"')) for token in cn["acts"]]))
            self.getState()
            return
        
        
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
                        if len(tokens)<3:
                            raise MyError("Short line Error in "+filename+":"+line)
                        state=tokens[0][5:]
                        cond=self.evaluator(tokens[1])
                        #self.log("parsing actions")
                        if tokens[2].strip()=="":
                            actions=[]
                        else :
                            actions=[self.action(token.strip()) for token in tokens[2].split(";")]
                        state=state.strip()
                        if state not in self.nodes:
                           self.nodes[state]=[]
                        self.nodes[state].append((cond,actions))
                        #self.log(repr(actions))
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
        if varname in BSM.sysvars:
            return BSM.sysvars[varname]()
        if varname.strip().isdigit():
            return int(varname)
        if varname=="timeout":
            return int(time.time())-self.getState()[0]
        if varname=="cursor":
            return self.cursor
        if varname.startswith("sensortime"):
            self.curs.execute("SELECT time FROM readings WHERE channel=(?);",varname[10:])
            sv=self.curs.fetchall()
            if sv==[]:
                return -1
            return int(calendar.timegm(time.gmtime())-calendar.timegm(time.strptime(sv[0][0])))
        if varname.startswith("sensor"):
            self.curs.execute("SELECT value FROM readings WHERE channel=(?);",varname[6:])
            sv=self.curs.fetchall()
            if sv==[]:
                return None
            return int(sv[0][0])
        if varname.startswith("battery"):
            self.curs.execute("SELECT batt FROM readings WHERE channel=(?);",varname[7:])
            sv=self.curs.fetchall()
            if sv==[]:
                return None
            return int(sv[0][0])
        if varname.startswith("event"):
#            self.log("checking for event "+varname[5:]+" in "+repr(BSM.ipc_events))
            return BSM.ipc_events.pop(varname[5:],None)
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
        return varname
     
    def evaluator(self,cond): #Effectively a parser for BSM event detection
#        oparts=cond.split()
        parts=tokenised(cond)
#        print("oparts="+repr(oparts))
#        print("parts="+repr(parts))
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
        print("action from "+self.name)    
        dv=action.strip().split("=")
        return dv[0].strip(),dv[1].strip()

    def perform(self,action):
#Perform action then return "newState" if action results in state change, otherwise return None
#        self.log("---performing:"+repr(action))
        if action[0].startswith("control"):
            self.log("  inititiating messsage control "+action[0][7:]+" = "+action[1])
            self.curs.execute("INSERT INTO control values((?),(?));",(action[0][7:],action[1]))
            self.curs.connection.commit()
            return None
        if action[0]=="state":
            self.log("Changing state to "+action[1])
            self.changeState(action[1])
            return "newState"
        if action[0]=="cursor":
            self.cursor=self.evaluator(action[1])()
            return None    
        if action[0]=="digits":
            self.digits=self.evaluator(action[1])()
            return None    
        if action[0]=="outdec":
            self.out.reportNum(int(self.evaluator(action[1])()),self.cursor,10,self.digits)
            self.cursor+=self.digits
            return None    
        if action[0]=="outhex":
            self.out.reportNum(int(self.evaluator(action[1])()),self.cursor,16,self.digits)
            self.cursor+=self.digits
            return None    
        if action[0]=="outchar":
            self.out.report(chr(self.evaluator(action[1])()),self.cursor)
            self.cursor+=1
            return None    
        if action[0]=="outstring":
            s=str(self.evaluator(action[1])())
            self.out.report(s,self.cursor)
            self.cursor+=len(s)
            return None    
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
        if action[0].startswith("event"):
#            self.log("SENDING EVENT "+repr(action[0][5:])+"="+repr(action[1]))
            BSM.ipc_events[action[0][5:]]=self.evaluator(action[1])()
#            self.log(" event stack is "+repr(BSM.ipc_events))
            return None        
            
        raise MyError("Unknown action:"+action[0])

    def runEvent(self):
#        self.curs.execute("SELECT state FROM system")
#        if self.curs.fetchall()!=[]:
#            return        #Suspend operations while not in auto
        sttime,state=self.getState()
        clauses=self.nodes[state]   #cond,actions
        if clauses==None:
            raise(MyError("Unknown state in "+self.name))
        self.log("state="+state)
        for cond,actions in clauses:
#            self.log("cond="+str(cond()))
            if cond()==1:
#                self.log("cond()=1 -tested. Action="+str(actions))
                for action in actions:
                    self.log("action:"+str(action)+":")
                    if self.perform(action)=="newState":
                        return
            
class Reporter:
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
    def __init__(self):
        pass

    def report(self,mess,index):
        print("= = = = Reporting {} @ {:d}".format(mess,index))

    def reportNum(self,num,index,radix,ndig):
        self.report(Reporter.num_str(num,radix,ndig),index)               

def main(): #This is used to test the module
    reporter=Reporter()
    
    def checkControls():
        curs=db.cursor()
        curs.execute("SELECT ALL channel,value FROM control")
        conts=curs.fetchall()
        curs.close()
        if conts==[] :
            return
        idNo,data=conts[0]
        print("Test Acknowledge Control {} = 0x{}".format(Reporter.num_str(idNo,10,2),data))
        curs=db.cursor()
        curs.execute("DELETE FROM control WHERE channel=(?);",(idNo,))
        db.commit()
        curs.close()

    global logging
    logging=True

    global db

    import createBubNetTables
    db=createBubNetTables.getdb()
    
    print("Testing Module executeBSM.py")
    print("The following output should be generated by the program")
    print("""
=========================
This has to be put in yet
=========================
        """)
    bsma=BSM("test","/home/barney/Desktop/bubblNet/installation/test.bsm",db,reporter)
    bsmb=BSM("testfire","/home/barney/Desktop/bubblNet/installation/testfire.bsm",db,reporter)

    while True:
        checkControls()
        bsma.runEvent()
        bsmb.runEvent()
        time.sleep(0.5)
  
if __name__=="__main__":
    main()

                          

 

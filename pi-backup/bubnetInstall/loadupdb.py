#!/usr/bin/python3
import time
import sys
import sqlite3
import createBubNetTables

bsmdb=createBubNetTables.getbsmdb()
config={}

with open("/home/barney/Desktop/bubblNet/installation/BUBBLnetConfig.bub","r",) as conf:
    for line in conf:
        if line[0:4]=="cfg(":
            cp=line.index(",")
            key=line[4:cp]
            config[key]=line[cp+1:-2]

scriptPath=config["scriptPath"]


bsmspec=config["BSMs"].split(",")
testbsmspec=config["TESTBSMs"].split(",")
bsms=[]
testbsms=[]

class BSM:
    def __init__(self,name,filename):
        print("loading:"+filename)
        self.name=name
        self.vars={}
        self.nodes={}    #state:[cond,[actions if cond true]]
        
        with open(filename,"r",) as f:
            for line in f:
                if line.startswith("#"):
                    continue
                tokens=line.strip().replace('"','&qut').split(",")
                print(tokens)
                if len(tokens)<2:
                    continue
                if tokens[0].startswith("variable("):
                    self.vars[tokens[0][9:]]=tokens[1].rstrip(")")
                else :
                    if tokens[0].startswith("node("):
                        if len(tokens)<3:
                            raise MyError("Short line Error in "+filename+":"+line)
                        state=tokens[0][5:].strip()
                        cond=tokens[1]

                        if len(tokens)>3:
                            tok2=tokens[2].strip()
                        else:
                            tok2=tokens[2].rstrip(")").strip()
                            
                        if tok2=="":
                            actions='[""]'
                        else :
                            actions=[token.strip() for token in tok2.split(";")]
                            actions="["+",".join(['"%s"'%a for a in actions])+"]"
                        if state not in self.nodes:
                           self.nodes[state]=[]
                        self.nodes[state].append((cond,actions))

    def getCond(self,state):
        conds=self.nodes[state]
        return ','.join(['{"cond":"%s","acts":%s}'%(c[0],c[1]) for c in conds])

    def getJSON(self):
        res='{"name":"'+self.name+'", "vars":['
        res+=",".join(['["%s","%s"]'%(v,self.vars[v]) for v in self.vars])
        res+='],"nodes":['

        res+=','.join(['{"state":"%s","conds":[%s]}'%(s,self.getCond(s)) for s in self.nodes])
        return res+"]}"


scriptPath="/home/barney/Desktop/bubblNet/installation/"


#deliberatelybroken

if bsmspec!="":
    for ms in bsmspec:
        fn=ms.split(";")
        print("loading:"+fn[0])        
        bsm=BSM(fn[0],scriptPath+fn[0]+".bsm")
        print("loaded:"+fn[0])  
        bsms.append(bsm)
        bsmdb.execute("INSERT INTO bsms values((?),(?),(?));",(fn[0],bsm.getJSON(),1))
        print(bsm.getJSON())


if testbsmspec!="" :
    for ms in testbsmspec:
        fn=ms.split(";")
        print("loading:"+fn[0])        
        bsm=BSM(fn[0],scriptPath+fn[0]+".bsm")
        print("loaded:"+fn[0]) 
        testbsms.append(bsm)
        bsmdb.execute("INSERT INTO bsms values((?),(?),(?));",(fn[0],bsm.getJSON(),2))
        print(bsm.getJSON())



bsmdb.commit()

        
 
 

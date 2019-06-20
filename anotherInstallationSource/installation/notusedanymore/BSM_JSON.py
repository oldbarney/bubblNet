#!/usr/bin/python

import sys
import json

logging=False






class BSM:
    def __init__(self,name,filename):
        self.name=name
        self.vars={}
        self.nodes={}    #state:[cond,[actions if cond true],[actions if cond false]]
        
        with open(filename,"r",) as f:
            for line in f:
                if line.startswith("#"):
                    continue
                tokens=line.strip().replace('"','\\"').split(",")
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
                            actions=[]
                        else :
                            actions=[token.strip() for token in tok2.split(";")]
                        actions="["+",".join(['\n        "%s"'%a for a in actions])+"]"
                        if state not in self.nodes:
                           self.nodes[state]=[]
                        self.nodes[state].append((cond,actions))

    def getCond(self,state):
        conds=self.nodes[state]
        return ','.join(['\n    ["%s",%s]'%(c[0],c[1]) for c in conds])

    def getJSON(self):
        res='{"name":"'+self.name+'",\n "vars":['
        res+=",".join(['\n  ["%s","%s"]'%(v,self.vars[v]) for v in self.vars])
        res+='\n ],\n"nodes":['

        res+=','.join(['\n  ["%s",[%s]]'%(s,self.getCond(s)) for s in self.nodes])
        return res+"\n]}"

def gettextfile(filename):
    res=""
    with open(filename,"r",) as f:
        for line in f:
            res+=line
    return res


def main(): #This is used to test the module
#    print("Testing Module BSM_JSON.py")
    tf=gettextfile("/home/barney/Desktop/bubblNet/installation/tt")
    print(tf)
    ob=json.loads(tf)
    print(ob)
                       
if __name__=="__main__":
    main()



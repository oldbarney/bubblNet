#!/usr/bin/python
import sys
import os
import cgi
import cgitb


def BSMtext(name,file):
    res="<h3>"+name+"</h3>"
    with open(file,"r") as f:
        for line in f:
            res=res+line+"<br />"
    return res

def getData():
    config={}
    res=""
    with open("/home/pi/BUBBLnetConfig.bub","r",) as conf:
        for line in conf:
            if line[0:4]=="cfg(":
                cp=line.index(",")
                key=line[4:cp]
                config[key]=line[cp+1:-2]

    scriptPath=config["scriptPath"]
    bsmspec=config["BSMs"].split(",")
    testbsmspec=config["TESTBSMs"].split(",")
    if bsmspec!="":
        for ms in bsmspec:
            fn=ms.split(";")
            res=res+BSMtext(str(fn[0]),scriptPath+str(fn[1]))+"<hr />"
    res=res+"<h2>Test machines</h2><br />"            
    if testbsmspec!="":
        for ms in testbsmspec:
            fn=ms.split(";")
            res=res+BSMtext(str(fn[0]),scriptPath+str(fn[1]))+"<hr />"
    return res
    
def printHTMLhead(title):
    print("<head>")
    print("   <title>")
    print(title)
    print("   </title>")
    print("</head>")
	
def main():
    cgitb.enable(display=0,logdir="/tmp")
    records=getData()
    print("Content-type: text/html\n\n")
    print("<html>")
    printHTMLhead("BUBBLnet Active BSMs")
    print("<body>")
    print("<h2>BUBBLnet Active BSMs</h2>")
    print("<br />")
    print(records)
    print("</body>")
    print("</html>")
    sys.stdout.flush()

if __name__=="__main__":
    main()





    

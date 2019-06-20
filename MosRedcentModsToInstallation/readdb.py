#!/usr/bin/python
#This has been superceded by bubblNet.py  2nd Oct 2016
import sqlite3
import sys
import os
import cgi
import cgitb
import time

db=sqlite3.connect("/tmp/network.db")
"""
db.execute("CREATE TABLE IF NOT EXISTS readings (time DATETIME, channel INTEGER, smode STRING, svalue STRING, mode INTEGER, value INTEGER)")
db.execute("CREATE TABLE IF NOT EXISTS machine (mname STRING, time INTEGER, state STRING)")
db.execute("CREATE TABLE IF NOT EXISTS button (bname STRING)")
db.execute("CREATE TABLE IF NOT EXISTS control (channel INTEGER,value INTEGER)")
db.execute("CREATE TABLE IF NOT EXISTS system (state STRING)")
db.execute('INSERT INTO readings VALUES("now",2,"dummy","100%",1,1000);')
db.execute('INSERT INTO readings VALUES("now",1,"Control","100%",3,1);')
db.commit()
"""

def getData():
    curs=db.cursor()
    curs.execute("SELECT * FROM readings")
    rows=curs.fetchall()
    return rows

def printHTMLhead(title):
    print("<head>")
    print("   <title>")
    print(title)
    print("   </title>")
    print("</head>")
	
def createTable(rows):
    res="<table border=1><tr><th>Time</th><th>Channel</th><th>Type</th><th>Value</th><th>Battery</th></tr>" 
    for row in rows:
        res+="<tr><td>{0}</td><td>{1}</td><td>{2}</td><td>{3}</td><td>{4}</td></tr>\n".format(str(row[0]),str(row[1]),str(row[2]),str(row[3]),str(row[7]))
    res+="</table>"
    return res

def createMachineTable():
    curs=db.cursor()
    curs.execute("SELECT * FROM machine")
    rows=curs.fetchall()
    curs.close()
    res="<table border=1><tr><th>Machine</th><th>Time</th><th>State</th></tr>" 
    for row in rows:
        res+="<tr><td>{0}</td><td>{1}</td><td>{2}</td></tr>\n".format(str(row[0]),time.ctime(row[1]),str(row[2]))
    res+="</table>"
    return res

def buttonWrapper(text,link):
    return "<a href="+link+' style="text-decoration:none"><input type="button" value="'+text+'"/></a>'

manBut=buttonWrapper("Switch to Manual Operation","readdb.py?manual")
autoBut=buttonWrapper("Switch to Automatic Operation","readdb.py?automatic")

def controlHTML(channel):
    return "<p>Control "+str(channel)+" : a)"+\
        buttonWrapper("On","readdb.py?manual:"+str(channel)+":0x101")+\
        "&nbsp;"+\
        buttonWrapper("Off","readdb.py?manual:"+str(channel)+":0x100")+\
        "&nbsp;&nbsp;b)"+\
        buttonWrapper("On","readdb.py?manual:"+str(channel)+":0x202")+\
        "&nbsp;"+\
        buttonWrapper("Off","readdb.py?manual:"+str(channel)+":0x200")+"</p>"

def ctbuttons():
    curs=db.cursor()
    curs.execute("SELECT channel FROM readings WHERE smode='Control'")
    res=""
    for c in curs.fetchall():
        res=res+controlHTML(int(c[0]))
    curs.close()
    return res

def getQ():
    query=os.environ["QUERY_STRING"]
    return query
#    return sys.argv[1]
   
def getButtons():
    query=getQ()
    curs=db.cursor()
    curs.execute("SELECT state FROM system;")
    manual=curs.fetchall()!=[]
    curs.close()
    qparts=query.split(":")
    if manual:
        if query=="automatic":
            db.execute("DELETE FROM system;")
            db.commit()
            return"<br /><br />Changed to Automatic Operation &nbsp;"+buttonWrapper("&nbsp;Ok&nbsp;","readdb.py")
        elif qparts[0]=="manual" and len(qparts)==3:
            db.execute("INSERT INTO control values((?),(?));",(qparts[1],qparts[2]))
            db.commit()
            qp2=int(qparts[2],0)
            if (qp2 & 0x100)==0x100:
                st="a) set to "+("On " if (qp2&1)==1 else "Off ")+"&nbsp;"
            else:
                st=""
            if (qp2 & 0x200)==0x200:
                st=st+"b) set to "+("On " if (qp2&2)==2 else "Off ")
            return"<h3>Manual Operation</h3>Control&nbsp;"+qparts[1]+"&nbsp;"+st+\
                "&nbsp;"+buttonWrapper("Ok","readdb.py")
    else :
        if query=="manual":
            db.execute('INSERT INTO system values("manual");')
            db.commit()
            return"<br /><br />Changed to Manual Operation &nbsp;"+buttonWrapper("&nbsp;Ok&nbsp;","readdb.py")

    if manual:   
        return "<h3>Manual Operation</h3>"+ctbuttons()+autoBut
    return "<h3>Automatic Operation</h3>"+manBut
       
def main():
#    cgitb.enable(display=0,logdir="/tmp")
    cgitb.enable()

    records=getData()
    buttons=getButtons()
    print("Content-type: text/html\n\n")
    print("<html>")
    printHTMLhead("BUBBLnet Humidity monitor")
    print("<body>")
    print("<h2>BUBBLnet Humidity monitor</h2>")
    if getQ()=="machine":
        print("<br />")
        print(createMachineTable())
    else:    
        if len(records) !=0 :
            table=createTable(records)
            print(table)
        else :
            print("*** No Data, sorry ***")
        print(buttons)
    print("<br />")
    print(buttonWrapper("View BSM programs","readbsm.py"))
    print("</body>")
    print("</html>")
    sys.stdout.flush()
    db.close()

if __name__=="__main__":
    main()





    

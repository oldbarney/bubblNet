#!/usr/bin/python
import sqlite3
import sys
import os
import cgi
import cgitb
import time

db=sqlite3.connect("/tmp/network.db")
"""
db.execute("CREATE TABLE IF NOT EXISTS readings (time DATETIME, channel INTEGER, smode STRING, svalue STRING, mode INTEGER, value INTEGER, batt INTEGER, sbatt STRING  )")
db.execute("CREATE TABLE IF NOT EXISTS machine (mname STRING, time INTEGER, state STRING)")
db.execute("CREATE TABLE IF NOT EXISTS button (bname STRING)")
db.execute("CREATE TABLE IF NOT EXISTS control (channel INTEGER,value INTEGER)")
db.execute("CREATE TABLE IF NOT EXISTS system (state STRING)")
db.execute("CREATE TABLE IF NOT EXISTS log (time DATETIME, event STRING)")

db.execute('INSERT INTO readings VALUES("now",2,"dummy","100%",1,1000);')
db.execute('INSERT INTO readings VALUES("now",1,"Control","100%",3,1);')
db.commit()
"""

def getData():
    curs=db.cursor()
    curs.execute("SELECT * FROM readings")
    rows=curs.fetchall()
    curs.close()
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

def buttonWrapper(prompt,text,key):
    return """<form action="bubblnet.py" method="POST">%s<input type="submit" name="%s" value="%s"></form>"""%(prompt,key,text)

manBut=buttonWrapper("","Switch to Manual Operation","manbut")
autoBut=buttonWrapper("","Switch to Automatic Operation","autobut")
testBut=buttonWrapper("","Switch to Test Mode","testbut")
machBut=buttonWrapper("","View State-Machines","machine")

def getControl(fi):
    keys=fi.keys()
    for key in keys:
        if key.startswith("cont"):
            return key[4:].split(";")
    return None

def controlHTML(no):
    return  """<p><form action="bubblnet.py" method="POST">
        Control %s:&nbsp;a)&nbsp;
        <input type="submit" name="cont%s;0x101" value='On'>
        <input type="submit" name="cont%s;0x100" value='Off'>
        &nbsp;b)&nbsp;
        <input type="submit" name="cont%s;0x202" value='On'>
        <input type="submit" name="cont%s;0x200" value='Off'>
        </form></p>"""%(str(no),str(no),str(no),str(no),str(no))
  
def ctbuttons():
    curs=db.cursor()
    curs.execute("SELECT channel FROM readings WHERE smode='Control'")
    res=""
    for c in curs.fetchall():
        res=res+controlHTML(int(c[0]))
    curs.close()
    return res
  
def getButtons(fi):
    curs=db.cursor()
    curs.execute("SELECT state FROM system;")
    mode=curs.fetchall()
    curs.close()
    if mode==[]:
        mode="auto"
    else :
        mode=mode[0][0]
    
    conts=getControl(fi)
    if mode=="manual":
    
    
        if "testbut" in fi:
            db.execute("DELETE FROM system;")
            db.execute('INSERT INTO system values("test");')
            db.commit()
            return "<br /><br />"+buttonWrapper("Changed to Test Mode &nbsp;","&nbsp;Ok&nbsp;","ok")
            
    
        if "autobut" in fi:
            db.execute("DELETE FROM system;")
            db.commit()
            return "<br /><br />"+buttonWrapper("Changed to Automatic Operation &nbsp;","&nbsp;Ok&nbsp;","ok")
        elif conts!=None:
            db.execute("INSERT INTO control values((?),(?));",(conts[0],conts[1]))
            db.commit()
            qp2=int(conts[1],0)
            if (qp2 & 0x100)==0x100:
                st="a) set to "+("On " if (qp2&1)==1 else "Off ")+"&nbsp;"
            else:
                st=""
            if (qp2 & 0x200)==0x200:
                st=st+"b) set to "+("On " if (qp2&2)==2 else "Off ")
            return"<h3>Manual Operation</h3>"+buttonWrapper("Control&nbsp;"+conts[0]+"&nbsp;"+st+"&nbsp;","Ok","readdb.py")
    else :
        if "manbut" in fi:
            db.execute('DELETE FROM machine;')
            db.execute("DELETE FROM system;")
            db.execute('INSERT INTO system values("manual");')
            db.commit()
            return"<br /><br />"+buttonWrapper("Changed to Manual Operation &nbsp;","&nbsp;Ok&nbsp;","readdb.py")

    if mode=="manual":   
        return "<h3>Manual Operation</h3>"+ctbuttons()+autoBut+testBut+machBut
    if mode=="test":
        return "<h3>(Automatic) Test-Mode</h3>"+manBut+machBut
    return "<h3>Automatic Operation</h3>"+manBut+machBut
       
def main():
    cgitb.enable()
##    records=getData()
    fi=cgi.FieldStorage()
##    buttons=getButtons(fi)

    print("Content-type: text/html\n\n")
    print("<html>")
    printHTMLhead("BUBBLnet Sensor and Control Network")
    print("<body>")
    print("<h2>BUBBLnet Sensor and Control Network</h2>")
    
    if "save" in fi:
        print(repr(fi))
        txt=fi.getfirst("bsmText")
        fn=fi.getfirst("filename")
        with open("/home/pi/"+fn,"w") as f:
            f.write(txt)
            f.close
        print("Text saved as "+fn)
        print("<br /><br />"+buttonWrapper("","&nbsp;Back&nbsp;","ok"))
    else:
        print("""<input type="button" value="Refresh Page" onClick="window.location.href=window.location.href"><br /><br />""")
        print("<p>")
        print(repr(fi))
        print("""
        <form action="bubblnetEd.py" method="POST">
                Filename:<input type="text" name="filename"><br />
                <textarea type="textarea rows=20 cols="80" id="bsmprog" name="bsmText"> 
        """)
        with open("/home/pi/BUBBLnetConfig.bub","r",) as conf:
            st=""
            for line in conf:
                st=st+line
            print(st)
            
        print("""
                </textarea> <br />
                <input type="submit" name="save" value="Save Edits">      
            </form>""")
        print("</p>")
    print("<br />")
    print("</body>")
    print("</html>")
    sys.stdout.flush()
    db.close()

if __name__=="__main__":
    main()



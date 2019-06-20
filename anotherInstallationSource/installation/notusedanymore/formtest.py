#!/usr/bin/python
import sqlite3
import sys
import os
import cgi
import cgitb
import time

def printHTMLhead(title):
    print("<head>")
    print("   <title>")
    print(title)
    print("   </title>")
    print("</head>")

form="""

<form action="/cgi-bin/formtest0.py" method="POST">
    <input type="submit" value="Go-Back"> 
    <input type="hidden" name="hello" value="Nesia">
    <input type="submit" name="againbutton" value="And-Again">
</form>
"""	



def main():
    cgitb.enable(display=0,logdir="/tmp")
    print("Content-type: text/html\n\n")
    print("<html>")
    printHTMLhead("BUBBLnet Humidity monitor")
    print("<body>")
    print(form)
    print("Hello content is this")
    print("<br />")
    print("</body>")
    print("</html>")
    sys.stdout.flush()
  
if __name__=="__main__":
    main()



#!/usr/bin/python
import sqlite3
import sys
import os
import cgi
import cgitb
import time


filename="formtest0.py"

def printHTMLhead(title):
    print("<head>")
    print("   <title>")
    print(title)
    print("   </title>")
    print("</head>")
	
	
	


forma="""

<form action="formtest0.py" method="POST">
    <input type="submit" name="formb" value="Formb" extravalue="that"> 
    <input type="submit" name="forma" value="Forma"> 
    <input type="submit" name="forma" value="Secondforma">

</form>
"""

def button(text,key):
    return """
<form action="%s" method="POST">
    <input type="submit" name="%s" value="%s"> 
</form>
    """%(filename,key,text)


def ctlrow(no):
    return """<form action=%s method='POST'><input type='hidden' name='channel' value=%s
        <input type="submit name="control" value='a%s On'>
        <input type="submit name="control" value='a%s Off'>
        <input type="submit name="control" value='b%s On'>
        <input type="submit name="control" value='b%s Off'>
        </form>"""%(filename,str(no),str(no),str(no),str(no),str(no))
        
def main():
    cgitb.enable(display=0,logdir="/tmp")
    print("Content-type: text/html\n\n")
    print("<html>")
    printHTMLhead("BUBBLnet Humidity monitor")
    print("<body>")
    fi=cgi.FieldStorage()
   
    print(button("this","keykey"))
   
    if "formb" in fi :
        print("<h2>This form b</h2>")
    elif "forma" in fi :
        print("<h2>This form a</h2>")
    else :
        print("not a form a or b")
    print(forma)
    print("<br />")
    print(sys.argv)
    print("<br />")
    print("<br />")
    print(cgi.print_form(fi))
    print(repr(fi))
    print("</body>")
    print("</html>")
    sys.stdout.flush()
  
if __name__=="__main__":
    main()


#window.location.reload(false); 


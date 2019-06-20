#!/usr/bin/python3
import sys
import time
import sqlite3
import cgi
import cgitb
import os

if os.path.isfile("/home/barney/survey.db"):
    home="/home/barney/"
else:
    home="/home/pi/"

db=sqlite3.connect(home+"survey.db")

def getPlot(channel):
    return  ("data.addColumn('number','Time'); data.addColumn('number','Channel{0}');".format(channel))



def getData(channel,period):
#period =   today - last 24hrs
#           yesterday
#           
#           week - last 7 days (midday and midnight)
#           month  last 31 days (midday)

    hour=int(time.mktime(time.gmtime()))//3600
    today=hour//24
    hour=hour%24
    curs=db.cursor()

    if period=="today":
        curs.execute("SELECT ALL h0,h1,h2,h3,h4,h5,h6,h7,h8,h9,h10,h11,h12,h13,h14,h15,h16,h17,h18,h19,h20,h21,h22,h23 FROM survey WHERE day=(?)",(today,))
        dt=curs.fetchall()
        curs.close()
        if dt==[] :
            return "[0,0]"
        return ",".join(["["+str(i)+","+str(dt[0][i]/1000)+"]" for i in range(0,24) if dt[0][i]!=-1])
    if period=="yesterday":
        curs.execute("SELECT ALL h0,h1,h2,h3,h4,h5,h6,h7,h8,h9,h10,h11,h12,h13,h14,h15,h16,h17,h18,h19,h20,h21,h22,h23 FROM survey WHERE day=(?)",(today-1,))
        dt=curs.fetchall()
        curs.close()
        if dt==[] :
            return "[0,0]"
        return ",".join(["["+str(i)+","+str(dt[0][i]/1000)+"]" for i in range(0,24)if dt[0][i]!=-1])
    if period=="last_week":
        curs.execute("SELECT ALL h0,h12 FROM survey WHERE day BETWEEN (?) AND (?) ORDER BY day",(today-7,today-1))
    elif period=="last_month":
        curs.execute("SELECT ALL h0,h12 FROM survey WHERE day BETWEEN (?) AND (?) ORDER BY day",(today-31,today-1))
    else:
        curs.execute("SELECT ALL h0,h12 FROM survey ORDER BY day")
    dt=curs.fetchall()
    curs.close()
    if dt==[] :
        return "[0,0]"
    ldt=len(dt)
    left=",".join(["["+str(i-ldt)+","+str(dt[i][0]/1000)+"]" for i in range(0,ldt) if dt[i][0]!=-1])
    right=",".join(["["+str(i-ldt+0.5)+","+str(dt[i][1]/1000)+"]" for i in range(0,ldt) if dt[i][1]!=-1])
    if left=="":
        return right
    if right=="":
        return left
    return ",".join([left,right])

def getHTML(channel,period):
    return  """Content-type: text/html\n\n


<html>
  <head>
    <script type="text/javascript" src="https://www.gstatic.com/charts/loader.js"></script>
    <script type="text/javascript">
      google.charts.load('current', {{'packages':['corechart']}});
      google.charts.setOnLoadCallback(drawChart);

      function drawChart() {{
        var data = new google.visualization.DataTable();
        {1}
        data.addRows([{0}]);

        var options = {{
          title: '{2}',
          curveType: 'line',
          legend: {{ position: 'bottom' }},
          vAxis: {{ viewWindowMax:1, viewWindowMin:0, minValue: 0.01, maxValue: 0.99 ,format: 'percent'}},
        
        }};

        var chart = new google.visualization.LineChart(document.getElementById('chart'));

        chart.draw(data, options);
      }}
    </script>
  </head>
  <body>
    <div id="chart" style="width: 900px; height: 500px"></div>
    <br /><form action="bubblnet.py" method="POST"><input type="submit" value="Back to control panel"/></form>'
  </body>
</html>
        """.format(getData(channel,period),getPlot(channel),"Humidity {}".format(period))

def getKeyName(key,fi):
    name=""
    keys=fi.keys()
    for k in keys:
        if k.startswith(key):
            name=k[len(key):]
            break
    return name    

def main():


    cgitb.enable()
    
    fi=cgi.FieldStorage()

    key=getKeyName("survey",fi)
    print(getHTML(4,key))
    sys.stdout.flush()
    db.close()


if __name__=="__main__":
    main()
   



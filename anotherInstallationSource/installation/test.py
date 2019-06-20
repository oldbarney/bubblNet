import executeBSM
from executeBSM import BSM
import sqlite3

db=sqlite3.connect("/tmp/network.db")

db.execute("CREATE TABLE IF NOT EXISTS readings (time DATETIME, channel INTEGER, smode STRING, svalue STRING, mode INTEGER, value INTEGER)")
db.execute("CREATE TABLE IF NOT EXISTS machine (mname STRING, time INTEGER, state STRING)")
db.execute("CREATE TABLE IF NOT EXISTS button (bname STRING)")
db.execute("CREATE TABLE IF NOT EXISTS control (channel INTEGER,value INTEGER)")
db.execute("CREATE TABLE IF NOT EXISTS system (state STRING)")
db.execute("CREATE TABLE IF NOT EXISTS log (time DATETIME, event STRING)")
db.commit() 

bsm1=BSM("test","/home/barney/Desktop/bubblNet/installation/testa.bsm",db)
bsm2=BSM("test","/home/barney/Desktop/bubblNet/installation/testa.bsm",db)
print("=======NOW RUNNING MACHINE ==========")
bsm.runEvent()
bsm.runEvent()
bsm.runEvent()




        

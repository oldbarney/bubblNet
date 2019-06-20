#!/usr/bin/python3

import sqlite3

def getdb():
    db=sqlite3.connect("/tmp/network.db")
    db.execute("CREATE TABLE IF NOT EXISTS readings (time DATETIME, channel INTEGER, smode STRING, svalue STRING, mode INTEGER, value INTEGER, batt INTEGER, sbatt STRING  )")
    db.execute("CREATE TABLE IF NOT EXISTS machine (mname STRING, time INTEGER, state STRING)")
    db.execute("CREATE TABLE IF NOT EXISTS button (bname STRING)")
    db.execute("CREATE TABLE IF NOT EXISTS control (channel INTEGER,value INTEGER)")
    db.execute("CREATE TABLE IF NOT EXISTS system (state STRING)")
    db.execute("CREATE TABLE IF NOT EXISTS log (time DATETIME, event STRING)")
    db.commit() 
    return db
    
def getbsmdb():
    db=sqlite3.connect("/tmp/bsmdb.db")
    db.execute("CREATE TABLE IF NOT EXISTS bsms(name STRING,json STRING,mode INTEGER)")
    db.commit()
    return db
    
def main():
    getdb()
    
    
if __name__=="__main__":
    main()
   



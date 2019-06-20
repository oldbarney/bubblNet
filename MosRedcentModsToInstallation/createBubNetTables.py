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
    db.execute("CREATE TABLE IF NOT EXISTS machineSpec (mname STRING,state STRING,line INTEGER,cond STRING,actions STRING,defaults STRING)")
    db.execute("CREATE TABLE IF NOT EXISTS machineVar (mname STRING,varname STRING,varvalue STRING)")
    db.commit() 
    return db
    
def main():
    getdb()
    
    
if __name__=="__main__":
    main()
   



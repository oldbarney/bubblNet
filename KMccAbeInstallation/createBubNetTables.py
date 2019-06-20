#!/usr/bin/python3
#version 1.0
import sqlite3

def getSurveydb():
    db=sqlite3.connect("/home/pi/survey.db")
    db.execute("CREATE TABLE IF NOT EXISTS survey(channel INTEGER,day INTEGER,h0 INTEGER DEFAULT -1,h1 INTEGER DEFAULT -1,h2 INTEGER DEFAULT -1,h3 INTEGER DEFAULT -1,h4 INTEGER DEFAULT -1,h5 INTEGER DEFAULT -1,h6 INTEGER DEFAULT -1,h7 INTEGER DEFAULT -1,h8 INTEGER DEFAULT -1,h9 INTEGER DEFAULT -1,h10 INTEGER DEFAULT -1,h11 INTEGER DEFAULT -1,h12 INTEGER DEFAULT -1,h13 INTEGER DEFAULT -1,h14 INTEGER DEFAULT -1,h15 INTEGER DEFAULT -1,h16 INTEGER DEFAULT -1,h17 INTEGER DEFAULT -1,h18 INTEGER DEFAULT -1,h19 INTEGER DEFAULT -1,h20 INTEGER DEFAULT -1,h21 INTEGER DEFAULT -1,h22 INTEGER DEFAULT -1,h23 INTEGER DEFAULT -1)")  
    db.commit()
    return db


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
    db=sqlite3.connect("/home/pi/bsmdb.db")
    db.execute("CREATE TABLE IF NOT EXISTS bsms(name STRING,json STRING,mode INTEGER)")
    db.commit()
    return db
    
def main():
    getdb()
    
    
if __name__=="__main__":
    main()
   



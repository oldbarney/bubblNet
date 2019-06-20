#!/usr/bin/python3
ob='{name:"nam",nodes:[{cond:"cnd",acts:["this=that","outmessage=&quothello&quot"]}]}'

def main():
    print(JSON.stringify(JSON.parse(ob)))


if __name__=="__main__":
    main()

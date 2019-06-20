#!/usr/bin/python

import sys
import os
import cgi
import cgitb
import sqlite3
import json


def asrelation(jsontext):
    js=json.loads(jsontext)
    res="#BSM "+js["name"]+"\n"
    res+="#variable(Name,Value)\n"
    for v in js["vars"]:
        res+="variable("+v[0]+","+v[1]+")\n"
    res+="#node(State,Cond,Actions)\n"
    for s in js["nodes"]:
        for c in s["conds"]:
            actions=";".join(c["acts"])
            res+="node("+s["state"]+","+c["cond"]+","+actions+")\n"
    return res            

def getModeButs(name,mode):
    if (mode & 1)==1:
        auto='<td><input type="submit" class="option" value="&times;" name="auto'+name+'"/></td>'
    else:
        auto='<td><input type="submit" class="nooption" value="&times;" name="auto'+name+'"/></td>'
    if (mode & 2)==2:
        test='<td><input type="submit" class="option" value="&times;" name="test'+name+'"/></td>'
    else:
        test='<td><input type="submit" class="nooption" value="&times;" name="test'+name+'"/></td>'
    return "<tr><td>"+name+'</td><td><input type="submit" value="Edit" name="edit'+name+'"/>&nbsp;<input type="submit" value="Delete" name="delete'+name+'"/></td>'+auto+test+'</tr>'
 
def getMachineButs():
    db=sqlite3.connect("/home/pi/bsmdb.db")
    cs=db.cursor()
    cs.execute("SELECT name,mode FROM bsms;")
    ms=cs.fetchall()
    cs.close()
    res='<table><tr><th>BSM Name</th><th>Action</th><th>Auto</th><th>Test</th></tr><form action="bsmeditor.py" method="POST">'+''.join([getModeButs(name[0],int(name[1])) for name in ms])+'</form></table>'
    res+='<br /><form action="bsmeditor.py" method="POST"><input type="submit" value="New" name="newbsm"/></form>'
    res+='<h3>Locally stored</h3>'
    res+='<span id="lbtablerows"></span>' 
    res+='<br /><form action="bubblnet.py" method="POST"><input type="submit" value="Back to control panel"/></form>'
    return res+'<script>console.log("gettingloadbuts");document.getElementById("lbtablerows").innerHTML=getLoadButs();console.log(getLoadButs());console.log("gottenloadbuts");</script>'


def hasEditBut(fi):
    keys=fi.keys()
    for key in keys:
        if key.startswith("edit"):
            return True
    return False

def getJS():
    return """<script>
function debugOb(ob) {
    if (ob==null) {
        console.log("debugOb>null");
    }
    var x;
    for (x in ob) {
        console.log("debugOb."+x+"="+ob[x]);
    }
}

function addVar() {
    addUndoer({op:"delv",vi:0});
    bsmsrc.vars.push(["-",""]);
    renew();
}

function getLoadButs() {
    var res="";
    var name="";
   
    for (var key in localStorage) { 
        console.log("localStorageKey="+key);
        if (key.startsWith("BSM")) {
            name=key.substring(3);
            console.log("Got name='"+name+"'");
            res+=name+"&nbsp;&nbsp;&nbsp;&nbsp;<form action='bsmeditor.py' method='POST'><input type='submit' value='Load' name='Load"+localStorage.getItem(key)+"'/></form>";
        }
    }
    return res;
}

function ncondrows(stat) {
    var res=0;
    var i;
    for (i=0;i<stat.conds.length;i++) {
       res+=stat.conds[i].acts.length;
    }
    return res;
}

function editable(bsm) {
    //debugOb(bsm);
    var res="<table border='2'><tr><th>BSM Name</th></tr><tr><td id='bsmname'>"+bsm.name+"</td></tr></table><br />";
    res += '<table id="vars" border="1"><tr><th>Variable</th><th>Value</th></tr>';
    var vars = bsm.vars;
    var i;
    for (i=0;i<vars.length;i++) {
        res+='<tr><td vi="'+i+'">'+vars[i][0]+'</td><td vvi="'+i+'">'+vars[i][1]+'</td></tr>';
    }
    res += '</table>';
    if (vars.length==0) res += '<br /><button onclick="addVar();">Add Variable</button><br />'
    res += '<br />';
    res += '<table id="states" border="1"><th>State</th><th>Condition(s)</th><th>Action(s)</th></tr>';
  
    var stats=bsm.nodes;
    var j,k;
    var stat,conds,cond,acts;
//console.log("DEBUGGING");        
//debugOb(stats);        
//console.log("DEBUGGING-DONE");        
    for (i=0;i<stats.length;i++) {
        stat=stats[i];
        conds=stat.conds;
        cond=conds[0];
//console.log("state="+stat[0]+" rsp="+ncondrows(stat));
        acts=cond.acts;
//console.log("cond="+cond.cond+" rowsp="+acts.length);
       res+='<tr><td rowspan="'+ncondrows(stat)+'" stat="'+i+'">'+stat.state+'</td><td rowspan="'+acts.length+'" stat="'+i+'" cond="0">'+cond.cond.replace(/&qut/g,'"')+'</td><td stat="'+i+'" cond="0" act="0">'+acts[0].replace(/&qut/g,'"')+'</td></tr>';

//console.log("act="+acts[0]);      
        for (k=1;k<acts.length;k++) {
//console.log("act="+acts[k]);
                 res+='<tr><td stat="'+i+'" cond="0" act="'+k+'">'+acts[k].replace(/&qut/g,'"')+'</td></tr>';
        }
        for (j=1;j<conds.length;j++) {
            cond=conds[j];
            acts=cond.acts;
//console.log("cond="+cond[0]+" rowsp="+acts.length);
//console.log("act="+acts[0]);            

            res+='<tr><td rowspan="'+acts.length+'" stat="'+i+'" cond="'+j+'">'+cond.cond.replace(/&qut/g,'"')+'</td><td stat="'+i+'" cond="'+j+'" act="0">'+acts[0]+'</td></tr>';
            for (k=1;k<acts.length;k++) {
//console.log("act="+acts[k]);            
                res+='<tr><td stat="'+i+'" cond="'+j+'" act="'+k+'">'+acts[k].replace(/&qut/g,'"')+'</td></tr>';
            }
        }
    }        
    res += '</table>';
    return res;
}

function getCell(vi,vvi,si,ci,ai) {
    var cells=document.getElementsByTagName("td");
    var i;
    var cell;
    if (vi!=null) {
        for (i=0;i<cells.length;i++) {
            if (cells[i].getAttribute("vi")==vi) return cells[i];
        }
        return null;
    }
    if (vvi!=null) {
        for (i=0;i<cells.length;i++) {
            if (cells[i].getAttribute("vvi")==vvi) return cells[i];
        }
        return null;
    }
    if (si==null) {
        for (i=0;i<cells.length;i++) {
            if (cells[i].getAttribute("id")=="bsmname") 
                return cells[i];
        }
        return null;
    }
    
    if (ci==null) {
        for (i=0;i<cells.length;i++) {
            if (cells[i].getAttribute("stat")==si) return cells[i];
        }
        return null;
    }
    if (ai==null) {
        for(i=0;i<cells.length;i++) {
            cell=cells[i];
            if (cell.getAttribute("stat")==si && cell.getAttribute("cond")==ci) return cell;
        }
        return null;
    }
    for(i=0;i<cells.length;i++) {
        cell=cells[i];
        if (cell.getAttribute("stat")==si && cell.getAttribute("cond")==ci &&cell.getAttribute("act")==ai) return cell;
    }
    return null;
}

function changeCellContents(src,vi,vvi,si,ci,ai,txt) {
    var cell;
    cell=getCell(vi,vvi,si,ci,ai);
    while (cell.hasChildNodes()) cell.removeChild(cell.childNodes[0]);
    cell.innerHTML=txt;
    if (oldText==txt) return;
    
    if (vi!=null) {
        addUndoer({op:"updv",vi:vi,name:oldText});
        src.vars[Number(vi)][0]=txt;
    } else if (vvi!=null) {
        addUndoer({op:"updvv",vi:vvi,value:oldText});
        src.vars[Number(vvi)][1]=txt;
    } else if (si==null) {
        addUndoer({op:"updn",name:oldText});
        src.name=txt;
    } else if (ci==null) {
        addUndoer({op:"upds",si:si,state:oldText});
        src.nodes[Number(si)].state=txt;
    } else if (ai==null) {
        addUndoer({op:"updc",si:si,ci:ci,cond:oldText});
        src.nodes[Number(si)].conds[Number(ci)].cond=txt;
    } else {
        addUndoer({op:"upda",si:si,ci:ci,ai:ai,act:oldText});
        src.nodes[Number(si)].conds[Number(ci)].acts[Number(ai)]=txt;
    }
}

function getButton(txt,func) {
    var b=document.createElement("BUTTON");
    b.innerHTML=txt;
    b.addEventListener('click', function(e) {
        e = e || window.event;
        func(e.target || e.srcElement);
    });
    return b;
}

var bsmsrc;
var oldText;    //
var editedCell;  //Non-null if being edited
var undolist=[];
var savable;

function updateCell(cell,txt) {
//console.log("updating..");
//debugOb(cell);
    var vi=cell.getAttribute("vi");
    var vvi=cell.getAttribute("vvi");
    var st=cell.getAttribute("stat");
    var cn=cell.getAttribute("cond");
    var ac=cell.getAttribute("act");
//console.log("typeofvi="+vi.type);
    changeCellContents(bsmsrc,vi,vvi,st,cn,ac,txt);
}

function unHighlightCell(cell) {
    if (cell==null) {
//console.log("cannot unhighlight null cell");
        return;
    }
    cell.setAttribute("class","selectable");
    if (cell.childNodes.length==0 || cell.childNodes[0].nodeName=='#text') return;
    if (cell.childNodes[0].nodeName=="INPUT") {
        updateCell(cell,cell.childNodes[0].getAttribute("value"));
    } else console.log("Error here, cannot unhighlight cell"+cell.nodeName);
    
}

var keyListener=function(e) {
    e = e || window.event;
    var t = e.target || e.srcElement;
    if (t.nodeName != "INPUT") return;
    var c = t.parentNode;   
    if (e.keyCode == 27) {
//console.log("Esc pressed");
        updateCell(c,oldText);
        unHighlightCell(c);
    } else if (e.keyCode == 13) {
//console.log("Enter pressed");
        updateCell(c,c.childNodes[0].value);
        unHighlightCell(c);
    }  
};

function cellType(cell) {
//returns from "var","val","stat","cond","act"
    if (cell.getAttribute("vi")) return "var";
    if (cell.getAttribute("vvi")) return "val";
    if (cell.getAttribute("act")) return "act";
    if (cell.getAttribute("cond")) return "cond";
    if (cell.getAttribute("stat")!=null) return "stat";
    console.log("Unknown cell type:"+cell.nodeName);
    return "unk";
}

var undos=[];

var undoKeyListener=function(e) {
// console.log("keypress "+e.charCode);   
    
    if (e.charCode == 90 || e.charCode == 122) {  //ctrl z
        undo();
    }
}

function addUndoer(undoer,cont) {
    if (cont) undoer.cont=true;
    undos.push(JSON.stringify(undoer));
}

//undoer functions
// inss  si,state,cond,act
// dels  si
// insc  si,ci, cond,act
// delc  si,ci
// insa  si,ci,ai,act
// dela  si,ci,ai
// upds  si,state
// updc  si,ci,cond
// upda  si,ci,ai,act
// insv  vi,name,value
// delv  var vi
// updv  var vi,vname
// updvv vi,val
// updn name

function undo() {

    if (undos.length==0) {
        window.alert("End of undo-records");
        return;
    }
//    var i
//    for (i=0;i<undos.length;i++)
//        console.log("undo="+undos[i]);
    
    do {
        var jsn=undos.pop();
        var instr=JSON.parse(jsn);

//console.log("undoer"+jsn);
    
        if (instr.op=="dels") {
            bsmsrc.nodes.splice(instr.si,1);
        } else if (instr.op=="delc") {
            bsmsrc.nodes[instr.si].conds.splice(instr.ci,1);
        } else if (instr.op=="dela") {
            bsmsrc.nodes[instr.si].conds[instr.ci].acts.splice(instr.ai,1);
        } else if (instr.op=="delv") {
            bsmsrc.vars.splice(instr.vi,1);
        } else if (instr.op=="upds") {
            bsmsrc.nodes[instr.si].state=instr.state;
        } else if (instr.op=="updc") {
            bsmsrc.nodes[instr.si].conds[instr.ci].cond=instr.cond;
        } else if (instr.op=="upda") {
            bsmsrc.nodes[instr.si].conds[instr.ci].acts[instr.ai]=instr.act;
        } else if (instr.op=="updv") {
            bsmsrc.vars[instr.vi][0]=instr.name;
        } else if (instr.op=="updvv") {
            bsmsrc.vars[instr.vi][1]=instr.value;
        } else if (instr.op=="updn") {
            bsmsrc.name=instr.name;
        } else if (instr.op=="inss") {
            bsmsrc.nodes.splice(instr.si,0,{state:instr.state,conds:[{cond:instr.cond,acts:[instr.act]}]}); 
        } else if (instr.op=="insc") {
            bsmsrc.nodes[instr.si].conds.splice(instr.ci,0,{cond:instr.cond,acts:[instr.act]}); 
        } else if (instr.op=="insa") {
            bsmsrc.nodes[instr.si].conds[instr.ci].acts.splice(instr.ai,0,instr.act);
        } else if (instr.op=="insv") {
            bsmsrc.vars.splice(instr.vi,0,[instr.name,instr.value]);
        } else if (instr.op=="sws") {
            var temp=bsmsrc.nodes[instr.si-1];
            bsmsrc.nodes[instr.si-1]=bsmsrc.nodes[instr.si];
            bsmsrc.nodes[instr.si]=temp;
        } else if (instr.op=="swc") {
            var temp=bsmsrc.nodes[instr.si].conds[instr.ci-1];
            bsmsrc.nodes[instr.si].conds[instr.ci-1]=bsmsrc.nodes[instr.si].conds[instr.ci];
            bsmsrc.nodes[instr.si].conds[instr.ci]=temp;
        } else if (instr.op=="swa") {
            var temp=bsmsrc.nodes[instr.si].conds[instr.ci].acts[instr.ai-1];
            bsmsrc.nodes[instr.si].conds[instr.ci].acts[instr.ai-1]=bsmsrc.nodes[instr.si].conds[instr.ci].acts[instr.ai];
            bsmsrc.nodes[instr.si].conds[instr.ci].acts[instr.ai]=temp;
        } else if (instr.op=="swv") {
            var temp=bsmsrc.vars[instr.vi-1];
            bsmsrc.vars[instr.vi-1]=bsmsrc.vars[instr.vi];
            bsmsrc.vars[instr.vi]=temp;
        } else if (instr.op=="pass") {
        } else {
            window.alert("unrecognised undo op:"+op);
            debugOb(instr);
        }
//console.log("JSON nodes:"+JSON.stringify(bsmsrc.nodes));
    } while (instr.cont);
    renew(); 
}

function swapUpCell(cell) {
    var typ = cellType(cell);
    if (typ == "stat") {
        var ind = cell.getAttribute("stat");
        if (ind<1) return false;
        addUndoer({op:"sws",si:ind});
        var temp=bsmsrc.nodes[ind-1];
        bsmsrc.nodes[ind-1]=bsmsrc.nodes[ind];
        bsmsrc.nodes[ind]=temp;
        renew();
    } else if (typ == "cond") {
        var si = cell.getAttribute("stat");
        var ci = cell.getAttribute("cond");
        if (ci<1) return false;
        addUndoer({op:"swc",si:si,ci:ci});
        var temp=bsmsrc.nodes[si].conds[ci-1];
        bsmsrc.nodes[si].conds[ci-1]=bsmsrc.nodes[si].conds[ci];
        bsmsrc.nodes[si].conds[ci]=temp;
        renew();
    } else if (typ == "act") {
        var si = cell.getAttribute("stat");
        var ci = cell.getAttribute("cond");
        var ai = cell.getAttribute("act");
        if (ai<1) return false;
        addUndoer({op:"swa",si:si,ci:ci,ai:ai});
        var temp=bsmsrc.nodes[si].conds[ci].acts[ai-1];
        bsmsrc.nodes[si].conds[ci].acts[ai-1]=bsmsrc.nodes[si].conds[ci].acts[ai];
        bsmsrc.nodes[si].conds[ci].acts[ai]=temp;
        renew();
    } else if (typ == "var") {
        var vi = cell.getAttribute("vi");
        if (vi<1) return false;
        addUndoer({op:"swv",vi:vi});
        var temp=bsmsrc.vars[vi-1];
        bsmsrc.vars[vi-1]=bsmsrc.vars[vi];
        bsmsrc.vars[vi]=temp;
        renew();
    } else if (typ == "val") {
        var vi = cell.getAttribute("vvi");
        if (vi<1) return false;
        var temp=bsmsrc.vars[vi-1];
        bsmsrc.vars[vi-1]=bsmsrc.vars[vi];
        bsmsrc.vars[vi]=temp;
        renew();
    } 
}

function addCell(cell,tag) {
    var typ = cellType(cell);
    if (typ == "stat") {
        var si = Number(cell.getAttribute("stat"));
        var blank={state:tag,conds:[{cond:tag,acts:[tag]}]};
        addUndoer({op:"dels",si:si});
        bsmsrc.nodes.splice(si,0,blank); 
        renew();

    } else if (typ == "cond") {
        var si = Number(cell.getAttribute("stat"));
        var ci = Number(cell.getAttribute("cond"));
        var blank = {cond:tag,acts:[tag]};
        addUndoer({op:"delc",si:si,ci:ci});
        bsmsrc.nodes[si].conds.splice(ci,0,blank);
        renew();
    } else if (typ == "act") {
        var si = Number(cell.getAttribute("stat"));
        var ci = Number(cell.getAttribute("cond"));
        var ai = Number(cell.getAttribute("act"));
        var blank=tag;
        addUndoer({op:"dela",si:si,ci:ci,ai:ai});
        bsmsrc.nodes[si].conds[ci].acts.splice(ai,0,blank);
        renew();
    } else if (typ == "var") {
        var vi = Number(cell.getAttribute("vi"));
        var blank=[tag,""];
        addUndoer({op:"delv",vi:vi});
        bsmsrc.vars.splice(vi,0,blank);
        renew();
    } else if (typ == "val") {
        var vi = Number(cell.getAttribute("vvi"));
        var blank=[tag,""];
        addUndoer({op:"delv",vi:vi});
        bsmsrc.vars.splice(vi,0,blank);
        renew();
    } else
    console.log("type identified as :"+typ);
}

function delCell(cell) {
    var typ = cellType(cell);
    if (typ == "stat") {
        var si = Number(cell.getAttribute("stat"));
        if (bsmsrc.nodes.length<=1) {
            window.alert("deleting this cell is not possible");
            return;
        }
        addUndoer({op:"pass"});
        var ci=bsmsrc.nodes[si].conds.length;
        while (ci>1) {
            ci--;
            var ai=bsmsrc.nodes[si].conds[ci].acts.length;
            while (ai>1) {
                ai--;
                addUndoer({op:"insa",si:si,ci:ci,ai:ai,act:bsmsrc.nodes[si].conds[ci].acts[ai]},true);
            }
            addUndoer({op:"insc",si:si,ci:ci,cond:bsmsrc.nodes[si].conds[ci].cond,act:bsmsrc.nodes[si].conds[ci].acts[0]},true);
        }
        
        var ai=bsmsrc.nodes[si].conds[0].acts.length;
        while (ai>1) {
            ai--;
            addUndoer({op:"insa",si:si,ci:0,ai:ai,act:bsmsrc.nodes[si].conds[0].acts[ai]},true);
            
        }
        addUndoer({op:"inss",si:si,state:bsmsrc.nodes[si].state,cond:bsmsrc.nodes[si].conds[0].cond,act:bsmsrc.nodes[si].conds[0].acts[0]},true);
        
        bsmsrc.nodes.splice(si,1); 
        renew();

    } else if (typ == "cond") {
        var si = Number(cell.getAttribute("stat"));
        var ci = Number(cell.getAttribute("cond"));
        if (bsmsrc.nodes[si].conds.length<=1) {
            window.alert("deleting this cell is not possible");
            return;
        }
        
        addUndoer({op:"pass"});
        var ai = Number(bsmsrc.nodes[si].conds[ci].acts.length);
        while (ai>1) {
            ai--;
            addUndoer({op:"insa",si:si,ci:ci,ai:ai,act:bsmsrc.nodes[si].conds[0].acts[ai]},true);
        }
        addUndoer({"op":"insc",si:si,ci:ci,cond:bsmsrc.nodes[si].conds[0].cond,act:bsmsrc.nodes[si].conds[ci].acts[0]},true);
        
        bsmsrc.nodes[si].conds.splice(ci,1);
        renew();
    } else if (typ == "act") {
        var si = Number(cell.getAttribute("stat"));
        var ci = Number(cell.getAttribute("cond"));
        var ai = Number(cell.getAttribute("act"));
        if (bsmsrc.nodes[si].conds[ci].acts.length<=1) {
            window.alert("deleting this cell is not possible");
            return;
        }
        addUndoer({op:"insa",si:si,ci:ci,ai:ai,act:bsmsrc.nodes[si].conds[ci].acts[ai]});
        bsmsrc.nodes[si].conds[ci].acts.splice(ai,1);
        renew();
    } else if (typ == "var") {
        var vi = cell.getAttribute("vi");
        if (bsmsrc.vars.length<=1) {
            window.alert("deleting this cell is not possible");
            return;
        }
        addUndoer({op:"insv",name:bsmsrc.vars[vi][0],value:bsmsrc.vars[vi][1],vi:vi});
        bsmsrc.vars.splice(vi,1);
        renew();
    } else if (typ == "val") {
        var vi = Number(cell.getAttribute("vvi"));
        if (bsmsrc.vars.length<=1) {
            window.alert("deleting this cell is not possible");
            return;
        }
        bsmsrc.vars.splice(vi,1);
        renew();
    } else
    console.log("type identified as :"+typ);
}

function commitCell(e) {
    var cell=e.parentNode;   
//console.log("affirming");
    updateCell(cell,cell.childNodes[0].value);
    unHighlightCell(cell);
    enableSave();
}

function revertCell(e) { 
    var cell=e.parentNode;  
//console.log("reverting");
    updateCell(cell,oldText);
    unHighlightCell(cell);
}

function makeCellEditable(cell) {
    editedCell=cell;
    cell.setAttribute("class","sel");
    oldText=cell.textContent;
    var x = document.createElement("INPUT");
    x.setAttribute("type", "text");
    x.setAttribute("value", oldText);
    x.onkeypress=keyListener;
    while (cell.hasChildNodes()) cell.removeChild(cell.childNodes[0]);
    cell.appendChild(x);
}

function editCell(cell,name) {
    unHighlightCell(editedCell);
    makeCellEditable(cell);
    if (!name) {
        cell.appendChild(getButton("+",function(e){ 
            var pcell=e.parentNode;
            revertCell(e);
            addCell(pcell,"-");
        }));
        cell.appendChild(getButton("^",function(e){ 
            var pcell=e.parentNode;
            revertCell(e);
            swapUpCell(pcell);
 //         makeCellEditable(pcell);
        }));
        cell.appendChild(getButton("-",function(e){ 
            var pcell=e.parentNode;
            revertCell(e);
            delCell(pcell);
        }));
    }
    cell.appendChild(document.createElement("BR"));
    cell.appendChild(getButton("Ok",commitCell));
    cell.appendChild(getButton("Esc",revertCell));
}

var clickListener=function(e) {
    e = e || window.event;
    var t=e.target || e.srcElement;
console.log("click on :"+t.nodeName);    
console.log("name="+t.getAttribute("name"));    
    if (t.nodeName!="TD" || t.getAttribute("disabled")!=undefined) {
//console.log("nodeName not TD");
        
        return;  
    }
    editCell(t,t.getAttribute("id")=="bsmname");
}

document.addEventListener('click',clickListener );
document.addEventListener('keypress',undoKeyListener);

function renew() { 
    document.getElementById("bsm").innerHTML=editable(bsmsrc);
    enableSave();
}

function enableSave() {
    savable=JSON.stringify(dequote(bsmsrc));
    dest=document.getElementById("bsmsave");
    dest.setAttribute("value","Save "+bsmsrc["name"]);
    dest.setAttribute("name",savable);
    console.log("enabledSaveAs"+bsmsrc["name"]);
}

function dequote(bsm) {
    var si;
    var ci;
    var ai;
    var st;
    var cn;
    for (si=0;si<bsm["nodes"].length;si++) {
        st=bsm["nodes"][si];
        for (ci=0;ci<st["conds"].length;ci++) {
            cn=st["conds"][ci];    
//            console.log("adjusting cond:"+cn["cond"]);
            cn.cond=cn.cond.replace(/"/g,"&qut");
            var as=cn.acts;
            for (ai=0;ai<as.length;ai++) {
//                console.log("adjusting act:"+as[ai]);
                as[ai]=as[ai].replace(/"/g,"&qut");
            }
        }
    }
    return bsm;
}

function xmlrqlistener() {
    console.log(this.responseText);
}

function sendText(callback) {
    var rawFile = new XMLHttpRequest();
    rawFile.addEventList
    var toSend=JSON.stringify(dequote(bsmsrc));
    rawFile.overrideMimeType("text/plain");
    rawFile.open("PUT", toSend, true);
    rawFile.onreadystatechange = function() {
        if (rawFile.readyState === 4 && rawFile.status == "200") {
            callback(rawFile.responseText);
        }
    };
    rawFile.send(null);
}

</script> """

def getButtons():
    res="<br /><button onclick='undo();'>Undo</button>&nbsp;&nbsp;&nbsp;&nbsp;"
    res+='<a class="button" href="/bsmhelp.html">Help</a><br /><br />'
    res+='<form action="bsmeditor.py" method="POST"><input type="submit" value="Save" id="bsmsave" /></form>'
    res+='<form action="bsmeditor.py" method="POST"><input type="submit" value="Exit (no save)" name="editBSM" /></form>'
    return res

def getKeyName(key,fi):
    name=""
    keys=fi.keys()
    for k in keys:
        if k.startswith(key):
            name=k[len(key):]
            break
    return name    

def getAutoName(fi):
    name=""
    keys=fi.keys()
    for key in keys:
        if key.startswith("auto"):
            print("<script>console.log('autobuttonpressed')</script>")        
            name=key[4:]
            break
    return name    

def getTestName(fi):
    name=""
    keys=fi.keys()
    for key in keys:
        if key.startswith("test"):
            name=key[4:]
            break
    return name    

def getSaveName(fi):
    name=""
    keys=fi.keys()
    for key in keys:
        if fi[key].value.startswith("Save"):
            name=fi[key].value[5:]
            break
    return name    

def getEdName(fi):
    name=""
    keys=fi.keys()
#    print(repr(fi.keys))
    for key in keys:
        if key.startswith("edit"):
            name=key[4:]
            break
    return name    

def getEditor(fi):
    name=getEdName(fi)
    if (name==""):
        name=getSaveName(fi)
    if (name==""):
        return "no editor"
    db=sqlite3.connect("/home/pi/bsmdb.db")
    curs=db.cursor()
    curs.execute("SELECT json,mode FROM bsms WHERE name=(?);",(name,))
    recs=curs.fetchall()
    curs.close()
#    print("name="+name)
#    print(repr(recs))
#    print("debugged")
    prg=recs[0][0]
#    print(prg)
    return '<script> var bsmtext='+"'"+prg+"';"+" bsmsrc=JSON.parse(bsmtext);</script>"
  
def newEditor():
    return '<script>bsmsrc={name:"new",vars:[["-","-"]],nodes:[{state:"-",conds:[{cond:"-",acts:["-"]}]}]};</script>'

def save(name,text):
    print("<script> console.log('saving-"+name+"');</script>")
    db=sqlite3.connect("/home/pi/bsmdb.db")   
    curs=db.cursor()
    curs.execute("SELECT mode FROM bsms WHERE name = (?);",(name,))
    recs=curs.fetchall()
    if (recs==[]):
        curs.execute("INSERT into bsms VALUES((?),(?),(?));",(name,text,0))
    else:
        curs.execute("UPDATE bsms SET json=(?) WHERE name = (?);",(text,name))
    db.commit()
    db.close()
    loc=open("/home/pi/"+name+".bsm","w")
    loc.write(asrelation(text))
    loc.close()
    print("<script>localStorage.setItem('BSM"+name+"','"+text+"');</script>")

def changeMode(name,value):
    print("<script> console.log('changingmode-"+name+"');</script>")
    db=sqlite3.connect("/home/pi/bsmdb.db") 
    curs=db.cursor()
    curs.execute("SELECT mode FROM bsms WHERE name=(?);",(name,))
    recs=curs.fetchall()  
    newmode=int(recs[0][0])^value
    curs.execute("UPDATE bsms SET mode=(?) WHERE name = (?);",(newmode,name))
    db.commit()
    db.close()
    
def deleteBSM(name):
    db=sqlite3.connect("/home/pi/bsmdb.db")   
    db.execute("DELETE from bsms WHERE name=(?);",(name,))
    db.commit()
    db.close()
    
def getSavable(fi):    
    keys=fi.keys()
    for key in keys:
        return key
    return ""

def getLoad(fi):
    keys=fi.keys()
    for k in keys:
        if k.startswith("Load"):
            return k[4:]
    return ""
    
def debugfi(fi,mess):
    keys=fi.keys()
    print("<script> console.log('debugfi-"+mess+"');</script>")
    for key in keys:
        print("<script> console.log('key:"+key+"');</script>")
        print("<script> console.log('value:"+fi[key].value+"');</script>")
    print("<script> console.log('debugfi done');</script>")

def main():
    cgitb.enable()
    
    fi=cgi.FieldStorage()
     
    print("Content-type: text/html\n\n") 
    print("")
    print("<html>")
    print("<head>")
    print('<meta charset="utf-8">')
    print('<style>.sel { background-color: lightblue; }')
    
    print('td { background-color:  white; vertical-align: text-top; }')
    print('table {  empty-cells:show; }')
    print('button {  background-color:#EEEEEE; }')
    print(".option {color: black; font-size: 14px; font-weight: bold; }")
    print(".nooption {color: white; font-size: 14px; }")
    print(".button {  font: 12px Arial;")
    print(" text-decoration: none;  background-color: #EEEEEE;  color: #333333; "+
          " padding: 2px 6px 2px 6px; border-top: 1px solid #CCCCCC;  border-right: 1px solid #333333;"+
          "  border-bottom: 1px solid #333333;  border-left: 1px solid #CCCCCC; }")
    print('</style>')
    print(getJS())
    print("<title> BSM Editor </title>")

    debugfi(fi,"head")

    an=getAutoName(fi)
    tn=getTestName(fi)
    dn=getKeyName("delete",fi)
    sn=getSaveName(fi)
    ld=getLoad(fi)
    deb="an="+an+" tn="+tn+"  dn="+dn+"  sn="+sn+" ld="+ld
    print("<script>console.log('"+deb+"')</script>")
    
    if sn!="":
        save(sn,getSavable(fi))
        
    if "editBSM" in fi or an!="" or tn!="" or dn!="" or ld!="":
        pass
    else:
        if "newbsm" in fi:
            print(newEditor())
        else:
            print(getEditor(fi))
    print("</head>")
    print("<body>")
    print("<h3>BSM Editor</h3>")
    print("<div id='bsm'></div>")

    debugfi(fi,"body")
    if ld!="":
        print("<script>bsmsrc=JSON.parse('"+ld+"');</script>")
        print(getButtons())
        print("<script>renew();</script>")
    elif an!="":
        changeMode(an,1)
        print(getMachineButs())
    elif tn!="":
        changeMode(tn,2)
        print(getMachineButs())
    elif dn!="":
        deleteBSM(dn)
        print(getMachineButs())
    elif "editBSM" in fi:
        print(getMachineButs())
    else:
        print(getButtons())
        print("<script>renew();</script>")
    print("</body>")
    print("</html>")
    
if __name__=="__main__":
    main()


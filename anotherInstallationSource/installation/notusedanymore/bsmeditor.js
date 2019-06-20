"""
function debugOb(ob) {
    if (ob==null) {
        console.log("debugOb>null");
    }
    var x;
    for (x in ob) {
        console.log("debugOb>"+x+"="+ob[x]);
    }
}

function readTextFile(file, callback) {
    var rawFile = new XMLHttpRequest();
    rawFile.overrideMimeType("application/json");
    rawFile.open("GET", file, true);
    rawFile.onreadystatechange = function() {
        if (rawFile.readyState === 4 && rawFile.status == "200") {
            callback(rawFile.responseText);
        }
    }
    rawFile.send(null);
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
    var res="<table border='2'><tr><th>BSM Name</th></tr><tr><td id='bsmname'>"+bsm.name+"</td></tr></table><br />";
    res += '<table id="vars" border="1"><tr><th>Variable</th><th>Value</th></tr>';
    var vars = bsm.vars;
    var i;
    for (i=0;i<vars.length;i++) {
        res+='<tr><td vi="'+i+'">'+vars[i][0]+'</td><td vvi="'+i+'">'+vars[i][1]+'</td></tr>';
    }
    res += '</table>';
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
       res+='<tr><td rowspan="'+ncondrows(stat)+'" stat="'+i+'">'+stat.state+'</td><td rowspan="'+acts.length+'" stat="'+i+'" cond="0">'+cond.cond+'</td><td stat="'+i+'" cond="0" act="0">'+acts[0]+'</td></tr>';

//console.log("act="+acts[0]);      
        for (k=1;k<acts.length;k++) {
//console.log("act="+acts[k]);
                 res+='<tr><td stat="'+i+'" cond="0" act="'+k+'">'+acts[k]+'</td></tr>';
        }
        for (j=1;j<conds.length;j++) {
            cond=conds[j];
            acts=cond.acts;
//console.log("cond="+cond[0]+" rowsp="+acts.length);
//console.log("act="+acts[0]);            

            res+='<tr><td rowspan="'+acts.length+'" stat="'+i+'" cond="'+j+'">'+cond.cond+'</td><td stat="'+i+'" cond="'+j+'" act="0">'+acts[0]+'</td></tr>';
            for (k=1;k<acts.length;k++) {
//console.log("act="+acts[k]);            
                res+='<tr><td stat="'+i+'" cond="'+j+'" act="'+k+'">'+acts[k]+'</td></tr>';
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

function getCellContents(src,si,ci,ai) {
    if (ci==null) return src.nodes[Number(si)].state;
    if (ai==null) return src.nodes[Number(si)].conds[Number(ci)].cond;
    return src.nodes[Number(si)].conds[Number(ci)].acts[Number(ai)];
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

function renew() { 
    document.getElementById("bsm").innerHTML=editable(bsmsrc);
    document.getElementById("loader").innerHTML="";
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

var menuListener=function(e) {
    e = e || window.event;
    var t=e.target || e.srcElement;
//console.log("click on :"+t.nodeName);  
    if (t.nodeName!="BUTTON") {
        document.getElementById("loader").innerHTML="";    
        return;
    }
    var ln=t.getAttribute("name");
    
//console.log("loading:"+ln);    
    bsmsrc=JSON.parse(localStorage.getItem(ln));
    renew();
}


function load() {
//  getMenu();
    var src=localStorage.getItem("BSMtest");
//console.log("loaded:"+src);    
    bsmsrc=JSON.parse(src);
undos=[];
debugOb(bsmsrc);
    var ll=[]
    for (k in localStorage) if (k.startsWith("BSM")) 
        ll.push(k.substring(3));
    if (ll==[]) {
        window.alert("nothing to load");
        return;
    }
    var i;
    var str="<table border='1'><tr><th>Select BSM to load</th></tr>\n";
    for (i=0;i<ll.length;i++) {
        str+="<tr><td disabled=true><button name=BSM"+ll[i]+" onclick='menuListener'>"+ll[i]+"</button></td></tr>\n";
    }
    document.getElementById("loader").innerHTML=str;
    document.getElementById("loader").addEventListener("click",menuListener);
}
    
function save() {
    var src=JSON.stringify(bsmsrc);
    var key="BSM"+bsmsrc.name;
    localStorage.setItem(key,src);
//console.log("saving:"+src);    
}

function newBSM() {
    save();
    bsmsrc={name:"yrmndt",vars:[["-","-"]],nodes:[{state:"-",conds:[{cond:"-",acts:["-"]}]}]};
    renew();
}


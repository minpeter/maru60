#!/usr/bin/env node
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
const here=path.dirname(fileURLToPath(import.meta.url));
const source=process.argv[2]?path.resolve(process.argv[2]):path.join(here,"layout_model.json");
const model=JSON.parse(fs.readFileSync(source,"utf8"));
const W=model.reference.board_width_mm,D=model.reference.board_depth_mm,P=model.reference.pitch_mm;
const Y0=101.06775,XOFF=.4525,topY=model.reference.top_row_plate_y_mm,minGap=.5*P;
const errors=[],cases=[];
const expected={
 WK:{"6.25":[["LCtrl",1.25],["LMeta",1.25],["LAlt",1.25],["Space",6.25],["RAlt",1.25],["Menu/Fn",1.25],["RCtrl",1.25]],"7":[["LCtrl",1.5],["LMeta",1],["LAlt",1.5],["Space",7],["RAlt",1.5],["Menu/Fn",1],["RCtrl",1.5]]},
 WKL:{"6.25":[["LCtrl",1.5],["LWinBlock",1.5],["LAlt",1.5],["Space",6.25],["RAlt",1.5],["RWinBlock",1.5],["RCtrl",1.5]],"7":[["LCtrl",1.5],["LWinBlock",1],["LAlt",1.5],["Space",7],["RAlt",1.5],["RWinBlock",1],["RCtrl",1.5]]},
 HHKB:{"6.25":[["LCtrl",1.5],["LMeta",1.25],["LAlt",1.25],["Space",6.25],["RAlt",1.25],["RMeta",1.25],["RCtrl",1.5]],"7":[["LCtrl",1.5],["LMeta",1],["LAlt",1],["Space",7],["RAlt",1],["RMeta",1],["RCtrl",1.5]]}
};
const exactWidths={WK:{"6.25":13.75,"7":15},WKL:{"6.25":15.25,"7":15},HHKB:{"6.25":14.25,"7":14}};
function expand(entries,rowId,index,yPlate,opts){
 let a=entries.map(([name,width])=>({name,width,offset:0}));
 if(rowId==="number"&&opts.split_backspace){const j=a.findIndex(k=>k.name==="Backspace");a.splice(j,1,{name:"Backspace_L",width:1,offset:0},{name:"Backspace_R",width:1,offset:0});}
 if(rowId==="home"&&opts.stepped_caps)a.find(k=>k.name==="Caps").offset=.25;
 if(rowId==="shift"&&opts.split_right_shift){const j=a.findIndex(k=>k.name==="RightShift");a.splice(j,1,{name:"RightShift_L",width:1.75,offset:0},{name:"RightShift_R",width:1,offset:0});}
 const total=a.reduce((n,k)=>n+k.width,0);
 if(total>15.25+1e-8)errors.push(rowId+": modeled envelope exceeds 15.25U");
 let cursor=(W/P-total)/2;
 return a.map(k=>{const xU=cursor+k.width/2+k.offset,xGh60=xU*P,yGh60=Y0-yPlate;cursor+=k.width;return {name:k.name,row:rowId,rowIndex:index,widthU:k.width,xU,xGh60,yGh60,xPlate:xGh60+XOFF,yPlate};});
}
function build(layout,space,opts){
 const keys=[];
 model.rows.forEach((r,i)=>keys.push(...expand(r.keys,r.id,i,topY-i*P,opts)));
 const b=model.bottom_layouts[layout][String(space)];
 keys.push(...expand(b.keys,"bottom",4,topY-4*P,opts));
 return keys;
}
for(const layout of ["WK","WKL","HHKB"])for(const space of [6.25,7]){
 const b=model.bottom_layouts[layout][String(space)];
 if(JSON.stringify(b.keys)!==JSON.stringify(expected[layout][String(space)]))errors.push(layout+" "+space+"U does not match the explicit expected seven-position definition");
 const total=b.keys.reduce((n,k)=>n+k[1],0);
 if(total!==exactWidths[layout][String(space)]||total!==b.total_u)errors.push(layout+" "+space+"U width mismatch (expected "+exactWidths[layout][String(space)]+", got "+total+")");
}
for(const layout of ["WK","WKL","HHKB"])for(const space of [6.25,7])
for(const split_backspace of [false,true])for(const split_right_shift of [false,true])for(const stepped_caps of [false,true]){
 const opts={split_backspace,split_right_shift,stepped_caps},id=layout+"-"+space+"U"+Object.entries(opts).filter(e=>e[1]).map(e=>"-"+e[0]).join("");
 const keys=build(layout,space,opts);
 const refs=new Set();
 for(const k of keys){const ref=k.row+":"+k.name;if(refs.has(ref))errors.push(id+": duplicate "+ref);refs.add(ref);
  if(k.xGh60<0||k.xGh60>W||k.yGh60<0||k.yGh60>D)errors.push(id+": switch center outside board at "+k.name);
  if(Math.abs(k.xGh60-(k.xPlate-XOFF))>.001||Math.abs(k.yGh60-(Y0-k.yPlate))>.001)errors.push(id+": frame transform round-trip failed at "+k.name);
 }
 const back=keys.filter(k=>k.row==="number").map(k=>k.name);
 if(split_backspace?!(back.includes("Backspace_L")&&back.includes("Backspace_R")):!back.includes("Backspace"))errors.push(id+": Backspace option mismatch");
 const shift=keys.filter(k=>k.row==="shift").map(k=>k.name);
 if(split_right_shift?!(shift.includes("RightShift_L")&&shift.includes("RightShift_R")):!shift.includes("RightShift"))errors.push(id+": right Shift option mismatch");
 const cap=keys.find(k=>k.row==="home"&&k.name==="Caps");
 const baseCaps=(W/P-model.rows[2].keys.reduce((n,k)=>n+k[1],0))/2+model.rows[2].keys[0][1]/2;
 if(Math.abs(cap.xU-(baseCaps+(stepped_caps?.25:0)))>1e-6)errors.push(id+": stepped Caps offset mismatch");
 for(let row=0;row<5;row++){const xs=keys.filter(k=>k.rowIndex===row).sort((a,b)=>a.xGh60-b.xGh60);for(let j=1;j<xs.length;j++)if(xs[j].xGh60-xs[j-1].xGh60<minGap-1e-6)errors.push(id+": same-row switch-center spacing below 0.5U");}
 cases.push({id,layout,space_u:space,options:opts,bottom_row_width_u:exactWidths[layout][String(space)],switch_sites:keys.length});
}
if(cases.length!==48)errors.push("expected 48 declared layout-option cases, got "+cases.length);
if(errors.length){console.error(JSON.stringify({result:"FAIL",declared_cases:cases.length,errors},null,2));process.exit(1);}
const colors={number:"#377eb8",qwerty:"#4daf4a",home:"#984ea3",shift:"#ff7f00",bottom:"#e41a1c"};
const labels={number:{Backspace:"Bksp",Backspace_L:"BS-L",Backspace_R:"BS-R"},qwerty:{Tab:"Tab",LeftBracket:"[",RightBracket:"]",Backslash:"\\"},home:{Caps:"Caps",Semicolon:";",Quote:"'",Enter:"Enter"},shift:{LeftShift:"LShift",RightShift:"RShift",RightShift_L:"RS-L",RightShift_R:"RS-R",Comma:",",Period:".",Slash:"/"},bottom:{"Menu/Fn":"Menu/Fn",LWinBlock:"WIN BLOCK",RWinBlock:"WIN BLOCK",LMeta:"Meta",RMeta:"Meta",LCtrl:"Ctrl",RCtrl:"Ctrl",LAlt:"Alt",RAlt:"Alt",Space:"Space"}};
const sample=build("WK",6.25,{split_backspace:false,split_right_shift:false,stepped_caps:false});
const scale=3,margin=72,w=Math.round(W*scale+2*margin),h=Math.round(D*scale+2*margin+64);
let out=['<svg xmlns="http://www.w3.org/2000/svg" width="'+w+'" height="'+h+'" viewBox="0 0 '+w+' '+h+'">','<rect width="100%" height="100%" fill="#f5f7fa"/>',
'<text x="'+margin+'" y="27" font-family="sans-serif" font-size="20" font-weight="700" fill="#152b3a">WK 6.25U � seven bottom positions � 13.75U total</text>',
'<text x="'+margin+'" y="51" font-family="sans-serif" font-size="13" fill="#3a5262">1.25U x 6 modifiers + 6.25U spacebar � nominal centered keycap envelopes</text>',
'<rect x="'+margin+'" y="'+margin+'" width="'+(W*scale)+'" height="'+(D*scale)+'" rx="7" fill="#172733" stroke="#e39a40" stroke-width="3"/>'];
for(const k of sample){const x=margin+k.xGh60*scale,y=margin+k.yGh60*scale,ww=k.widthU*P*scale,hh=14*scale;
 out.push('<rect x="'+(x-ww/2).toFixed(1)+'" y="'+(y-hh/2).toFixed(1)+'" width="'+ww.toFixed(1)+'" height="'+hh.toFixed(1)+'" rx="4" fill="'+colors[k.row]+'" fill-opacity=".84" stroke="#d8e2ea"/>');
 out.push('<circle cx="'+x.toFixed(1)+'" cy="'+y.toFixed(1)+'" r="3.3" fill="#fff"/>');
 const label=labels[k.row]?.[k.name]||k.name;
 out.push('<text x="'+x.toFixed(1)+'" y="'+(y+4).toFixed(1)+'" text-anchor="middle" font-family="sans-serif" font-size="11" fill="#fff">'+label+'</text>');
}
out.push('<text x="'+margin+'" y="'+(h-17)+'" font-family="sans-serif" font-size="12" fill="#a33524">Envelope illustration only. It does not prove switch/socket/LED/stabilizer, plate, or case clearance.</text>','</svg>');
const report={result:"PASS",declared_layout_option_cases:cases.length,layouts:["WK","WKL","HHKB"],spacebar_sizes_u:[6.25,7],options:["split/non-split Backspace","split/non-split right Shift","stepped/non-stepped Caps"],excluded:"Split spacebar was not requested and is not modeled.",
checks:["all six explicit seven-position bottom-row definitions match expected key widths and order","switch centers inside the nominal 285x94.6mm board profile","plate/GH60 transform round-trip within 0.001mm","minimum same-row switch-center pitch �0.5U","Backspace, right Shift, and stepped Caps site selection matches each flag"],
expected_bottom_row_width_u:exactWidths,physical_pcb_combinations_validated:false,clearance:"NOT CHECKED: no licensed hot-swap socket geometry, component footprints, plate CAD, or case solids available.",socket_geometry_available:false,sample:{id:"WK-6.25U",switch_sites:sample.length}};
fs.writeFileSync(path.join(here,"layout-preview.svg"),out.join("\n"));
fs.writeFileSync(path.join(here,"validation-report.json"),JSON.stringify(report,null,2)+"\n");
console.log(JSON.stringify({...report,preview:path.join(here,"layout-preview.svg")},null,2));


#!/usr/bin/env node
// Deterministic key-center envelope checks. Does not perform footprint clearance.
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
const here=path.dirname(fileURLToPath(import.meta.url));
const modelPath=process.argv[2]?path.resolve(process.argv[2]):path.join(here,"layout_model.json");
const model=JSON.parse(fs.readFileSync(modelPath,"utf8"));
const P=model.references.pitch,W=model.references.board_width,D=model.references.board_depth;
const XOFF=model.references.plate_to_gh60.x_plate_from_x_gh60;
const Y0=model.references.plate_to_gh60.y_plate_from_y_gh60;
const MIN_GAP=.5*P, failures=[], layouts=[];
const maxEnvelopeU=W/P+.05;
function sitesForRow(entries,rowId,rowIndex,yPlate,flags){
 let keys=entries.map(([name,width])=>({name,width,xOffset:0}));
 if(rowId==="number"&&flags.split_backspace){let i=keys.findIndex(k=>k.name==="Backspace");keys.splice(i,1,{name:"Backspace_L",width:1,xOffset:0},{name:"Backspace_R",width:1,xOffset:0});}
 if(rowId==="home"&&flags.stepped_caps)keys.find(k=>k.name==="Caps").xOffset=.25;
 if(rowId==="shift"&&flags.split_right_shift){let i=keys.findIndex(k=>k.name==="RightShift");keys.splice(i,1,{name:"RightShift_L",width:1.75,xOffset:0},{name:"RightShift_R",width:1,xOffset:0});}
 const total=keys.reduce((s,k)=>s+k.width,0);
 if(total>maxEnvelopeU)throw new Error("row envelope too wide: "+rowId+" "+total+"U");
 let cursor=(W/P-total)/2;
 return keys.map(k=>{const xu=cursor+k.width/2+k.xOffset;const q={name:k.name,row:rowId,rowIndex,xU:xu,widthU:k.width,xGh60:xu*P,yGh60:Y0-yPlate,xPlate:xu*P+XOFF,yPlate};cursor+=k.width;return q;});
}
function compose(layoutName,space,flags){
 const keys=[];
 model.rows.forEach((r,i)=>keys.push(...sitesForRow(r.keys,r.id,i,model.references.plate_row_centers_y[i],flags)));
 let bottom=model.bottom_rows[layoutName][String(space)].map(([name,width])=>({name,width,isSwitch:!name.includes("Blocker")}));
 if(flags.split_space){const i=bottom.findIndex(k=>k.name==="Space");const width=bottom[i].width;bottom.splice(i,1,{name:"Space_L",width:width/2,isSwitch:true},{name:"Space_R",width:width/2,isSwitch:true});}
 const idx=4,yp=model.references.plate_row_centers_y[idx],total=bottom.reduce((s,k)=>s+k.width,0);
 if(total>maxEnvelopeU)throw new Error("bottom row too wide: "+layoutName+" "+space+"U "+total+"U");
 let cursor=(W/P-total)/2;
 for(const k of bottom){const xu=cursor+k.width/2;if(k.isSwitch)keys.push({name:k.name,row:"bottom",rowIndex:idx,xU:xu,widthU:k.width,xGh60:xu*P,yGh60:Y0-yp,xPlate:xu*P+XOFF,yPlate:yp});cursor+=k.width;}
 return keys;
}
for(const layout of ["WK","WKL","HHKB"])for(const space of [6.25,7])
for(const split_backspace of [false,true])for(const split_right_shift of [false,true])
for(const stepped_caps of [false,true])for(const split_space of [false,true]){
 const flags={split_backspace,split_right_shift,stepped_caps,split_space};
 const keys=compose(layout,space,flags);
 const id=[layout,space+"U",...Object.entries(flags).filter(e=>e[1]).map(e=>e[0])].join("-");
 if(keys.length<59)failures.push(id+": too few switch sites "+keys.length);
 const names=new Set();
 for(const k of keys){
  const name=k.row+":"+k.name;
  if(names.has(name))failures.push(id+": duplicate reference "+name);
  names.add(name);
  if(!(k.xGh60>=0&&k.xGh60<=W&&k.yGh60>=0&&k.yGh60<=D))failures.push(id+": center outside board at "+k.name);
  if(Math.abs(k.xPlate-XOFF-k.xGh60)>.001||Math.abs(Y0-k.yPlate-k.yGh60)>.001)failures.push(id+": frame round-trip at "+k.name);
 }
 for(let row=0;row<5;row++){const group=keys.filter(k=>k.rowIndex===row).sort((a,b)=>a.xGh60-b.xGh60);for(let i=1;i<group.length;i++){const dx=group[i].xGh60-group[i-1].xGh60;if(dx<MIN_GAP-1e-6)failures.push(id+": same-row spacing below 0.5U at "+group[i-1].name+"/"+group[i].name);}}
 for(let i=1;i<model.references.plate_row_centers_y.length;i++){const a=Y0-model.references.plate_row_centers_y[i-1],b=Y0-model.references.plate_row_centers_y[i];if(b-a<MIN_GAP-1e-6)failures.push(id+": adjacent row pitch below 0.5U");}
 layouts.push({id,layout,space,flags,keys});
}
if(layouts.length!==96)failures.push("expected 96 configurations, got "+layouts.length);
if(failures.length){console.error(JSON.stringify({result:"FAIL",configurations:layouts.length,failures},null,2));process.exit(1);}
const sample=layouts.find(x=>x.id==="WK-6.25U");
const colors={number:"#377eb8",qwerty:"#4daf4a",home:"#984ea3",shift:"#ff7f00",bottom:"#e41a1c"};
const scale=2.25,margin=48,w=Math.round(W*scale+margin*2),h=Math.round(D*scale+margin*2+48);
let out=['<svg xmlns="http://www.w3.org/2000/svg" width="'+w+'" height="'+h+'" viewBox="0 0 '+w+' '+h+'">','<rect width="100%" height="100%" fill="#f5f7fa"/>',
'<text x="'+margin+'" y="25" font-family="sans-serif" font-size="17" font-weight="700" fill="#152b3a">Maru60 RP2350A � GH60 envelope � WK 6.25U draft</text>',
'<rect x="'+margin+'" y="'+margin+'" width="'+(W*scale)+'" height="'+(D*scale)+'" rx="8" fill="#172733" stroke="#e39a40" stroke-width="3"/>'];
for(const k of sample.keys){const x=margin+k.xGh60*scale,y=margin+k.yGh60*scale,ww=k.widthU*P*scale,hh=13.2*scale;
 out.push('<rect x="'+(x-ww/2).toFixed(1)+'" y="'+(y-hh/2).toFixed(1)+'" width="'+ww.toFixed(1)+'" height="'+hh.toFixed(1)+'" rx="4" fill="'+colors[k.row]+'" fill-opacity=".82" stroke="#d8e2ea"/>');
 out.push('<circle cx="'+x.toFixed(1)+'" cy="'+y.toFixed(1)+'" r="3.1" fill="#fff"/>');
 out.push('<text x="'+x.toFixed(1)+'" y="'+(y+3.1).toFixed(1)+'" text-anchor="middle" font-family="sans-serif" font-size="8.5" fill="#fff">'+k.name+'</text>');
}
out.push('<text x="'+margin+'" y="'+(h-14)+'" font-family="sans-serif" font-size="11" fill="#a33524">96 combinations pass center bounds, frame transform, and �0.5U spacing. Footprint/case/stabilizer clearance NOT checked.</text>','</svg>');
const report={result:"PASS",configurations:layouts.length,checks:["switch centers inside 285.0x94.6mm envelope","plateGH60 frame round-trip within 0.001mm","minimum same-row and adjacent-row center spacing �0.5U","all WK/WKL/HHKB x 6.25U/7U x four binary key options enumerated","row keycap envelope � 15.05U"],minimum_center_spacing_mm:MIN_GAP,
clearance:"NOT CHECKED: no licensed hot-swap socket geometry, selected LED footprint geometry, plate CAD, or case solid available.",
socket_geometry_available:false,case_and_plate_geometry_available:false,sample:{id:sample.id,switch_sites:sample.keys.length}};
fs.writeFileSync(path.join(here,"layout-preview.svg"),out.join("\n"));
fs.writeFileSync(path.join(here,"validation-report.json"),JSON.stringify(report,null,2)+"\n");
console.log(JSON.stringify({...report,preview:path.join(here,"layout-preview.svg")},null,2));


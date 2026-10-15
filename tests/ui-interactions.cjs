/*
SPDX-License-Identifier: AGPL-3.0-or-later
Copyright (C) 2026 Mystical Mark Astrology contributors
This program is free software: you can redistribute it and/or modify it under
 the GNU Affero General Public License, version 3 or (at your option) any later version.
Distributed WITHOUT ANY WARRANTY; without even the implied warranty of
 MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See LICENSE for details.
You should have received a copy of the license; if not, see https://www.gnu.org/licenses/.
*/
/* Run with NODE_PATH pointing to a local jsdom installation. No browser/server required. */
const {JSDOM}=require('jsdom');
const fs=require('node:fs');const path=require('node:path');const assert=require('node:assert/strict');
const base=path.join(__dirname,'../app/static');
const dom=new JSDOM(fs.readFileSync(path.join(base,'index.html'),'utf8'),{url:'http://127.0.0.1:8876',runScripts:'outside-only'});
const w=dom.window;const $=id=>w.document.getElementById(id);const calls=[];
const asp={a:'0',b:'1',a_name:'Sun',b_name:'Moon',name:'Square',glyph:'□',angle:90,orb:1,allowance:7,applying:true};
const spec={name:'Natal A',datetime:'1990-05-01T14:00',timezone:'UTC',location:'Saskatoon',latitude:52,longitude:-106,fold:0};
const bodies=[{key:'0',name:'Sun',glyph:'☉'},{key:'1',name:'Moon',glyph:'☽'}];
function chart(name,index=0){return {...spec,name,method:'Test fixture',warnings:[],houses:[],aspects:[{...asp,orb:index+1}],objects:bodies.map((p,i)=>({...p,lon:i*89+index*10,degree:i*29,sign:'Aries',sign_index:0,sign_glyph:'♈',decan:1,decan_ruler:'Mars',house:null,retrograde:false}))};}
const settings={engine:'moshier',houses:false,timezone:'UTC',latitude:52,longitude:-106,location:'Saskatoon',progressed_houses:'natal',sort:'time',moon_aspects:false,objects:['0','1'],aspects:[{...asp,enabled:true}]};
const meta={version:'1.1.0',swisseph:'test',settings,bodies,sign_glyphs:Array(12).fill('♈'),rulers:Array(12).fill('Sun')};
const event={title:'Sun square Moon',kind:'aspect',time:'2026-10-15T12:00:00+00:00',keys:['0','1'],angle:90};
w.fetch=async(url,options)=>{calls.push({url,options});let data;
 if(url==='/api/meta')data=meta;
 else if(url.startsWith('/api/events'))data={events:[event],warnings:[]};
 else if(url==='/api/chart'){
  const req=JSON.parse(options.body);let charts=req.mode==='composite'?[chart('Composite')]:req.mode==='progressed'?[chart('Natal'),chart('Progressed',1)]:req.charts.map((s,i)=>chart(s.name,i));
  let cross_aspects=[];for(let i=0;i<charts.length;i++)for(let j=i+1;j<charts.length;j++)cross_aspects.push({...asp,ring_a:i,ring_b:j,orb:.25});
  data={mode:req.mode,charts,cross_aspects};
 }else if(url==='/api/charts')data=[];else throw Error(url);
 return {ok:true,json:async()=>data};};
w.eval(fs.readFileSync(path.join(base,'chart-state.js'),'utf8'));
w.eval(fs.readFileSync(path.join(base,'app.js'),'utf8')+`\nwindow.testUI={async open(mode,count=1){saved=Array.from({length:count},(_,i)=>({...current,id:String(i),name:'Natal '+i}));selected=new Set(saved.map(c=>c.id));await useSaved(mode);},state(){return {mode,chartContext,sidebarView,aspectScope,highlight,result,rawResult};}};`);
const tick=async()=>{for(let i=0;i<8;i++)await new Promise(r=>setImmediate(r));};
const selectedObjects=()=>[...w.document.querySelectorAll('.svg-object[aria-pressed="true"]')];
(async()=>{
 await tick();assert($('dayEvents').textContent.includes('Sun square Moon'));
 $('sidebarView').value='aspects';$('sidebarView').dispatchEvent(new w.Event('change'));assert.equal($('dayEvents').querySelectorAll('.aspect-choice').length,1);
 const count=calls.length;$('dayEvents').querySelector('button').click();assert.equal(calls.length,count,'Aspect selection must not recalculate or move time');assert.equal(selectedObjects().length,2);
 $('clearSelection').click();assert.equal(selectedObjects().length,0);assert($('clearSelection').disabled);
 await w.testUI.open('single');assert($('sidebarViewControl').classList.contains('hidden'));assert.equal($('dayEvents').querySelectorAll('.aspect-choice').length,1);
 await w.testUI.open('synastry',2);assert.equal($('dayEvents').querySelectorAll('.aspect-choice').length,3);assert(!$('convertComposite').classList.contains('hidden'));
 w.document.querySelector('.svg-object[data-ring="1"][data-key="1"]').dispatchEvent(new w.MouseEvent('click'));
 assert.equal(selectedObjects().length,1);assert.equal(selectedObjects()[0].dataset.ring,'1');
 $('aspectScope').value='between';$('aspectScope').dispatchEvent(new w.Event('change'));assert.equal($('dayEvents').querySelectorAll('.aspect-choice').length,1);
 $('dayEvents').querySelector('button').click();assert.deepEqual(selectedObjects().map(p=>p.dataset.ring).sort(),['0','1']);
 $('aspectScope').value='1';$('aspectScope').dispatchEvent(new w.Event('change'));$('dayEvents').querySelector('button').click();assert(selectedObjects().every(p=>p.dataset.ring==='1'));
 $('clearSelection').click();assert.equal(selectedObjects().length,0);
 $('convertComposite').click();await tick();assert.equal(w.testUI.state().mode,'composite');assert.equal(w.testUI.state().result.charts.length,1);assert.equal($('dayEvents').querySelectorAll('.aspect-choice').length,1);
 $('dayEvents').querySelector('button').click();assert.equal(selectedObjects().length,2);
 $('returnSynastry').click();await tick();assert.equal(w.testUI.state().mode,'synastry');assert.equal(w.testUI.state().result.charts.length,2);
 await w.testUI.open('progressed');assert(!$('progressedViewControl').classList.contains('hidden'));
 $('progressedView').value='only';$('progressedView').dispatchEvent(new w.Event('change'));assert.equal(w.testUI.state().result.charts.length,1);assert.equal(w.testUI.state().result.charts[0].name,'Progressed');assert.equal($('dayEvents').querySelectorAll('.aspect-choice').length,1);
 $('aspects').querySelector('button').click();assert.equal(selectedObjects().length,2);
 $('progressedView').value='biwheel';$('progressedView').dispatchEvent(new w.Event('change'));assert.equal(w.testUI.state().result.charts.length,2);assert.equal(selectedObjects().length,0);
 await w.testUI.open('synastry',6);assert($('convertComposite').classList.contains('hidden'));assert.equal($('dayEvents').querySelectorAll('.aspect-choice').length,21);
 $('aspectScope').value='5';$('aspectScope').dispatchEvent(new w.Event('change'));$('dayEvents').querySelector('button').click();assert(selectedObjects().every(p=>p.dataset.ring==='5'));
 $('now').click();await tick();$('sidebarView').value='moments';$('sidebarView').dispatchEvent(new w.Event('change'));$('dayEvents').querySelector('button').click();await tick();assert.equal(selectedObjects().length,2);assert.equal(w.testUI.state().mode,'single');
 $('clearSelection').click();assert.equal(selectedObjects().length,0);assert.equal(w.document.querySelectorAll('#dayEvents .selected').length,0);
 assert(!$('status').classList.contains('error'),$('status').textContent);
 console.log('PASS: moments/aspects toggle, natal defaults, all scope filters, exact wheel selection, clear, in-chart composite round trip, progressed-only round trip, six-wheel scopes, table selection, moment navigation.');
 dom.window.close();
})().catch(e=>{console.error(e);dom.window.close();process.exitCode=1;});

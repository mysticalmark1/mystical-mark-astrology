/*
SPDX-License-Identifier: AGPL-3.0-or-later
Copyright (C) 2026 Mystical Mark Astrology contributors
This program is free software: you can redistribute it and/or modify it under
 the GNU Affero General Public License, version 3 or (at your option) any later version.
Distributed WITHOUT ANY WARRANTY; without even the implied warranty of
 MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See LICENSE for details.
You should have received a copy of the license; if not, see https://www.gnu.org/licenses/.
*/
const {test}=require('node:test');
const assert=require('node:assert/strict');
const C=require('../app/static/chart-state.js');
const aspect={a:'0',b:'1',a_name:'Sun',b_name:'Moon',name:'Square',angle:90,orb:1,allowance:7};
const raw={mode:'progressed',charts:[{name:'Natal',aspects:[aspect]},{name:'Progressed',aspects:[{...aspect,orb:2}]}],cross_aspects:[{...aspect,ring_a:0,ring_b:1,orb:.5},{...aspect,a:'1',b:'1',name:'Conjunction',angle:0,ring_a:0,ring_b:1}]};
test('All/between/specific-wheel filters keep complete aspect sets and unique identities',()=>{
 assert.equal(C.allAspects(raw).length,4);
 assert.equal(new Set(C.allAspects(raw).map(a=>a.id)).size,4);
 assert.equal(C.filterAspects(raw,'between').length,2);
 assert.equal(C.filterAspects(raw,'0').length,1);
 assert.equal(C.filterAspects(raw,'1')[0].orb,2);
});
test('A planet selection is restricted to its exact wheel',()=>{
 const selected={refs:[{ring:1,key:'1'}]};
 assert.equal(C.objectSelected(selected,1,'1'),true);
 assert.equal(C.objectSelected(selected,0,'1'),false);
 assert.equal(C.objectSelected(selected,1,'0'),false);
 assert.equal(C.aspectSelected(selected,C.allAspects(raw)[0]),false);
});
test('A same-planet cross-chart aspect selects exactly its two endpoints',()=>{
 const a=C.filterAspects(raw,'between').find(a=>a.a==='1');
 const s={aspectId:a.id,refs:[{ring:a.ring_a,key:a.a},{ring:a.ring_b,key:a.b}]};
 assert(C.objectSelected(s,0,'1'));assert(C.objectSelected(s,1,'1'));
 assert(!C.objectSelected(s,2,'1'));assert(C.aspectSelected(s,a));
 assert.equal(C.allAspects(raw).filter(a=>C.aspectSelected(s,a)).length,1);
});
test('Progressed-only display preserves progressed data and restores biwheel without mutation',()=>{
 const original=JSON.stringify(raw);const only=C.displayResult(raw,true);
 assert.equal(only.charts.length,1);assert.equal(only.charts[0].name,'Progressed');
 assert.equal(C.allAspects(only).length,1);assert.equal(C.allAspects(only)[0].ring_a,0);
 assert.equal(C.displayResult(raw,false),raw);assert.equal(JSON.stringify(raw),original);
});
test('Clear selection clears both object and aspect highlight decisions',()=>{
 assert(!C.objectSelected(null,0,'0'));assert(!C.aspectSelected(null,C.allAspects(raw)[0]));
});

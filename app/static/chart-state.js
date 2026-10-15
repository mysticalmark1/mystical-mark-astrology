/*
SPDX-License-Identifier: AGPL-3.0-or-later
Copyright (C) 2026 Mystical Mark Astrology contributors
This program is free software: you can redistribute it and/or modify it under
 the GNU Affero General Public License, version 3 or (at your option) any later version.
Distributed WITHOUT ANY WARRANTY; without even the implied warranty of
 MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See LICENSE for details.
You should have received a copy of the license; if not, see https://www.gnu.org/licenses/.
*/
/* Pure chart-view and selection logic shared with regression tests. */
(function(root){
'use strict';
function aspectId(a){return JSON.stringify([a.ring_a,a.a,a.ring_b,a.b,a.angle,a.name]);}
function allAspects(result){
 const rows=result.charts.flatMap((c,i)=>c.aspects.map(a=>({...a,ring_a:i,ring_b:i})));
 rows.push(...result.cross_aspects);
 return rows.map(a=>({...a,id:aspectId(a)})).sort((a,b)=>a.orb-b.orb);
}
function filterAspects(result,scope='all'){
 return allAspects(result).filter(a=>scope==='all'||(scope==='between'?a.ring_a!==a.ring_b:a.ring_a===Number(scope)&&a.ring_b===Number(scope)));
}
function objectSelected(selection,ring,key){return !!selection?.refs?.some(r=>r.ring===ring&&r.key===key);}
function aspectSelected(selection,a){
 if(!selection)return false;
 if(selection.aspectId)return selection.aspectId===a.id;
 return (!selection.aspect_name||selection.aspect_name===a.name)&&selection.angle!==undefined&&Math.abs(a.angle-selection.angle)<.001&&objectSelected(selection,a.ring_a,a.a)&&objectSelected(selection,a.ring_b,a.b);
}
function displayResult(raw,progressedOnly){
 if(raw.mode!=='progressed'||!progressedOnly)return raw;
 // Hide the natal reference wheel, retaining and remapping the transit wheel.
 const keep=raw.charts.map((_,i)=>i).filter(i=>i!==0);
 const remap=i=>keep.indexOf(i);
 return {...raw,charts:keep.map(i=>raw.charts[i]),
  transit_index:raw.transit_index==null?null:remap(raw.transit_index),
  cross_aspects:raw.cross_aspects.filter(a=>keep.includes(a.ring_a)&&keep.includes(a.ring_b)).map(a=>({...a,ring_a:remap(a.ring_a),ring_b:remap(a.ring_b)}))};
}
const api={aspectId,allAspects,filterAspects,objectSelected,aspectSelected,displayResult};
if(typeof module!=='undefined'&&module.exports)module.exports=api;
root.ChartState=api;
})(typeof globalThis!=='undefined'?globalThis:this);

(function(){
  const els = {
    range: ()=> document.getElementById('mag-range'),
    magVal: ()=> document.getElementById('mag-val'),
    count: ()=> document.getElementById('quakes-count'),
    auto: ()=> document.getElementById('auto-refresh'),
    refresh: ()=> document.getElementById('refresh-btn'),
    export: ()=> document.getElementById('export-csv'),
    winBtns: ()=> document.querySelectorAll('.controls .btn[data-win]'),
    list: ()=> document.getElementById('quakes-list'),
    hist: ()=> document.getElementById('quakes-hist'),
  };
  let map, layerGroup, autoTimer, lastData = [];

  function fmtWhen(t){ try{ const d = new Date(t); return d.toLocaleString(); } catch(_){ return String(t); } }
  function el(tag, attrs, html){ const e=document.createElement(tag); if(attrs){ for(const k in attrs){ e.setAttribute(k, attrs[k]); } } if(html!=null) e.innerHTML=html; return e; }
  function activeWindow(){ const a=[...els.winBtns()].find(b=>b.classList.contains('active')); return a ? a.dataset.win : 'day'; }

  function colorForMag(m){
    if (m>=5) return '#ea580c';  // orange
    if (m>=3) return '#16a34a';  // green
    return '#1f6feb';            // blue
  }

  function filterByWindow(events, win){
    const now = Date.now();
    const span = (win==='hour') ? 3600e3 : (win==='week' ? 7*86400e3 : 86400e3);
    return events.filter(ev=>{
      const t = ev.time || (ev.properties && ev.properties.time);
      return t && (now - t) <= span;
    });
  }

  function normalize(data){
    if (Array.isArray(data)) return data;
    if (data && Array.isArray(data.features)) {
      return data.features.map(f=>{
        const p=f.properties||{}, g=f.geometry||{};
        const c = Array.isArray(g.coordinates) ? g.coordinates : [null,null,null];
        return { mag:p.mag, place:p.place, time:p.time, url:p.url, depth:c[2], lon:c[0], lat:c[1] };
      });
    }
    return [];
  }

  function clientFilter(events){
    const win = activeWindow();
    let filtered = filterByWindow(events, win);
    const mmin = Number(els.range().value || 0);
    filtered = filtered.filter(ev=>{
      const m = ev.mag ?? (ev.properties && ev.properties.mag) ?? 0;
      return Number(m) >= mmin;
    });
    return filtered;
  }

  function ensureMap(){
    if (!document.getElementById('quakes-map') || typeof L === 'undefined') return null;
    if (!map){
      map = L.map('quakes-map', {scrollWheelZoom:false}).setView([20,0], 2);
      L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution:'&copy; OpenStreetMap'
      }).addTo(map);
      layerGroup = L.layerGroup().addTo(map);
    }
    return map;
  }

  function renderHistogram(events){
    const canvas = els.hist();
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    // Resize for crisp drawing
    const w = canvas.clientWidth, h = canvas.clientHeight;
    canvas.width = w; canvas.height = h;
    // Bins: [0,1), [1,2), … [6,7)
    const bins = new Array(7).fill(0);
    events.forEach(ev=>{
      const m = ev.mag ?? (ev.properties && ev.properties.mag);
      if (m==null) return;
      const b = Math.max(0, Math.min(6, Math.floor(Number(m))));
      bins[b] += 1;
    });
    const max = Math.max(1, ...bins);
    // Draw axes
    ctx.clearRect(0,0,w,h);
    ctx.fillStyle = '#0f172a';
    ctx.font = '12px system-ui, -apple-system, Segoe UI, Roboto';
    // Bars
    const pad = 30, bw = Math.floor((w - pad*2) / bins.length) - 8;
    bins.forEach((v, i)=>{
      const x = pad + i * (bw + 8);
      const col = colorForMag(i+0.1);
      const bh = Math.floor((h - 40) * (v / max));
      ctx.fillStyle = col;
      ctx.fillRect(x, h - 20 - bh, bw, bh);
      ctx.fillStyle = '#64748b';
      ctx.fillText(`M${i}–${i+1}`, x, h - 6);
      ctx.fillText(String(v), x + bw - 10, h - 22 - bh - 4);
    });
    // Title
    ctx.fillStyle = '#64748b';
    ctx.fillText('Magnitude distribution (filtered)', pad, 16);
  }

  async function loadGlobalQuakes(){
    const list = els.list();
    if (!list) return;

    let data;
    try{
      const r = await fetch('/api/global_quakes', {cache:'no-store'});
      if(!r.ok) throw new Error('HTTP '+r.status);
      data = await r.json();
    }catch(e){
      list.innerHTML = '<li class="muted">Failed to load global seismic data.</li>';
      els.count().textContent = '';
      return;
    }

    const norm = normalize(data);
    lastData = norm.slice();  // keep copy for CSV export
    const filtered = clientFilter(norm);

    // Counters
    const win = activeWindow();
    const total = norm.length;
    const vis = filtered.length;
    els.count().textContent = `Showing ${vis} of ${total} events (window: ${win})`;

    // List
    list.innerHTML = '';
    filtered.slice(0, 20).forEach(ev=>{
      const mag = ev.mag ?? (ev.properties && ev.properties.mag);
      const place = ev.place || (ev.properties && ev.properties.place) || 'Unknown';
      const time = ev.time || (ev.properties && ev.properties.time);
      const url = ev.url || (ev.properties && ev.properties.url);
      const depth = (ev.depth!=null) ? ev.depth : (ev.geometry && Array.isArray(ev.geometry.coordinates) ? ev.geometry.coordinates[2] : null);
      const li = el('li', null,
        '<span class="badge mag">M '+(mag!=null? (mag.toFixed?mag.toFixed(1):mag):'?')+'</span> '+
        '<strong>'+place+'</strong><br>'+
        '<span class="small muted">'+
          (depth!=null?'<span class="badge depth">Depth '+depth+' km</span> ':'')+
          '<span class="badge when">'+(time?fmtWhen(time):'')+'</span> '+
          (url?'<a href="'+url+'" target="_blank" rel="noopener">USGS</a>':'')+
        '</span>'
      );
      list.appendChild(li);
    });

    // Map markers
    const m = ensureMap();
    if (m){
      layerGroup.clearLayers();
      filtered.slice(0, 200).forEach(ev=>{
        const lat = ev.lat ?? (ev.geometry && ev.geometry.coordinates ? ev.geometry.coordinates[1] : null);
        const lon = ev.lon ?? (ev.geometry && ev.geometry.coordinates ? ev.geometry.coordinates[0] : null);
        const mag = ev.mag ?? (ev.properties && ev.properties.mag);
        if (lat==null || lon==null) return;
        const radius = Math.max(3, Math.min(14, (Number(mag)||0) * 2.2));
        const col = colorForMag(Number(mag)||0);
        const marker = L.circleMarker([lat, lon], {
          radius: radius, color: col, fillColor: col, fillOpacity: 0.65, weight: 1
        });
        const place = ev.place || (ev.properties && ev.properties.place) || '';
        const time = fmtWhen(ev.time || (ev.properties && ev.properties.time));
        marker.bindPopup(`<strong>${place}</strong><br>M ${mag ?? '?'}<br>${time}`);
        marker.addTo(layerGroup);
      });
    }

    // Histogram
    renderHistogram(filtered);
  }

  function bindControls(){
    els.winBtns().forEach(btn=>{
      btn.addEventListener('click', ()=>{
        els.winBtns().forEach(b=>b.classList.remove('active'));
        btn.classList.add('active');
        loadGlobalQuakes();
      });
    });
    els.range().addEventListener('input', ()=>{ els.magVal().textContent = Number(els.range().value).toFixed(1); });
    els.range().addEventListener('change', ()=> loadGlobalQuakes());
    els.refresh().addEventListener('click', ()=> loadGlobalQuakes());
    els.auto().addEventListener('change', ()=>{
      if (autoTimer) { clearInterval(autoTimer); autoTimer = null; }
      if (els.auto().checked) autoTimer = setInterval(loadGlobalQuakes, 60000);
    });
    els.export().addEventListener('click', ()=> exportCSV());
  }

  function exportCSV(){
    // Use current filtered set for consistency with UI
    const filtered = clientFilter(lastData || []);
    const rows = [['time_iso','magnitude','place','depth_km','lat','lon','source_url']];
    filtered.forEach(ev=>{
      const time = ev.time ?? (ev.properties && ev.properties.time) ?? null;
      const mag = ev.mag ?? (ev.properties && ev.properties.mag) ?? null;
      const place = ev.place ?? (ev.properties && ev.properties.place) ?? '';
      const depth = (ev.depth!=null) ? ev.depth : (ev.geometry && Array.isArray(ev.geometry.coordinates) ? ev.geometry.coordinates[2] : null);
      const lat = ev.lat ?? (ev.geometry && Array.isArray(ev.geometry.coordinates) ? ev.geometry.coordinates[1] : null);
      const lon = ev.lon ?? (ev.geometry && Array.isArray(ev.geometry.coordinates) ? ev.geometry.coordinates[0] : null);
      const url = ev.url ?? (ev.properties && ev.properties.url) ?? '';
      const iso = time ? new Date(time).toISOString() : '';
      rows.push([iso, mag, place, depth, lat, lon, url]);
    });
    const csv = rows.map(r=>r.map(v=>{
      const s = (v==null) ? '' : String(v);
      return s.includes(',') ? `"${s.replace(/"/g,'""')}"` : s;
    }).join(',')).join('\n');
    const blob = new Blob([csv], {type:'text/csv'});
    const a = document.createElement('a');
    a.href = URL.createObjectURL(blob);
    a.download = 'global_quakes_filtered.csv';
    a.click();
    URL.revokeObjectURL(a.href);
  }

  document.addEventListener('DOMContentLoaded', ()=>{
    els.magVal().textContent = Number(els.range().value).toFixed(1);
    bindControls();
    loadGlobalQuakes();
  });
})();

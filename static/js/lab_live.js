// GeoTiny EDU Live Lab — /static/js/lab_live.js
// ============================================================
// PURPOSE
//   - Poll /api/wave and /api/spectrum (HTTP JSON)
//   - Draw waveform + FFT into canvases
//   - Update status lines + optional bandpower bars
//
// TROUBLESHOOTING (fast)
//   A) Open DevTools Console: you must see "LAB LIVE OK" once.
//   B) If plots are blank, check that THESE ids exist in /lab HTML:
//        canvases:   #cv-wave, #cv-fft
//        status:     #dataStatus, #dataMeta, #jsStatus
//        controls:   #station, #channel, #window_s, #refresh_ms
//        optional:   #waveInfo, #specInfo
//        band bars:  #bp_micro/#bp_micro_v, #bp_local/#bp_local_v, #bp_mains/#bp_mains_v
//   C) Quick backend check (server):
//        curl -sS "http://127.0.0.1:8050/api/spectrum?station=GTN34&channel=SHZ&window_s=10&fmax=50" \
//        | python3 -c 'import sys,json; j=json.load(sys.stdin); print(j["ok"], j.get("dominant_hz"), len(j["freq_hz"]))'
//
// NOTE ABOUT WEBSOCKET ERRORS
//   - This lab page uses NO websockets.
//   - If you see ws://127.0.0.1:8050/ failing, it comes from some OTHER script
//     (e.g., base template / vendor UI). It does not affect this file.
//
// ============================================================

console.log("LAB LIVE OK");

(function () {
  "use strict";

  // ============================================================
  // SECTION A — CONFIG (edit here)
  // ============================================================
  var DEFAULTS = {
    station: "GTN34",
    channel: "SHZ",
    window_s: 10,
    refresh_ms: 5000, // IMPORTANT: this is milliseconds (matches your <select id="refresh_ms">)
    fmax: 50
  };

  // DOM ids used by YOUR lab.html (do not change unless HTML changes)
  var DOM = {
    waveCanvas: "#cv-wave",
    specCanvas: "#cv-fft",
    status: "#dataStatus",
    meta: "#dataMeta",
    jsStatus: "#jsStatus",
    station: "#station",
    channel: "#channel",
    window_s: "#window_s",
    refresh_ms: "#refresh_ms",
    waveInfo: "#waveInfo",
    specInfo: "#specInfo"
  };

  // ============================================================
  // SECTION B — DOM helpers
  // ============================================================
  function q(sel) { return document.querySelector(sel); }
  function setText(sel, txt) { var el = q(sel); if (el) el.textContent = txt; }

  function num(v, dflt) {
    var x = parseFloat(v);
    return (isFinite(x) ? x : dflt);
  }

  function ensureCanvasPixels(c) {
    // Canvas must have real pixel buffer size, not just CSS size.
    var rect = c.getBoundingClientRect();
    var w = Math.max(300, Math.floor(rect.width || c.width || 900));
    var h = Math.max(160, Math.floor(rect.height || c.height || 360));
    if (c.width !== w) c.width = w;
    if (c.height !== h) c.height = h;
  }

  // ============================================================
  // SECTION C — UI parameters (read DOM, fall back to defaults)
  // ============================================================
  function getParams() {
    var stationEl = q(DOM.station);
    var channelEl = q(DOM.channel);
    var windowEl  = q(DOM.window_s);
    var refreshEl = q(DOM.refresh_ms);

    var station = (stationEl && stationEl.value) ? stationEl.value : DEFAULTS.station;
    var channel = (channelEl && channelEl.value) ? channelEl.value : DEFAULTS.channel;

    var window_s = num(windowEl && windowEl.value, DEFAULTS.window_s);
    if (!isFinite(window_s) || window_s <= 0) window_s = DEFAULTS.window_s;

    var refresh_ms = num(refreshEl && refreshEl.value, DEFAULTS.refresh_ms);
    if (!isFinite(refresh_ms) || refresh_ms < 0) refresh_ms = DEFAULTS.refresh_ms;

    return { station: station, channel: channel, window_s: window_s, refresh_ms: refresh_ms, fmax: DEFAULTS.fmax };
  }

  // ============================================================
  // SECTION D — stats + band helpers
  // ============================================================
  function stats(arr) {
    if (!arr || !arr.length) return { n: 0, mean: 0, rms: 0, p2p: 0, min: 0, max: 0 };
    var n = arr.length;

    var mean = 0;
    for (var i = 0; i < n; i++) mean += arr[i];
    mean /= n;

    var v = 0;
    var mn = arr[0], mx = arr[0];
    for (var j = 0; j < n; j++) {
      var d = arr[j] - mean;
      v += d * d;
      if (arr[j] < mn) mn = arr[j];
      if (arr[j] > mx) mx = arr[j];
    }
    return { n: n, mean: mean, rms: Math.sqrt(v / n), p2p: (mx - mn), min: mn, max: mx };
  }

  function bandMean(freq, mag, f1, f2) {
    if (!freq || !mag || freq.length < 2 || mag.length < 2) return 0;
    var n = Math.min(freq.length, mag.length);
    var sum = 0, cnt = 0;
    for (var i = 0; i < n; i++) {
      var f = freq[i];
      if (f >= f1 && f <= f2) {
        var v = mag[i];
        if (isFinite(v)) { sum += v; cnt++; }
      }
    }
    return cnt ? (sum / cnt) : 0;
  }

  function argmaxNoDC(arr) {
    if (!arr || arr.length < 3) return { i: 0, v: 0 };
    var bestI = 1, bestV = -Infinity;
    for (var i = 1; i < arr.length; i++) {
      var v = arr[i];
      if (isFinite(v) && v > bestV) { bestV = v; bestI = i; }
    }
    return { i: bestI, v: bestV };
  }

  function clamp01(x) { return x < 0 ? 0 : (x > 1 ? 1 : x); }

  function setBar(fillId, valId, raw, ref) {
    // Visual normalization: LOG compression so one band doesn't flatten the others.
    // raw/ref are magnitudes (>=0).
    var fill = q("#" + fillId);
    var val  = q("#" + valId);
    if (!fill || !val) return;

    var eps = 1e-12;
    var r = Math.max(raw, eps);
    var R = Math.max(ref, eps);

    // 60 dB-ish compression range: ref .. ref*1e-6
    var lo = R * 1e-6;
    var frac = (Math.log10(r) - Math.log10(lo)) / (Math.log10(R) - Math.log10(lo));
    frac = clamp01(frac);

    fill.style.width = (frac * 100).toFixed(1) + "%";
    val.textContent = raw > 0 ? raw.toFixed(3) : "0.000";
  }

  // ============================================================
  // SECTION E — drawing (canvas)
  // ============================================================
  function draw(canvas, xs, ys, title, xlabel) {
    var ctx = canvas.getContext("2d");
    var W = canvas.width, H = canvas.height;
    ctx.clearRect(0, 0, W, H);

    var padL = 55, padR = 15, padT = 14, padB = 28;

    // frame
    ctx.strokeStyle = "rgba(16,24,40,.12)";
    ctx.lineWidth = 1;
    ctx.strokeRect(padL, padT, W - padL - padR, H - padT - padB);

    if (!xs || !ys || xs.length < 2 || ys.length < 2) {
      ctx.fillStyle = "rgba(16,24,40,.45)";
      ctx.font = "12px system-ui, -apple-system, Segoe UI, Roboto, Arial";
      ctx.fillText("No data", padL, padT + 20);
      return;
    }

    var n = Math.min(xs.length, ys.length);

    var xmin = xs[0], xmax = xs[n - 1];
    if (xmax === xmin) xmax = xmin + 1;

    var ymin = ys[0], ymax = ys[0];
    for (var i = 1; i < n; i++) {
      var v = ys[i];
      if (v < ymin) ymin = v;
      if (v > ymax) ymax = v;
    }
    if (ymax === ymin) ymax = ymin + 1;

    // small y padding
    var yr = (ymax - ymin);
    ymin -= 0.05 * yr;
    ymax += 0.05 * yr;

    function X(v) { return padL + (v - xmin) * (W - padL - padR) / (xmax - xmin); }
    function Y(v) { return padT + (ymax - v) * (H - padT - padB) / (ymax - ymin); }

    ctx.beginPath();
    ctx.lineWidth = 2;
    ctx.strokeStyle = "rgba(16,24,40,.90)";
    for (var k = 0; k < n; k++) {
      var px = X(xs[k]), py = Y(ys[k]);
      if (k === 0) ctx.moveTo(px, py);
      else ctx.lineTo(px, py);
    }
    ctx.stroke();

    ctx.fillStyle = "rgba(16,24,40,.85)";
    ctx.font = "600 13px system-ui, -apple-system, Segoe UI, Roboto, Arial";
    ctx.fillText(title, padL, 16);

    ctx.fillStyle = "rgba(16,24,40,.65)";
    ctx.font = "12px system-ui, -apple-system, Segoe UI, Roboto, Arial";
    ctx.fillText(xlabel, padL, H - 8);
  }

  // ============================================================
  // SECTION F — networking (robust fetch)
  // ============================================================
  async function fetchJson(url) {
    var r = await fetch(url, { cache: "no-store" });
    var ct = (r.headers.get("content-type") || "").toLowerCase();
    var txt = await r.text();

    if (!r.ok) throw new Error("HTTP " + r.status + " for " + url + " :: " + txt.slice(0, 200));
    if (ct.indexOf("application/json") === -1) throw new Error("Non-JSON for " + url + " (ct=" + ct + ") :: " + txt.slice(0, 200));

    return JSON.parse(txt);
  }

  // ============================================================
  // SECTION G — main loop (wave + spectrum)
  // ============================================================
  async function refreshOnce() {
    var stEl = q(DOM.status);
    var metaEl = q(DOM.meta);
    var jsEl = q(DOM.jsStatus);
    var waveC = q(DOM.waveCanvas);
    var specC = q(DOM.specCanvas);

    if (!stEl || !metaEl || !waveC || !specC) {
      // If these are missing, the template is not the expected lab.html.
      return;
    }

    ensureCanvasPixels(waveC);
    ensureCanvasPixels(specC);

    var p = getParams();
    metaEl.textContent = "station " + p.station + " · channel " + p.channel + " · window " + p.window_s + " s";
    if (jsEl) jsEl.textContent = "JS: running";

    try {
      // --- Wave ---
      var wurl = "/api/wave?station=" + encodeURIComponent(p.station)
        + "&channel=" + encodeURIComponent(p.channel)
        + "&window_s=" + encodeURIComponent(p.window_s);

      var wj = await fetchJson(wurl);
      if (!wj || wj.ok === false) {
        stEl.textContent = "NO LIVE DATA (" + ((wj && (wj.error || wj.detail)) || "wave ok=false") + ")";
        return;
      }

      var xs = wj.time_s || [];
      var y = wj.wave || [];

      // de-mean for display
      var mean = 0;
      for (var i = 0; i < y.length; i++) mean += y[i];
      if (y.length) mean /= y.length;

      var yd = new Array(y.length);
      for (var j = 0; j < y.length; j++) yd[j] = y[j] - mean;

      var ws = stats(yd);
      draw(waveC, xs, yd, "Waveform (time domain)", "time [s]");

      if (q(DOM.waveInfo)) {
        setText(DOM.waveInfo,
          "samples " + (y.length || 0) +
          " · fs " + (wj.fs != null ? wj.fs : "—") + " Hz" +
          " · RMS " + ws.rms.toFixed(4) +
          " · P2P " + ws.p2p.toFixed(4)
        );
      }

      // --- Spectrum ---
      var surl = "/api/spectrum?station=" + encodeURIComponent(p.station)
        + "&channel=" + encodeURIComponent(p.channel)
        + "&window_s=" + encodeURIComponent(p.window_s)
        + "&fmax=" + encodeURIComponent(p.fmax);

      var sj = await fetchJson(surl);
      if (!sj || sj.ok === false) {
        stEl.textContent = "NO SPECTRUM (" + ((sj && (sj.error || sj.detail)) || "spectrum ok=false") + ")";
        return;
      }

      var f = sj.freq_hz || [];
      var m = sj.mag || [];
      draw(specC, f, m, "Spectrum (FFT)", "frequency [Hz]");

      // peak info
      var pk = argmaxNoDC(m);
      var peakF = (f && f.length) ? (f[pk.i] || 0) : 0;
      var peakV = pk.v || 0;

      // Bandpower bars (UPDATED: stable + readable)
      // bands:
      //  - microseisms: 0.10–0.50 Hz
      //  - local:       1–10 Hz
      //  - mains:       49–51 Hz
      var micro = bandMean(f, m, 0.10, 0.50);
      var local = bandMean(f, m, 1.00, 10.0);
      var mains = bandMean(f, m, 49.0, 51.0);

      // ref = strongest band (for relative bar scaling)
      var ref = Math.max(micro, local, mains, 1e-12);

      setBar("bp_micro", "bp_micro_v", micro, ref);
      setBar("bp_local", "bp_local_v", local, ref);
      setBar("bp_mains", "bp_mains_v", mains, ref);

      if (q(DOM.specInfo)) {
        setText(DOM.specInfo,
          "bins " + Math.min(f.length, m.length) +
          " · window " + (sj.window_s != null ? sj.window_s : "—") + " s" +
          " · peak " + Number(peakF).toFixed(3) + " Hz" +
          " · mag " + Number(peakV).toFixed(3) +
          " · bands: micro 0.1–0.5 Hz, local 1–10 Hz, mains ~50 Hz"
        );
      }

      stEl.textContent = "OK · RMS " + ws.rms.toFixed(3) + " · P2P " + ws.p2p.toFixed(3) + " · " + (new Date()).toLocaleTimeString();

    } catch (e) {
      stEl.textContent = "ERROR (console): " + String(e.message || e);
      console.error(e);
    }
  }

  // ============================================================
  // SECTION H — scheduling (refresh_ms from UI)
  // ============================================================
  function schedule() {
    if (window.__geotinyTimer) clearInterval(window.__geotinyTimer);

    var p = getParams();
    var ms = Math.round(p.refresh_ms);

    if (ms <= 0) {
      // refresh OFF
      return;
    }
    if (ms < 500) ms = 500;

    window.__geotinyTimer = setInterval(refreshOnce, ms);
  }

  // Hook UI changes
  ["station", "channel", "window_s", "refresh_ms"].forEach(function (id) {
    var el = document.getElementById(id);
    if (el) el.addEventListener("change", function () { refreshOnce(); schedule(); });
  });

  // First paint
  refreshOnce();
  schedule();

})();

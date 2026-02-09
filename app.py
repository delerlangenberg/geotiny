#!/usr/bin/env python3
from __future__ import annotations

# Standard library
import os
import re
import time
from pathlib import Path
from typing import List, Tuple

# Third‑party
import requests
import numpy as np
from flask import (
    Flask,
    render_template,
    jsonify,
    request,
    Response,
)

# -----------------------------------------------------------------------------
# App setup
# -----------------------------------------------------------------------------
app = Flask(__name__, template_folder="templates", static_folder="static")
STARTED = time.time()

STATIONS = ["GTN34", "GTN33", "GTN37"]
CHANNELS = ["SHZ", "SHN", "SHE"]

# -----------------------------------------------------------------------------
# Real‑data helpers (miniSEED only; no synthetic fallback)
# -----------------------------------------------------------------------------
def _raw_dir() -> Path:
    here = Path(__file__).resolve().parent
    candidates = [
        here / "data" / "raw",
        here.parent / "data" / "raw",
        Path("/srv/learnlab/geotiny-edu/data/raw"),
        Path("/srv/learnlab/geotiny/data/raw"),
    ]
    for c in candidates:
        if c.is_dir():
            return c
    return candidates[0]

def _latest_mseed_path(station: str, channel: str) -> Path | None:
    root = _raw_dir()
    st_dir = root / station
    search_dirs = [st_dir, root]  # allow both station subdir and flat
    pats = [
        f"*{station}*{channel}*",
        f"*{channel}*",
        f"*{station}*{channel}*.mseed",
        f"*{station}*{channel}*.miniseed",
        f"*{station}*{channel}*.msd",
        f"*{station}*{channel}*.seed",
        f"*{station}*{channel}*.mseed.gz",
        f"*{station}*{channel}*.miniseed.gz",
    ]
    best = None
    best_mtime = -1.0
    for d in search_dirs:
        if not d.is_dir():
            continue
        for pat in pats:
            for p in d.glob(pat):
                try:
                    mt = p.stat().st_mtime
                except Exception:
                    continue
                if mt > best_mtime:
                    best, best_mtime = p, mt
    return best

def _load_last_window(station: str, channel: str, window_s: float) -> dict:
    """Load last window from latest miniSEED; return dict with fs, time_s, wave, stats."""
    try:
        from obspy import read as _read
    except Exception as e:
        raise RuntimeError(f"ObsPy not available: {e}")

    p = _latest_mseed_path(station, channel)
    if not p:
        raise FileNotFoundError(f"No miniSEED found for {station} {channel} under {_raw_dir()}")

    st = _read(str(p), format="MSEED")
    if len(st) < 1:
        raise RuntimeError(f"Empty stream in {p}")

    tr = st[0].copy()
    # Basic hygiene
    try:
        tr.merge(method=1, fill_value="interpolate")
    except Exception:
        pass
    try:
        tr.detrend("linear")
    except Exception:
        pass
    try:
        tr.taper(max_percentage=0.02)
    except Exception:
        pass

    fs = float(tr.stats.sampling_rate)
    if fs <= 0:
        raise RuntimeError("Invalid sampling rate")

    # Trim to the last window_s seconds
    end = tr.stats.endtime
    start = end - float(window_s)
    try:
        tr.trim(starttime=start, endtime=end, pad=True, fill_value=0)
    except Exception:
        pass

    y = np.asarray(tr.data, dtype=np.float64)
    n = int(y.size)
    if n < 10:
        raise RuntimeError("Trace too short")

    t = np.arange(n, dtype=np.float64) / fs

    rms = float(np.sqrt(np.mean(y * y)))
    p2p = float(np.max(y) - np.min(y))

    return {
        "path": str(p),
        "fs": fs,
        "time_s": t.tolist(),
        "wave": y.tolist(),
        "rms": rms,
        "p2p": p2p,
        "n": n,
        "ts_end": float(time.time()),
    }

def _fft_hann_mag(wave: List[float], fs: float, fmax: float = 50.0) -> Tuple[List[float], List[float], float]:
    y = np.asarray(wave, dtype=np.float64)
    n = int(y.size)
    if n < 16:
        raise RuntimeError("wave too short for FFT")
    w = np.hanning(n)
    Y = np.fft.rfft(y * w)
    f = np.fft.rfftfreq(n, d=1.0 / fs)
    mag = np.abs(Y)

    fmax_eff = min(float(fmax), float(fs) / 2.0)
    sel = f <= fmax_eff
    f2 = f[sel]
    mag2 = mag[sel]

    dom_f = 0.0
    if f2.size > 2:
        idx = int(np.argmax(mag2[1:])) + 1  # ignore DC
        dom_f = float(f2[idx])

    return f2.tolist(), mag2.tolist(), dom_f

# -----------------------------------------------------------------------------
# Health
# -----------------------------------------------------------------------------
@app.get("/healthz")
def healthz():
    return jsonify(ok=True, uptime_s=int(time.time() - STARTED))

# -----------------------------------------------------------------------------
# Pages
# -----------------------------------------------------------------------------
@app.get("/", endpoint="overview")
def overview():
    vendor_url = os.environ.get("GEOTINY_VENDOR_URL", "http://127.0.0.1:8051/")
    return render_template(
        "pages/overview.html",
        title="GeoTiny EDU · Overview",
        active="overview",
        vendor_url=vendor_url,
    )

@app.get("/lab", endpoint="lab")
def lab():
    return render_template(
        "pages/lab.html",
        title="GeoTiny EDU · Live Lab",
        active="lab",
        STATIONS=STATIONS,
        CHANNELS=CHANNELS,
    )

@app.get("/spectrum", endpoint="spectrum")
def spectrum():
    return render_template(
        "pages/spectrum.html",
        title="GeoTiny EDU · Spectrum analysis",
        active="spectrum",
        STATIONS=STATIONS,
        CHANNELS=CHANNELS,
    )

@app.get("/data", endpoint="data")
def data():
    return render_template(
        "pages/data.html",
        title="GeoTiny EDU · Data downloads",
        active="data",
        STATIONS=STATIONS,
        CHANNELS=CHANNELS,
    )

@app.get("/education", endpoint="education")
def education():
    return render_template(
        "pages/education.html",
        title="GeoTiny EDU · Education and projects",
        active="education",
    )

# -----------------------------------------------------------------------------
# APIs (real‑data only)
# -----------------------------------------------------------------------------
@app.get("/api/wave")
def api_wave():
    station = request.args.get("station", "GTN34")
    channel = request.args.get("channel", "SHZ")
    window_s = float(request.args.get("window_s", "10"))
    try:
        d = _load_last_window(station, channel, window_s)
        return {
            "station": station,
            "channel": channel,
            "fs": d["fs"],
            "time_s": d["time_s"],
            "wave": d["wave"],
            "rms": d["rms"],
            "p2p": d["p2p"],
            "n": d["n"],
            "source": "miniseed",
            "path": d["path"],
            "ok": True,
        }
    except Exception as e:
        return {"station": station, "channel": channel, "ok": False, "error": str(e)}, 503

@app.get("/api/wave.csv")
def api_wave_csv():
    # Build CSV from the same data source as /api/wave (to avoid Response.get_json gymnastics)
    station = request.args.get("station", "GTN34")
    channel = request.args.get("channel", "SHZ")
    window_s = float(request.args.get("window_s", "10"))
    try:
        d = _load_last_window(station, channel, window_s)
        lines = ["t_s,x"]
        for t, x in zip(d["time_s"], d["wave"]):
            lines.append(f"{t},{x}")
        out = "\n".join(lines) + "\n"
        return Response(out, mimetype="text/csv",
                        headers={"Content-Disposition": "attachment; filename=waveform.csv"})
    except Exception as e:
        return Response(f"error,{e}\n", status=503, mimetype="text/plain")

@app.get("/api/spectrum")
def api_spectrum():
    station = request.args.get("station", "GTN34")
    channel = request.args.get("channel", "SHZ")
    window_s = float(request.args.get("window_s", "10"))
    fmax = float(request.args.get("fmax", "50"))
    try:
        d = _load_last_window(station, channel, window_s)
        freq_hz, mag, dom_f = _fft_hann_mag(d["wave"], float(d["fs"]), fmax=fmax)
        return {
            "station": station,
            "channel": channel,
            "fs": d["fs"],
            "window_s": window_s,
            "freq_hz": freq_hz,
            "mag": mag,
            "dominant_hz": dom_f,
            "source": "miniseed",
            "path": d.get("path"),
            "ok": True,
        }
    except Exception as e:
        return {"station": station, "channel": channel, "ok": False, "error": str(e)}, 503

@app.get("/api/spectrum.csv")
def api_spectrum_csv():
    station = request.args.get("station", "GTN34")
    channel = request.args.get("channel", "SHZ")
    window_s = float(request.args.get("window_s", "10"))
    fmax = float(request.args.get("fmax", "50"))
    try:
        d = _load_last_window(station, channel, window_s)
        freq_hz, mag, _ = _fft_hann_mag(d["wave"], float(d["fs"]), fmax=fmax)
        lines = ["f_hz,mag"]
        for f, m in zip(freq_hz, mag):
            lines.append(f"{f},{m}")
        out = "\n".join(lines) + "\n"
        return Response(out, mimetype="text/csv",
                        headers={"Content-Disposition": "attachment; filename=spectrum.csv"})
    except Exception as e:
        return Response(f"error,{e}\n", status=503, mimetype="text/plain")

# USGS last‑24h proxy with a simple 5‑minute cache; returns a compact list for the Overview UI
_USGS_CACHE = {"t": 0.0, "payload": None}
@app.get("/api/global_quakes")
def api_global_quakes():
    now = time.time()
    if _USGS_CACHE["payload"] and now - _USGS_CACHE["t"] < 300:
        return jsonify(_USGS_CACHE["payload"])
    url = "https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/all_day.geojson"
    try:
        r = requests.get(url, timeout=12)
        r.raise_for_status()
        data = r.json()
        feats = data.get("features", [])[:50]
        out = []
        for f in feats:
            p = f.get("properties", {}) or {}
            g = f.get("geometry", {}) or {}
            coords = (g.get("coordinates") or [None, None, None])
            out.append({
                "time": p.get("time"),
                "mag": p.get("mag"),
                "place": p.get("place"),
                "url": p.get("url"),
                "lon": coords[0],
                "lat": coords[1],
                "depth_km": coords[2],
            })
        payload = {"ok": True, "count": len(out), "quakes": out}
        _USGS_CACHE.update({"t": now, "payload": payload})
        return jsonify(payload)
    except Exception as e:
        return jsonify(ok=False, error=str(e)), 502

# -----------------------------------------------------------------------------
# Vendor UI reverse proxies (same‑origin)
# -----------------------------------------------------------------------------
HOP_HEADERS = {
    "connection",
    "keep-alive",
    "proxy-authenticate",
    "proxy-authorization",
    "te",
    "trailers",
    "transfer-encoding",
    "upgrade",
}

def _proxy_to(env_var: str, default_base: str, subpath: str = ""):
    """
    Reverse proxy to vendor endpoint with optional Basic Auth (env),
    stripped frame blockers, and link rewriting for same-origin embedding.
    """
    base = os.environ.get(env_var, default_base).rstrip("/")

    user = os.environ.get("GEOTINY_VENDOR_USER", "")
    pw   = os.environ.get("GEOTINY_VENDOR_PASS", "")
    auth = (user, pw) if user and pw else None

    url = f"{base}/{subpath}".rstrip("/")
    if request.query_string:
        url += "?" + request.query_string.decode("utf-8", "ignore")

    def _rewrite_location(loc: str) -> str:
        if not loc:
            return loc
        maps = [
            ("https://10.0.18.34:9091", "/vendor"),
            ("http://10.0.18.34:9091", "/vendor"),
            ("http://127.0.0.1:8051", "/vendor8091"),
            ("http://10.0.18.34:8091", "/vendor8091"),
            ("https://10.0.0.100:7051", "/vendor8091"),
            ("http://10.0.0.100:7051", "/vendor8091"),
            ("https://10.0.0.100:6051", "/vendor8091"),
            ("http://10.0.0.100:6051", "/vendor8091"),
        ]
        for a, b in maps:
            if loc.startswith(a):
                return b + loc[len(a):]
        return loc

    def _maybe_rewrite_body(content: bytes, content_type: str) -> bytes:
        ct = (content_type or "").lower()
        if not (ct.startswith("text/") or "javascript" in ct or "json" in ct or "xml" in ct):
            return content
        txt = content.decode("utf-8", "ignore")
        repl = [
            ("https://10.0.18.34:9091", "/vendor"),
            ("http://10.0.18.34:9091", "/vendor"),
            ("http://127.0.0.1:8051", "/vendor8091"),
            ("http://10.0.18.34:8091", "/vendor8091"),
            ("https://10.0.0.100:7051", "/vendor8091"),
            ("http://10.0.0.100:7051", "/vendor8091"),
            ("https://10.0.0.100:6051", "/vendor8091"),
            ("http://10.0.0.100:6051", "/vendor8091"),
        ]
        for a, b in repl:
            txt = txt.replace(a, b)
        # Rewrite root‑relative links to remain under /vendor or /vendor8091
        txt = re.sub(
            r'(?i)\b(href|src|action)="/(?!vendor/|vendor8091/|static/|api/|healthz\b)([^"]*)"',
            r'\1="/vendor/\2"',
            txt,
        )
        return txt.encode("utf-8", "ignore")

    fwd_headers = {}
    for k, v in request.headers.items():
        lk = k.lower()
        if lk in HOP_HEADERS or lk in {"host", "accept-encoding"}:
            continue
        fwd_headers[k] = v
    fwd_headers["Accept-Encoding"] = "identity"

    rr = requests.request(
        method=request.method,
        url=url,
        headers=fwd_headers,
        data=request.get_data(),
        cookies=request.cookies,
        allow_redirects=True,
        timeout=20,
        verify=False,  # self‑signed
        auth=auth,
    )

    out_headers = []
    for k, v in rr.headers.items():
        lk = k.lower()
        if lk in HOP_HEADERS:
            continue
        if lk in {"x-frame-options", "content-security-policy", "content-encoding", "content-length"}:
            continue
        if lk == "location":
            v = _rewrite_location(v)
        out_headers.append((k, v))

    body = _maybe_rewrite_body(rr.content, rr.headers.get("Content-Type", ""))
    return Response(body, status=rr.status_code, headers=out_headers)

# 9091: main vendor UI
@app.get("/vendor/", endpoint="vendor_9091_root")
@app.get("/vendor/<path:subpath>", endpoint="vendor_9091_path")
def vendor_proxy(subpath: str = ""):
    return _proxy_to("GEOTINY_VENDOR_URL", "https://10.0.18.34:9091/", subpath)

# 8091: WebSWave/VIEWS
@app.get("/vendor8091/", endpoint="vendor_8091_root")
@app.get("/vendor8091/<path:subpath>", endpoint="vendor_8091_path")
def vendor8091_proxy(subpath: str = ""):
    return _proxy_to("GEOTINY_VENDOR_WAVE_URL", "http://127.0.0.1:8051/", subpath)

# -----------------------------------------------------------------------------
# Entrypoint
# -----------------------------------------------------------------------------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8050)
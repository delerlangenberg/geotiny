

#!/usr/bin/env python3
from __future__ import annotations
from flask import render_template



# === GEOTINY_EDU_REALDATA_HELPERS ===
# Real-data-only acquisition from latest miniSEED file on disk (no synthetic fallback).
# This mirrors the stable "past approach": load latest -> trim -> stats -> FFT (0-50 Hz).

from pathlib import Path as _Path
import time as _time

def _raw_dir():
    # Common layouts (keep it simple but robust)
    here = _Path(__file__).resolve().parent
    candidates = [
        here / "data" / "raw",
        here.parent / "data" / "raw",
        _Path("/srv/learnlab/geotiny-edu/data/raw"),
        _Path("/srv/learnlab/geotiny/data/raw"),
    ]
    for c in candidates:
        if c.is_dir():
            return c
    return candidates[0]  # default (may not exist)

def _latest_mseed_path(station: str, channel: str):
    root = _raw_dir()
    st_dir = root / station
    # allow both flat and station-subdir layouts
    search_dirs = [st_dir, root]
    pats = [
        f"*{station}*{channel}*",
        f"*{channel}*",
        # common explicit extensions too (keep)
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

def _load_last_window(station: str, channel: str, window_s: float):
    # returns dict with station/channel/fs/time_s/wave + stats
    try:
        from obspy import read as _read
    except Exception as e:
        raise RuntimeError(f"ObsPy not available: {e}")

    import numpy as _np

    p = _latest_mseed_path(station, channel)
    if not p:
        raise FileNotFoundError(f"No miniSEED found for {station} {channel} under {_raw_dir()}")

    st = _read(str(p), format="MSEED")
    if len(st) < 1:
        raise RuntimeError(f"Empty stream in {p}")

    tr = st[0].copy()
    # basic hygiene
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

    # trim to last window_s seconds
    end = tr.stats.endtime
    start = end - float(window_s)
    try:
        tr.trim(starttime=start, endtime=end, pad=True, fill_value=0)
    except Exception:
        # if trim fails, still proceed with whatever we have
        pass

    y = _np.asarray(tr.data, dtype=_np.float64)
    n = int(y.size)
    if n < 10:
        raise RuntimeError("Trace too short")

    t = _np.arange(n, dtype=_np.float64) / fs

    # stats
    rms = float(_np.sqrt(_np.mean(y*y)))
    p2p = float(_np.max(y) - _np.min(y))

    return {
        "path": str(p),
        "fs": fs,
        "time_s": t.tolist(),
        "wave": y.tolist(),
        "rms": rms,
        "p2p": p2p,
        "n": n,
        "ts_end": float(_time.time()),
    }

def _fft_mag(wave, fs: float, fmax: float = 50.0):
    import numpy as _np
    y = _np.asarray(wave, dtype=_np.float64)
    n = int(y.size)

    # windowed rfft
    w = _np.hanning(n)
    Y = _np.fft.rfft(y * w)
    f = _np.fft.rfftfreq(n, d=1.0/fs)
    mag = _np.abs(Y)

    # limit to fmax and Nyquist
    fmax_eff = min(float(fmax), float(fs)/2.0)
    m = f <= fmax_eff
    f2 = f[m]
    mag2 = mag[m]

    # dominant frequency (ignore DC)
    dom_f = 0.0
    if f2.size > 2:
        idx = int(_np.argmax(mag2[1:])) + 1
        dom_f = float(f2[idx])

    return f2.tolist(), mag2.tolist(), dom_f


import os
import re
import time
import math
from typing import List, Tuple

import requests
from flask import Flask, render_template, jsonify, request, Response

app = Flask(__name__, template_folder="templates", static_folder="static")
STARTED = time.time()

STATIONS = ["GTN34", "GTN33", "GTN37"]
CHANNELS = ["SHZ", "SHN", "SHE"]

def _clamp_int(v: str | None, default: int, lo: int, hi: int) -> int:
    try:
        x = int(v) if v is not None else default
    except Exception:
        x = default
    return max(lo, min(hi, x))

def _pick(v: str | None, allowed: List[str], default: str) -> str:
    return v if (v and v in allowed) else default

def _fake_wave(fs: float, seconds: int) -> Tuple[List[float], List[float]]:
    n = int(fs * seconds)
    t = [i / fs for i in range(n)]
    x = []
    for ti in t:

        if REAL_ONLY:
            return jsonify(ok=False, error="REAL_ONLY: no live GeoTiny feed configured")

        val = (

        )
        x.append(val)
    return t, x

def _fft_mag(x: List[float], fs: float) -> Tuple[List[float], List[float]]:
    n = len(x)
    half = n // 2
    freqs = [k * fs / n for k in range(half)]
    mags = []
    for k in range(half):
        re = 0.0
        im = 0.0
        for n_i, xn in enumerate(x):
            ang = 2.0 * math.pi * k * n_i / n
            re += xn * math.cos(ang)
            im -= xn * math.sin(ang)
        mags.append((re*re + im*im) ** 0.5)
    return freqs, mags


@app.get("/api/spectrum")
def api_spectrum():
    # Real-data-only FFT endpoint (NO synthetic fallback).
    from flask import request
    import numpy as np

    station = request.args.get("station", "GTN34")
    channel = request.args.get("channel", "SHZ")
    window_s = float(request.args.get("window_s", "10"))
    fmax = float(request.args.get("fmax", "50"))

    try:
        d = _load_last_window(station, channel, window_s)

        y = np.asarray(d["wave"], dtype=np.float64)
        n = int(y.size)
        if n < 16:
            raise RuntimeError("wave too short for FFT")

        w = np.hanning(n)
        Y = np.fft.rfft(y * w)
        f = np.fft.rfftfreq(n, d=1.0 / float(d["fs"]))
        mag = np.abs(Y)

        fmax_eff = min(float(fmax), float(d["fs"]) / 2.0)
        sel = f <= fmax_eff
        f2 = f[sel]
        mag2 = mag[sel]

        dom_f = 0.0
        if f2.size > 2:
            idx = int(np.argmax(mag2[1:])) + 1
            dom_f = float(f2[idx])

        return {
            "station": station,
            "channel": channel,
            "fs": d["fs"],
            "window_s": window_s,
            "freq_hz": f2.tolist(),
            "mag": mag2.tolist(),
            "dominant_hz": dom_f,
            "source": "miniseed",
            "path": d.get("path"),
            "ok": True,
        }
    except Exception as e:
        return {
            "station": station,
            "channel": channel,
            "ok": False,
            "error": "real FFT failed (no fallback)",
            "detail": str(e),
        }, 503

@app.get("/healthz")
def healthz():
    return jsonify(ok=True, uptime_s=int(time.time() - STARTED))

# --- BEGIN: Clean routes for 5 pages ---

# Overview (root)
@app.get("/", endpoint="overview")
def overview():
    vendor_url = os.environ.get("GEOTINY_VENDOR_URL", "https://10.0.18.34:9091/")
    return render_template(
        "pages/overview.html",
        title="GeoTiny EDU · Overview",
        active="overview",
        vendor_url=vendor_url
    )

# Spectrum analysis (replaces Live Lab as the dedicated page)
@app.get("/spectrum", endpoint="spectrum")
def spectrum():
    return render_template(
        "pages/spectrum.html",
        title="GeoTiny EDU · Spectrum analysis",
        active="spectrum",
        STATIONS=STATIONS,
        CHANNELS=CHANNELS
    )

# Data downloads (JSON and CSV)
@app.get("/data", endpoint="data")
def data():
    return render_template(
        "pages/data.html",
        title="GeoTiny EDU · Data downloads",
        active="data",
        STATIONS=STATIONS,
        CHANNELS=CHANNELS
    )

# Education and projects
@app.get("/education", endpoint="education")
def education():
    return render_template(
        "pages/education.html",
        title="GeoTiny EDU · Education and projects",
        active="education"
    )

# Backward compatibility: /lab renders Spectrum
@app.get("/lab", endpoint="lab")
def lab():
    return render_template(
        "pages/spectrum.html",
        title="GeoTiny EDU · Spectrum analysis",
        active="spectrum",
        STATIONS=STATIONS,
        CHANNELS=CHANNELS
    )

# --- END: Clean routes for 5 pages ---

@app.get("/api/wave")
def api_wave():
    """Real-data-only waveform endpoint (NO synthetic fallback)."""
    from flask import request
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
        return {
            "station": station,
            "channel": channel,
            "ok": False,
            "error": "real data acquisition failed (no fallback)",
            "detail": str(e),
        }, 503


def api_spectrum():
    """Real-data-only FFT endpoint (NO synthetic fallback)."""
    from flask import request
    station = request.args.get("station", "GTN34")
    channel = request.args.get("channel", "SHZ")
    window_s = float(request.args.get("window_s", "10"))
    fmax = float(request.args.get("fmax", "50"))
    try:
        d = _load_last_window(station, channel, window_s)
        freq_hz, mag, dom_f = _fft_mag(d["wave"], d["fs"], fmax=fmax)
        return {
            "station": station,
            "channel": channel,
            "fs": d["fs"],
            "window_s": window_s,
            "freq_hz": freq_hz,
            "mag": mag,
            "dominant_hz": dom_f,
            "source": "miniseed",
            "path": d["path"],
            "ok": True,
        }
    except Exception as e:
        return {
            "station": station,
            "channel": channel,
            "ok": False,
            "error": "real FFT failed (no fallback)",
            "detail": str(e),
        }, 503

def api_wave_csv():
    j = api_wave().get_json()
    lines = ["t_s,x"]
    for t, x in zip(j["time_s"], j["wave"]):
        lines.append(f"{t},{x}")
    out = "\n".join(lines) + "\n"
    return Response(out, mimetype="text/csv", headers={"Content-Disposition": "attachment; filename=waveform.csv"})

@app.get("/api/spectrum.csv")
def api_spectrum_csv():
    j = api_spectrum().get_json()
    lines = ["f_hz,mag"]
    for f, m in zip(j["freq_hz"], j["mag"]):
        lines.append(f"{f},{m}")
    out = "\n".join(lines) + "\n"
    return Response(out, mimetype="text/csv", headers={"Content-Disposition": "attachment; filename=spectrum.csv"})

@app.get("/api/global_quakes")
def api_global_quakes():
    url = "https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/all_day.geojson"
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
    return jsonify(ok=True, count=len(out), quakes=out)

# ---------------------------------------------------------------------
# Vendor UI reverse proxies (same-origin)
# ---------------------------------------------------------------------

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
    Reverse proxy to vendor endpoint, including:
      - server-side Basic Auth (from env)
      - remove CSP / frame blockers
      - rewrite Location redirects to our proxy paths
      - rewrite absolute links inside HTML/JS/CSS
    """
    base = os.environ.get(env_var, default_base).rstrip("/")

    user = os.environ.get("GEOTINY_VENDOR_USER", "")
    pw   = os.environ.get("GEOTINY_VENDOR_PASS", "")
    auth = (user, pw) if user and pw else None

    # Build outgoing URL
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

            # broken VIEW jump
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

        
        # Also rewrite root-relative links so the UI stays inside /vendor/...
        # Example: href="/sys" -> href="/vendor/sys"
        txt = re.sub(r'(?i)\b(href|src|action)="/(?!vendor/|vendor8091/|static/|api/|healthz\b)([^"]*)"',
                     r'\1="/vendor/\2"', txt)

        return txt.encode("utf-8", "ignore")

    # Forward headers
    fwd_headers = {}
    for k, v in request.headers.items():
        lk = k.lower()
        if lk in HOP_HEADERS:
            continue
        if lk in {"host", "accept-encoding"}:
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
        verify=False,  # vendor uses self-signed cert
        auth=auth,
    )

    # Return headers (strip CSP / frame blockers) + rewrite Location
    out_headers = []
    for k, v in rr.headers.items():
        lk = k.lower()
        if lk in HOP_HEADERS:
            continue
        if lk in {"x-frame-options", "content-security-policy"}:
            continue
        if lk in {"content-encoding", "content-length"}:
            continue
        if lk == "location":
            v = _rewrite_location(v)
        out_headers.append((k, v))

    body = _maybe_rewrite_body(rr.content, rr.headers.get("Content-Type", ""))
    return Response(body, status=rr.status_code, headers=out_headers)

# --- 9091: main vendor UI (config/data pages etc.) ---
@app.get("/vendor/", endpoint="vendor_9091_root")
@app.get("/vendor/<path:subpath>", endpoint="vendor_9091_path")
def vendor_proxy(subpath: str = ""):
    return _proxy_to("GEOTINY_VENDOR_URL", "https://10.0.18.34:9091/", subpath)

# --- 8091: WebSWave VIEW popup target ---
@app.get("/vendor8091/", endpoint="vendor_8091_root")
@app.get("/vendor8091/<path:subpath>", endpoint="vendor_8091_path")
def vendor8091_proxy(subpath: str = ""):
    return _proxy_to("GEOTINY_VENDOR_WAVE_URL", "http://127.0.0.1:8051/", subpath)

# (disabled) Early run blocked route registration; keep only a single run at the end.
# if __name__ == "__main__":
#     port = int(os.environ.get("PORT", "8051"))
#     app.run(host="0.0.0.0", port=8050)
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8050)

@app.get("/api/spectrum")
def api_spectrum():
    """Real-data-only FFT endpoint (NO synthetic fallback)."""
    from flask import request
    station = request.args.get("station", "GTN34")
    channel = request.args.get("channel", "SHZ")
    window_s = float(request.args.get("window_s", "10"))
    fmax = float(request.args.get("fmax", "50"))

    try:
        d = _load_last_window(station, channel, window_s)
        import numpy as np
        y = np.asarray(d["wave"], dtype=np.float64)
        n = int(y.size)
        w = np.hanning(n)
        Y = np.fft.rfft(y * w)
        f = np.fft.rfftfreq(n, d=1.0/d["fs"])
        mag = np.abs(Y)
        fmax_eff = min(float(fmax), float(d["fs"])/2.0)
        m = f <= fmax_eff
        f2 = f[m]
        mag2 = mag[m]
        dom_f = 0.0
        if f2.size > 2:
            idx = int(np.argmax(mag2[1:])) + 1
            dom_f = float(f2[idx])

        return {
            "station": station,
            "channel": channel,
            "fs": d["fs"],
            "window_s": window_s,
            "freq_hz": f2.tolist(),
            "mag": mag2.tolist(),
            "dominant_hz": dom_f,
            "source": "miniseed",
            "path": d.get("path"),
            "ok": True,
        }
    except Exception as e:
        return {
            "station": station,
            "channel": channel,
            "ok": False,
            "error": "real FFT failed (no fallback)",
            "detail": str(e),
        }, 503

@app.get("/spectrum")
def spectrum():
    return render_template("pages/spectrum.html",
                           title="GeoTiny EDU · Spectrum",
                           active="spectrum",
                           STATIONS=STATIONS,
                           CHANNELS=CHANNELS)

# --- GeoTiny EDU: USGS last-24h proxy (idempotent) ---
try:
    @app.route("/api/global_quakes", methods=["GET"])
    def api_global_quakes():
        url = "https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/all_day.geojson"
        try:
            r = requests.get(url, timeout=6)
            r.raise_for_status()
            j = r.json()
            feats = j.get("features", []) if isinstance(j, dict) else []
            return jsonify(ok=True, features=feats)
        except Exception as e:
            return jsonify(ok=False, error=str(e)), 502
except Exception:
    # If app is not yet defined in import order, define a no-op placeholder route later.
    pass

if __name__ == "__main__":
    try:
        app
        app.run(host="0.0.0.0", port=8050)
    except NameError:
        from flask import Flask
        app = Flask(__name__)
        app.run(host="0.0.0.0", port=8050)

# Simple 5-min cache for USGS
_USGS_CACHE = {"t": 0, "data": None}
@app.route("/api/global_quakes", methods=["GET"])
def api_global_quakes():
    import time, requests
    if _USGS_CACHE["data"] and time.time() - _USGS_CACHE["t"] < 300:
        return jsonify(_USGS_CACHE["data"])
    url = "https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/all_day.geojson"
    try:
        r = requests.get(url, timeout=6)
        r.raise_for_status()
        j = r.json()
        feats = j.get("features", []) if isinstance(j, dict) else []
        data = {"ok": True, "features": feats}
        _USGS_CACHE.update({"t": time.time(), "data": data})
        return jsonify(data)
    except Exception as e:
        return jsonify(ok=False, error=str(e)), 502

# --- BEGIN: Education route (single, correct endpoint) ---


# Make sure this is the ONLY /education route in app.py
@app.route('/education', endpoint='education')
def education():
    # Renders /srv/learnlab/geotiny-edu/templates/pages/education.html
    return render_template('pages/education.html')
# --- END: Education route ---
# ----- Register Education blueprint (safe for factory-less apps) -----


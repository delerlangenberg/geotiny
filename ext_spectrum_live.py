def attach_spectrum_live(app):
    from flask import request, jsonify
    import numpy as _np
    import sys

    # Resolve loader from either the app module or __main__
    loader = None
    try:
        from app import _load_last_window as loader
    except Exception:
        pass
    if loader is None:
        try:
            from app import load_last_window as loader  # alternate name without underscore
        except Exception:
            pass
    if loader is None:
        main_mod = sys.modules.get('__main__')
        if main_mod is not None:
            loader = getattr(main_mod, '_load_last_window', None) or getattr(main_mod, 'load_last_window', None)

    def _welch_amp2(wave, fs, nperseg, noverlap, fmax=None):
        x = _np.asarray(wave, dtype=float)
        n = x.size
        if n < max(2, nperseg) or not fs or fs <= 0:
            return _np.array([]), _np.array([]), {"fs": fs, "N": n, "method": "welch2"}

        x = x - _np.mean(x)  # record mean removal

        hop = max(1, nperseg - noverlap)
        nseg = 1 + (n - nperseg) // hop
        if nseg < 1:
            return _np.array([]), _np.array([]), {"fs": fs, "N": n, "method": "welch2"}

        win = _np.hanning(nperseg)
        cg = win.sum() / nperseg  # coherent gain
        freq = _np.fft.rfftfreq(nperseg, d=1.0/fs)
        P = _np.zeros_like(freq, dtype=float)

        for s in range(nseg):
            i0 = s * hop
            seg = x[i0:i0 + nperseg]
            if seg.size != nperseg:
                break
            seg = seg - _np.mean(seg)
            X = _np.fft.rfft(seg * win)
            S = ( _np.abs(X) / (nperseg * cg) )**2
            if nperseg % 2 == 0:
                if S.size > 2:
                    S[1:-1] *= 2.0
            else:
                if S.size > 1:
                    S[1:] *= 2.0
            P += S

        P /= max(1, nseg)
        mag = _np.sqrt(P)

        if fmax is not None:
            sel = freq <= float(fmax)
            freq = freq[sel]
            mag = mag[sel]

        return freq, mag, {"fs": fs, "N": n, "method": "welch2", "window": "hann"}

    @app.get("/api/spectrum_live")
    def api_spectrum_live():
        try:
            station = request.args.get("station", "GTN34")
            channel = request.args.get("channel", "SHZ")
            duration_s = float(request.args.get("duration_s", "60"))
            fmax = float(request.args.get("fmax", "50"))

            if loader is None:
                return jsonify({
                    "freq_hz": [],
                    "mag": [],
                    "dominant_hz": None,
                    "fs": None,
                    "window_s": request.args.get("duration_s", "60"),
                    "avg": "welch",
                    "error": "internal loader function not found in app"
                }), 200

            d = loader(station, channel, duration_s)
            fs = d["fs"]; x = d["wave"]

            nperseg = int(max(256, round(duration_s * fs)))  # ~4 s segments
            noverlap = nperseg // 2
            freq_hz, mag, _meta = _welch_amp2(x, fs, nperseg=nperseg, noverlap=noverlap, fmax=fmax)

            dom = None
            if getattr(freq_hz, "size", 0) and getattr(mag, "size", 0):
                dom = float(freq_hz[int(_np.argmax(mag))])

            return jsonify({
                "freq_hz": freq_hz.tolist() if hasattr(freq_hz, "tolist") else [],
                "mag": mag.tolist() if hasattr(mag, "tolist") else [],
                "dominant_hz": dom,
                "fs": fs,
                "window_s": duration_s,
                "avg": "welch",
                "method": "welch_hann_amplitude"
            })
        except Exception as e:
            return jsonify({
                "freq_hz": [],
                "mag": [],
                "dominant_hz": None,
                "fs": None,
                "window_s": request.args.get("duration_s", "60"),
                "avg": "welch",
                "error": str(e)
            }), 200

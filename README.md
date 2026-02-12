# Geotiny Seismometer Project (Skeleton)

A clean, user‑friendly structure for your Geotiny + Raspberry Pi seismic project.

> Note: I couldn't open the uploaded `seismo.7z` in this environment because the 7z tools are not installed here.  
> Please re‑upload the project as a `.zip` (or `.tar.gz`) **or** upload the already‑extracted folder.  
> Once uploaded, I can automatically sort every file and hand back a clean, packaged bundle.

## Quick Start (when data is present)

1. Put raw files (e.g., `.mseed`, `.sac`, `.wav`, raw `.csv`/`.json`) into `data/raw/`.
2. Configure connection and parsing in `config/geotiny.yml` (placeholder file below).
3. Run `scripts/convert_to_csv.py` to create quick summaries (requires `obspy` if you want waveform parsing).
4. Explore data using `notebooks/01_quicklook.ipynb`.
5. Save derived tables in `data/processed/` and figures/reports in `output/`.

## Structure

```
seismo_clean/
├─ data/
│  ├─ raw/
│  └─ processed/
├─ notebooks/
├─ scripts/
├─ config/
├─ docs/
├─ env/
├─ logs/
├─ output/
└─ misc/
```

## Raspberry Pi + Geotiny tips

- Ensure Geotiny is reachable over Ethernet (static IP or DHCP reservation).
- On the Pi, install Python 3.10+, `numpy`, `pandas`, `matplotlib`; `obspy` is optional but useful.
- Use the pull script below to fetch files from Geotiny to the Pi or to your NAS.
- Schedule periodic pulls with `cron` or a `systemd` timer.

## Re‑upload instructions

- On macOS: right‑click the folder → “Compress”. Upload the resulting `.zip`.
- On Linux: `zip -r seismo.zip /path/to/folder` and upload `seismo.zip`.
- On Windows: right‑click → “Send to → Compressed (zipped) folder”.

---

Clean skeleton created: 2025-11-11T15:00:20

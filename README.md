# Geotiny Seismometer Project

A clean, user-friendly framework for your Geotiny + Raspberry Pi seismic data acquisition and analysis project.

## 🌍 Overview

This project provides a complete toolkit for:
- Connecting to Geotiny seismometer devices
- Acquiring seismic data in real-time
- Converting and processing waveform data
- Visualizing seismograms and spectrograms
- Analyzing seismic events

## 📦 Installation

### Prerequisites

- Python 3.10 or higher
- Raspberry Pi (optional, for field deployment)
- Geotiny seismometer device

### Setup

```bash
# Clone the repository
git clone <your-repo-url> geotiny
cd geotiny

# Create virtual environment
python -m venv env
source env/bin/activate  # On Windows: env\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

## 🚀 Quick Start

### 1. Configure Your Device

Edit `config/geotiny.yml` to match your setup:

```yaml
device:
  ip_address: "192.168.1.100"  # Your Geotiny IP
  port: 8080

acquisition:
  sampling_rate: 100  # Hz
  channels: 3  # X, Y, Z
```

### 2. Fetch Data

```bash
# Fetch data for 5 minutes
python scripts/fetch_data.py --duration 300

# Run continuously
python scripts/fetch_data.py --continuous
```

### 3. Convert to CSV

```bash
# Convert all miniSEED files to CSV
python scripts/convert_to_csv.py data/raw/ --output data/processed/
```

### 4. Visualize

```bash
# Plot CSV data
python scripts/plot_data.py data/processed/seismo_20260215_120000.csv

# Save plots
python scripts/plot_data.py data/processed/ --output output/plots/
```

### 5. Analyze in Jupyter

```bash
jupyter lab notebooks/01_quickstart.ipynb
```

## 📂 Project Structure

```
geotiny/
├── config/              # Configuration files
│   └── geotiny.yml     # Device and acquisition settings
├── data/
│   ├── raw/            # Raw seismic data (miniSEED, SAC, etc.)
│   └── processed/      # Converted CSV files
├── scripts/            # Utility scripts
│   ├── fetch_data.py   # Data acquisition
│   ├── convert_to_csv.py  # Format conversion
│   └── plot_data.py    # Quick visualization
├── notebooks/          # Jupyter notebooks for analysis
│   └── 01_quickstart.ipynb
├── output/             # Generated plots and reports
├── logs/               # Application logs
├── env/                # Virtual environment
└── requirements.txt    # Python dependencies
```

## 🔧 Configuration Options

### Device Connection

- **Ethernet**: Set `connection: ethernet` and provide IP/port
- **Serial**: Set `connection: serial` and provide serial port/baud rate

### Data Formats

Supported formats:
- **miniSEED** (.mseed) - Standard seismology format
- **SAC** (.sac) - Seismic Analysis Code format
- **CSV** (.csv) - For easy analysis in Excel/Python

### Processing

Configure filters and processing in `config/geotiny.yml`:
- Bandpass filtering
- Detrending
- Instrument response removal

## 🌐 Raspberry Pi Deployment

### Auto-start on Boot

```bash
# Add to crontab
crontab -e

# Add this line:
@reboot cd /home/pi/geotiny && /home/pi/geotiny/env/bin/python scripts/fetch_data.py --continuous >> logs/acquisition.log 2>&1
```

### Sync to NAS

Enable in `config/geotiny.yml`:

```yaml
raspberry_pi:
  sync_to_nas: true
  nas_path: "/mnt/nas/seismo/"
  sync_interval: 3600  # seconds
```

## 📊 Data Analysis

The included Jupyter notebook provides:
- Time series visualization
- Frequency analysis (FFT)
- Spectrogram generation
- Event detection
- Statistical summaries

## 🛠️ Development

### Adding Custom Processing

Create new scripts in `scripts/` or add processing functions to notebooks.

### Custom Formats

Extend `convert_to_csv.py` to support additional data formats.

## 🔍 Troubleshooting

### Connection Issues

- Verify Geotiny IP address with `ping <ip-address>`
- Check firewall settings
- Ensure Geotiny is powered on and connected

### Missing Data

- Check `logs/` directory for error messages
- Verify write permissions on `data/` directories
- Ensure sufficient disk space

### ObsPy Installation

If ObsPy fails to install:
```bash
# On Raspberry Pi, install system dependencies first
sudo apt-get install python3-dev python3-numpy python3-scipy
pip install obspy
```

## 📝 Notes

- **Sampling Rate**: Geotiny typically operates at 100 Hz
- **Storage**: Plan for ~10 MB/hour of continuous data (compressed miniSEED)
- **Power**: Ensure stable power supply for continuous acquisition

## 📄 License

MIT License - Feel free to use and modify as needed.

## 👤 Author

Dr. Deler Langenberg

---

**Status**: Framework ready - implement device-specific communication protocols

*Last updated: 2026-02-15*

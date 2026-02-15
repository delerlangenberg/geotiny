# Geotiny Web Interface

Professional real-time seismic monitoring dashboard for the Geotiny seismic sensor network.

## Quick Start

### Prerequisites
- Python 3.8+
- pip (Python package manager)

### Installation

1. **Install backend dependencies:**
```bash
pip install -r requirements-web.txt
```

2. **Run the development server:**
```bash
python app.py
```

The dashboard will be available at `http://localhost:5000`

### Running in Production

```bash
# Using gunicorn with SocketIO support
pip install gunicorn python-socketio python-engineio
gunicorn --worker-class eventlet -w 1 --bind 0.0.0.0:5000 app:app
```

## Project Structure

```
web/
├── app.py                      # Main Flask application
├── requirements-web.txt        # Python dependencies
├── api/                        # API modules
│   ├── devices.py             # Device communication & data acquisition
│   ├── spectrum.py            # FFT and spectrogram analysis
│   ├── global_seismic.py      # USGS earthquake data integration
│   └── vendor.py              # Geotiny device specifications
├── templates/                  # HTML templates
│   ├── base.html              # Base template with navigation
│   ├── dashboard.html         # Main dashboard
│   ├── spectrum.html          # Spectrum analysis page
│   ├── global.html            # Global earthquake monitoring
│   └── about.html             # About and educational content
└── static/                     # Static files
    ├── css/
    │   └── style.css          # Custom styles
    └── js/
        └── utils.js           # Frontend utilities
```

## API Endpoints

### Device Status
- `GET /api/devices/status` - Get status of all 3 devices
- `GET /api/devices/<device_id>/info` - Get device specifications

### Spectrum Analysis
- `POST /api/spectrum/analyze` - Comprehensive spectrum analysis
- `POST /api/spectrum/fft` - Compute FFT for a device/channel
- `POST /api/spectrum/spectrogram` - Compute spectrogram

Request body example:
```json
{
    "device_id": "device_1",
    "channel": "Z",
    "time_window": "10min"
}
```

### Global Seismic Data
- `GET /api/global/earthquakes?min_magnitude=5.0&time_period=1day` - Recent earthquakes
- `GET /api/global/earthquakes/<event_id>` - Earthquake details

### Vendor Information
- `GET /api/vendor/info` - Geotiny device specifications

### System
- `GET /health` - Health check

## WebSocket Events

The frontend connects via WebSocket for real-time data streaming.

### Client → Server
- `subscribe_device` - Subscribe to device data stream
- `unsubscribe_device` - Unsubscribe from device
- `request_waveform` - Request waveform data

### Server → Client
- `waveform_data` - Streaming waveform data
- `connection_response` - Connection acknowledgement
- `error` - Error messages

## Frontend Pages

### Dashboard (`/`)
Real-time monitoring of all 3 devices with:
- Live waveforms (Z channel)
- Current amplitude values (X, Y, Z)
- System status overview
- Buffer statistics
- Vendor information card
- Global earthquake alert

### Spectrum Analysis (`/spectrum`)
Detailed frequency domain analysis with:
- Device selector
- Time-window selector (1, 10, 30 min)
- FFT magnitude spectrum (dB)
- Spectrogram (power vs time vs frequency)
- Peak frequency identification
- Educational annotations

### Global Seismic (`/global`)
Worldwide earthquake monitoring featuring:
- Interactive map (Leaflet.js)
- Earthquake event list (filterable)
- Magnitude and depth information
- USGS data integration
- Time-based filtering
- Real-time statistics

### About (`/about`)
Educational content including:
- Project overview
- Learning objectives
- Hardware specifications
- Getting started guide
- Technical stack
- External resources

## Configuration

Default configuration in `app.py`:
```python
device_manager.device_config = {
    'device_1': {'ip': '192.168.1.100', 'port': 8080},
    'device_2': {'ip': '192.168.1.101', 'port': 8080},
    'device_3': {'ip': '192.168.1.102', 'port': 8080},
}
```

Modify device IPs/ports to match your network setup.

## Data Acquisition

The DeviceManager continuously acquires data from the 3 Geotiny devices:
- Sampling rate: 100 Hz
- 3 channels per device (X, Y, Z accelerometers)
- Circular buffer stores last 30 seconds of data per channel
- WebSocket streams data to connected clients
- Background thread handles reconnection logic

## Signal Processing

SpectrumAnalyzer provides:
- FFT using scipy.fft
- Hann window for spectral leakage reduction
- Power spectrogram using scipy.signal.spectrogram
- dB scale normalization
- Peak detection
- Statistics computation

Time windows:
- 1 minute = 6,000 samples @ 100 Hz
- 10 minutes = 60,000 samples @ 100 Hz
- 30 minutes = 180,000 samples @ 100 Hz

## Global Earthquake Data

Integrated with USGS Earthquake Hazards Program API:
- Real-time earthquake data
- Magnitude, location, depth
- Time-based filtering (1 day, 7 days, 30 days)
- 5-minute caching to limit API calls
- Automatic refresh in frontend (1-minute intervals)

## Troubleshooting

### Devices not connecting
1. Check device IP addresses in `app.py`
2. Verify devices are on the LAN
3. Ping devices: `ping 192.168.1.100`
4. Check firewall settings

### No waveform data appearing
1. Verify devices are powered on
2. Check logs in `logs/geotiny_web.log`
3. Ensure network connectivity
4. Try reconnecting in the browser (F5)

### USGS API errors
- Check internet connectivity
- Verify API is accessible: `curl https://earthquake.usgs.gov/fdsnws/event/1/query`
- System retries after 5 minutes if initial request fails

### Performance issues
- Reduce WebSocket update frequency in `app.py`
- Use time-window decimation for large datasets
- Clear browser cache (Ctrl+Shift+Del)
- Reduce number of active client connections

## Development

### Adding new endpoints
```python
@app.route('/api/new/endpoint', methods=['GET', 'POST'])
def new_endpoint():
    try:
        # Implementation
        return jsonify({'status': 'success', 'data': result})
    except Exception as e:
        logger.error(f"Error: {str(e)}")
        return jsonify({'status': 'error', 'message': str(e)}), 500
```

### Adding new pages
1. Create template in `templates/new_page.html` extending `base.html`
2. Add route in `app.py`
3. Add navigation link in `base.html`

### Testing
```bash
pip install pytest pytest-flask
pytest
```

## Deployment

### Docker Deployment
```dockerfile
FROM python:3.10-slim
WORKDIR /app
COPY requirements-web.txt .
RUN pip install -r requirements-web.txt
COPY . .
CMD ["python", "app.py"]
```

### Systemd Service (Linux)
```ini
[Unit]
Description=Geotiny Web Interface
After=network.target

[Service]
Type=simple
User=www-data
WorkingDirectory=/opt/geotiny/web
ExecStart=/usr/bin/python3 app.py
Restart=on-failure

[Install]
WantedBy=multi-user.target
```

## Security Notes

- Change `SECRET_KEY` in production (use environment variable)
- Use HTTPS in production (nginx with SSL proxy)
- Implement authentication for sensitive endpoints
- Rate limit API endpoints
- Validate all user inputs
- Keep dependencies updated

## Performance Specifications

- Real-time streaming: 100 Hz × 3 devices × 3 channels = 900 samples/sec
- Data rate: ~3.6 KB/s (IEEE 754 floats)
- Supporting ~50 concurrent WebSocket connections
- FFT computation: <100ms for 10-minute window
- Spectrogram computation: <200ms for 10-minute window

## License

MIT License - See LICENSE file

## Support

For issues or questions:
1. Check logs in `logs/geotiny_web.log`
2. Review GitHub issues
3. Contact: support@geotiny.com

---

**Version**: 1.0.0  
**Status**: Beta  
**Last Updated**: 2026-02-15

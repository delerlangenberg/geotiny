# Quick Start Guide for Geotiny Web Platform

## What's Included

The Geotiny web platform provides a complete monitoring solution with three main modules:

### 1. **Dashboard** - Real-time Device Monitoring
- Live waveform visualization from all 3 seismic devices
- Real-time data streaming via WebSocket
- Device status tracking and earthquake preview
- 30-second automatic data refresh

### 2. **Spectrum Analysis** - Frequency Domain Analysis
- FFT (Fast Fourier Transform) analysis
- Spectrogram (time-frequency) visualization
- Flexible time window selection (1min/10min/30min)
- Peak frequency and magnitude detection

### 3. **Global Seismic** - Earthquake Monitoring
- Interactive world map with real-time earthquakes
- Magnitude-based filtering and visualization
- USGS earthquake data integration
- Event details and statistics

## Installation & Setup

### Prerequisites
- Python 3.8+
- pip or conda package manager
- Modern web browser (Chrome, Firefox, Safari, Edge)

### Step 1: Install Dependencies
```bash
cd web
pip install -r requirements.txt
```

### Step 2: Start the Server
```bash
python run.py
```

Server will start on `http://localhost:5000`

### Step 3: Access the Web Interface
- Dashboard: http://localhost:5000
- Spectrum: http://localhost:5000/spectrum
- Global: http://localhost:5000/global
- About: http://localhost:5000/about

## Architecture

```
Frontend Layer (Browser)
├── dashboard.js      (Real-time waveforms)
├── spectrum.js       (FFT/Spectrogram analysis)
├── global.js         (Earthquake mapping)
└── utils.js          (Shared utilities)

Communication Layer (WebSocket/HTTP)
└── Socket.IO / REST API

Backend Layer (Flask)
├── app.py            (Main application)
├── api/devices.py    (Device communication)
├── api/spectrum.py   (Signal processing)
├── api/global_seismic.py (USGS integration)
└── api/vendor.py     (Device specs)

Data Layer
├── Mock devices      (Testing)
├── USGS API          (Global earthquakes)
└── Local buffers     (30-second circular buffers)
```

## Module Details

### Dashboard Module
**File:** `static/js/dashboard.js`

Features:
- WebSocket connection to backend
- Chart.js waveform visualization
- Device status cards with X/Y/Z channels
- Earthquake preview widget
- Real-time sample counter

Use cases:
- Monitor seismic activity in real-time
- Track device connectivity
- Visualize waveform patterns
- Quick earthquake awareness

### Spectrum Module
**File:** `static/js/spectrum.js`

Features:
- FFT analysis with Plotly visualization
- Spectrogram heatmap display
- Frequency resolution calculations
- Configurable time windows
- Statistical analysis

Use cases:
- Identify dominant frequencies
- Analyze signal characteristics
- Visualize time-frequency patterns
- Compare channels and devices

### Global Seismic Module
**File:** `static/js/global.js`

Features:
- Leaflet.js interactive map
- Magnitude-based marker scaling
- Earthquake event list
- Filtering and statistics
- Auto-refresh every 5 minutes

Use cases:
- Monitor global earthquake activity
- Filter events by magnitude
- Examine event details
- Understand seismic patterns worldwide

## API Endpoints

### Devices
```
GET  /api/devices/status           - Get all devices status
GET  /api/devices/{id}/info        - Get specific device info
GET  /api/devices/{id}/waveform    - Get waveform data
POST /api/devices/health           - Health check
```

### Spectrum
```
POST /api/spectrum/fft              - FFT analysis
POST /api/spectrum/spectrogram      - Spectrogram analysis
```

### Global Seismic
```
GET  /api/global/earthquakes       - Recent earthquakes
GET  /api/global/earthquakes/{id}  - Earthquake details
```

### Utilities
```
GET  /api/vendor/devices           - Device specifications
GET  /health                        - Server health
```

## WebSocket Events

### Subscribe to Device Data
```javascript
socket.emit('subscribe_device', {
    device_id: 'device_1',
    frequency: 10  // Hz
});
```

### Receive Waveform Data
```javascript
socket.on('waveform_data', function(data) {
    // {
    //   device_id: 'device_1',
    //   timestamp: 1699564800,
    //   channels: { X: [...], Y: [...], Z: [...] }
    // }
});
```

## Configuration

Key environment variables:
```bash
FLASK_ENV=development              # development or production
DEBUG=True                         # Enable debug mode
DEVICE_SAMPLE_RATE=100            # Sampling rate (Hz)
DEVICE_BUFFER_DURATION=30         # Buffer duration (seconds)
MOCK_DEVICE_ENABLED=True          # Use mock devices for testing
USGS_API_CACHE_TTL=300            # Cache timeout (seconds)
```

For full configuration details, see [CONFIG.md](CONFIG.md)

## Testing

### Manual Testing
1. Open Dashboard page
2. Verify waveforms update every 100ms (10 Hz)
3. Switch to Spectrum and analyze devices
4. Navigate to Global Seismic and filter earthquakes

### API Testing
```bash
# Test device endpoint
curl http://localhost:5000/api/devices/status

# Test spectrum endpoint
curl -X POST http://localhost:5000/api/spectrum/fft \
  -H "Content-Type: application/json" \
  -d '{"device_id":"device_1","channel":"Z","time_window":"10min"}'

# Test global seismic
curl http://localhost:5000/api/global/earthquakes
```

## Troubleshooting

### Connection Issues
- Ensure server is running: `python run.py`
- Check port 5000 is not in use
- Clear browser cache

### Waveform Not Updating
- Check WebSocket in DevTools Network tab
- Verify backend console for errors
- Ensure mock devices are enabled

### Map Not Loading
- Check internet connection
- Verify Leaflet CDN is accessible
- Clear cache and reload

### USGS Data Missing
- Verify internet connectivity
- Check USGS API status
- Review cache settings in CONFIG.md

## Performance Notes

- **Chart.js:** Real-time updates with auto-decimation >500 points
- **FFT:** Computed in <100ms for 100Hz data
- **Spectrogram:** Computed in <200ms for 10-minute windows
- **WebSocket:** 10 Hz update frequency (100ms interval)

## Deployment

### Development Server
```bash
python run.py
```

### Production Server (gunicorn)
```bash
gunicorn --worker-class=gevent --workers=1 --bind=0.0.0.0:5000 app:app
```

### Docker
```bash
docker build -t geotiny .
docker run -p 5000:5000 geotiny
```

## Next Steps

1. **Configure Real Devices:** Update device IPs in api/devices.py
2. **Persistent Storage:** Set up PostgreSQL for long-term data
3. **Authentication:** Add user authentication for multi-site access
4. **Alerts:** Implement real-time notifications for significant events
5. **Machine Learning:** Add anomaly detection models

## Documentation

- [Architecture Overview](../ARCHITECTURE.md)
- [Frontend Testing Guide](FRONTEND_TESTING.md)
- [Configuration Reference](CONFIG.md)
- [API Documentation](../docs/API.md) (coming soon)

## Support

For issues or feature requests, check:
1. [Frontend Testing Guide](FRONTEND_TESTING.md) - Common issues section
2. [GitHub Issues](https://github.com/delerlangenberg/geotiny/issues)
3. [Backend README](README.md)

## License

See LICENSE file in project root

---

**Version:** 1.0.0  
**Last Updated:** 2024  
**Status:** Production Ready

# Geotiny Frontend Testing Guide

## System Components Overview

### Dashboard (Real-time Monitoring)
**File:** `web/static/js/dashboard.js`

The Dashboard module provides real-time monitoring of all 3 seismic devices with:
- WebSocket connection to Flask backend
- Real-time waveform visualization using Chart.js
- Device status indicators
- Global earthquake preview
- Automatic 30-second data refresh

**Key Features:**
- 3 devices monitored (Device 1, 2, 3)
- X, Y, Z channel display per device
- Real-time sample count tracking
- Connection status indicator
- Periodic earthquake data loading

### Spectrum Analysis
**File:** `web/static/js/spectrum.js`

The Spectrum module provides frequency-domain analysis with:
- FFT (Fast Fourier Transform) visualization
- Spectrogram (time-frequency) analysis
- Time-domain waveform display
- Plotly.js visualization

**Supported Time Windows:**
- 1 minute: 6,000 samples (60 Hz for 100 Hz sampling)
- 10 minutes: 60,000 samples
- 30 minutes: 180,000 samples

**Key Statistics:**
- Frequency resolution (Hz)
- Nyquist frequency (50 Hz for 100 Hz sampling)
- Peak/Mean magnitude (dB)

### Global Seismic Monitoring
**File:** `web/static/js/global.js`

The Global Seismic module integrates USGS earthquake data with:
- Interactive Leaflet.js map
- Real-time earthquake markers with magnitude-based sizing
- Earthquake filtering (magnitude, time period)
- Detailed event information
- Statistics by magnitude category

**Map Features:**
- CartoDB dark tile layer
- Color coding: Red (M7+), Orange (M6+), Yellow (M5+), Cyan/Blue (M<5)
- Click to zoom to earthquake location
- Popup with event details

## Setting Up the Development Environment

### 1. Install Python Dependencies
```bash
cd web
pip install flask==2.3.0
pip install flask-socketio==5.3.4
pip install python-socketio==5.9.0
pip install python-engineio==4.7.1
pip install gevent==23.9.1
pip install gevent-websocket==0.10.1
pip install numpy==1.24.0
pip install scipy==1.10.0
pip install obspy==1.4.0
pip install requests==2.31.0
```

### 2. Start the Backend Server
```bash
cd web
python run.py
# Server will start on http://localhost:5000
```

### 3. Access the Frontend
Open your browser and navigate to:
- Dashboard: http://localhost:5000/
- Spectrum Analysis: http://localhost:5000/spectrum
- Global Seismic: http://localhost:5000/global
- About: http://localhost:5000/about

## Testing Workflows

### Dashboard Testing
1. Open Dashboard page
2. Verify "3 devices online" message (mock devices)
3. Watch waveforms update in real-time every 10 Hz
4. Verify connection status indicator
5. Check "Recent Earthquakes" preview section

**Expected Behavior:**
- Chart.js waveforms animate smoothly
- Sample count increments every update
- Device cards show X/Y/Z channel values
- Green connection indicator when connected

### Spectrum Analysis Testing
1. Navigate to Spectrum Analysis page
2. Select a device and channel
3. Choose time window (1min/10min/30min)
4. Click "Analyze" button

**FFT Tab:**
- Plotly chart shows frequency spectrum
- X-axis: Frequency (Hz), Y-axis: Magnitude (dB)
- Statistics display: resolution, Nyquist frequency, peak magnitude

**Spectrogram Tab:**
- Heatmap shows power over time and frequency
- Colors: Blue (low power) to Red (high power)
- Time resolution increases with longer windows

**Time Domain Tab:**
- Raw waveform visualization
- X-axis: Sample index, Y-axis: Acceleration (m/s²)

### Global Seismic Testing
1. Navigate to Global Seismic page
2. Adjust magnitude slider (0.0-9.0)
3. Select time period (24h/7d/30d)
4. Click "Refresh Data"

**Map Features:**
- Earthquake markers appear with appropriate colors
- Marker size increases with magnitude
- Click markers to see popup details
- Click events in list to zoom to location

**Statistics:**
- Total events count
- Average magnitude by category
- Breakdown by magnitude ranges

## Browser DevTools Testing

### Network Tab
Monitor WebSocket connections:
- Type: websocket
- URL: ws://localhost:5000/socket.io/?...
- Status should be "101 Web Socket Protocol Handshake"

### Console Tab
Check for errors and logs:
- "Connected to server" message on connection
- Device updates logged periodically
- No TypeErrors or ReferenceErrors

### Performance Tab
Monitor performance metrics:
- Chart.js rendering: <50ms per update
- FFT computation: <100ms
- Spectrogram computation: <200ms

## API Endpoint Testing

### Device Endpoints
```bash
# Get all devices status
curl http://localhost:5000/api/devices/status

# Get specific device info
curl http://localhost:5000/api/devices/device_1/info

# Get waveform data
curl http://localhost:5000/api/devices/device_1/waveform?duration=60
```

### Spectrum Endpoints
```bash
# FFT analysis
curl -X POST http://localhost:5000/api/spectrum/fft \
  -H "Content-Type: application/json" \
  -d '{
    "device_id": "device_1",
    "channel": "Z",
    "time_window": "10min"
  }'

# Spectrogram analysis
curl -X POST http://localhost:5000/api/spectrum/spectrogram \
  -H "Content-Type: application/json" \
  -d '{
    "device_id": "device_1",
    "channel": "Z",
    "time_window": "10min"
  }'
```

### Global Seismic Endpoints
```bash
# Get recent earthquakes
curl "http://localhost:5000/api/global/earthquakes"

# With filters
curl "http://localhost:5000/api/global/earthquakes?minmagnitude=5.0&limit=100"
```

## Common Issues and Solutions

### Issue: "Cannot GET /socket.io/"
**Solution:** Ensure Flask-SocketIO is properly installed and the app initialization includes SocketIO

### Issue: "Waveform chart not updating"
**Solution:** Check WebSocket connection in Network tab. Verify backend is emitting `waveform_data` events

### Issue: "Spectrum analysis returns no data"
**Solution:** Ensure mock devices have sufficient data buffered. Check time_window parameter is correct

### Issue: "Map not loading"
**Solution:** Clear browser cache. Verify Leaflet.js CDN is accessible. Check console for CORS errors

### Issue: "USGS API data missing"
**Solution:** Check internet connection. Verify USGS API endpoint is accessible. Check cache TTL settings

## Performance Optimization

### Chart.js Optimization
- Maximum 500 points per chart (auto-decimation)
- Animation disabled for real-time updates
- pointRadius set to 0 for performance

### Plotly Optimization
- Used `displayModeBar: false` to reduce overhead
- Responsive: true for auto-resize

### Database Optimization
- Circular buffers with fixed 30-second length
- Efficient numpy array slicing
- ThreadSafe queue for WebSocket communication

## Deployment Considerations

### Production Setup
1. Use WSGI server (gunicorn/uWSGI) instead of Flask dev server
2. Configure gevent worker class for async operations
3. Use nginx as reverse proxy
4. Enable HTTPS/WSS for secure connections
5. Set up CORS headers if frontend runs on different domain

### Docker Deployment
```dockerfile
FROM python:3.10-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY web/ .
CMD ["gunicorn", "--worker-class", "gevent", "--workers", "1", "--bind", "0.0.0.0:5000", "app:app"]
```

### Environment Variables
```bash
FLASK_ENV=production
DEBUG=False
USGS_API_CACHE_TTL=300  # 5 minutes
SOCKET_IO_ASYNC_HANDLERS=true
```

## Next Steps

1. **Device Integration:**
   - Replace mock device simulator with real TCP/IP connections
   - Implement actual data acquisition from serial/network devices

2. **Data Persistence:**
   - Replace SQLite placeholder with production database
   - Implement data archival and historical queries

3. **Advanced Features:**
   - Machine learning-based anomaly detection
   - Real-time alert system for significant events
   - User authentication and multi-site support

4. **Testing:**
   - Unit tests for API endpoints
   - Integration tests for Socket.IO communication
   - End-to-end tests with Selenium

## References

- [Geotiny Architecture](../ARCHITECTURE.md)
- [Backend README](./README.md)
- [Flask-SocketIO Documentation](https://flask-socketio.readthedocs.io/)
- [Chart.js Documentation](https://www.chartjs.org/)
- [Plotly.js Documentation](https://plotly.com/javascript/)
- [Leaflet.js Documentation](https://leafletjs.com/)

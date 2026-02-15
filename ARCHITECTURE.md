# Geotiny Web Interface Architecture

## Project Vision
Create a professional seismic data visualization platform for the Geotiny project, enabling students at an interdisciplinary transformational university in Austria to:
- Monitor 3 local seismic devices in real-time
- Analyze seismic spectra with adjustable time windows (1min, 10min, 30min)
- View FFT analysis for frequency domain understanding
- Access global seismic data and earthquake information
- Experience professional seismic geology interface design

## Technology Stack

### Backend
- **Framework**: Flask (lightweight, Python-native)
- **WebSocket**: Flask-SocketIO for real-time data streaming
- **Seismic Processing**: ObsPy (standard in seismology)
- **Data Science**: NumPy, Pandas, SciPy for FFT and analysis
- **Database**: SQLite (local) / PostgreSQL (production)

### Frontend
- **HTML5/CSS3**: Professional, responsive design inspired by USGS/IRIS seismic platforms
- **Chart.js / Plotly.js**: Real-time waveform and spectrogram visualization
- **Bootstrap 5**: Responsive grid layout
- **JavaScript**: Real-time data updates via WebSocket

### Data Sources
1. **Local Devices**: 3 Geotiny seismometers (Ethernet, 100 Hz sampling)
2. **Global Data**: USGS Earthquake Hazards Program API
3. **External Vendor Page**: Embedded iframe/card showing Geotiny specs

## Page Structure

### 1. Dashboard / Home Page
- **Purpose**: Overview of all 3 local seismic stations
- **Components**:
  - Real-time waveform traces (Z, N, E channels)
  - Status indicators for each device
  - Current earthquake activity widget
  - Navigation to detailed views
- **Layout**: Professional seismic monitoring aesthetic

### 2. Spectrum Analysis Page
- **Purpose**: Detailed frequency domain analysis with time-window selection
- **Features**:
  - Time-window selector: 1 min / 10 min / 30 min
  - Real-time waveform display
  - FFT spectrum (magnitude and phase)
  - Spectrogram (power vs time vs frequency)
  - Station selector (device 1, 2, or 3)
  - Channel selector (X, Y, Z)
- **Educational Features**:
  - Toggle between time-domain and frequency-domain views
  - Nyquist frequency indicator
  - Annotation of signal harmonics
  - Peak frequency highlighting

### 3. Vendor Information Card
- **Purpose**: Display Geotiny device specifications and vendor information
- **Location**: Embedded on main dashboard + dedicated section
- **Content**:
  - Device specifications
  - Sampling rate, resolution, frequency response
  - Link to official vendor page
  - Contact information

### 4. Global Seismic Data Page
- **Purpose**: Monitor worldwide earthquake activity and seismic events
- **Features**:
  - Interactive world map showing recent earthquakes (USGS API)
  - Magnitude and depth filtering
  - Time range selection (last 24h, 1 week, 1 month)
  - Event list with magnitude, location, depth
  - Click-to-view event details and waveforms (if available)
  - Real-time earthquake alerts
- **Data Source**: USGS Earthquake Hazards Program API
- **Professional Design**: Similar to USGS/IRIS online platforms

### 5. About / Educational Page
- **Content**: Project overview for students
- **Sections**:
  - Introduction to seismology
  - How Geotiny devices work
  - Local network setup
  - Data interpretation guide
  - Links to external resources

## Data Flow Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    Web Browser                          │
│              (Dashboard + Analysis Views)               │
└────────────────────┬────────────────────────────────────┘
                     │ WebSocket
                     ▼
┌─────────────────────────────────────────────────────────┐
│              Flask Backend Server                       │
│  ┌──────────────────────────────────────────────────┐  │
│  │  WebSocket Handler (Real-time data streaming)   │  │
│  │  REST API Endpoints (Static data, config)       │  │
│  │  Data Processing (FFT, filtering)               │  │
│  │  Database Manager (SQLite/PostgreSQL)           │  │
│  └──────────────────────────────────────────────────┘  │
└────┬──────────────────────────────────────────────┬────┘
     │ Ethernet                                     │ HTTP
     ▼                                              ▼
┌──────────────┐ ┌──────────────┐ ┌──────────────┐  ┌──────────────────┐
│  Geotiny #1  │ │  Geotiny #2  │ │  Geotiny #3  │  │  USGS API Server │
│ 192.168.1.x  │ │ 192.168.1.y  │ │ 192.168.1.z  │  │  Global Seismic  │
│  Port 8080   │ │  Port 8080   │ │  Port 8080   │  │  Data            │
└──────────────┘ └──────────────┘ └──────────────┘  └──────────────────┘
```

## Project Structure

```
geotiny/
├── config/
│   ├── geotiny.yml                 # Device configuration
│   └── app_config.yml              # Web app configuration
├── web/                            # NEW: Web interface
│   ├── app.py                      # Flask application entry point
│   ├── requirements-web.txt        # Web dependencies
│   ├── templates/
│   │   ├── base.html              # Base template
│   │   ├── dashboard.html         # Home/dashboard page
│   │   ├── spectrum.html          # Spectrum analysis page
│   │   ├── global.html            # Global seismic data page
│   │   ├── about.html             # About/educational page
│   │   └── vendor.html            # Vendor info card (component)
│   ├── static/
│   │   ├── css/
│   │   │   ├── style.css          # Main stylesheet
│   │   │   ├── spectrum.css       # Spectrum view specific
│   │   │   └── global.css         # Global view specific
│   │   ├── js/
│   │   │   ├── app.js             # Main app logic
│   │   │   ├── websocket.js       # Real-time data handler
│   │   │   ├── spectrum.js        # Spectrum analysis logic
│   │   │   ├── global.js          # Global data handler
│   │   │   ├── vendor-card.js     # Vendor card interactions
│   │   │   └── chart-utils.js     # Chart.js utilities
│   │   └── images/
│   │       └── vendor-logo.png
│   └── api/
│       ├── devices.py             # Device API endpoints
│       ├── spectrum.py            # Spectrum API endpoints
│       ├── global.py              # Global data API endpoints
│       └── vendor.py              # Vendor info API
│
├── data/
│   ├── raw/                       # Raw seismic data
│   └── processed/                 # Processed data
├── scripts/
│   ├── fetch_data.py              # Data acquisition
│   ├── convert_to_csv.py          # Format conversion
│   ├── plot_data.py               # Visualization
│   └── start_web.py               # NEW: Start web server
├── notebooks/
│   └── 01_quickstart.ipynb
├── docs/                          # NEW: Documentation
│   ├── USER_GUIDE.md
│   ├── DEVELOPER_GUIDE.md
│   └── API_REFERENCE.md
├── tests/                         # NEW: Test suite
│   ├── test_devices.py
│   ├── test_spectrum.py
│   └── test_global_api.py
├── logs/
├── README.md
├── requirements.txt               # Original dependencies
└── ARCHITECTURE.md                # This file
```

## Phase 1: Architecture & Planning (Current)
- ✅ Define technology stack
- ✅ Design page structure
- ✅ Plan data flow
- Create this architecture document

## Phase 2: Backend Foundation
- [ ] Create Flask app structure
- [ ] Implement Geotiny device communication
- [ ] Build WebSocket server for real-time data
- [ ] Create REST API endpoints
- [ ] Implement FFT/spectrum processing

## Phase 3: Frontend - Dashboard
- [ ] Create base HTML template with professional styling
- [ ] Build real-time waveform display
- [ ] Implement device status indicators
- [ ] Add vendor information card
- [ ] Create responsive layout

## Phase 4: Frontend - Spectrum Analysis
- [ ] Build spectrum analysis interface
- [ ] Implement time-window selector (1/10/30 min)
- [ ] Create FFT visualization
- [ ] Add spectrogram display
- [ ] Implement channel/station selector

## Phase 5: Frontend - Global Seismic Data
- [ ] Integrate USGS Earthquake API
- [ ] Create interactive world map
- [ ] Implement earthquake event list
- [ ] Add filtering and search
- [ ] Create event detail view

## Phase 6: Deployment & Polish
- [ ] Testing and quality assurance
- [ ] Documentation (user and developer guides)
- [ ] Deployment scripts
- [ ] Performance optimization
- [ ] Educational materials for students

## Key Technology Decisions

### Why Flask?
- Lightweight and Pythonic
- Perfect for scientific applications
- Easy integration with ObsPy and NumPy
- WebSocket support via Flask-SocketIO
- Excellent for educational projects

### Why Chart.js + Plotly.js?
- Chart.js: Lightweight, fast real-time updates
- Plotly.js: Professional scientific visualizations
- Both have educational documentation

### Why USGS API?
- Free, reliable, well-documented
- Real-time earthquake data
- Global coverage
- No authentication required for basic access

## Professional Design Principles

The interface will follow professional seismic monitoring standards:
- **Color scheme**: Dark background (like USGS NEIC), bright overlays
- **Waveform traces**: Standard seismo plot styling (Z on top, E in middle, N on bottom)
- **FFT plots**: Log-scale frequency axis (industry standard)
- **Status indicators**: Traffic light colors (green=good, yellow=warning, red=alert)
- **Typography**: Clean, readable fonts with proper contrast
- **Responsive design**: Works on desktop, tablet, mobile

## Data Retention & Privacy

- Local device data: Stored locally in SQLite
- Global API data: Cached for 1 hour, then refreshed
- No user personal data collection
- Educational use only
- Compliant with GDPR (no tracking)

## Performance Considerations

- WebSocket connection pooling
- Data decimation for large time windows
- FFT computation in background thread
- Caching of USGS API results
- Database indexing for fast queries

## Security Considerations

- Local device communication only (LAN)
- No remote access by default
- API rate limiting (USGS)
- CSRF protection on forms
- Input validation on all endpoints

---

**Status**: Architecture designed, ready for Phase 2 implementation
**Last Updated**: 2026-02-15

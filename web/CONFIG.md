# Configuration for Geotiny Web Application

## Environment Variables
```bash
# Flask Configuration
FLASK_APP=app.py
FLASK_ENV=development
DEBUG=True

# Server Configuration
HOST=0.0.0.0
PORT=5000

# Socket.IO Configuration
SOCKET_IO_ASYNC_MODE=gevent  # or 'threading', 'eventlet'
SOCKET_IO_CORS_ALLOWED_ORIGINS="*"  # Restrict in production

# Device Configuration
DEVICE_SAMPLE_RATE=100  # Hz
DEVICE_BUFFER_DURATION=30  # seconds
DEVICE_BUFFER_SIZE=3000  # samples per channel

# USGS API Configuration
USGS_API_ENDPOINT="https://earthquake.usgs.gov/fdsnws/event/1/query"
USGS_API_CACHE_TTL=300  # 5 minutes
USGS_API_DEFAULT_MAGNITUDE=3.0  # minimum magnitude

# Spectral Analysis Configuration
FFT_WINDOW_FUNCTION="hann"  # or 'hamming', 'blackman'
SPECTROGRAM_TIME_RESOLUTION=1  # seconds
SPECTROGRAM_OVERLAP=0.5  # 50% overlap

# Mock Device Configuration (for testing)
MOCK_DEVICE_ENABLED=True
MOCK_AMPLITUDE=0.1  # m/s^2
MOCK_NOISE_LEVEL=0.05  # m/s^2
```

## Device Configuration

### Geotiny GT-3 Models
```python
DEVICES = {
    'device_1': {
        'name': 'Geotiny GT-3 Unit 1',
        'location': 'San Francisco', 
        'latitude': 37.7749,
        'longitude': -122.4194,
        'channels': {
            'X': {'name': 'North-South', 'sensitivity': 1.0},
            'Y': {'name': 'East-West', 'sensitivity': 1.0},
            'Z': {'name': 'Vertical', 'sensitivity': 1.0}
        },
        'ip_address': '192.168.1.101',
        'port': 8000,
        'sample_rate': 100
    },
    'device_2': {
        'name': 'Geotiny GT-3 Unit 2',
        'location': 'Los Angeles',
        'latitude': 34.0522,
        'longitude': -118.2437,
        'channels': { ... },
        'ip_address': '192.168.1.102',
        'port': 8000,
        'sample_rate': 100
    },
    'device_3': {
        'name': 'Geotiny GT-3 Unit 3',
        'location': 'San Diego',
        'latitude': 32.7157,
        'longitude': -117.1611,
        'channels': { ... },
        'ip_address': '192.168.1.103',
        'port': 8000,
        'sample_rate': 100
    }
}
```

## API Configuration

### Spectrum Analysis Parameters
```python
# FFT Analysis
FFT_CONFIG = {
    'nperseg': 1024,  # Window length
    'noverlap': 512,  # Window overlap
    'window': 'hann',  # Window function
    'scaling': 'density'  # Power spectral density
}

# Spectrogram Parameters
SPECTROGRAM_CONFIG = {
    'nfft': 256,
    'noverlap': 128,
    'window': 'hann',
    'cmap': 'viridis'
}
```

### Time Window Definitions
```python
TIME_WINDOWS = {
    '1min': 60,      # 60 seconds
    '10min': 600,    # 10 minutes
    '30min': 1800    # 30 minutes
}
```

## Frontend Configuration

### Chart.js Configuration
```javascript
CHART_CONFIG = {
    line: {
        animation: false,
        tension: 0.1,
        borderWidth: 1,
        pointRadius: 0,
        fill: false,
        borderColor: '#06b6d4',
        backgroundColor: 'rgba(6, 182, 212, 0.1)'
    },
    responsive: true,
    maintainAspectRatio: false,
    scales: {
        y: {
            beginAtZero: true,
            max: 1.0,
            min: -1.0
        }
    }
}
```

### Plotly Configuration
```javascript
PLOTLY_CONFIG = {
    responsive: true,
    displayModeBar: false,
    displaylogo: false,
    toImageButtonOptions: { format: 'png', width: 1200, height: 600 }
}
```

### Leaflet Configuration
```javascript
LEAFLET_CONFIG = {
    zoom: 2,
    center: [20, 0],
    tileLayer: 'https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png',
    attribution: '© CartoDB',
    maxZoom: 19,
    preferCanvas: true
}
```

## Socket.IO Events

### Client to Server
```javascript
socket.emit('subscribe_device', {
    device_id: 'device_1',
    frequency: 10  // Hz
});

socket.emit('unsubscribe_device', {
    device_id: 'device_1'
});

socket.emit('request_waveform', {
    device_id: 'device_1',
    duration: 60  // seconds
});
```

### Server to Client
```javascript
socket.on('waveform_data', function(data) {
    // {
    //   device_id: 'device_1',
    //   timestamp: 1699564800,
    //   channels: {
    //     X: [0.001, 0.002, ...],
    //     Y: [-0.001, 0.002, ...],
    //     Z: [0.1, 0.09, ...]
    //   }
    // }
});
```

## Logging Configuration
```python
LOG_CONFIG = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'standard': {
            'format': '[%(asctime)s] %(levelname)s in %(module)s: %(message)s'
        }
    },
    'handlers': {
        'default': {
            'level': 'INFO',
            'class': 'logging.StreamHandler',
            'formatter': 'standard'
        },
        'file': {
            'level': 'WARNING',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': 'logs/geotiny.log',
            'maxBytes': 10485760,  # 10MB
            'backupCount': 5,
            'formatter': 'standard'
        }
    },
    'loggers': {
        'app': {
            'handlers': ['default', 'file'],
            'level': 'INFO',
            'propagate': False
        },
        'api': {
            'handlers': ['default', 'file'],
            'level': 'DEBUG',
            'propagate': False
        }
    }
}
```

## Database Configuration (Future)
```python
# SQLite (Development)
SQLALCHEMY_DATABASE_URI = 'sqlite:///geotiny.db'

# PostgreSQL (Production)
# SQLALCHEMY_DATABASE_URI = 'postgresql://user:password@localhost/geotiny'

SQLALCHEMY_TRACK_MODIFICATIONS = False
SQLALCHEMY_ECHO = False
```

## Security Configuration (Production)
```python
# CORS Configuration
CORS_CONFIG = {
    'origins': ['https://monitor.yourdomain.com'],
    'methods': ['GET', 'POST', 'OPTIONS'],
    'allow_headers': ['Content-Type', 'Authorization']
}

# Session Configuration
SESSION_TIMEOUT = 3600  # 1 hour
SECURE_COOKIES = True
SAMESITE = 'Lax'  # or 'Strict'

# Rate Limiting
RATELIMIT_STORAGE_URL = 'memory://'
RATELIMIT_DEFAULT = '100 per hour'
```

## Example .env File
```
FLASK_ENV=development
DEBUG=True
SECRET_KEY=your-secret-key-here
USGS_API_CACHE_TTL=300
DEVICE_SAMPLE_RATE=100
MOCK_DEVICE_ENABLED=True
```

## Starting the Application

### Development
```bash
cd web
python run.py
```

### Production (with gunicorn)
```bash
cd web
gunicorn --worker-class=gevent --workers=1 --bind=0.0.0.0:5000 app:app
```

### Docker
```bash
docker build -t geotiny:latest .
docker run -p 5000:5000 geotiny:latest
```

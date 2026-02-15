"""
Geotiny Web Interface - Main Flask Application

Real-time seismic monitoring dashboard for 3 Geotiny devices
with spectrum analysis and global earthquake data visualization.
"""

import os
import sys
import logging
from datetime import datetime
from flask import Flask, render_template, jsonify, request
from flask_socketio import SocketIO, emit, join_room, leave_room
from flask_cors import CORS

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import API modules
from web.api.devices import DeviceManager
from web.api.spectrum import SpectrumAnalyzer
from web.api.global_seismic import GlobalSeismicManager
from web.api.vendor import get_vendor_info

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/geotiny_web.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Create Flask app
app = Flask(__name__, template_folder='templates', static_folder='static')
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-insecure-key-change-in-production')
app.config['JSON_SORT_KEYS'] = False

# Enable CORS
CORS(app)

# Initialize SocketIO for real-time communication
socketio = SocketIO(app, cors_allowed_origins="*")

# Initialize managers
device_manager = DeviceManager()
spectrum_analyzer = SpectrumAnalyzer()
global_seismic_manager = GlobalSeismicManager()

# Store connected clients for broadcasting
connected_clients = {}


# ============================================================================
# ROUTES
# ============================================================================

@app.route('/')
def index():
    """Main dashboard page"""
    logger.info("Dashboard page requested")
    return render_template('dashboard.html')


@app.route('/spectrum')
def spectrum():
    """Spectrum analysis page"""
    logger.info("Spectrum analysis page requested")
    return render_template('spectrum.html')


@app.route('/global')
def global_seismic():
    """Global seismic data page"""
    logger.info("Global seismic page requested")
    return render_template('global.html')


@app.route('/about')
def about():
    """About and educational page"""
    logger.info("About page requested")
    return render_template('about.html')


@app.route('/health')
def health():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.utcnow().isoformat(),
        'devices_connected': len(device_manager.get_device_status())
    })


# ============================================================================
# REST API ENDPOINTS
# ============================================================================

@app.route('/api/devices/status', methods=['GET'])
def get_devices_status():
    """Get status of all connected devices"""
    try:
        status = device_manager.get_device_status()
        return jsonify({'status': 'success', 'data': status})
    except Exception as e:
        logger.error(f"Error getting device status: {str(e)}")
        return jsonify({'status': 'error', 'message': str(e)}), 500


@app.route('/api/devices/<device_id>/info', methods=['GET'])
def get_device_info(device_id):
    """Get detailed info for a specific device"""
    try:
        info = device_manager.get_device_info(device_id)
        if info:
            return jsonify({'status': 'success', 'data': info})
        else:
            return jsonify({'status': 'error', 'message': 'Device not found'}), 404
    except Exception as e:
        logger.error(f"Error getting device info: {str(e)}")
        return jsonify({'status': 'error', 'message': str(e)}), 500


@app.route('/api/spectrum/analyze', methods=['POST'])
def analyze_spectrum():
    """Analyze spectrum for given device and time window"""
    try:
        data = request.get_json()
        device_id = data.get('device_id')
        time_window = data.get('time_window', '1min')  # '1min', '10min', '30min'
        channel = data.get('channel', 'Z')  # 'X', 'Y', 'Z'

        result = spectrum_analyzer.analyze(device_id, time_window, channel)
        return jsonify({'status': 'success', 'data': result})
    except Exception as e:
        logger.error(f"Error analyzing spectrum: {str(e)}")
        return jsonify({'status': 'error', 'message': str(e)}), 500


@app.route('/api/spectrum/fft', methods=['POST'])
def get_fft():
    """Get FFT for specified parameters"""
    try:
        data = request.get_json()
        device_id = data.get('device_id')
        time_window = data.get('time_window', '1min')
        channel = data.get('channel', 'Z')

        fft_data = spectrum_analyzer.compute_fft(device_id, time_window, channel)
        return jsonify({'status': 'success', 'data': fft_data})
    except Exception as e:
        logger.error(f"Error computing FFT: {str(e)}")
        return jsonify({'status': 'error', 'message': str(e)}), 500


@app.route('/api/spectrum/spectrogram', methods=['POST'])
def get_spectrogram():
    """Get spectrogram data"""
    try:
        data = request.get_json()
        device_id = data.get('device_id')
        time_window = data.get('time_window', '10min')
        channel = data.get('channel', 'Z')

        spectrogram_data = spectrum_analyzer.compute_spectrogram(
            device_id, time_window, channel
        )
        return jsonify({'status': 'success', 'data': spectrogram_data})
    except Exception as e:
        logger.error(f"Error computing spectrogram: {str(e)}")
        return jsonify({'status': 'error', 'message': str(e)}), 500


@app.route('/api/global/earthquakes', methods=['GET'])
def get_earthquakes():
    """Get recent earthquake data from USGS"""
    try:
        min_magnitude = request.args.get('min_magnitude', 5.0, type=float)
        time_period = request.args.get('time_period', '1day')  # '1day', '7days', '30days'

        earthquakes = global_seismic_manager.get_recent_earthquakes(
            min_magnitude=min_magnitude,
            time_period=time_period
        )
        return jsonify({'status': 'success', 'data': earthquakes})
    except Exception as e:
        logger.error(f"Error getting earthquakes: {str(e)}")
        return jsonify({'status': 'error', 'message': str(e)}), 500


@app.route('/api/global/earthquakes/<event_id>', methods=['GET'])
def get_earthquake_detail(event_id):
    """Get detailed info for specific earthquake"""
    try:
        event = global_seismic_manager.get_earthquake_detail(event_id)
        if event:
            return jsonify({'status': 'success', 'data': event})
        else:
            return jsonify({'status': 'error', 'message': 'Event not found'}), 404
    except Exception as e:
        logger.error(f"Error getting earthquake detail: {str(e)}")
        return jsonify({'status': 'error', 'message': str(e)}), 500


@app.route('/api/vendor/info', methods=['GET'])
def get_vendor():
    """Get vendor information (Geotiny specs)"""
    try:
        vendor_info = get_vendor_info()
        return jsonify({'status': 'success', 'data': vendor_info})
    except Exception as e:
        logger.error(f"Error getting vendor info: {str(e)}")
        return jsonify({'status': 'error', 'message': str(e)}), 500


# ============================================================================
# WEBSOCKET EVENTS
# ============================================================================

@socketio.on('connect')
def handle_connect():
    """Handle client connection"""
    client_id = request.sid
    connected_clients[client_id] = {
        'connected_at': datetime.utcnow(),
        'subscribed_to': []
    }
    logger.info(f"Client connected: {client_id}")
    emit('connection_response', {'status': 'connected', 'client_id': client_id})


@socketio.on('disconnect')
def handle_disconnect():
    """Handle client disconnection"""
    client_id = request.sid
    if client_id in connected_clients:
        del connected_clients[client_id]
    logger.info(f"Client disconnected: {client_id}")


@socketio.on('subscribe_device')
def handle_subscribe_device(data):
    """Subscribe to real-time data from a device"""
    client_id = request.sid
    device_id = data.get('device_id')
    sampling_rate = data.get('sampling_rate', 10)  # Hz

    if client_id in connected_clients:
        if device_id not in connected_clients[client_id]['subscribed_to']:
            connected_clients[client_id]['subscribed_to'].append(device_id)

    join_room(f'device_{device_id}')
    logger.info(f"Client {client_id} subscribed to device {device_id}")
    emit('subscription_response', {
        'status': 'subscribed',
        'device_id': device_id,
        'sampling_rate': sampling_rate
    })


@socketio.on('unsubscribe_device')
def handle_unsubscribe_device(data):
    """Unsubscribe from device data"""
    client_id = request.sid
    device_id = data.get('device_id')

    if client_id in connected_clients:
        if device_id in connected_clients[client_id]['subscribed_to']:
            connected_clients[client_id]['subscribed_to'].remove(device_id)

    leave_room(f'device_{device_id}')
    logger.info(f"Client {client_id} unsubscribed from device {device_id}")
    emit('unsubscription_response', {'status': 'unsubscribed', 'device_id': device_id})


@socketio.on('request_waveform')
def handle_waveform_request(data):
    """Request current waveform data"""
    try:
        device_id = data.get('device_id')
        channel = data.get('channel', 'Z')

        waveform = device_manager.get_latest_waveform(device_id, channel)
        if waveform:
            emit('waveform_data', {
                'device_id': device_id,
                'channel': channel,
                'data': waveform,
                'timestamp': datetime.utcnow().isoformat()
            })
        else:
            emit('error', {'message': f'No data available for {device_id}/{channel}'})
    except Exception as e:
        logger.error(f"Error handling waveform request: {str(e)}")
        emit('error', {'message': str(e)})


# ============================================================================
# ERROR HANDLERS
# ============================================================================

@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors"""
    return jsonify({'status': 'error', 'message': 'Not found'}), 404


@app.errorhandler(500)
def internal_error(error):
    """Handle 500 errors"""
    logger.error(f"Internal server error: {str(error)}")
    return jsonify({'status': 'error', 'message': 'Internal server error'}), 500


# ============================================================================
# STARTUP
# ============================================================================

@app.before_request
def before_request():
    """Before each request"""
    pass


@app.after_request
def after_request(response):
    """After each request"""
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'SAMEORIGIN'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    return response


def create_log_directory():
    """Ensure logs directory exists"""
    os.makedirs('logs', exist_ok=True)


def initialize_app():
    """Initialize app on startup"""
    logger.info("=" * 70)
    logger.info("GEOTINY WEB INTERFACE - STARTING UP")
    logger.info("=" * 70)

    try:
        create_log_directory()
        device_manager.initialize()
        global_seismic_manager.initialize()
        logger.info("App initialized successfully")
    except Exception as e:
        logger.error(f"Error during initialization: {str(e)}")
        raise


if __name__ == '__main__':
    initialize_app()

    logger.info("Starting web server on http://0.0.0.0:5000")
    logger.info("Dashboard: http://localhost:5000/")
    logger.info("Spectrum Analysis: http://localhost:5000/spectrum")
    logger.info("Global Seismic: http://localhost:5000/global")

    socketio.run(
        app,
        host='0.0.0.0',
        port=5000,
        debug=True,
        allow_unsafe_werkzeug=True
    )

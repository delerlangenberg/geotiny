"""
Device Manager Module - Communication with Geotiny Seismometers

Handles connection, data acquisition, and status monitoring of 3 Geotiny devices.
"""

import socket
import logging
import threading
import time
from datetime import datetime
from collections import deque
import numpy as np
from typing import Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


class GeotinyDevice:
    """Manages connection to a single Geotiny seismometer"""

    def __init__(self, device_id: str, ip_address: str, port: int = 8080):
        """
        Initialize device connection

        Args:
            device_id: Unique identifier (e.g., 'device_1')
            ip_address: IP address of device
            port: TCP port (default 8080)
        """
        self.device_id = device_id
        self.ip_address = ip_address
        self.port = port

        # Connection state
        self.connected = False
        self.socket = None
        self.last_connection_attempt = None
        self.last_data_received = None

        # Data buffers (store last 30 seconds at 100 Hz = 3000 samples)
        self.buffer_size = 3000
        self.channels = {}  # {'X': deque, 'Y': deque, 'Z': deque}
        for ch in ['X', 'Y', 'Z']:
            self.channels[ch] = deque(maxlen=self.buffer_size)

        # Metadata
        self.sampling_rate = 100  # Hz
        self.device_info = {
            'manufacturer': 'Geotiny',
            'model': 'GT-3',
            'sampling_rate': self.sampling_rate,
            'channels': 3,
            'sensitivity': 1.0,  # V/m/s (placeholder)
        }

        # Lock for thread-safe operations
        self.lock = threading.Lock()

    def connect(self) -> bool:
        """
        Establish connection to device

        Returns:
            True if successful, False otherwise
        """
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.settimeout(5)
            self.socket.connect((self.ip_address, self.port))
            self.connected = True
            self.last_connection_attempt = datetime.utcnow()
            logger.info(f"Connected to {self.device_id} at {self.ip_address}:{self.port}")
            return True
        except socket.error as e:
            logger.warning(f"Failed to connect to {self.device_id}: {str(e)}")
            self.connected = False
            self.last_connection_attempt = datetime.utcnow()
            return False

    def disconnect(self):
        """Close device connection"""
        if self.socket:
            try:
                self.socket.close()
            except:
                pass
        self.connected = False
        logger.info(f"Disconnected from {self.device_id}")

    def read_data(self) -> Optional[Tuple[float, float, float]]:
        """
        Read single data point from device

        Returns:
            Tuple of (x, y, z) acceleration values or None if no data
        """
        if not self.connected:
            if not self.connect():
                return None

        try:
            # Receive 12 bytes (3 floats @ 4 bytes each)
            data = self.socket.recv(12)
            if len(data) == 12:
                x, y, z = np.frombuffer(data, dtype=np.float32)
                self.last_data_received = datetime.utcnow()

                # Store in circular buffers
                with self.lock:
                    self.channels['X'].append(float(x))
                    self.channels['Y'].append(float(y))
                    self.channels['Z'].append(float(z))

                return (float(x), float(y), float(z))
            else:
                logger.warning(f"Incomplete data received from {self.device_id}")
                return None
        except socket.timeout:
            logger.warning(f"Timeout reading from {self.device_id}")
            self.disconnect()
            return None
        except Exception as e:
            logger.error(f"Error reading from {self.device_id}: {str(e)}")
            self.disconnect()
            return None

    def get_buffer(self, channel: str = 'Z') -> np.ndarray:
        """
        Get current buffer for a channel

        Args:
            channel: 'X', 'Y', or 'Z'

        Returns:
            NumPy array of samples
        """
        with self.lock:
            if channel in self.channels:
                return np.array(list(self.channels[channel]))
            else:
                return np.array([])

    def get_status(self) -> Dict:
        """Get device status"""
        return {
            'device_id': self.device_id,
            'ip_address': self.ip_address,
            'connected': self.connected,
            'last_data': self.last_data_received.isoformat() if self.last_data_received else None,
            'buffer_samples': len(self.channels['Z']),
            'sampling_rate': self.sampling_rate,
        }

    def get_info(self) -> Dict:
        """Get detailed device information"""
        return {
            'device_id': self.device_id,
            'status': self.get_status(),
            **self.device_info
        }


class DeviceManager:
    """Manages all 3 Geotiny devices"""

    def __init__(self):
        """Initialize device manager"""
        self.devices: Dict[str, GeotinyDevice] = {}
        self.running = False
        self.acquisition_thread = None

        # Configuration (can load from config/geotiny.yml)
        self.device_config = {
            'device_1': {'ip': '192.168.1.100', 'port': 8080},
            'device_2': {'ip': '192.168.1.101', 'port': 8080},
            'device_3': {'ip': '192.168.1.102', 'port': 8080},
        }

    def initialize(self):
        """Initialize all devices"""
        logger.info("Initializing DeviceManager")

        # Create device objects
        for device_id, config in self.device_config.items():
            self.devices[device_id] = GeotinyDevice(
                device_id,
                config['ip'],
                config['port']
            )

        # Start acquisition thread
        self.start_acquisition()

    def start_acquisition(self):
        """Start continuous data acquisition thread"""
        if self.running:
            logger.warning("Acquisition already running")
            return

        self.running = True
        self.acquisition_thread = threading.Thread(
            target=self._acquisition_loop,
            daemon=True
        )
        self.acquisition_thread.start()
        logger.info("Data acquisition started")

    def stop_acquisition(self):
        """Stop data acquisition"""
        self.running = False
        if self.acquisition_thread:
            self.acquisition_thread.join(timeout=5)
        logger.info("Data acquisition stopped")

    def _acquisition_loop(self):
        """Main acquisition loop running in background thread"""
        retry_count = {did: 0 for did in self.devices}

        while self.running:
            for device_id, device in self.devices.items():
                if not device.connected:
                    # Try to reconnect every 10 seconds
                    if retry_count[device_id] >= 10:
                        device.connect()
                        retry_count[device_id] = 0
                    else:
                        retry_count[device_id] += 1
                else:
                    # Read data
                    data = device.read_data()
                    if data:
                        retry_count[device_id] = 0  # Reset on success

            # Sleep to approximately match sampling times
            # With 3 devices, try to read ~10 times per second
            time.sleep(0.033)  # ~30 ms

    def get_device_status(self) -> Dict[str, Dict]:
        """Get status of all devices"""
        return {
            device_id: device.get_status()
            for device_id, device in self.devices.items()
        }

    def get_device_info(self, device_id: str) -> Optional[Dict]:
        """Get detailed info for a device"""
        if device_id in self.devices:
            return self.devices[device_id].get_info()
        return None

    def get_latest_waveform(self, device_id: str, channel: str = 'Z',
                           samples: int = 1000) -> Optional[Dict]:
        """
        Get latest waveform data for a device

        Args:
            device_id: Device identifier
            channel: 'X', 'Y', or 'Z'
            samples: Number of most recent samples to return

        Returns:
            Dict with waveform data and metadata
        """
        if device_id not in self.devices:
            return None

        device = self.devices[device_id]
        buffer = device.get_buffer(channel)

        if len(buffer) == 0:
            return None

        # Get last N samples
        if len(buffer) > samples:
            data = buffer[-samples:]
        else:
            data = buffer

        # Generate time array (in seconds, relative to end of buffer)
        dt = 1.0 / device.sampling_rate
        times = np.arange(len(data)) * dt - (len(buffer) * dt)

        return {
            'device_id': device_id,
            'channel': channel,
            'sampling_rate': device.sampling_rate,
            'data': data.tolist(),
            'times': times.tolist(),
            'amplitude_range': {
                'min': float(np.min(data)),
                'max': float(np.max(data)),
            },
            'timestamp': datetime.utcnow().isoformat(),
        }

    def get_multi_channel_waveform(self, device_id: str,
                                   samples: int = 1000) -> Optional[Dict]:
        """Get all 3 channels simultaneously"""
        if device_id not in self.devices:
            return None

        return {
            'device_id': device_id,
            'X': self.get_latest_waveform(device_id, 'X', samples),
            'Y': self.get_latest_waveform(device_id, 'Y', samples),
            'Z': self.get_latest_waveform(device_id, 'Z', samples),
            'timestamp': datetime.utcnow().isoformat(),
        }

    def list_devices(self) -> List[Dict]:
        """List all available devices"""
        return [
            {'device_id': device_id, 'ip': device.ip_address}
            for device_id, device in self.devices.items()
        ]


# Singleton instance
_device_manager = None


def get_device_manager() -> DeviceManager:
    """Get singleton instance of DeviceManager"""
    global _device_manager
    if _device_manager is None:
        _device_manager = DeviceManager()
    return _device_manager

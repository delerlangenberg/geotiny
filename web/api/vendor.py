"""
Vendor Information Module - Geotiny Device Specifications

Provides vendor information and product details for display.
"""

import logging

logger = logging.getLogger(__name__)


def get_vendor_info():
    """
    Get Geotiny vendor information

    Returns:
        Dict with product specifications and vendor details
    """
    return {
        'vendor': {
            'name': 'Geotiny',
            'website': 'https://www.geotiny.com',
            'support_email': 'support@geotiny.com',
            'country': 'Austria',
        },
        'devices': [
            {
                'device_id': 'device_1',
                'model': 'GT-3 Seismometer',
                'ip_address': '192.168.1.100',
                'status': 'active',
                'specifications': {
                    'sensor_type': 'MEMS Accelerometer (3-axis)',
                    'sampling_rate': '100 Hz',
                    'channels': 3,
                    'channel_labels': ['X (North-South)', 'Y (East-West)', 'Z (Vertical)'],
                    'frequency_response': '0.1 - 50 Hz',
                    'sensitivity': '1 V/(m/s²)',
                    'measurement_range': '±20 m/s²',
                    'resolution': '12-bit',
                    'noise_floor': '~10 µg/√Hz',
                    'power_consumption': '2 W',
                    'interface': 'Ethernet (RJ45)',
                    'protocol': 'TCP/IP',
                    'port': 8080,
                }
            },
            {
                'device_id': 'device_2',
                'model': 'GT-3 Seismometer',
                'ip_address': '192.168.1.101',
                'status': 'active',
                'specifications': {
                    'sensor_type': 'MEMS Accelerometer (3-axis)',
                    'sampling_rate': '100 Hz',
                    'channels': 3,
                    'channel_labels': ['X (North-South)', 'Y (East-West)', 'Z (Vertical)'],
                    'frequency_response': '0.1 - 50 Hz',
                    'sensitivity': '1 V/(m/s²)',
                    'measurement_range': '±20 m/s²',
                    'resolution': '12-bit',
                    'noise_floor': '~10 µg/√Hz',
                    'power_consumption': '2 W',
                    'interface': 'Ethernet (RJ45)',
                    'protocol': 'TCP/IP',
                    'port': 8080,
                }
            },
            {
                'device_id': 'device_3',
                'model': 'GT-3 Seismometer',
                'ip_address': '192.168.1.102',
                'status': 'active',
                'specifications': {
                    'sensor_type': 'MEMS Accelerometer (3-axis)',
                    'sampling_rate': '100 Hz',
                    'channels': 3,
                    'channel_labels': ['X (North-South)', 'Y (East-West)', 'Z (Vertical)'],
                    'frequency_response': '0.1 - 50 Hz',
                    'sensitivity': '1 V/(m/s²)',
                    'measurement_range': '±20 m/s²',
                    'resolution': '12-bit',
                    'noise_floor': '~10 µg/√Hz',
                    'power_consumption': '2 W',
                    'interface': 'Ethernet (RJ45)',
                    'protocol': 'TCP/IP',
                    'port': 8080,
                }
            }
        ],
        'product_details': {
            'description': 'Professional MEMS-based seismometer network for educational and research applications',
            'use_cases': [
                'Earthquake monitoring',
                'Seismic event detection',
                'Ground vibration analysis',
                'Building monitoring',
                'Educational demonstrations',
                'Research applications',
            ],
            'advantages': [
                'Real-time data acquisition at 100 Hz',
                'Compact and affordable',
                'Low power consumption',
                'Network-ready (Ethernet)',
                'Easy integration',
                'High sensitivity MEMS sensors',
            ],
        },
        'data_formats': {
            'input': 'IEEE 754 Float (4 bytes per sample)',
            'supported_formats': ['Raw binary', 'miniSEED', 'SAC', 'CSV'],
            'sampling_rate': 100,
            'channels': 3,
            'data_rate': '1.2 KB/s per device (100 Hz × 3 channels × 4 bytes)',
        },
        'network_specs': {
            'connection': 'Ethernet (LAN)',
            'protocol': 'TCP/IP',
            'stream_format': 'Binary (IEEE 754 floats)',
            'reconnection': 'Automatic on disconnect',
            'latency': '< 50 ms typical',
        },
        'educational_resources': {
            'documentation': 'https://www.geotiny.com/docs',
            'api_reference': 'https://www.geotiny.com/api',
            'tutorials': 'https://www.geotiny.com/tutorials',
            'support_forum': 'https://forum.geotiny.com',
        },
    }


def get_device_specs(device_id: str):
    """
    Get specifications for a specific device

    Args:
        device_id: Device identifier (device_1, device_2, or device_3)

    Returns:
        Device specifications or None if not found
    """
    vendor_info = get_vendor_info()
    for device in vendor_info.get('devices', []):
        if device.get('device_id') == device_id:
            return device
    return None


def get_sampling_rate():
    """Get global sampling rate (all devices use same rate)"""
    return 100  # Hz


def get_channel_info():
    """Get information about channels"""
    return {
        'X': {
            'label': 'North-South (X)',
            'abbreviation': 'N-S',
            'component': 'Horizontal',
            'description': 'North-South horizontal component of ground motion',
        },
        'Y': {
            'label': 'East-West (Y)',
            'abbreviation': 'E-W',
            'component': 'Horizontal',
            'description': 'East-West horizontal component of ground motion',
        },
        'Z': {
            'label': 'Vertical (Z)',
            'abbreviation': 'V',
            'component': 'Vertical',
            'description': 'Vertical (up-down) component of ground motion',
        },
    }

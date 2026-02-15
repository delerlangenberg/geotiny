#!/usr/bin/env python3
"""
Fetch seismic data from Geotiny device.

This script connects to a Geotiny seismometer and retrieves data,
saving it in the configured format.
"""

import argparse
import yaml
from pathlib import Path
from datetime import datetime
import time


def load_config(config_path="config/geotiny.yml"):
    """Load configuration from YAML file."""
    with open(config_path, 'r') as f:
        return yaml.safe_load(f)


def connect_to_device(config):
    """Establish connection to Geotiny device."""
    device_config = config['device']
    
    if device_config['connection'] == 'ethernet':
        print(f"Connecting to Geotiny at {device_config['ip_address']}:{device_config['port']}")
        # TODO: Implement Ethernet connection
        # import socket
        # sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        # sock.connect((device_config['ip_address'], device_config['port']))
        # return sock
        
    elif device_config['connection'] == 'serial':
        print(f"Connecting to Geotiny on {device_config.get('serial_port', '/dev/ttyUSB0')}")
        # TODO: Implement serial connection
        # import serial
        # ser = serial.Serial(device_config['serial_port'], device_config['baud_rate'])
        # return ser
    
    raise NotImplementedError("Connection type not yet implemented")


def fetch_data(connection, config):
    """Fetch seismic data from the device."""
    acq_config = config['acquisition']
    
    print(f"Fetching data at {acq_config['sampling_rate']} Hz")
    print(f"Channels: {acq_config['channels']}")
    
    # TODO: Implement data fetching
    # This would depend on the Geotiny protocol
    
    return None  # Return the fetched data


def save_data(data, config):
    """Save fetched data to disk."""
    storage_config = config['storage']
    output_path = Path(storage_config['raw_data_path'])
    output_path.mkdir(parents=True, exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = output_path / f"seismo_{timestamp}.{storage_config['format']}"
    
    print(f"Saving data to {filename}")
    
    # TODO: Implement data saving based on format
    # if storage_config['format'] == 'mseed':
    #     # Use ObsPy to save as miniSEED
    #     pass
    # elif storage_config['format'] == 'csv':
    #     # Use pandas to save as CSV
    #     pass
    
    return filename


def main():
    parser = argparse.ArgumentParser(description="Fetch data from Geotiny seismometer")
    parser.add_argument("--config", default="config/geotiny.yml", help="Path to config file")
    parser.add_argument("--duration", type=int, default=300, help="Duration in seconds")
    parser.add_argument("--continuous", action="store_true", help="Run continuously")
    args = parser.parse_args()
    
    config = load_config(args.config)
    
    try:
        connection = connect_to_device(config)
        
        if args.continuous:
            print("Starting continuous data acquisition (Ctrl+C to stop)")
            while True:
                data = fetch_data(connection, config)
                if data:
                    save_data(data, config)
                time.sleep(config['acquisition']['save_interval'])
        else:
            print(f"Acquiring data for {args.duration} seconds")
            data = fetch_data(connection, config)
            if data:
                save_data(data, config)
    
    except KeyboardInterrupt:
        print("\nStopped by user")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        print("Closing connection")


if __name__ == "__main__":
    main()

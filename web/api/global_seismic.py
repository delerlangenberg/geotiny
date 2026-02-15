"""
Global Seismic Manager - Integration with USGS Earthquake API

Fetches and manages global earthquake data for the dashboard.
"""

import logging
import requests
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import threading

logger = logging.getLogger(__name__)


class GlobalSeismicManager:
    """Manages global earthquake data from USGS"""

    # USGS Earthquake API endpoints
    USGS_API_BASE = "https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary"
    USGS_GEOJSON_BASE = "https://earthquake.usgs.gov/fdsnws/event/1/query"

    def __init__(self):
        """Initialize global seismic manager"""
        self.cache = []
        self.cache_timestamp = None
        self.cache_ttl = 300  # 5 minutes
        self.lock = threading.Lock()

    def initialize(self):
        """Initialize manager"""
        logger.info("Initializing GlobalSeismicManager")
        # Fetch initial data
        self.get_recent_earthquakes()

    def get_recent_earthquakes(self, min_magnitude: float = 5.0,
                               time_period: str = '1day') -> List[Dict]:
        """
        Get recent earthquakes from USGS

        Args:
            min_magnitude: Minimum magnitude to include
            time_period: '1day', '7days', '30days'

        Returns:
            List of earthquake events
        """
        try:
            # Check cache
            if self._is_cache_valid():
                return self._filter_earthquakes(self.cache, min_magnitude)

            # Fetch from USGS
            earthquakes = self._fetch_from_usgs(min_magnitude, time_period)

            with self.lock:
                self.cache = earthquakes
                self.cache_timestamp = datetime.utcnow()

            return earthquakes

        except Exception as e:
            logger.error(f"Error getting earthquakes: {str(e)}")
            return []

    def get_earthquake_detail(self, event_id: str) -> Optional[Dict]:
        """
        Get detailed information for a specific earthquake

        Args:
            event_id: USGS event ID

        Returns:
            Detailed event information or None
        """
        try:
            url = f"{self.USGS_GEOJSON_BASE}?eventid={event_id}&format=geojson"
            response = requests.get(url, timeout=5)
            response.raise_for_status()

            data = response.json()
            if data.get('features') and len(data['features']) > 0:
                feature = data['features'][0]
                return self._format_event(feature)
            return None

        except Exception as e:
            logger.error(f"Error getting earthquake detail: {str(e)}")
            return None

    def _fetch_from_usgs(self, min_magnitude: float, time_period: str) -> List[Dict]:
        """Fetch earthquakes from USGS API"""
        try:
            # Map time period to starttime
            time_map = {
                '1day': 1,
                '7days': 7,
                '30days': 30,
            }
            days_back = time_map.get(time_period, 1)
            start_time = (datetime.utcnow() - timedelta(days=days_back)).isoformat()

            # Query USGS
            params = {
                'starttime': start_time,
                'minmagnitude': min_magnitude,
                'format': 'geojson',
                'limit': 300,
                'orderby': 'time-asc'
            }

            response = requests.get(
                self.USGS_GEOJSON_BASE,
                params=params,
                timeout=10
            )
            response.raise_for_status()

            data = response.json()
            earthquakes = []

            for feature in data.get('features', []):
                event = self._format_event(feature)
                if event:
                    earthquakes.append(event)

            logger.info(f"Fetched {len(earthquakes)} earthquakes from USGS")
            return earthquakes

        except Exception as e:
            logger.error(f"Error fetching from USGS: {str(e)}")
            return []

    def _format_event(self, feature: Dict) -> Optional[Dict]:
        """Format USGS feature as event dict"""
        try:
            props = feature.get('properties', {})
            geom = feature.get('geometry', {})
            coords = geom.get('coordinates', [0, 0, 0])

            return {
                'event_id': props.get('ids', '').lstrip(',').split(',')[0],
                'magnitude': props.get('mag', 0),
                'magnitude_type': props.get('magType', 'M'),
                'latitude': coords[1],
                'longitude': coords[0],
                'depth_km': coords[2],
                'datetime': datetime.utcfromtimestamp(
                    props.get('time', 0) / 1000
                ).isoformat(),
                'title': props.get('title', ''),
                'place': props.get('place', ''),
                'url': props.get('url', ''),
                'felt_reports': props.get('felt'),
                'tsunami': props.get('tsunami'),
                'status': props.get('status'),
                'updated': datetime.utcfromtimestamp(
                    props.get('updated', 0) / 1000
                ).isoformat(),
            }
        except Exception as e:
            logger.error(f"Error formatting event: {str(e)}")
            return None

    def _filter_earthquakes(self, earthquakes: List[Dict],
                           min_magnitude: float) -> List[Dict]:
        """Filter earthquakes by magnitude"""
        return [
            eq for eq in earthquakes
            if eq.get('magnitude', 0) >= min_magnitude
        ]

    def _is_cache_valid(self) -> bool:
        """Check if cache is still valid"""
        if not self.cache_timestamp:
            return False
        age = (datetime.utcnow() - self.cache_timestamp).total_seconds()
        return age < self.cache_ttl

    def search_earthquakes(self, latitude: float, longitude: float,
                          radius_km: float = 1000,
                          min_magnitude: float = 3.0) -> List[Dict]:
        """
        Search for earthquakes near a location

        Args:
            latitude: Center latitude
            longitude: Center longitude
            radius_km: Search radius in kilometers
            min_magnitude: Minimum magnitude

        Returns:
            List of earthquakes
        """
        try:
            params = {
                'latitude': latitude,
                'longitude': longitude,
                'maxradiuskm': radius_km,
                'minmagnitude': min_magnitude,
                'format': 'geojson',
                'limit': 100,
                'orderby': 'magnitude'
            }

            response = requests.get(
                self.USGS_GEOJSON_BASE,
                params=params,
                timeout=10
            )
            response.raise_for_status()

            data = response.json()
            earthquakes = []

            for feature in data.get('features', []):
                event = self._format_event(feature)
                if event:
                    earthquakes.append(event)

            return earthquakes

        except Exception as e:
            logger.error(f"Error searching earthquakes: {str(e)}")
            return []

    def get_stats(self) -> Dict:
        """Get statistics about cached earthquakes"""
        with self.lock:
            if not self.cache:
                return {
                    'total_events': 0,
                    'magnitude_range': None,
                    'cache_age_seconds': None,
                }

            magnitudes = [eq.get('magnitude', 0) for eq in self.cache]
            age = (datetime.utcnow() - self.cache_timestamp).total_seconds() \
                if self.cache_timestamp else None

            return {
                'total_events': len(self.cache),
                'magnitude_min': float(min(magnitudes)),
                'magnitude_max': float(max(magnitudes)),
                'magnitude_mean': float(sum(magnitudes) / len(magnitudes)),
                'cache_age_seconds': age,
                'last_updated': self.cache_timestamp.isoformat() if self.cache_timestamp else None,
            }


# Singleton instance
_global_seismic_manager = None


def get_global_seismic_manager() -> GlobalSeismicManager:
    """Get singleton instance"""
    global _global_seismic_manager
    if _global_seismic_manager is None:
        _global_seismic_manager = GlobalSeismicManager()
    return _global_seismic_manager

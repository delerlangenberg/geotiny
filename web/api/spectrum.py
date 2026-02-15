"""
Spectrum Analyzer Module - FFT and Spectrogram Analysis

Provides frequency domain analysis for seismic data from Geotiny devices.
"""

import logging
import numpy as np
from scipy import signal
from scipy.fft import fft, fftfreq
from datetime import datetime, timedelta
from typing import Dict, Optional, List
import threading

logger = logging.getLogger(__name__)


class SpectrumAnalyzer:
    """Analyzes frequency spectra and spectrograms for seismic data"""

    def __init__(self, sampling_rate: int = 100):
        """
        Initialize spectrum analyzer

        Args:
            sampling_rate: Sampling rate in Hz (default 100 from Geotiny)
        """
        self.sampling_rate = sampling_rate
        self.nyquist_freq = sampling_rate / 2
        self.cache = {}  # Simple caching mechanism

    def analyze(self, device_id: str, time_window: str = '1min',
                channel: str = 'Z') -> Dict:
        """
        Comprehensive spectrum analysis

        Args:
            device_id: Device identifier
            time_window: '1min', '10min', or '30min'
            channel: 'X', 'Y', or 'Z'

        Returns:
            Dict with FFT, spectrogram, and statistics
        """
        try:
            # Get data for the time window
            samples = self._get_sample_count(time_window)
            data = self._get_data_from_device(device_id, channel, samples)

            if data is None or len(data) < 2:
                return {'error': 'Insufficient data'}

            # Apply window function to reduce spectral leakage
            window = signal.hann(len(data))
            windowed_data = data * window

            # Compute FFT
            fft_result = self._compute_fft(windowed_data)

            # Compute spectrogram
            spec_result = self._compute_spectrogram(data)

            # Compute statistics
            stats = self._compute_statistics(data)

            return {
                'device_id': device_id,
                'channel': channel,
                'time_window': time_window,
                'sampling_rate': self.sampling_rate,
                'nyquist_frequency': self.nyquist_freq,
                'fft': fft_result,
                'spectrogram': spec_result,
                'statistics': stats,
                'timestamp': datetime.utcnow().isoformat(),
            }
        except Exception as e:
            logger.error(f"Error in spectrum analysis: {str(e)}")
            return {'error': str(e)}

    def compute_fft(self, device_id: str, time_window: str = '1min',
                    channel: str = 'Z') -> Dict:
        """
        Compute FFT for visualization

        Returns:
            Dict with frequency and magnitude arrays
        """
        try:
            samples = self._get_sample_count(time_window)
            data = self._get_data_from_device(device_id, channel, samples)

            if data is None or len(data) < 2:
                return {'error': 'Insufficient data'}

            # Remove mean
            data = data - np.mean(data)

            # Apply Hann window
            window = signal.hann(len(data))
            windowed_data = data * window

            # Compute FFT
            n = len(windowed_data)
            fft_vals = np.abs(fft(windowed_data))[:n // 2]
            freqs = fftfreq(n, 1 / self.sampling_rate)[:n // 2]

            # Convert to dB scale
            fft_db = 20 * np.log10(fft_vals + 1e-10)

            # Normalize
            fft_db = fft_db - np.max(fft_db)

            return {
                'device_id': device_id,
                'channel': channel,
                'frequencies': freqs.tolist(),
                'magnitude_db': fft_db.tolist(),
                'magnitude_linear': fft_vals.tolist(),
                'nyquist_frequency': float(self.nyquist_freq),
                'frequency_resolution': float(self.sampling_rate / n),
                'timestamp': datetime.utcnow().isoformat(),
            }
        except Exception as e:
            logger.error(f"Error computing FFT: {str(e)}")
            return {'error': str(e)}

    def compute_spectrogram(self, device_id: str, time_window: str = '10min',
                           channel: str = 'Z') -> Dict:
        """
        Compute spectrogram (power vs time vs frequency)

        Args:
            device_id: Device identifier
            time_window: Time window for analysis
            channel: Channel to analyze

        Returns:
            Dict with spectrogram data
        """
        try:
            samples = self._get_sample_count(time_window)
            data = self._get_data_from_device(device_id, channel, samples)

            if data is None or len(data) < 256:
                return {'error': 'Insufficient data'}

            # Compute spectrogram using scipy
            # nperseg: window length (256 samples = ~2.5 sec at 100 Hz)
            # noverlap: overlap between windows (75% = 192 samples)
            freqs, times, Sxx = signal.spectrogram(
                data,
                fs=self.sampling_rate,
                window='hann',
                nperseg=256,
                noverlap=192,
                scaling='density'
            )

            # Convert to dB scale
            Sxx_db = 10 * np.log10(Sxx + 1e-10)

            # Create time array relative to start
            time_seconds = times.tolist()

            return {
                'device_id': device_id,
                'channel': channel,
                'time_window': time_window,
                'frequencies': freqs.tolist(),
                'time_seconds': time_seconds,
                'power_db': Sxx_db.tolist(),
                'frequency_resolution': float(freqs[1] - freqs[0]) if len(freqs) > 1 else 0,
                'time_resolution': float(times[1] - times[0]) if len(times) > 1 else 0,
                'color_scale': {
                    'min': float(np.min(Sxx_db)),
                    'max': float(np.max(Sxx_db)),
                    'mean': float(np.mean(Sxx_db)),
                },
                'timestamp': datetime.utcnow().isoformat(),
            }
        except Exception as e:
            logger.error(f"Error computing spectrogram: {str(e)}")
            return {'error': str(e)}

    def _compute_fft(self, data: np.ndarray) -> Dict:
        """Internal FFT computation"""
        n = len(data)
        fft_vals = np.abs(fft(data))[:n // 2]
        freqs = fftfreq(n, 1 / self.sampling_rate)[:n // 2]

        # dB scale
        fft_db = 20 * np.log10(fft_vals + 1e-10)
        fft_db = fft_db - np.max(fft_db)

        # Find peaks
        peaks, _ = signal.find_peaks(fft_db, height=-20)

        return {
            'frequencies': freqs.tolist(),
            'magnitude_db': fft_db.tolist(),
            'peaks': peaks.tolist(),
            'peak_frequencies': freqs[peaks].tolist() if len(peaks) > 0 else [],
        }

    def _compute_spectrogram(self, data: np.ndarray) -> Dict:
        """Internal spectrogram computation"""
        freqs, times, Sxx = signal.spectrogram(
            data,
            fs=self.sampling_rate,
            window='hann',
            nperseg=256,
            noverlap=192,
            scaling='density'
        )

        Sxx_db = 10 * np.log10(Sxx + 1e-10)

        return {
            'frequencies': freqs.tolist(),
            'times': times.tolist(),
            'power_db': Sxx_db.tolist(),
        }

    def _compute_statistics(self, data: np.ndarray) -> Dict:
        """Compute statistics of time series"""
        return {
            'mean': float(np.mean(data)),
            'std': float(np.std(data)),
            'min': float(np.min(data)),
            'max': float(np.max(data)),
            'rms': float(np.sqrt(np.mean(data ** 2))),
            'peak_to_peak': float(np.max(data) - np.min(data)),
        }

    def _get_sample_count(self, time_window: str) -> int:
        """
        Convert time window to sample count

        Args:
            time_window: '1min', '10min', or '30min'

        Returns:
            Number of samples
        """
        windows = {
            '1min': 60,
            '10min': 600,
            '30min': 1800,
        }
        seconds = windows.get(time_window, 60)
        return int(seconds * self.sampling_rate)

    def _get_data_from_device(self, device_id: str, channel: str,
                             samples: int) -> Optional[np.ndarray]:
        """
        Get data from device buffer

        This is a stub - in production would fetch from DeviceManager
        """
        # Placeholder: In real implementation, would call:
        # from web.api.devices import get_device_manager
        # device_manager = get_device_manager()
        # waveform = device_manager.get_latest_waveform(device_id, channel, samples)
        # return np.array(waveform['data'])

        # For now, generate synthetic seismic noise for testing
        t = np.arange(samples) / self.sampling_rate
        # Synthetic seismic noise with multiple frequency components
        data = (
            0.5 * np.sin(2 * np.pi * 2 * t) +  # 2 Hz component
            0.3 * np.sin(2 * np.pi * 5 * t) +  # 5 Hz component
            0.2 * np.sin(2 * np.pi * 10 * t) +  # 10 Hz component
            0.1 * np.random.normal(0, 1, samples)  # Noise
        )
        return data


# Singleton instance
_spectrum_analyzer = None


def get_spectrum_analyzer() -> SpectrumAnalyzer:
    """Get singleton instance"""
    global _spectrum_analyzer
    if _spectrum_analyzer is None:
        _spectrum_analyzer = SpectrumAnalyzer()
    return _spectrum_analyzer

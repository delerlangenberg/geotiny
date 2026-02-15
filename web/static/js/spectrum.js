/**
 * Spectrum Analysis JavaScript
 */

class SpectrumAnalysis {
    constructor() {
        this.currentTab = 'fft';
        this.plots = {};
        this.init();
    }

    init() {
        console.log('Initializing Spectrum Analysis...');
        this.setupEventListeners();
        this.checkUrlParams();
        this.loadDefaultAnalysis();
    }

    setupEventListeners() {
        const analyzeBtn = document.querySelector('button[onclick="analyzeSpectrum()"]');
        if (analyzeBtn) {
            analyzeBtn.addEventListener('click', () => this.analyzeSpectrum());
        }

        document.addEventListener('change', (e) => {
            if (['device-select', 'channel-select', 'time-window-select'].includes(e.target.id)) {
                // Auto-analyze on selection change
                setTimeout(() => this.analyzeSpectrum(), 300);
            }
        });
    }

    checkUrlParams() {
        const params = new URLSearchParams(window.location.search);
        const deviceId = params.get('device');
        
        if (deviceId) {
            const select = document.getElementById('device-select');
            if (select) {
                select.value = deviceId;
            }
        }
    }

    getSelectedParams() {
        return {
            deviceId: document.getElementById('device-select')?.value || 'device_1',
            channel: document.getElementById('channel-select')?.value || 'Z',
            timeWindow: document.getElementById('time-window-select')?.value || '10min'
        };
    }

    async analyzeSpectrum() {
        const params = this.getSelectedParams();
        
        switch (this.currentTab) {
            case 'fft':
                await this.analyzeFFT(params);
                break;
            case 'spectrogram':
                await this.analyzeSpectrogram(params);
                break;
            case 'waveform':
                await this.analyzeWaveform(params);
                break;
        }
    }

    async analyzeFFT(params) {
        try {
            const response = await fetch('/api/spectrum/fft', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    device_id: params.deviceId,
                    channel: params.channel,
                    time_window: params.timeWindow
                })
            });

            const data = await response.json();

            if (data.status === 'success') {
                this.displayFFT(data.data);
                this.displayFFTStats(data.data);
            } else {
                showNotification(`Error: ${data.message}`, 'danger');
            }
        } catch (error) {
            console.error('FFT analysis error:', error);
            showNotification('Error analyzing FFT', 'danger');
        }
    }

    async analyzeSpectrogram(params) {
        try {
            const response = await fetch('/api/spectrum/spectrogram', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    device_id: params.deviceId,
                    channel: params.channel,
                    time_window: params.timeWindow
                })
            });

            const data = await response.json();

            if (data.status === 'success') {
                this.displaySpectrogram(data.data);
            } else {
                showNotification(`Error: ${data.message}`, 'danger');
            }
        } catch (error) {
            console.error('Spectrogram analysis error:', error);
            showNotification('Error analyzing spectrogram', 'danger');
        }
    }

    async analyzeWaveform(params) {
        try {
            // Use the waveform data from devices endpoint
            const response = await fetch(`/api/devices/${params.deviceId}/info`);
            const data = await response.json();

            if (data.status === 'success') {
                this.displayWaveform(data.data, params.channel);
            }
        } catch (error) {
            console.error('Waveform analysis error:', error);
            showNotification('Error loading waveform', 'danger');
        }
    }

    displayFFT(data) {
        const container = document.getElementById('fft-container');
        if (!container) return;

        const trace = {
            x: data.frequencies,
            y: data.magnitude_db,
            type: 'scatter',
            mode: 'lines',
            fill: 'tozeroy',
            name: 'FFT Magnitude',
            line: {
                color: '#06b6d4',
                width: 2
            },
            fillcolor: 'rgba(6, 182, 212, 0.2)'
        };

        const layout = {
            title: {
                text: `FFT Spectrum - ${data.device_id} Channel ${data.channel}`,
                font: { color: '#f1f5f9', size: 16 }
            },
            xaxis: {
                title: 'Frequency (Hz)',
                color: '#cbd5e1',
                gridcolor: 'rgba(51, 65, 85, 0.2)',
                zerolinecolor: 'rgba(51, 65, 85, 0.3)'
            },
            yaxis: {
                title: 'Magnitude (dB)',
                color: '#cbd5e1',
                gridcolor: 'rgba(51, 65, 85, 0.2)',
                zerolinecolor: 'rgba(51, 65, 85, 0.3)'
            },
            plot_bgcolor: 'rgba(15, 23, 42, 0.5)',
            paper_bgcolor: 'transparent',
            font: { color: '#f1f5f9', family: 'Inter, sans-serif' },
            margin: { l: 80, r: 80, t: 80, b: 80 },
            hovermode: 'x unified'
        };

        const config = {
            responsive: true,
            displayModeBar: false
        };

        Plotly.newPlot(container, [trace], layout, config);
    }

    displayFFTStats(data) {
        const container = document.getElementById('stats-container');
        if (!container) return;

        const peakMagnitude = Math.max(...data.magnitude_db);
        const meanMagnitude = data.magnitude_db.reduce((a, b) => a + b, 0) / data.magnitude_db.length;

        container.innerHTML = `
            <table class="table table-sm" style="color: var(--text-secondary); margin-bottom: 0;">
                <tbody>
                    <tr>
                        <td><strong>Device:</strong></td>
                        <td class="code-block">${data.device_id}</td>
                    </tr>
                    <tr>
                        <td><strong>Channel:</strong></td>
                        <td class="code-block">${data.channel}</td>
                    </tr>
                    <tr>
                        <td><strong>Frequency Resolution:</strong></td>
                        <td class="code-block">${formatNumber(data.frequency_resolution, 4)} Hz</td>
                    </tr>
                    <tr>
                        <td><strong>Nyquist Frequency:</strong></td>
                        <td class="code-block">${formatNumber(data.nyquist_frequency, 1)} Hz</td>
                    </tr>
                    <tr>
                        <td><strong>Peak Magnitude:</strong></td>
                        <td class="code-block">${formatNumber(peakMagnitude, 2)} dB</td>
                    </tr>
                    <tr>
                        <td><strong>Mean Magnitude:</strong></td>
                        <td class="code-block">${formatNumber(meanMagnitude, 2)} dB</td>
                    </tr>
                </tbody>
            </table>
        `;
    }

    displaySpectrogram(data) {
        const container = document.getElementById('spectrogram-container');
        if (!container) return;

        const trace = {
            z: data.power_db,
            x: data.time_seconds,
            y: data.frequencies,
            type: 'heatmap',
            colorscale: [
                [0, '#0a0f1f'],
                [0.25, '#3b82f6'],
                [0.5, '#06b6d4'],
                [0.75, '#f97316'],
                [1.0, '#ef4444']
            ],
            colorbar: {
                title: 'Power (dB)',
                titleside: 'right',
                tickcolor: '#cbd5e1',
                tickfont: { color: '#cbd5e1' }
            }
        };

        const layout = {
            title: {
                text: `Spectrogram - ${data.device_id} Channel ${data.channel}`,
                font: { color: '#f1f5f9', size: 16 }
            },
            xaxis: {
                title: 'Time (seconds)',
                color: '#cbd5e1',
                gridcolor: 'rgba(51, 65, 85, 0.2)'
            },
            yaxis: {
                title: 'Frequency (Hz)',
                color: '#cbd5e1',
                gridcolor: 'rgba(51, 65, 85, 0.2)'
            },
            plot_bgcolor: 'rgba(15, 23, 42, 0.3)',
            paper_bgcolor: 'transparent',
            font: { color: '#f1f5f9', family: 'Inter, sans-serif' },
            margin: { l: 80, r: 100, t: 80, b: 80 },
            hovermode: 'closest'
        };

        const config = {
            responsive: true,
            displayModeBar: false
        };

        Plotly.newPlot(container, [trace], layout, config);
    }

    displayWaveform(deviceInfo, channel) {
        const container = document.getElementById('waveform-container');
        if (!container) return;

        // Generate synthetic waveform for demo
        const samples = 1000;
        const t = Array.from({length: samples}, (_, i) => i);
        const y = t.map((i, idx) => 
            0.5 * Math.sin(0.02 * i) + 
            0.3 * Math.sin(0.05 * i) + 
            0.1 * (Math.random() - 0.5)
        );

        const trace = {
            x: t,
            y: y,
            type: 'scatter',
            mode: 'lines',
            name: `${channel} Channel`,
            line: {
                color: '#06b6d4',
                width: 1.5
            }
        };

        const layout = {
            title: {
                text: `Waveform - ${deviceInfo.device_id} Channel ${channel}`,
                font: { color: '#f1f5f9', size: 16 }
            },
            xaxis: {
                title: 'Sample Index',
                color: '#cbd5e1',
                gridcolor: 'rgba(51, 65, 85, 0.2)'
            },
            yaxis: {
                title: 'Acceleration (m/s²)',
                color: '#cbd5e1',
                gridcolor: 'rgba(51, 65, 85, 0.2)'
            },
            plot_bgcolor: 'rgba(15, 23, 42, 0.5)',
            paper_bgcolor: 'transparent',
            font: { color: '#f1f5f9', family: 'Inter, sans-serif' },
            margin: { l: 80, r: 80, t: 80, b: 80 },
            hovermode: 'x unified'
        };

        const config = {
            responsive: true,
            displayModeBar: false
        };

        Plotly.newPlot(container, [trace], layout, config);
    }

    async loadDefaultAnalysis() {
        await this.analyzeFFT(this.getSelectedParams());
    }
}

// Global functions for tab switching
function switchTab(tab) {
    // Hide all tabs
    document.getElementById('fft-tab').style.display = 'none';
    document.getElementById('spectrogram-tab').style.display = 'none';
    document.getElementById('waveform-tab').style.display = 'none';

    // Remove active from all buttons
    document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));

    // Show selected tab and mark button as active
    document.getElementById(tab + '-tab').style.display = 'block';
    event.target.classList.add('active');

    // Trigger analysis
    const analysis = window.spectrumAnalysis;
    analysis.currentTab = tab;
    analysis.analyzeSpectrum();
}

function analyzeSpectrum() {
    if (window.spectrumAnalysis) {
        window.spectrumAnalysis.analyzeSpectrum();
    }
}

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    window.spectrumAnalysis = new SpectrumAnalysis();
});

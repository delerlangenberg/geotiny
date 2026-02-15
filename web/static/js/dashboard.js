/**
 * Dashboard JavaScript - Real-time seismic monitoring
 */

class Dashboard {
    constructor() {
        this.socket = io();
        this.deviceIds = ['device_1', 'device_2', 'device_3'];
        this.charts = {};
        this.updateInterval = 1000;
        this.lastUpdate = {};
        
        this.init();
    }

    init() {
        console.log('Initializing Dashboard...');
        this.setupSocketListeners();
        this.loadInitialData();
        this.setupPeriodicUpdates();
    }

    setupSocketListeners() {
        this.socket.on('connect', () => {
            console.log('Connected to server');
            this.updateConnectionStatus(true);
            this.subscribeToAllDevices();
        });

        this.socket.on('disconnect', () => {
            console.log('Disconnected from server');
            this.updateConnectionStatus(false);
        });

        this.socket.on('waveform_data', (data) => {
            this.handleWaveformData(data);
        });

        this.socket.on('error', (error) => {
            console.error('Socket error:', error);
            showNotification(`Error: ${error.message}`, 'danger');
        });
    }

    subscribeToAllDevices() {
        this.deviceIds.forEach(deviceId => {
            this.socket.emit('subscribe_device', {
                device_id: deviceId,
                sampling_rate: 10
            });
        });
    }

    updateConnectionStatus(connected) {
        const statusEl = document.getElementById('connection-status');
        if (statusEl) {
            if (connected) {
                statusEl.innerHTML = `
                    <span class="status-badge status-connected">
                        <span class="spinner-grow spinner-grow-sm me-2" style="color: var(--accent-green);"></span>
                        Connected
                    </span>
                `;
            } else {
                statusEl.innerHTML = `
                    <span class="status-badge status-disconnected">
                        <span class="spinner-grow spinner-grow-sm me-2" style="color: #ef4444;"></span>
                        Disconnected - Reconnecting...
                    </span>
                `;
            }
        }
    }

    async loadInitialData() {
        try {
            // Load device status
            const response = await fetch('/api/devices/status');
            const data = await response.json();

            if (data.status === 'success') {
                this.renderDevices(data.data);
                this.updateSystemStatus(data.data);
            }

            // Load earthquakes
            this.loadGlobalEarthquakes();

        } catch (error) {
            console.error('Error loading initial data:', error);
            showNotification('Failed to load initial data', 'danger');
        }
    }

    renderDevices(devicesData) {
        const container = document.getElementById('devices-container');
        if (!container) return;

        container.innerHTML = '';

        for (const [deviceId, status] of Object.entries(devicesData)) {
            const card = this.createDeviceCard(deviceId, status);
            container.appendChild(card);

            // Initialize chart for this device
            this.initializeWaveformChart(deviceId);
        }
    }

    createDeviceCard(deviceId, status) {
        const card = document.createElement('div');
        card.className = 'card device-card';
        card.id = `card-${deviceId}`;

        const statusBadge = status.connected 
            ? '<span class="status-badge status-connected">● Online</span>'
            : '<span class="status-badge status-disconnected">● Offline</span>';

        card.innerHTML = `
            <div class="card-body">
                <div class="device-header">
                    <div class="device-name">${deviceId.replace('_', ' ').toUpperCase()}</div>
                    ${statusBadge}
                </div>

                <div class="channel-display">
                    <div class="channel">
                        <div class="channel-label">X (N-S)</div>
                        <div class="channel-value" id="${deviceId}-x">-- </div>
                        <div class="channel-unit">m/s²</div>
                    </div>
                    <div class="channel">
                        <div class="channel-label">Y (E-W)</div>
                        <div class="channel-value" id="${deviceId}-y">--</div>
                        <div class="channel-unit">m/s²</div>
                    </div>
                    <div class="channel">
                        <div class="channel-label">Z (Vertical)</div>
                        <div class="channel-value" id="${deviceId}-z">--</div>
                        <div class="channel-unit">m/s²</div>
                    </div>
                </div>

                <div class="waveform-mini">
                    <canvas id="${deviceId}-waveform-canvas"></canvas>
                </div>

                <div class="stats-grid">
                    <div class="stat-item">
                        <div class="stat-label">Buffer Samples</div>
                        <div class="stat-value">${status.buffer_samples || 0}</div>
                    </div>
                    <div class="stat-item">
                        <div class="stat-label">Last Update</div>
                        <div class="stat-value text-muted" style="font-size: 0.875rem;">
                            ${status.last_data ? new Date(status.last_data).toLocaleTimeString() : 'N/A'}
                        </div>
                    </div>
                </div>

                <div class="mt-3">
                    <a href="/spectrum?device=${deviceId}" class="btn btn-primary btn-sm w-100">
                        Analyze Spectrum
                    </a>
                </div>
            </div>
        `;

        return card;
    }

    initializeWaveformChart(deviceId) {
        const canvasId = `${deviceId}-waveform-canvas`;
        const canvas = document.getElementById(canvasId);
        
        if (!canvas) return;

        const ctx = canvas.getContext('2d');
        const chart = new Chart(ctx, {
            type: 'line',
            data: {
                labels: [],
                datasets: [{
                    label: 'Z Channel (m/s²)',
                    data: [],
                    borderColor: 'rgba(6, 182, 212, 0.9)',
                    backgroundColor: 'rgba(6, 182, 212, 0.1)',
                    borderWidth: 1.5,
                    fill: true,
                    pointRadius: 0,
                    tension: 0.15,
                    segment: {
                        borderColor: ctx => ctx.p0DataIndex % 10 === 0 ? 'rgba(6, 182, 212, 0.9)' : 'rgba(6, 182, 212, 0.6)',
                    }
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                animation: {
                    duration: 0
                },
                plugins: {
                    legend: { 
                        display: false,
                        labels: { color: 'rgba(226, 232, 240, 0.7)' }
                    },
                    tooltip: {
                        backgroundColor: 'rgba(15, 23, 42, 0.8)',
                        titleColor: '#06b6d4',
                        bodyColor: '#e2e8f0',
                        borderColor: 'rgba(6, 182, 212, 0.5)',
                        borderWidth: 1
                    }
                },
                scales: {
                    x: { 
                        display: false,
                        grid: { display: false }
                    },
                    y: {
                        display: true,
                        ticks: { 
                            color: 'rgba(226, 232, 240, 0.5)',
                            maxTicksLimit: 4,
                            font: { size: 10 }
                        },
                        grid: { 
                            color: 'rgba(51, 65, 85, 0.2)',
                            drawBorder: false
                        }
                    }
                }
            }
        });

        this.charts[deviceId] = chart;
    }

    handleWaveformData(data) {
        const { device_id, channel, data: waveformData } = data;

        // Update channel value
        const valueEl = document.getElementById(`${device_id}-${channel.toLowerCase()}`);
        if (valueEl && waveformData.length > 0) {
            const lastValue = waveformData[waveformData.length - 1];
            valueEl.textContent = formatNumber(lastValue, 4);
        }

        // Update chart (only for Z channel)
        if (channel === 'Z' && this.charts[device_id]) {
            this.updateWaveformChart(device_id, waveformData);
        }
    }

    updateWaveformChart(deviceId, waveformData) {
        const chart = this.charts[deviceId];
        if (!chart) return;

        const maxPoints = 500; // Keep visualization responsive
        let data = waveformData;
        
        if (data.length > maxPoints) {
            // Decimate data for performance
            const step = Math.ceil(data.length / maxPoints);
            data = data.filter((_, i) => i % step === 0);
        }

        chart.data.labels = Array(data.length).fill('');
        chart.data.datasets[0].data = data;
        chart.update('none');
    }

    updateSystemStatus(devicesData) {
        const container = document.getElementById('system-status-container');
        if (!container) return;

        const connectedCount = Object.values(devicesData).filter(d => d.connected).length;
        const totalBufferSamples = Object.values(devicesData).reduce((sum, d) => sum + (d.buffer_samples || 0), 0);

        container.innerHTML = '';

        const statusItems = [
            {
                label: 'Devices Online',
                value: `${connectedCount}/3`,
                status: connectedCount === 3 ? 'success' : connectedCount > 0 ? 'warning' : 'error'
            },
            {
                label: 'Total Samples Buffered',
                value: formatLargeNumber(totalBufferSamples),
                status: 'success'
            },
            {
                label: 'Last Updated',
                value: new Date().toLocaleTimeString(),
                status: 'success'
            }
        ];

        statusItems.forEach(item => {
            const el = document.createElement('div');
            const statusClass = item.status !== 'success' ? (item.status === 'warning' ? 'warning' : 'error') : '';
            el.className = `status-item ${statusClass}`;
            el.innerHTML = `
                <div style="color: var(--text-tertiary); font-size: 0.875rem;">${item.label}</div>
                <div style="font-weight: 600; color: var(--accent-cyan); font-size: 1.5rem;">${item.value}</div>
            `;
            container.appendChild(el);
        });
    }

    async loadGlobalEarthquakes() {
        try {
            const response = await fetch('/api/global/earthquakes?min_magnitude=5.0&time_period=1day');
            const data = await response.json();

            if (data.status === 'success' && data.data.length > 0) {
                this.displayEarthquakesPreview(data.data.slice(0, 3));
            } else {
                document.getElementById('global-quake-container').innerHTML = `
                    <p class="text-secondary">No earthquakes detected in the last 24 hours with magnitude ≥ 5.0</p>
                `;
            }
        } catch (error) {
            console.error('Error loading earthquakes:', error);
            document.getElementById('global-quake-container').innerHTML = `
                <p class="text-danger">Error loading earthquake data</p>
            `;
        }
    }

    displayEarthquakesPreview(earthquakes) {
        const container = document.getElementById('global-quake-container');
        container.innerHTML = '';

        earthquakes.forEach(eq => {
            const eqElement = document.createElement('div');
            eqElement.className = 'border-bottom pb-3 mb-3';
            const magColor = eq.magnitude >= 7.0 ? '#ef4444' : eq.magnitude >= 6.0 ? '#f97316' : '#eab308';
            eqElement.innerHTML = `
                <div class="d-flex justify-content-between align-items-start">
                    <div class="text-start flex-grow-1">
                        <h5 style="color: ${magColor};">M${eq.magnitude.toFixed(1)} - ${eq.place}</h5>
                        <p class="text-tertiary" style="margin: 0; font-size: 0.875rem;">
                            ${new Date(eq.datetime).toLocaleString()}
                        </p>
                        <p class="text-tertiary" style="margin: 0; font-size: 0.875rem;">
                            Location: ${eq.latitude.toFixed(2)}°, ${eq.longitude.toFixed(2)}° | Depth: ${eq.depth_km.toFixed(1)} km
                        </p>
                    </div>
                </div>
            `;
            container.appendChild(eqElement);
        });

        container.innerHTML += `<a href="/global" class="btn btn-secondary mt-3 w-100">View Global Earthquake Map →</a>`;
    }

    setupPeriodicUpdates() {
        setInterval(() => this.loadInitialData(), 30000); // Every 30 seconds
    }
}

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    window.dashboard = new Dashboard();
});

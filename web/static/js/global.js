/**
 * Global Seismic Monitoring JavaScript
 */

class GlobalSeismic {
    constructor() {
        this.map = null;
        this.earthquakes = [];
        this.markers = {};
        this.mapInitialized = false;
        this.currentFilters = {
            minMagnitude: 0,
            maxMagnitude: 9,
            startDate: new Date(Date.now() - 7 * 24 * 60 * 60 * 1000), // 7 days ago
            selected: null
        };
        this.init();
    }

    init() {
        console.log('Initializing Global Seismic Monitoring...');
        this.setupMap();
        this.setupEventListeners();
        this.loadEarthquakes();
        this.setupPeriodicUpdates();
    }

    setupMap() {
        const mapContainer = document.getElementById('earthquake-map');
        if (!mapContainer) {
            console.warn('Map container not found');
            return;
        }

        // Initialize Leaflet map
        this.map = L.map('earthquake-map', {
            center: [20, 0],
            zoom: 2,
            preferCanvas: true,
            layers: [L.tileLayer('https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png', {
                attribution: '&copy; CartoDB',
                maxZoom: 19,
                crossOrigin: true
            })]
        });

        this.mapInitialized = true;
    }

    setupEventListeners() {
        // Magnitude filter
        const magSlider = document.getElementById('magnitude-slider');
        if (magSlider) {
            magSlider.addEventListener('input', (e) => {
                this.currentFilters.minMagnitude = parseFloat(e.target.value);
                document.getElementById('magnitude-value').textContent = parseFloat(e.target.value).toFixed(1);
                this.filterEarthquakes();
            });
        }

        // Time period filter
        const timePeriod = document.getElementById('time-period');
        if (timePeriod) {
            timePeriod.addEventListener('change', (e) => {
                this.updateTimePeriod(e.target.value);
                this.loadEarthquakes();
            });
        }

        // Refresh button
        const refreshBtn = document.querySelector('button[onclick="window.globSeismic.loadEarthquakes()"]');
        if (refreshBtn) {
            refreshBtn.addEventListener('click', () => this.loadEarthquakes());
        }
    }

    updateTimePeriod(period) {
        const now = new Date();
        switch (period) {
            case '24h':
                this.currentFilters.startDate = new Date(now.getTime() - 24 * 60 * 60 * 1000);
                break;
            case '7d':
                this.currentFilters.startDate = new Date(now.getTime() - 7 * 24 * 60 * 60 * 1000);
                break;
            case '30d':
                this.currentFilters.startDate = new Date(now.getTime() - 30 * 24 * 60 * 60 * 1000);
                break;
            default:
                this.currentFilters.startDate = new Date(now.getTime() - 7 * 24 * 60 * 60 * 1000);
        }
    }

    async loadEarthquakes() {
        try {
            const params = new URLSearchParams({
                minmagnitude: this.currentFilters.minMagnitude,
                starttime: this.currentFilters.startDate.toISOString().split('T')[0],
                limit: 500
            });

            const response = await fetch(`/api/global/earthquakes?${params}`);
            const data = await response.json();

            if (data.status === 'success') {
                this.earthquakes = data.data;
                this.displayEarthquakes();
                this.updateStatistics();
                showNotification(`Loaded ${this.earthquakes.length} earthquakes`, 'info');
            } else {
                showNotification(`Error: ${data.message}`, 'danger');
            }
        } catch (error) {
            console.error('Error loading earthquakes:', error);
            showNotification('Error loading earthquakes', 'danger');
        }
    }

    displayEarthquakes() {
        // Clear existing markers
        Object.values(this.markers).forEach(marker => this.map.removeLayer(marker));
        this.markers = {};

        // Add new markers
        this.earthquakes.forEach((eq, idx) => {
            const magnitude = parseFloat(eq.magnitude) || 0;
            const depth = parseFloat(eq.depth) || 0;
            const lat = parseFloat(eq.latitude) || 0;
            const lon = parseFloat(eq.longitude) || 0;

            // Skip invalid coordinates
            if (lat === 0 && lon === 0) return;

            const color = this.getMagnitudeColor(magnitude);
            const radius = 5 + (magnitude * 2);

            const circleMarker = L.circleMarker([lat, lon], {
                radius: Math.min(radius, 30),
                fillColor: color,
                color: color,
                weight: 2,
                opacity: 0.8,
                fillOpacity: 0.7,
                className: `earthquake-marker magnitude-${Math.floor(magnitude)}`
            });

            const popupContent = `
                <div style="color: #f1f5f9; font-size: 12px;">
                    <strong>Magnitude: ${magnitude.toFixed(1)}</strong><br>
                    Depth: ${depth.toFixed(1)} km<br>
                    Location: ${eq.place}<br>
                    Time: ${formatTimestamp(eq.time)}
                </div>
            `;

            circleMarker.bindPopup(popupContent);
            circleMarker.on('click', () => this.selectEarthquake(eq, idx));
            
            this.map.addLayer(circleMarker);
            this.markers[idx] = circleMarker;
        });

        // Fit bounds if earthquakes exist
        if (this.earthquakes.length > 0) {
            const group = new L.featureGroup(Object.values(this.markers));
            this.map.fitBounds(group.getBounds(), { padding: [50, 50] });
        }
    }

    getMagnitudeColor(magnitude) {
        if (magnitude >= 7) return '#ef4444';     // Red
        if (magnitude >= 6) return '#f97316';     // Orange
        if (magnitude >= 5) return '#eab308';     // Yellow
        if (magnitude >= 4) return '#06b6d4';     // Cyan
        return '#3b82f6';                         // Blue
    }

    filterEarthquakes() {
        this.displayEarthquakes();
        this.updateEarthquakeList();
    }

    selectEarthquake(eq, idx) {
        this.currentFilters.selected = idx;
        this.displayEarthquakeDetails(eq);
        
        // Highlight marker
        Object.values(this.markers).forEach(marker => marker.setStyle({ weight: 2, opacity: 0.8 }));
        if (this.markers[idx]) {
            this.markers[idx].setStyle({ weight: 3, opacity: 1 });
        }
    }

    displayEarthquakeDetails(eq) {
        const container = document.getElementById('earthquake-details');
        if (!container) return;

        const magnitude = parseFloat(eq.magnitude) || 0;
        const depth = parseFloat(eq.depth) || 0;
        const color = this.getMagnitudeColor(magnitude);

        container.innerHTML = `
            <div style="border-left: 4px solid ${color}; padding-left: 12px;">
                <h5 style="color: ${color}; margin-bottom: 8px;">
                    Magnitude ${magnitude.toFixed(1)}
                </h5>
                <table class="table table-sm" style="color: var(--text-secondary); margin-bottom: 0;">
                    <tbody>
                        <tr>
                            <td><strong>Location:</strong></td>
                            <td>${eq.place}</td>
                        </tr>
                        <tr>
                            <td><strong>Latitude:</strong></td>
                            <td class="code-block">${parseFloat(eq.latitude).toFixed(4)}°</td>
                        </tr>
                        <tr>
                            <td><strong>Longitude:</strong></td>
                            <td class="code-block">${parseFloat(eq.longitude).toFixed(4)}°</td>
                        </tr>
                        <tr>
                            <td><strong>Depth:</strong></td>
                            <td class="code-block">${depth.toFixed(1)} km</td>
                        </tr>
                        <tr>
                            <td><strong>Time (UTC):</strong></td>
                            <td>${formatTimestamp(eq.time)}</td>
                        </tr>
                        <tr>
                            <td><strong>Time Ago:</strong></td>
                            <td>${getRelativeTime(new Date(eq.time))}</td>
                        </tr>
                    </tbody>
                </table>
            </div>
        `;
    }

    updateEarthquakeList() {
        const container = document.getElementById('earthquake-list');
        if (!container) return;

        const sorted = [...this.earthquakes]
            .sort((a, b) => parseFloat(b.magnitude) - parseFloat(a.magnitude))
            .slice(0, 50); // Top 50

        if (sorted.length === 0) {
            container.innerHTML = '<p style="color: var(--text-secondary); text-align: center; padding: 20px;">No earthquakes found</p>';
            return;
        }

        container.innerHTML = sorted.map((eq, idx) => {
            const magnitude = parseFloat(eq.magnitude) || 0;
            const color = this.getMagnitudeColor(magnitude);
            const depth = parseFloat(eq.depth) || 0;

            return `
                <div class="earthquake-item" onclick="window.globSeismic.selectEarthquake(this.dataset.earthquake, ${idx})"
                     data-earthquake='${JSON.stringify(eq).replace(/'/g, "&apos;")}' 
                     style="border-left: 3px solid ${color}; cursor: pointer; transition: all 0.2s; padding: 10px; margin-bottom: 8px; border-radius: 4px; background-color: rgba(15, 23, 42, 0.3); padding-left: 10px;">
                    <div style="display: flex; justify-content: space-between; align-items: start;">
                        <div>
                            <strong style="color: ${color}; font-size: 14px;">M${magnitude.toFixed(1)}</strong>
                            <div style="font-size: 12px; color: var(--text-secondary); margin-top: 4px;">
                                ${eq.place}
                            </div>
                            <div style="font-size: 11px; color: var(--text-tertiary); margin-top: 2px;">
                                ${depth.toFixed(1)} km deep • ${getRelativeTime(new Date(eq.time))}
                            </div>
                        </div>
                    </div>
                </div>
            `;
        }).join('');

        // Re-attach click handlers (needed because of dynamic HTML)
        document.querySelectorAll('.earthquake-item').forEach(item => {
            item.addEventListener('click', () => {
                const eq = JSON.parse(item.dataset.earthquake);
                this.selectEarthquake(eq, this.earthquakes.indexOf(eq));
                this.displayEarthquakeDetails(eq);
            });
        });
    }

    updateStatistics() {
        const container = document.getElementById('stats-container');
        if (!container) return;

        const magnitudes = this.earthquakes.map(e => parseFloat(e.magnitude) || 0);
        const magnitudeCount = {
            major: magnitudes.filter(m => m >= 7).length,
            strong: magnitudes.filter(m => m >= 6 && m < 7).length,
            moderate: magnitudes.filter(m => m >= 5 && m < 6).length,
            minor: magnitudes.filter(m => m >= 4 && m < 5).length,
            light: magnitudes.filter(m => m < 4).length
        };

        container.innerHTML = `
            <div class="row">
                <div class="col-6">
                    <div style="background-color: rgba(15, 23, 42, 0.3); padding: 12px; border-radius: 4px; margin-bottom: 8px;">
                        <div style="font-size: 11px; color: var(--text-tertiary); text-transform: uppercase;">Total Earthquakes</div>
                        <div style="font-size: 20px; font-weight: bold; color: #06b6d4;">${this.earthquakes.length}</div>
                    </div>
                </div>
                <div class="col-6">
                    <div style="background-color: rgba(15, 23, 42, 0.3); padding: 12px; border-radius: 4px; margin-bottom: 8px;">
                        <div style="font-size: 11px; color: var(--text-tertiary); text-transform: uppercase;">Avg Magnitude</div>
                        <div style="font-size: 20px; font-weight: bold; color: #3b82f6;">${(magnitudes.reduce((a,b) => a+b, 0) / magnitudes.length).toFixed(1)}</div>
                    </div>
                </div>
            </div>
            <div style="margin-top: 12px; padding: 12px; background-color: rgba(15, 23, 42, 0.3); border-radius: 4px;">
                <div style="font-size: 11px; color: var(--text-tertiary); text-transform: uppercase; margin-bottom: 8px;">By Magnitude</div>
                <table class="table table-sm" style="color: var(--text-secondary); margin-bottom: 0;">
                    <tbody>
                        <tr>
                            <td style="color: #ef4444;">7.0+</td>
                            <td style="text-align: right;"><strong>${magnitudeCount.major}</strong></td>
                        </tr>
                        <tr>
                            <td style="color: #f97316;">6.0-6.9</td>
                            <td style="text-align: right;"><strong>${magnitudeCount.strong}</strong></td>
                        </tr>
                        <tr>
                            <td style="color: #eab308;">5.0-5.9</td>
                            <td style="text-align: right;"><strong>${magnitudeCount.moderate}</strong></td>
                        </tr>
                        <tr>
                            <td style="color: #06b6d4;">4.0-4.9</td>
                            <td style="text-align: right;"><strong>${magnitudeCount.minor}</strong></td>
                        </tr>
                        <tr>
                            <td style="color: #3b82f6;">&lt;4.0</td>
                            <td style="text-align: right;"><strong>${magnitudeCount.light}</strong></td>
                        </tr>
                    </tbody>
                </table>
            </div>
        `;
    }

    setupPeriodicUpdates() {
        // Refresh earthquakes every 5 minutes
        setInterval(() => this.loadEarthquakes(), 5 * 60 * 1000);
    }
}

// Global functions
function refreshEarthquakeData() {
    if (window.globSeismic) {
        window.globSeismic.loadEarthquakes();
    }
}

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    window.globSeismic = new GlobalSeismic();
});

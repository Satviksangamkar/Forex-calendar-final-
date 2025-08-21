class ForexCalendar {
    constructor() {
        this.baseUrl = 'http://localhost:8000';
        this.events = [];
        this.filteredEvents = [];
        this.currentFilters = {
            search: '',
            currency: ''
        };
        
        this.init();
    }

    init() {
        this.setupEventListeners();
        this.setDefaultDates();
        this.checkHealth();
        this.loadDatabaseStats();
    }

    setupEventListeners() {
        // Load events button
        document.getElementById('loadEvents').addEventListener('click', () => this.loadEvents());
        
        // Test connection button
        document.getElementById('testConnection').addEventListener('click', () => this.checkHealth());
        
        // Search and filter
        const searchInput = document.getElementById('searchInput');
        searchInput.addEventListener('input', (e) => {
            console.log('Search input:', e.target.value);
            this.handleSearch(e.target.value);
        });
        searchInput.addEventListener('keyup', (e) => {
            this.handleSearch(e.target.value);
        });
        
        document.getElementById('currencyFilter').addEventListener('change', (e) => this.handleCurrencyFilter(e.target.value));
        
        // Export button
        document.getElementById('exportBtn').addEventListener('click', () => this.exportToCSV());
        
        // Database management
        document.getElementById('refreshStatsBtn').addEventListener('click', () => this.loadDatabaseStats());
        document.getElementById('deleteRangeBtn').addEventListener('click', () => this.deleteRange());
        
        // Modal controls
        document.getElementById('closeModal').addEventListener('click', () => this.hideModal());
        document.getElementById('eventModal').addEventListener('click', (e) => {
            if (e.target.classList.contains('modal-backdrop')) {
                this.hideModal();
            }
        });
        
        // Notification controls
        document.getElementById('closeNotification').addEventListener('click', () => this.hideNotification());
        
        // Retry button
        document.getElementById('retryBtn').addEventListener('click', () => this.loadEvents());
        
        // Escape key to close modal
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape') {
                this.hideModal();
            }
        });
    }

    setDefaultDates() {
        const today = new Date();
        const todayStr = today.toISOString().split('T')[0];
        
        document.getElementById('startDate').value = todayStr;
        document.getElementById('endDate').value = todayStr;
    }

    async checkHealth() {
        try {
            console.log('Checking health at:', `${this.baseUrl}/health`);
            const response = await fetch(`${this.baseUrl}/health`);
            const isOnline = response.ok;
            
            console.log('Health response:', response.status, response.statusText);
            
            const statusDot = document.getElementById('statusDot');
            const statusText = document.getElementById('statusText');
            
            if (isOnline) {
                const data = await response.json();
                statusDot.className = 'status-dot status-dot--online';
                statusText.textContent = `Connected (Redis: ${data.redis})`;
                console.log('Backend is online:', data);
                this.showNotification(`Backend connected successfully! Redis: ${data.redis}`, 'success');
            } else {
                statusDot.className = 'status-dot status-dot--offline';
                statusText.textContent = 'Offline';
                console.log('Backend is offline');
                this.showNotification('Backend is offline', 'error');
            }
        } catch (error) {
            console.error('Health check error:', error);
            const statusDot = document.getElementById('statusDot');
            const statusText = document.getElementById('statusText');
            statusDot.className = 'status-dot status-dot--offline';
            statusText.textContent = 'Offline';
            this.showNotification(`Connection failed: ${error.message}`, 'error');
        }
    }

    async loadEvents() {
        const startDate = document.getElementById('startDate').value;
        const endDate = document.getElementById('endDate').value;
        const useOriginal = !document.getElementById('dataToggle').checked;

        if (!startDate || !endDate) {
            this.showNotification('Please select both start and end dates', 'error');
            return;
        }

        this.showLoading();
        this.hideError();
        this.hideEmpty();

        try {
            const url = `${this.baseUrl}/events?start=${startDate}&end=${endDate}&original=${useOriginal}`;
            console.log('Fetching events from:', url);
            
            const response = await fetch(url);
            console.log('Events response:', response.status, response.statusText);

            if (!response.ok) {
                const errorText = await response.text();
                throw new Error(`HTTP ${response.status}: ${response.statusText} - ${errorText}`);
            }

            const responseData = await response.json();
            console.log('Response data:', responseData);
            
            // Handle the structured response from backend
            if (responseData.success && responseData.data) {
                this.events = responseData.data;
                console.log(`Loaded ${this.events.length} events from ${responseData.source} in ${responseData.processing_time_ms}ms`);
                
                // Apply filters and render
                this.applyFilters();
                this.hideLoading();
                this.renderEvents();
                
                const dataType = useOriginal ? 'original' : 'paraphrased';
                this.showNotification(
                    `Loaded ${this.events.length} events from ${responseData.source} (${dataType}) in ${responseData.processing_time_ms}ms`, 
                    'success'
                );
            } else {
                this.events = [];
                this.hideLoading();
                this.showEmpty();
                this.showNotification('No events found for the selected date range', 'info');
            }

        } catch (error) {
            console.error('Error loading events:', error);
            this.hideLoading();
            this.showError(error.message);
            this.showNotification(`Failed to load events: ${error.message}`, 'error');
        }
    }

    applyFilters() {
        this.filteredEvents = this.events.filter(event => {
            const matchesSearch = !this.currentFilters.search || 
                event.event.toLowerCase().includes(this.currentFilters.search.toLowerCase()) ||
                event.currency.toLowerCase().includes(this.currentFilters.search.toLowerCase());
            
            const matchesCurrency = !this.currentFilters.currency || 
                event.currency === this.currentFilters.currency;
            
            return matchesSearch && matchesCurrency;
        });
    }

    handleSearch(searchTerm) {
        this.currentFilters.search = searchTerm;
        this.applyFilters();
        this.renderEvents();
        console.log(`Filtered ${this.filteredEvents.length} events for search: "${searchTerm}"`);
    }

    handleCurrencyFilter(currency) {
        this.currentFilters.currency = currency;
        this.applyFilters();
        this.renderEvents();
    }

    renderEvents() {
        const tbody = document.getElementById('eventsTableBody');
        tbody.innerHTML = '';

        if (this.filteredEvents.length === 0) {
            this.showEmpty();
            return;
        }

        this.hideEmpty();
        document.getElementById('eventsSection').classList.remove('hidden');

        this.filteredEvents.forEach((event, index) => {
            const row = document.createElement('tr');
            
            // Apply impact-based row coloring
            const impactClass = this.getImpactRowClass(event.impact);
            if (impactClass) {
                row.classList.add(impactClass);
            }

            row.innerHTML = `
                <td>${this.formatTime(event.time)}</td>
                <td>
                    <span class="currency-badge">${event.currency}</span>
                </td>
                <td>
                    <span class="impact-badge ${this.getImpactClass(event.impact)}">${event.impact}</span>
                </td>
                <td class="event-name">${event.event}</td>
                <td>${event.actual || '-'}</td>
                <td>${event.forecast || '-'}</td>
                <td>${event.previous || '-'}</td>
                <td>
                    <button class="details-btn" data-event-index="${index}">
                        View Details
                    </button>
                </td>
            `;

            tbody.appendChild(row);
        });

        // Add event listeners for detail buttons
        const detailButtons = tbody.querySelectorAll('.details-btn');
        detailButtons.forEach(button => {
            button.addEventListener('click', (e) => {
                const index = parseInt(e.target.getAttribute('data-event-index'));
                this.showEventDetails(index);
            });
        });
    }

    getImpactClass(impact) {
        const impactLower = impact.toLowerCase();
        if (impactLower === 'high') return 'impact-high';
        if (impactLower === 'medium') return 'impact-medium';
        if (impactLower === 'low') return 'impact-low';
        return '';
    }

    getImpactRowClass(impact) {
        const impactLower = impact.toLowerCase();
        if (impactLower === 'high') return 'impact-high';
        if (impactLower === 'medium') return 'impact-medium';
        if (impactLower === 'low') return 'impact-low';
        return '';
    }

    formatTime(time) {
        if (!time) return '-';
        return time;
    }

    showEventDetails(index) {
        const event = this.filteredEvents[index];
        if (!event) return;

        const modal = document.getElementById('eventModal');
        const modalTitle = document.getElementById('modalTitle');
        const modalBody = document.getElementById('modalBody');

        modalTitle.textContent = event.event;

        const details = event.details || {};
        const basicInfo = [
            { label: 'Date', value: event.date },
            { label: 'Time', value: event.time },
            { label: 'Currency', value: event.currency },
            { label: 'Impact', value: event.impact },
            { label: 'Actual', value: event.actual || 'N/A' },
            { label: 'Forecast', value: event.forecast || 'N/A' },
            { label: 'Previous', value: event.previous || 'N/A' }
        ];

        const detailInfo = [
            { label: 'Source', value: details.source },
            { label: 'Measures', value: details.measures },
            { label: 'Usual Effect', value: details.usual_effect },
            { label: 'Frequency', value: details.frequency },
            { label: 'Next Release', value: details.next_release },
            { label: 'FF Notes', value: details.ff_notes },
            { label: 'Description', value: details.description }
        ];

        let html = '<div class="modal-section"><h4>Event Information</h4>';
        basicInfo.forEach(item => {
            if (item.value) {
                html += `
                    <div class="modal-field">
                        <span class="modal-field-label">${item.label}:</span>
                        <span class="modal-field-value">${item.value}</span>
                    </div>
                `;
            }
        });
        html += '</div>';

        if (Object.keys(details).length > 0) {
            html += '<div class="modal-section"><h4>Additional Details</h4>';
            detailInfo.forEach(item => {
                if (item.value) {
                    html += `
                        <div class="modal-field">
                            <span class="modal-field-label">${item.label}:</span>
                            <span class="modal-field-value">${item.value}</span>
                        </div>
                    `;
                }
            });
            html += '</div>';
        }

        modalBody.innerHTML = html;
        modal.classList.remove('hidden');
    }

    hideModal() {
        document.getElementById('eventModal').classList.add('hidden');
    }

    async loadDatabaseStats() {
        try {
            const response = await fetch(`${this.baseUrl}/database/info`);
            if (response.ok) {
                const data = await response.json();
                document.getElementById('totalRecords').textContent = data.total_records || '0';
                document.getElementById('dateRange').textContent = 
                    data.date_range ? `${data.date_range.start} to ${data.date_range.end}` : 'No data';
            } else {
                throw new Error('Backend not available');
            }
        } catch (error) {
            console.error('Error loading database stats:', error);
            document.getElementById('totalRecords').textContent = 'N/A';
            document.getElementById('dateRange').textContent = 'N/A';
        }
    }

    async deleteRange() {
        const startDate = document.getElementById('startDate').value;
        const endDate = document.getElementById('endDate').value;

        if (!startDate || !endDate) {
            this.showNotification('Please select date range to delete', 'error');
            return;
        }

        if (!confirm(`Are you sure you want to delete all records from ${startDate} to ${endDate}?`)) {
            return;
        }

        try {
            const url = `${this.baseUrl}/database/delete?start=${startDate}&end=${endDate}`;
            const response = await fetch(url, { method: 'DELETE' });

            if (response.ok) {
                this.showNotification('Records deleted successfully', 'success');
                this.loadDatabaseStats();
                // Clear current events if they fall in deleted range
                this.events = [];
                this.filteredEvents = [];
                this.renderEvents();
            } else {
                const errorText = await response.text();
                throw new Error(`Failed to delete records: ${response.statusText} - ${errorText}`);
            }
        } catch (error) {
            console.error('Error deleting records:', error);
            this.showNotification(`Cannot delete - ${error.message}`, 'error');
        }
    }

    exportToCSV() {
        if (this.filteredEvents.length === 0) {
            this.showNotification('No events to export', 'error');
            return;
        }

        const headers = ['Date', 'Time', 'Currency', 'Impact', 'Event', 'Actual', 'Forecast', 'Previous'];
        const csvContent = [
            headers.join(','),
            ...this.filteredEvents.map(event => [
                event.date,
                event.time,
                event.currency,
                event.impact,
                `"${event.event.replace(/"/g, '""')}"`,
                event.actual || '',
                event.forecast || '',
                event.previous || ''
            ].join(','))
        ].join('\n');

        const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
        const link = document.createElement('a');
        const url = URL.createObjectURL(blob);
        link.setAttribute('href', url);
        link.setAttribute('download', `forex-events-${new Date().toISOString().split('T')[0]}.csv`);
        link.style.visibility = 'hidden';
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);

        this.showNotification('Events exported successfully', 'success');
    }

    showLoading() {
        document.getElementById('loadingState').classList.remove('hidden');
        document.getElementById('eventsSection').classList.add('hidden');
    }

    hideLoading() {
        document.getElementById('loadingState').classList.add('hidden');
    }

    showError(message = 'Failed to load events') {
        document.getElementById('errorMessage').textContent = message;
        document.getElementById('errorState').classList.remove('hidden');
        document.getElementById('eventsSection').classList.add('hidden');
    }

    hideError() {
        document.getElementById('errorState').classList.add('hidden');
    }

    showEmpty() {
        document.getElementById('emptyState').classList.remove('hidden');
        document.getElementById('eventsSection').classList.add('hidden');
    }

    hideEmpty() {
        document.getElementById('emptyState').classList.add('hidden');
    }

    showNotification(message, type = 'success') {
        const notification = document.getElementById('notification');
        const messageEl = document.getElementById('notificationMessage');
        
        messageEl.textContent = message;
        notification.className = `notification ${type}`;
        notification.classList.add('show');

        // Auto-hide after 5 seconds
        setTimeout(() => {
            this.hideNotification();
        }, 5000);
    }

    hideNotification() {
        const notification = document.getElementById('notification');
        notification.classList.remove('show');
    }
}

// Initialize the application
document.addEventListener('DOMContentLoaded', () => {
    console.log('Initializing Forex Calendar application...');
    const forexCalendar = new ForexCalendar();
});
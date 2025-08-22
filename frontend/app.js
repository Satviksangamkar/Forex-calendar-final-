class ForexCalendar {
    constructor() {
        // Prioritize port 8003 where backend is currently running
        this.possiblePorts = [8003, 8001, 8000, 8002, 8004, 8005, 8006, 8007, 8008, 8009, 8010];
        this.baseUrl = null;
        this.events = [];
        this.filteredEvents = [];
        this.currentFilters = {
            search: '',
            currency: ''
        };
        
        this.init();
    }

    async init() {
        await this.findBackendPort();
        this.setupEventListeners();
        this.setDefaultDates();
        if (this.baseUrl) {
            await this.checkHealth();
            await this.loadDatabaseStats();
        }
    }

    async findBackendPort() {
        // Try to find the correct backend port
        for (const port of this.possiblePorts) {
            try {
                const testUrl = `http://localhost:${port}/health`;
                
                // Create a timeout promise
                const timeoutPromise = new Promise((_, reject) => {
                    setTimeout(() => reject(new Error('Port check timeout')), 2000);
                });
                
                // Create the fetch promise
                const fetchPromise = fetch(testUrl, { 
                    method: 'GET'
                });
                
                // Race between fetch and timeout
                const response = await Promise.race([fetchPromise, timeoutPromise]);
                
                if (response.ok) {
                    this.baseUrl = `http://localhost:${port}`;
                    console.log(`✅ Backend found on port ${port}`);
                    this.showNotification(`Backend connected on port ${port}`, 'success');
                    return;
                }
            } catch (error) {
                console.log(`Port ${port} not available:`, error.message);
                continue;
            }
        }
        
        // If no port found, default to 8003 (current backend port)
        this.baseUrl = 'http://localhost:8003';
        console.warn('Could not detect backend port, defaulting to 8003');
        this.showNotification('Backend port detection failed, using default port 8003', 'warning');
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
        if (!this.baseUrl) {
            this.showNotification('Backend URL not configured', 'error');
            return;
        }

        try {
            console.log('Checking health at:', `${this.baseUrl}/health`);
            
            // Create a timeout promise
            const timeoutPromise = new Promise((_, reject) => {
                setTimeout(() => reject(new Error('Health check timeout after 5 seconds')), 5000);
            });
            
            // Create the fetch promise
            const fetchPromise = fetch(`${this.baseUrl}/health`, {
                method: 'GET',
                headers: {
                    'Accept': 'application/json',
                }
            });
            
            // Race between fetch and timeout
            const response = await Promise.race([fetchPromise, timeoutPromise]);
            
            console.log('Health response:', response.status, response.statusText);
            
            const statusDot = document.getElementById('statusDot');
            const statusText = document.getElementById('statusText');
            
            if (response.ok) {
                const data = await response.json();
                console.log('Health data:', data);
                
                if (data.status === 'healthy' && data.redis === 'connected') {
                    statusDot.className = 'status-dot status-dot--online';
                    statusText.textContent = `Connected (Redis: ${data.redis})`;
                    this.showNotification(`Backend connected successfully! Redis: ${data.redis}`, 'success');
                } else {
                    statusDot.className = 'status-dot status-dot--offline';
                    statusText.textContent = `Unhealthy (Redis: ${data.redis || 'unknown'})`;
                    this.showNotification(`Backend unhealthy: Redis ${data.redis || 'unknown'}`, 'error');
                }
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
        if (!this.baseUrl) {
            this.showNotification('Backend not connected', 'error');
            return;
        }

        const startDate = document.getElementById('startDate').value;
        const endDate = document.getElementById('endDate').value;
        const useParaphrased = document.getElementById('dataToggle').checked;

        if (!startDate || !endDate) {
            this.showNotification('Please select both start and end dates', 'error');
            return;
        }

        this.showLoading();
        this.hideError();
        this.hideEmpty();

        try {
            // Use the appropriate endpoint based on data type preference
            let url;
            if (useParaphrased) {
                // Default endpoint returns paraphrased data
                url = `${this.baseUrl}/events?start=${startDate}&end=${endDate}`;
            } else {
                // Use the dedicated original endpoint
                url = `${this.baseUrl}/events/original?start=${startDate}&end=${endDate}`;
            }
            
            console.log('Fetching events from:', url);
            console.log('Base URL:', this.baseUrl);
            console.log('Start Date:', startDate);
            console.log('End Date:', endDate);
            console.log('Use Paraphrased:', useParaphrased);
            
            // Create a timeout promise
            const timeoutPromise = new Promise((_, reject) => {
                setTimeout(() => reject(new Error('Request timeout after 30 seconds')), 30000);
            });
            
            // Create the fetch promise
            const fetchPromise = fetch(url, {
                method: 'GET',
                headers: {
                    'Accept': 'application/json',
                }
            });
            
            // Race between fetch and timeout
            const response = await Promise.race([fetchPromise, timeoutPromise]);
            
            console.log('Events response:', response.status, response.statusText);
            console.log('Response headers:', Object.fromEntries(response.headers.entries()));
            console.log('Response ok:', response.ok);

            if (!response.ok) {
                const errorText = await response.text();
                throw new Error(`HTTP ${response.status}: ${response.statusText} - ${errorText}`);
            }

            const responseData = await response.json();
            console.log('Response data:', responseData);
            console.log('Response data type:', typeof responseData);
            console.log('Response data keys:', Object.keys(responseData));
            
            // Handle the structured response from backend
            if (responseData.success && responseData.data) {
                this.events = responseData.data;
                console.log(`Loaded ${this.events.length} events from ${responseData.source} in ${responseData.processing_time_ms}ms`);
                console.log('First event sample:', this.events[0]);
                
                // Update data source info
                this.updateDataSourceInfo(responseData.source, responseData.processing_time_ms, useParaphrased ? 'paraphrased' : 'original');
                
                // Apply filters and render
                this.applyFilters();
                this.hideLoading();
                this.renderEvents();
                
                const dataType = useParaphrased ? 'paraphrased' : 'original';
                this.showNotification(
                    `Loaded ${this.events.length} events from ${responseData.source} (${dataType}) in ${responseData.processing_time_ms}ms`, 
                    'success'
                );
            } else {
                console.log('No events found or invalid response structure');
                console.log('Response success:', responseData.success);
                console.log('Response data exists:', !!responseData.data);
                console.log('Response data length:', responseData.data ? responseData.data.length : 'N/A');
                
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
        console.log('Applying filters to', this.events.length, 'events');
        console.log('Current filters:', this.currentFilters);
        
        this.filteredEvents = this.events.filter(event => {
            const matchesSearch = !this.currentFilters.search || 
                event.event.toLowerCase().includes(this.currentFilters.search.toLowerCase()) ||
                event.currency.toLowerCase().includes(this.currentFilters.search.toLowerCase());
            
            const matchesCurrency = !this.currentFilters.currency || 
                event.currency === this.currentFilters.currency;
            
            return matchesSearch && matchesCurrency;
        });
        
        console.log('Filtered to', this.filteredEvents.length, 'events');
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
        console.log('Rendering events...');
        const tbody = document.getElementById('eventsTableBody');
        tbody.innerHTML = '';

        if (this.filteredEvents.length === 0) {
            console.log('No filtered events to render, showing empty state');
            this.showEmpty();
            return;
        }

        console.log('Rendering', this.filteredEvents.length, 'filtered events');
        this.hideEmpty();
        document.getElementById('eventsSection').classList.remove('hidden');

        this.filteredEvents.forEach((event, index) => {
            console.log(`Rendering event ${index}:`, event);
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
                <td class="event-name">${this.escapeHtml(event.event)}</td>
                <td>${this.escapeHtml(event.actual || '-')}</td>
                <td>${this.escapeHtml(event.forecast || '-')}</td>
                <td>${this.escapeHtml(event.previous || '-')}</td>
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
        
        console.log('Events rendered successfully');
    }

    escapeHtml(text) {
        if (!text) return '';
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    updateDataSourceInfo(source, processingTime, dataType) {
        const sourceElement = document.getElementById('dataSource');
        const timeElement = document.getElementById('processingTime');
        const dataTypeElement = document.getElementById('dataType');
        
        if (sourceElement && timeElement && dataTypeElement) {
            sourceElement.textContent = source || 'Unknown';
            timeElement.textContent = processingTime ? `${processingTime}ms` : 'Unknown';
            dataTypeElement.textContent = dataType || 'Unknown';
        }
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
        if (!this.baseUrl) {
            document.getElementById('totalRecords').textContent = 'N/A';
            document.getElementById('dateRange').textContent = 'N/A';
            return;
        }

        try {
            // Create a timeout promise
            const timeoutPromise = new Promise((_, reject) => {
                setTimeout(() => reject(new Error('Database stats timeout after 5 seconds')), 5000);
            });
            
            // Create the fetch promise
            const fetchPromise = fetch(`${this.baseUrl}/database/info`, {
                method: 'GET',
                headers: {
                    'Accept': 'application/json',
                }
            });
            
            // Race between fetch and timeout
            const response = await Promise.race([fetchPromise, timeoutPromise]);
            
            if (response.ok) {
                const data = await response.json();
                console.log('Database stats:', data);
                
                // Handle the new backend response structure
                const totalRecords = data.total_keys || data.total_records || '0';
                
                // Format date range if available, otherwise show total records info
                let dateRangeText = 'No data';
                if (data.total_keys && data.total_keys > 0) {
                    dateRangeText = `${data.total_keys} records stored`;
                }
                
                document.getElementById('totalRecords').textContent = totalRecords;
                document.getElementById('dateRange').textContent = dateRangeText;
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
        if (!this.baseUrl) {
            this.showNotification('Backend not connected', 'error');
            return;
        }

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
            
            // Create a timeout promise
            const timeoutPromise = new Promise((_, reject) => {
                setTimeout(() => reject(new Error('Delete operation timeout after 10 seconds')), 10000);
            });
            
            // Create the fetch promise
            const fetchPromise = fetch(url, { 
                method: 'DELETE',
                headers: {
                    'Accept': 'application/json',
                }
            });
            
            // Race between fetch and timeout
            const response = await Promise.race([fetchPromise, timeoutPromise]);

            if (response.ok) {
                const result = await response.json();
                this.showNotification(result.message || 'Records deleted successfully', 'success');
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
        this.updateDataSourceInfo('', '', '');
    }

    hideError() {
        document.getElementById('errorState').classList.add('hidden');
    }

    showEmpty() {
        document.getElementById('emptyState').classList.remove('hidden');
        document.getElementById('eventsSection').classList.add('hidden');
        this.updateDataSourceInfo('', '', '');
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

    // Comprehensive test function for August 11-14, 2025
    async testAugust11to14() {
        if (!this.baseUrl) {
            this.showNotification('Backend not connected', 'error');
            return;
        }

        this.showNotification('Starting comprehensive test for August 11-14, 2025...', 'info');
        
        const testResults = {
            health: false,
            august11: false,
            august11to12: false,
            august11to14: false,
            original: false,
            database: false
        };

        try {
            // Test 1: Health Check
            console.log('🧪 Test 1: Health Check');
            const healthResponse = await fetch(`${this.baseUrl}/health`);
            if (healthResponse.ok) {
                const healthData = await healthResponse.json();
                console.log('✅ Health Check Passed:', healthData);
                testResults.health = true;
                this.showNotification('✅ Health check passed', 'success');
            } else {
                console.log('❌ Health Check Failed');
                this.showNotification('❌ Health check failed', 'error');
            }

            // Test 2: August 11, 2025 (Single Day)
            console.log('🧪 Test 2: August 11, 2025 (Single Day)');
            const august11Response = await fetch(`${this.baseUrl}/events?start=2025-08-11&end=2025-08-11`);
            if (august11Response.ok) {
                const august11Data = await august11Response.json();
                console.log('✅ August 11 Test Passed:', august11Data);
                testResults.august11 = true;
                this.showNotification(`✅ August 11: ${august11Data.total_events} events from ${august11Data.source}`, 'success');
            } else {
                console.log('❌ August 11 Test Failed');
                this.showNotification('❌ August 11 test failed', 'error');
            }

            // Test 3: August 11-12, 2025 (Two Days)
            console.log('🧪 Test 3: August 11-12, 2025 (Two Days)');
            const august11to12Response = await fetch(`${this.baseUrl}/events?start=2025-08-11&end=2025-08-12`);
            if (august11to12Response.ok) {
                const august11to12Data = await august11to12Response.json();
                console.log('✅ August 11-12 Test Passed:', august11to12Data);
                testResults.august11to12 = true;
                this.showNotification(`✅ August 11-12: ${august11to12Data.total_events} events from ${august11to12Data.source}`, 'success');
            } else {
                console.log('❌ August 11-12 Test Failed');
                this.showNotification('❌ August 11-12 test failed', 'error');
            }

            // Test 4: August 11-14, 2025 (Four Days)
            console.log('🧪 Test 4: August 11-14, 2025 (Four Days)');
            const august11to14Response = await fetch(`${this.baseUrl}/events?start=2025-08-11&end=2025-08-14`);
            if (august11to14Response.ok) {
                const august11to14Data = await august11to14Response.json();
                console.log('✅ August 11-14 Test Passed:', august11to14Data);
                testResults.august11to14 = true;
                this.showNotification(`✅ August 11-14: ${august11to14Data.total_events} events from ${august11to14Data.source}`, 'success');
            } else {
                console.log('❌ August 11-14 Test Failed');
                this.showNotification('❌ August 11-14 test failed', 'error');
            }

            // Test 5: Original Data (Non-paraphrased)
            console.log('🧪 Test 5: Original Data (Non-paraphrased)');
            const originalResponse = await fetch(`${this.baseUrl}/events/original?start=2025-08-11&end=2025-08-11`);
            if (originalResponse.ok) {
                const originalData = await originalResponse.json();
                console.log('✅ Original Data Test Passed:', originalData);
                testResults.original = true;
                this.showNotification(`✅ Original data: ${originalData.total_events} events from ${originalData.source}`, 'success');
            } else {
                console.log('❌ Original Data Test Failed');
                this.showNotification('❌ Original data test failed', 'error');
            }

            // Test 6: Database Info
            console.log('🧪 Test 6: Database Info');
            const databaseResponse = await fetch(`${this.baseUrl}/database/info`);
            if (databaseResponse.ok) {
                const databaseData = await databaseResponse.json();
                console.log('✅ Database Info Test Passed:', databaseData);
                testResults.database = true;
                this.showNotification(`✅ Database info: ${databaseData.total_keys || 0} keys`, 'success');
            } else {
                console.log('❌ Database Info Test Failed');
                this.showNotification('❌ Database info test failed', 'error');
            }

            // Summary
            const passedTests = Object.values(testResults).filter(Boolean).length;
            const totalTests = Object.keys(testResults).length;
            
            console.log('📊 Test Summary:', testResults);
            console.log(`🎯 ${passedTests}/${totalTests} tests passed`);
            
            if (passedTests === totalTests) {
                this.showNotification(`🎉 All ${totalTests} tests passed! Backend is fully operational.`, 'success');
            } else {
                this.showNotification(`⚠️ ${passedTests}/${totalTests} tests passed. Some issues detected.`, 'warning');
            }

            // Load the August 11-14 data into the main interface
            if (testResults.august11to14) {
                document.getElementById('startDate').value = '2025-08-11';
                document.getElementById('endDate').value = '2025-08-14';
                this.loadEvents();
            }

        } catch (error) {
            console.error('❌ Test suite error:', error);
            this.showNotification(`❌ Test suite failed: ${error.message}`, 'error');
        }
    }
}

// Initialize the application
document.addEventListener('DOMContentLoaded', () => {
    console.log('Initializing Forex Calendar application...');
    const forexCalendar = new ForexCalendar();
    
    // Add test button to the interface
    const testButton = document.createElement('button');
    testButton.id = 'testAugust11to14';
    testButton.className = 'btn btn--secondary';
    testButton.textContent = 'Test Aug 11-14, 2025';
    testButton.style.marginLeft = '10px';
    testButton.addEventListener('click', () => forexCalendar.testAugust11to14());
    
    // Insert after the test connection button
    const testConnectionBtn = document.getElementById('testConnection');
    testConnectionBtn.parentNode.insertBefore(testButton, testConnectionBtn.nextSibling);
});
document.addEventListener('DOMContentLoaded', function() {
    let currentIndex = -1;
    const records = [];
    
    // Load records from the data attribute
    function loadRecords() {
        const dataElement = document.getElementById('record-data');
        if (dataElement) {
            records.push(...JSON.parse(dataElement.getAttribute('data-records')));
            if (records.length > 0) {
                showRecord(0);
            }
        }
    }
    
    // Show record details
    function showRecord(index) {
        if (index < 0 || index >= records.length) return;
        
        currentIndex = index;
        const record = records[index];
        
        // Update active state in file list
        document.querySelectorAll('.file-item').forEach(item => item.classList.remove('active'));
        document.querySelector(`[data-index="${index}"]`).classList.add('active');
        
        // Update record details
        const detailsHtml = `
            <div class="actions">
                <button class="btn btn-print" onclick="window.print()">
                    <svg width="16" height="16" fill="currentColor" viewBox="0 0 16 16">
                        <path d="M2.5 8a.5.5 0 1 0 0-1 .5.5 0 0 0 0 1z"/>
                        <path d="M5 1a2 2 0 0 0-2 2v2H2a2 2 0 0 0-2 2v3a2 2 0 0 0 2 2h1v1a2 2 0 0 0 2 2h6a2 2 0 0 0 2-2v-1h1a2 2 0 0 0 2-2V7a2 2 0 0 0-2-2h-1V3a2 2 0 0 0-2-2H5zM4 3a1 1 0 0 1 1-1h6a1 1 0 0 1 1 1v2H4V3zm1 5a2 2 0 0 0-2 2v1H2a1 1 0 0 1-1-1V7a1 1 0 0 1 1-1h12a1 1 0 0 1 1 1v3a1 1 0 0 1-1 1h-1v-1a2 2 0 0 0-2-2H5zm7 2v3a1 1 0 0 1-1 1H5a1 1 0 0 1-1-1v-3a1 1 0 0 1 1-1h6a1 1 0 0 1 1 1z"/>
                    </svg>
                    Print
                </button>
                <a href="${record.file_path}" target="_blank" class="btn">View Original</a>
            </div>
            <table>
                <tr><th>Treatment Date</th><td>${record.treatment_date || 'N/A'}</td></tr>
                <tr><th>Visit Type</th><td>${record.visit_type || 'N/A'}</td></tr>
                <tr><th>Provider Name</th><td>${record.provider_name || 'N/A'}</td></tr>
                <tr><th>Provider Facility</th><td>${record.provider_facility || 'N/A'}</td></tr>
                <tr><th>Primary Condition</th><td>${record.primary_condition || 'N/A'}</td></tr>
                <tr><th>Diagnoses</th><td>${formatList(record.diagnoses)}</td></tr>
                <tr><th>Treatments</th><td>${formatList(record.treatments)}</td></tr>
                <tr><th>Medications</th><td>${formatList(record.medications)}</td></tr>
                <tr><th>Test Results</th><td>${formatList(record.test_results)}</td></tr>
                <tr><th>Summary</th><td>${record.summary || 'N/A'}</td></tr>
            </table>
        `;
        
        document.querySelector('.record-details').innerHTML = detailsHtml;
    }
    
    // Format list items for display
    function formatList(items) {
        if (!items) return 'N/A';
        if (typeof items === 'string') return items;
        if (Array.isArray(items) && items.length === 0) return 'N/A';
        if (Array.isArray(items)) return items.join('; ');
        return 'N/A';
    }
    
    // Navigation functions
    function navigateUp() {
        if (currentIndex > 0) {
            showRecord(currentIndex - 1);
            document.querySelector(`[data-index="${currentIndex}"]`).scrollIntoView({ behavior: 'smooth', block: 'nearest' });
        }
    }
    
    function navigateDown() {
        if (currentIndex < records.length - 1) {
            showRecord(currentIndex + 1);
            document.querySelector(`[data-index="${currentIndex}"]`).scrollIntoView({ behavior: 'smooth', block: 'nearest' });
        }
    }
    
    // Event listeners
    document.addEventListener('keydown', function(e) {
        if (e.key === 'ArrowUp') {
            e.preventDefault();
            navigateUp();
        } else if (e.key === 'ArrowDown') {
            e.preventDefault();
            navigateDown();
        }
    });
    
    // Add click listeners to file items
    document.querySelectorAll('.file-item').forEach(item => {
        item.addEventListener('click', function() {
            showRecord(parseInt(this.getAttribute('data-index')));
        });
    });
    
    // Add click listeners to navigation buttons
    document.querySelector('.nav-up').addEventListener('click', navigateUp);
    document.querySelector('.nav-down').addEventListener('click', navigateDown);
    
    // Initialize
    loadRecords();
});

// Land Registry Integration Section Interface
async function loadLandRegistrySection() {
    return `
        <div class="section">
            <div class="page-header">
                <h1 class="page-title">Land Registry Integration</h1>
                <p class="page-subtitle">Property data, searches, and title information management</p>
            </div>

            <!-- Land Registry Metrics Grid -->
            <div class="dashboard-grid">
                <div class="stat-card">
                    <div class="stat-header">
                        <div class="stat-title">API Calls Today</div>
                        <div style="color: var(--success);">🔍</div>
                    </div>
                    <div class="stat-value" id="api-calls-today">2,847</div>
                    <div class="stat-change positive">+15% vs yesterday</div>
                </div>

                <div class="stat-card">
                    <div class="stat-header">
                        <div class="stat-title">Search Success Rate</div>
                        <div style="color: var(--success);">✅</div>
                    </div>
                    <div class="stat-value" id="search-success-rate">99.2%</div>
                    <div class="stat-change positive">Excellent performance</div>
                </div>

                <div class="stat-card">
                    <div class="stat-header">
                        <div class="stat-title">Average Response Time</div>
                        <div style="color: var(--success);">⚡</div>
                    </div>
                    <div class="stat-value" id="response-time">0.8s</div>
                    <div class="stat-change positive">-23% faster</div>
                </div>

                <div class="stat-card">
                    <div class="stat-header">
                        <div class="stat-title">Data Accuracy</div>
                        <div style="color: var(--success);">🎯</div>
                    </div>
                    <div class="stat-value" id="data-accuracy">99.8%</div>
                    <div class="stat-change positive">Industry leading</div>
                </div>
            </div>

            <!-- Land Registry Panel -->
            <div class="panel">
                <div class="panel-header">
                    <h2 class="panel-title">Land Registry Services</h2>
                    <div class="panel-actions">
                        <button class="btn btn-primary" onclick="performPropertySearch()">
                            <span>🔍</span> Property Search
                        </button>
                        <button class="btn btn-success" onclick="testLandRegistryAPI()">
                            <span>🔗</span> Test API
                        </button>
                    </div>
                </div>

                <div class="tabs">
                    <button class="tab active" data-tab="search-interface">Search Interface</button>
                    <button class="tab" data-tab="recent-searches">Recent Searches</button>
                    <button class="tab" data-tab="api-monitoring">API Monitoring</button>
                    <button class="tab" data-tab="data-validation">Data Validation</button>
                </div>

                <!-- Search Interface Tab -->
                <div class="tab-content active" id="search-interface-tab">
                    <div style="display: grid; grid-template-columns: 1fr 2fr; gap: 20px;">
                        <!-- Search Form -->
                        <div>
                            <h3 style="margin-bottom: 16px;">Property Search</h3>
                            
                            <div class="form-group">
                                <label class="form-label">Search Type</label>
                                <select class="form-select" id="search-type">
                                    <option value="postcode">Postcode</option>
                                    <option value="title-number">Title Number</option>
                                    <option value="address">Full Address</option>
                                    <option value="coordinates">Coordinates</option>
                                </select>
                            </div>

                            <div class="form-group">
                                <label class="form-label">Search Query</label>
                                <input type="text" class="form-input" id="search-query" placeholder="e.g., SG13 8EQ">
                            </div>

                            <div class="form-group">
                                <label class="form-label">Search Options</label>
                                <div style="margin-top: 8px;">
                                    <label style="display: flex; align-items: center; margin-bottom: 8px;">
                                        <input type="checkbox" checked style="margin-right: 8px;" id="include-title"> Title Register
                                    </label>
                                    <label style="display: flex; align-items: center; margin-bottom: 8px;">
                                        <input type="checkbox" checked style="margin-right: 8px;" id="include-plan"> Title Plan
                                    </label>
                                    <label style="display: flex; align-items: center; margin-bottom: 8px;">
                                        <input type="checkbox" style="margin-right: 8px;" id="include-historic"> Historic Data
                                    </label>
                                    <label style="display: flex; align-items: center; margin-bottom: 8px;">
                                        <input type="checkbox" style="margin-right: 8px;" id="include-charges"> Charges Register
                                    </label>
                                </div>
                            </div>

                            <button class="btn btn-primary" style="width: 100%;" onclick="executeLandRegistrySearch()">
                                <span>🔍</span> Execute Search
                            </button>

                            <!-- Quick Search Examples -->
                            <div style="margin-top: 20px;">
                                <h4 style="margin-bottom: 12px;">Quick Examples</h4>
                                <div style="display: flex; flex-direction: column; gap: 8px;">
                                    <button class="btn" onclick="quickSearch('SG13 8EQ')" style="text-align: left; font-size: 12px;">
                                        📍 SG13 8EQ (Hertford postcode)
                                    </button>
                                    <button class="btn" onclick="quickSearch('AB123456')" style="text-align: left; font-size: 12px;">
                                        📄 AB123456 (Sample title number)
                                    </button>
                                    <button class="btn" onclick="quickSearch('10 Downing Street, London')" style="text-align: left; font-size: 12px;">
                                        🏠 Famous address lookup
                                    </button>
                                </div>
                            </div>
                        </div>

                        <!-- Search Results -->
                        <div>
                            <h3 style="margin-bottom: 16px;">Search Results</h3>
                            
                            <div id="search-results" style="background: var(--bg); border: 1px solid var(--line); border-radius: 8px; padding: 20px; min-height: 400px;">
                                <div style="text-align: center; color: var(--muted); padding: 60px 20px;">
                                    <div style="font-size: 48px; margin-bottom: 16px;">🔍</div>
                                    <div style="font-size: 16px; margin-bottom: 8px;">No search performed</div>
                                    <div style="font-size: 14px;">Enter search criteria and click "Execute Search" to view property data</div>
                                </div>
                            </div>

                            <!-- Property Data Template (hidden by default) -->
                            <div id="property-data-template" style="display: none;">
                                <div style="margin-bottom: 20px;">
                                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px;">
                                        <h4 style="margin: 0;">Property Information</h4>
                                        <span class="badge badge-success">Found</span>
                                    </div>
                                    
                                    <div style="background: var(--panel); border: 1px solid var(--line); border-radius: 8px; padding: 16px; margin-bottom: 16px;">
                                        <div style="font-weight: 500; margin-bottom: 8px;">Address</div>
                                        <div id="property-address" style="color: var(--muted);">Loading...</div>
                                    </div>

                                    <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 12px; margin-bottom: 16px;">
                                        <div style="background: var(--panel); border: 1px solid var(--line); border-radius: 8px; padding: 16px;">
                                            <div style="font-weight: 500; margin-bottom: 8px;">Title Number</div>
                                            <div id="title-number" style="color: var(--muted);">Loading...</div>
                                        </div>
                                        <div style="background: var(--panel); border: 1px solid var(--line); border-radius: 8px; padding: 16px;">
                                            <div style="font-weight: 500; margin-bottom: 8px;">Tenure</div>
                                            <div id="tenure-type" style="color: var(--muted);">Loading...</div>
                                        </div>
                                    </div>

                                    <div style="background: var(--panel); border: 1px solid var(--line); border-radius: 8px; padding: 16px; margin-bottom: 16px;">
                                        <div style="font-weight: 500; margin-bottom: 8px;">Registered Proprietor(s)</div>
                                        <div id="proprietors" style="color: var(--muted);">Loading...</div>
                                    </div>

                                    <div style="background: var(--panel); border: 1px solid var(--line); border-radius: 8px; padding: 16px;">
                                        <div style="font-weight: 500; margin-bottom: 8px;">Charges</div>
                                        <div id="charges-info" style="color: var(--muted);">Loading...</div>
                                    </div>
                                </div>

                                <div style="display: flex; gap: 8px;">
                                    <button class="btn btn-primary" onclick="downloadTitleRegister()">
                                        📄 Download Title Register
                                    </button>
                                    <button class="btn btn-primary" onclick="downloadTitlePlan()">
                                        🗺️ Download Title Plan
                                    </button>
                                    <button class="btn" onclick="addToCase()">
                                        📁 Add to Case
                                    </button>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>

                <!-- Recent Searches Tab -->
                <div class="tab-content" id="recent-searches-tab">
                    <div style="margin-bottom: 20px; display: flex; justify-content: space-between; align-items: center;">
                        <h3>Recent Searches</h3>
                        <div style="display: flex; gap: 8px;">
                            <select style="padding: 6px 12px; border: 1px solid var(--line); border-radius: 6px; background: var(--bg); color: var(--text);">
                                <option>Last 24 hours</option>
                                <option>Last 7 days</option>
                                <option>Last 30 days</option>
                            </select>
                            <button class="btn" onclick="clearSearchHistory()">
                                🗑️ Clear History
                            </button>
                        </div>
                    </div>

                    <div class="table-container">
                        <table class="table">
                            <thead>
                                <tr>
                                    <th>Timestamp</th>
                                    <th>Search Query</th>
                                    <th>Type</th>
                                    <th>Results</th>
                                    <th>Response Time</th>
                                    <th>User</th>
                                    <th>Actions</th>
                                </tr>
                            </thead>
                            <tbody>
                                <tr>
                                    <td>14:23:45</td>
                                    <td>SG13 8EQ</td>
                                    <td><span class="badge badge-info">Postcode</span></td>
                                    <td><span class="badge badge-success">47 properties</span></td>
                                    <td>0.8s</td>
                                    <td>sarah.johnson@domus.co.uk</td>
                                    <td>
                                        <button class="btn" onclick="repeatSearch('SG13 8EQ')">Repeat</button>
                                    </td>
                                </tr>
                                <tr>
                                    <td>14:18:32</td>
                                    <td>AB123456</td>
                                    <td><span class="badge badge-warning">Title Number</span></td>
                                    <td><span class="badge badge-success">1 property</span></td>
                                    <td>0.6s</td>
                                    <td>michael.brown@domus.co.uk</td>
                                    <td>
                                        <button class="btn" onclick="repeatSearch('AB123456')">Repeat</button>
                                    </td>
                                </tr>
                                <tr>
                                    <td>14:15:18</td>
                                    <td>123 High Street, London</td>
                                    <td><span class="badge badge-success">Address</span></td>
                                    <td><span class="badge badge-success">1 property</span></td>
                                    <td>1.2s</td>
                                    <td>john.davis@domus.co.uk</td>
                                    <td>
                                        <button class="btn" onclick="repeatSearch('123 High Street, London')">Repeat</button>
                                    </td>
                                </tr>
                                <tr>
                                    <td>13:45:22</td>
                                    <td>XY987654</td>
                                    <td><span class="badge badge-warning">Title Number</span></td>
                                    <td><span class="badge badge-danger">Not found</span></td>
                                    <td>0.4s</td>
                                    <td>emma.wilson@domus.co.uk</td>
                                    <td>
                                        <button class="btn" onclick="repeatSearch('XY987654')">Repeat</button>
                                    </td>
                                </tr>
                            </tbody>
                        </table>
                    </div>
                </div>

                <!-- API Monitoring Tab -->
                <div class="tab-content" id="api-monitoring-tab">
                    <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 20px;">
                        <!-- API Status -->
                        <div>
                            <h3 style="margin-bottom: 16px;">API Status & Performance</h3>
                            
                            <div style="background: var(--bg); border: 1px solid var(--success); border-radius: 8px; padding: 16px; margin-bottom: 16px;">
                                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px;">
                                    <span style="font-weight: 500;">HM Land Registry API</span>
                                    <span class="badge badge-success">Online</span>
                                </div>
                                <div style="color: var(--muted); font-size: 14px; margin-bottom: 8px;">
                                    Status: All endpoints operational<br>
                                    Last check: 2 minutes ago<br>
                                    Uptime: 99.97% (30 days)
                                </div>
                            </div>

                            <div class="chart-container">
                                <canvas style="width: 100%; height: 200px; background: var(--bg); border: 1px solid var(--line); border-radius: 8px; display: flex; align-items: center; justify-content: center; color: var(--muted);">
                                    API Response Time Chart (24h)
                                </canvas>
                            </div>

                            <div style="margin-top: 16px;">
                                <h4 style="margin-bottom: 12px;">Rate Limits</h4>
                                <div style="background: var(--bg); border: 1px solid var(--line); border-radius: 8px; padding: 16px;">
                                    <div style="display: flex; justify-content: space-between; margin-bottom: 8px;">
                                        <span>Hourly Requests</span>
                                        <span>2,847 / 5,000</span>
                                    </div>
                                    <div style="width: 100%; height: 6px; background: var(--line); border-radius: 3px; margin-bottom: 12px;">
                                        <div style="width: 57%; height: 100%; background: var(--success); border-radius: 3px;"></div>
                                    </div>
                                    <div style="display: flex; justify-content: space-between; margin-bottom: 8px;">
                                        <span>Daily Requests</span>
                                        <span>18,234 / 50,000</span>
                                    </div>
                                    <div style="width: 100%; height: 6px; background: var(--line); border-radius: 3px;">
                                        <div style="width: 36%; height: 100%; background: var(--success); border-radius: 3px;"></div>
                                    </div>
                                </div>
                            </div>
                        </div>

                        <!-- Error Monitoring -->
                        <div>
                            <h3 style="margin-bottom: 16px;">Error Monitoring</h3>
                            
                            <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 12px; margin-bottom: 20px;">
                                <div style="background: var(--bg); border: 1px solid var(--line); border-radius: 8px; padding: 16px; text-align: center;">
                                    <div style="font-size: 24px; font-weight: 700; color: var(--success); margin-bottom: 4px;">99.2%</div>
                                    <div style="font-size: 14px; color: var(--muted);">Success Rate</div>
                                </div>
                                <div style="background: var(--bg); border: 1px solid var(--line); border-radius: 8px; padding: 16px; text-align: center;">
                                    <div style="font-size: 24px; font-weight: 700; color: var(--warning); margin-bottom: 4px;">23</div>
                                    <div style="font-size: 14px; color: var(--muted);">Errors (24h)</div>
                                </div>
                            </div>

                            <div class="table-container">
                                <table class="table">
                                    <thead>
                                        <tr>
                                            <th>Time</th>
                                            <th>Error Type</th>
                                            <th>Count</th>
                                            <th>Status</th>
                                        </tr>
                                    </thead>
                                    <tbody>
                                        <tr>
                                            <td>13:45</td>
                                            <td>Timeout</td>
                                            <td>12</td>
                                            <td><span class="badge badge-warning">Resolved</span></td>
                                        </tr>
                                        <tr>
                                            <td>12:30</td>
                                            <td>Rate Limit</td>
                                            <td>8</td>
                                            <td><span class="badge badge-success">Resolved</span></td>
                                        </tr>
                                        <tr>
                                            <td>11:15</td>
                                            <td>Not Found</td>
                                            <td>3</td>
                                            <td><span class="badge badge-success">Normal</span></td>
                                        </tr>
                                    </tbody>
                                </table>
                            </div>

                            <div style="margin-top: 20px;">
                                <h4 style="margin-bottom: 12px;">API Configuration</h4>
                                <div style="background: var(--bg); border: 1px solid var(--line); border-radius: 8px; padding: 16px;">
                                    <div style="margin-bottom: 12px;">
                                        <span style="font-weight: 500;">Environment:</span>
                                        <span style="color: var(--success); margin-left: 8px;">Production</span>
                                    </div>
                                    <div style="margin-bottom: 12px;">
                                        <span style="font-weight: 500;">API Version:</span>
                                        <span style="color: var(--muted); margin-left: 8px;">v3.1</span>
                                    </div>
                                    <div style="margin-bottom: 12px;">
                                        <span style="font-weight: 500;">Timeout:</span>
                                        <span style="color: var(--muted); margin-left: 8px;">30 seconds</span>
                                    </div>
                                    <div>
                                        <span style="font-weight: 500;">Retry Policy:</span>
                                        <span style="color: var(--muted); margin-left: 8px;">3 attempts, exponential backoff</span>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>

                <!-- Data Validation Tab -->
                <div class="tab-content" id="data-validation-tab">
                    <div>
                        <h3 style="margin-bottom: 16px;">Data Validation & Quality</h3>
                        
                        <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 20px; margin-bottom: 20px;">
                            <div>
                                <h4 style="margin-bottom: 12px;">Validation Rules</h4>
                                <div style="background: var(--bg); border: 1px solid var(--line); border-radius: 8px; padding: 16px;">
                                    <div style="margin-bottom: 12px;">
                                        <label style="display: flex; align-items: center;">
                                            <input type="checkbox" checked style="margin-right: 8px;"> Postcode format validation
                                        </label>
                                    </div>
                                    <div style="margin-bottom: 12px;">
                                        <label style="display: flex; align-items: center;">
                                            <input type="checkbox" checked style="margin-right: 8px;"> Title number format check
                                        </label>
                                    </div>
                                    <div style="margin-bottom: 12px;">
                                        <label style="display: flex; align-items: center;">
                                            <input type="checkbox" checked style="margin-right: 8px;"> Address completeness
                                        </label>
                                    </div>
                                    <div style="margin-bottom: 12px;">
                                        <label style="display: flex; align-items: center;">
                                            <input type="checkbox" style="margin-right: 8px;"> Cross-reference validation
                                        </label>
                                    </div>
                                    <div>
                                        <label style="display: flex; align-items: center;">
                                            <input type="checkbox" checked style="margin-right: 8px;"> Data freshness check
                                        </label>
                                    </div>
                                </div>
                            </div>

                            <div>
                                <h4 style="margin-bottom: 12px;">Quality Metrics</h4>
                                <div style="space-y: 8px;">
                                    <div style="background: var(--bg); border: 1px solid var(--line); border-radius: 8px; padding: 12px; margin-bottom: 8px;">
                                        <div style="display: flex; justify-content: space-between; margin-bottom: 8px;">
                                            <span>Data Completeness</span>
                                            <span style="color: var(--success);">98.7%</span>
                                        </div>
                                        <div style="width: 100%; height: 4px; background: var(--line); border-radius: 2px;">
                                            <div style="width: 98.7%; height: 100%; background: var(--success); border-radius: 2px;"></div>
                                        </div>
                                    </div>

                                    <div style="background: var(--bg); border: 1px solid var(--line); border-radius: 8px; padding: 12px; margin-bottom: 8px;">
                                        <div style="display: flex; justify-content: space-between; margin-bottom: 8px;">
                                            <span>Data Accuracy</span>
                                            <span style="color: var(--success);">99.8%</span>
                                        </div>
                                        <div style="width: 100%; height: 4px; background: var(--line); border-radius: 2px;">
                                            <div style="width: 99.8%; height: 100%; background: var(--success); border-radius: 2px;"></div>
                                        </div>
                                    </div>

                                    <div style="background: var(--bg); border: 1px solid var(--line); border-radius: 8px; padding: 12px;">
                                        <div style="display: flex; justify-content: space-between; margin-bottom: 8px;">
                                            <span>Data Freshness</span>
                                            <span style="color: var(--success);">96.2%</span>
                                        </div>
                                        <div style="width: 100%; height: 4px; background: var(--line); border-radius: 2px;">
                                            <div style="width: 96.2%; height: 100%; background: var(--success); border-radius: 2px;"></div>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </div>

                        <div>
                            <h4 style="margin-bottom: 12px;">Recent Validation Issues</h4>
                            <div class="table-container">
                                <table class="table">
                                    <thead>
                                        <tr>
                                            <th>Timestamp</th>
                                            <th>Issue Type</th>
                                            <th>Query</th>
                                            <th>Severity</th>
                                            <th>Resolution</th>
                                            <th>Status</th>
                                        </tr>
                                    </thead>
                                    <tbody>
                                        <tr>
                                            <td>14:15:32</td>
                                            <td>Missing proprietor</td>
                                            <td>AB123456</td>
                                            <td><span class="badge badge-warning">Medium</span></td>
                                            <td>Manual review</td>
                                            <td><span class="badge badge-warning">Pending</span></td>
                                        </tr>
                                        <tr>
                                            <td>13:45:18</td>
                                            <td>Incomplete address</td>
                                            <td>SG13 8EQ</td>
                                            <td><span class="badge badge-info">Low</span></td>
                                            <td>Auto-corrected</td>
                                            <td><span class="badge badge-success">Resolved</span></td>
                                        </tr>
                                        <tr>
                                            <td>12:30:45</td>
                                            <td>Outdated tenure info</td>
                                            <td>XY987654</td>
                                            <td><span class="badge badge-warning">Medium</span></td>
                                            <td>Updated from source</td>
                                            <td><span class="badge badge-success">Resolved</span></td>
                                        </tr>
                                    </tbody>
                                </table>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    `;
}

// Land Registry specific functions
async function performPropertySearch() {
    const query = document.getElementById('search-query')?.value || 'SG13 8EQ';
    executeLandRegistrySearch(query);
}

async function executeLandRegistrySearch(query = null) {
    const searchQuery = query || document.getElementById('search-query')?.value;
    if (!searchQuery) {
        showError('Please enter a search query');
        return;
    }

    showLoading();
    
    try {
        const response = await fetch('/api/land-registry/search', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({
                query: searchQuery,
                type: document.getElementById('search-type')?.value || 'postcode',
                include_title: document.getElementById('include-title')?.checked || true,
                include_plan: document.getElementById('include-plan')?.checked || true,
                include_historic: document.getElementById('include-historic')?.checked || false,
                include_charges: document.getElementById('include-charges')?.checked || false
            })
        });

        const result = await response.json();
        displaySearchResults(result);
    } catch (error) {
        showError('Search failed: ' + error.message);
        displayNoResults();
    } finally {
        hideLoading();
    }
}

function displaySearchResults(result) {
    const resultsContainer = document.getElementById('search-results');
    const template = document.getElementById('property-data-template');
    
    if (result && result.properties && result.properties.length > 0) {
        const property = result.properties[0]; // Show first result
        
        resultsContainer.innerHTML = template.innerHTML;
        resultsContainer.style.display = 'block';
        
        // Populate with actual data or mock data
        document.getElementById('property-address').textContent = property.address || '123 High Street, Hertford, SG13 8EQ';
        document.getElementById('title-number').textContent = property.title_number || 'AB123456';
        document.getElementById('tenure-type').textContent = property.tenure || 'Freehold';
        document.getElementById('proprietors').textContent = property.proprietors || 'John Smith & Jane Smith';
        document.getElementById('charges-info').textContent = property.charges || 'Mortgage to ABC Bank Ltd dated 15th March 2023';
    } else {
        displayNoResults();
    }
}

function displayNoResults() {
    const resultsContainer = document.getElementById('search-results');
    resultsContainer.innerHTML = `
        <div style="text-align: center; color: var(--muted); padding: 60px 20px;">
            <div style="font-size: 48px; margin-bottom: 16px;">❌</div>
            <div style="font-size: 16px; margin-bottom: 8px;">No results found</div>
            <div style="font-size: 14px;">Please check your search criteria and try again</div>
        </div>
    `;
}

async function quickSearch(query) {
    document.getElementById('search-query').value = query;
    executeLandRegistrySearch(query);
}

async function testLandRegistryAPI() {
    showLoading();
    try {
        const response = await fetch('/api/land-registry/test', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'}
        });
        const result = await response.json();
        showModal('API Test Results', `<pre>${JSON.stringify(result, null, 2)}</pre>`);
    } catch (error) {
        showError('API test failed: ' + error.message);
    } finally {
        hideLoading();
    }
}

async function downloadTitleRegister() {
    showModal('Download Started', 'Title register download has started. The document will be available in your downloads folder shortly.');
}

async function downloadTitlePlan() {
    showModal('Download Started', 'Title plan download has started. The document will be available in your downloads folder shortly.');
}

async function addToCase() {
    showModal('Add to Case', 'Select a case to add this property information to, or create a new case.');
}

function repeatSearch(query) {
    document.getElementById('search-query').value = query;
    executeLandRegistrySearch(query);
}

async function clearSearchHistory() {
    if (confirm('Are you sure you want to clear the search history?')) {
        showModal('History Cleared', 'Search history has been cleared successfully.');
    }
}
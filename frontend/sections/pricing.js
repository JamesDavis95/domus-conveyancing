// Dynamic Pricing Engine Section Interface
async function loadPricingEngineSection() {
    return `
        <div class="section">
            <div class="page-header">
                <h1 class="page-title">Dynamic Pricing Engine</h1>
                <p class="page-subtitle">Advanced pricing optimization and revenue management</p>
            </div>

            <!-- Pricing Metrics Grid -->
            <div class="dashboard-grid">
                <div class="stat-card">
                    <div class="stat-header">
                        <div class="stat-title">Revenue Optimization</div>
                        <div style="color: var(--success);">📈</div>
                    </div>
                    <div class="stat-value" id="revenue-optimization">+24%</div>
                    <div class="stat-change positive">vs fixed pricing</div>
                </div>

                <div class="stat-card">
                    <div class="stat-header">
                        <div class="stat-title">Average Case Value</div>
                        <div style="color: var(--success);">💰</div>
                    </div>
                    <div class="stat-value" id="avg-case-value">£2,340</div>
                    <div class="stat-change positive">+18% increase</div>
                </div>

                <div class="stat-card">
                    <div class="stat-header">
                        <div class="stat-title">Pricing Accuracy</div>
                        <div style="color: var(--success);">🎯</div>
                    </div>
                    <div class="stat-value" id="pricing-accuracy">96.7%</div>
                    <div class="stat-change positive">AI-powered</div>
                </div>

                <div class="stat-card">
                    <div class="stat-header">
                        <div class="stat-title">Client Acceptance Rate</div>
                        <div style="color: var(--success);">✅</div>
                    </div>
                    <div class="stat-value" id="acceptance-rate">89.3%</div>
                    <div class="stat-change positive">Optimal pricing</div>
                </div>
            </div>

            <!-- Pricing Management Panel -->
            <div class="panel">
                <div class="panel-header">
                    <h2 class="panel-title">Pricing Management</h2>
                    <div class="panel-actions">
                        <button class="btn btn-primary" onclick="runPricingAnalysis()">
                            <span>🔍</span> Run Analysis
                        </button>
                        <button class="btn btn-success" onclick="optimizePricing()">
                            <span>⚡</span> Optimize Pricing
                        </button>
                    </div>
                </div>

                <div class="tabs">
                    <button class="tab active" data-tab="live-pricing">Live Pricing</button>
                    <button class="tab" data-tab="price-models">Price Models</button>
                    <button class="tab" data-tab="competitor-analysis">Competitor Analysis</button>
                    <button class="tab" data-tab="revenue-forecasting">Revenue Forecasting</button>
                </div>

                <!-- Live Pricing Tab -->
                <div class="tab-content active" id="live-pricing-tab">
                    <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 20px;">
                        <!-- Current Pricing Rules -->
                        <div>
                            <h3 style="margin-bottom: 16px;">Current Pricing Rules</h3>
                            <div class="table-container">
                                <table class="table">
                                    <thead>
                                        <tr>
                                            <th>Service</th>
                                            <th>Base Price</th>
                                            <th>Dynamic Range</th>
                                            <th>Current Multiplier</th>
                                            <th>Status</th>
                                        </tr>
                                    </thead>
                                    <tbody>
                                        <tr>
                                            <td>Standard Conveyancing</td>
                                            <td>£1,200</td>
                                            <td>0.8x - 1.4x</td>
                                            <td><span class="badge badge-success">1.2x</span></td>
                                            <td><span class="badge badge-success">Active</span></td>
                                        </tr>
                                        <tr>
                                            <td>Leasehold Purchase</td>
                                            <td>£1,400</td>
                                            <td>0.9x - 1.3x</td>
                                            <td><span class="badge badge-warning">1.1x</span></td>
                                            <td><span class="badge badge-success">Active</span></td>
                                        </tr>
                                        <tr>
                                            <td>Right to Buy</td>
                                            <td>£900</td>
                                            <td>0.8x - 1.2x</td>
                                            <td><span class="badge badge-info">1.0x</span></td>
                                            <td><span class="badge badge-success">Active</span></td>
                                        </tr>
                                        <tr>
                                            <td>Remortgage</td>
                                            <td>£600</td>
                                            <td>0.7x - 1.3x</td>
                                            <td><span class="badge badge-success">1.3x</span></td>
                                            <td><span class="badge badge-success">Active</span></td>
                                        </tr>
                                    </tbody>
                                </table>
                            </div>
                        </div>

                        <!-- Pricing Factors -->
                        <div>
                            <h3 style="margin-bottom: 16px;">Current Pricing Factors</h3>
                            
                            <div style="background: var(--bg); border: 1px solid var(--line); border-radius: 8px; padding: 16px; margin-bottom: 16px;">
                                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
                                    <span style="font-weight: 500;">Market Demand</span>
                                    <span style="color: var(--success);">High (+15%)</span>
                                </div>
                                <div style="width: 100%; height: 6px; background: var(--line); border-radius: 3px;">
                                    <div style="width: 80%; height: 100%; background: var(--success); border-radius: 3px;"></div>
                                </div>
                            </div>

                            <div style="background: var(--bg); border: 1px solid var(--line); border-radius: 8px; padding: 16px; margin-bottom: 16px;">
                                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
                                    <span style="font-weight: 500;">Capacity Utilization</span>
                                    <span style="color: var(--warning);">Medium (+5%)</span>
                                </div>
                                <div style="width: 100%; height: 6px; background: var(--line); border-radius: 3px;">
                                    <div style="width: 65%; height: 100%; background: var(--warning); border-radius: 3px;"></div>
                                </div>
                            </div>

                            <div style="background: var(--bg); border: 1px solid var(--line); border-radius: 8px; padding: 16px; margin-bottom: 16px;">
                                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
                                    <span style="font-weight: 500;">Complexity Score</span>
                                    <span style="color: var(--info);">Standard (0%)</span>
                                </div>
                                <div style="width: 100%; height: 6px; background: var(--line); border-radius: 3px;">
                                    <div style="width: 50%; height: 100%; background: #60a5fa; border-radius: 3px;"></div>
                                </div>
                            </div>

                            <div style="background: var(--bg); border: 1px solid var(--line); border-radius: 8px; padding: 16px; margin-bottom: 16px;">
                                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
                                    <span style="font-weight: 500;">Client History</span>
                                    <span style="color: var(--success);">Loyal (-10%)</span>
                                </div>
                                <div style="width: 100%; height: 6px; background: var(--line); border-radius: 3px;">
                                    <div style="width: 90%; height: 100%; background: var(--success); border-radius: 3px;"></div>
                                </div>
                            </div>

                            <div style="background: var(--bg); border: 1px solid var(--line); border-radius: 8px; padding: 16px;">
                                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
                                    <span style="font-weight: 500;">Time Sensitivity</span>
                                    <span style="color: var(--danger);">Urgent (+20%)</span>
                                </div>
                                <div style="width: 100%; height: 6px; background: var(--line); border-radius: 3px;">
                                    <div style="width: 85%; height: 100%; background: var(--danger); border-radius: 3px;"></div>
                                </div>
                            </div>
                        </div>
                    </div>

                    <!-- Recent Pricing Decisions -->
                    <div style="margin-top: 30px;">
                        <h3 style="margin-bottom: 16px;">Recent Pricing Decisions</h3>
                        <div class="table-container">
                            <table class="table">
                                <thead>
                                    <tr>
                                        <th>Case Reference</th>
                                        <th>Service Type</th>
                                        <th>Base Price</th>
                                        <th>Final Price</th>
                                        <th>Adjustment Reason</th>
                                        <th>Client Response</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    <tr>
                                        <td>DOM-2025-245</td>
                                        <td>Standard Conveyancing</td>
                                        <td>£1,200</td>
                                        <td>£1,440</td>
                                        <td>High demand +20%</td>
                                        <td><span class="badge badge-success">Accepted</span></td>
                                    </tr>
                                    <tr>
                                        <td>DOM-2025-246</td>
                                        <td>Remortgage</td>
                                        <td>£600</td>
                                        <td>£540</td>
                                        <td>Repeat client -10%</td>
                                        <td><span class="badge badge-success">Accepted</span></td>
                                    </tr>
                                    <tr>
                                        <td>DOM-2025-247</td>
                                        <td>Leasehold Purchase</td>
                                        <td>£1,400</td>
                                        <td>£1,680</td>
                                        <td>Complex case +20%</td>
                                        <td><span class="badge badge-warning">Negotiating</span></td>
                                    </tr>
                                </tbody>
                            </table>
                        </div>
                    </div>
                </div>

                <!-- Price Models Tab -->
                <div class="tab-content" id="price-models-tab">
                    <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 20px;">
                        <div>
                            <h3 style="margin-bottom: 16px;">AI Pricing Models</h3>
                            
                            <div style="background: var(--bg); border: 1px solid var(--success); border-radius: 8px; padding: 16px; margin-bottom: 16px;">
                                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px;">
                                    <h4 style="margin: 0;">Dynamic Market Model</h4>
                                    <span class="badge badge-success">Active</span>
                                </div>
                                <div style="color: var(--muted); font-size: 14px; margin-bottom: 12px;">
                                    Real-time market analysis with demand forecasting
                                </div>
                                <div style="display: flex; gap: 12px;">
                                    <div style="text-align: center;">
                                        <div style="font-size: 18px; font-weight: 600; color: var(--success);">97.2%</div>
                                        <div style="font-size: 12px; color: var(--muted);">Accuracy</div>
                                    </div>
                                    <div style="text-align: center;">
                                        <div style="font-size: 18px; font-weight: 600; color: var(--success);">+28%</div>
                                        <div style="font-size: 12px; color: var(--muted);">Revenue</div>
                                    </div>
                                </div>
                            </div>

                            <div style="background: var(--bg); border: 1px solid var(--line); border-radius: 8px; padding: 16px; margin-bottom: 16px;">
                                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px;">
                                    <h4 style="margin: 0;">Complexity Scoring</h4>
                                    <span class="badge badge-success">Active</span>
                                </div>
                                <div style="color: var(--muted); font-size: 14px; margin-bottom: 12px;">
                                    AI analysis of case complexity and resource requirements
                                </div>
                                <div style="display: flex; gap: 12px;">
                                    <div style="text-align: center;">
                                        <div style="font-size: 18px; font-weight: 600; color: var(--success);">94.8%</div>
                                        <div style="font-size: 12px; color: var(--muted);">Accuracy</div>
                                    </div>
                                    <div style="text-align: center;">
                                        <div style="font-size: 18px; font-weight: 600; color: var(--success);">+15%</div>
                                        <div style="font-size: 12px; color: var(--muted);">Efficiency</div>
                                    </div>
                                </div>
                            </div>

                            <div style="background: var(--bg); border: 1px solid var(--line); border-radius: 8px; padding: 16px;">
                                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px;">
                                    <h4 style="margin: 0;">Client Value Model</h4>
                                    <span class="badge badge-warning">Training</span>
                                </div>
                                <div style="color: var(--muted); font-size: 14px; margin-bottom: 12px;">
                                    Lifetime value prediction and loyalty-based pricing
                                </div>
                                <div style="display: flex; gap: 12px;">
                                    <div style="text-align: center;">
                                        <div style="font-size: 18px; font-weight: 600; color: var(--warning);">89.3%</div>
                                        <div style="font-size: 12px; color: var(--muted);">Accuracy</div>
                                    </div>
                                    <div style="text-align: center;">
                                        <div style="font-size: 18px; font-weight: 600; color: var(--warning);">+8%</div>
                                        <div style="font-size: 12px; color: var(--muted);">Retention</div>
                                    </div>
                                </div>
                            </div>
                        </div>

                        <div>
                            <h3 style="margin-bottom: 16px;">Model Performance</h3>
                            <div class="chart-container">
                                <canvas style="width: 100%; height: 300px; background: var(--bg); border: 1px solid var(--line); border-radius: 8px; display: flex; align-items: center; justify-content: center; color: var(--muted);">
                                    Pricing Model Performance Chart
                                </canvas>
                            </div>

                            <div style="margin-top: 20px;">
                                <h4 style="margin-bottom: 12px;">Training Data</h4>
                                <div class="table-container">
                                    <table class="table">
                                        <thead>
                                            <tr>
                                                <th>Data Source</th>
                                                <th>Records</th>
                                                <th>Last Update</th>
                                                <th>Quality</th>
                                            </tr>
                                        </thead>
                                        <tbody>
                                            <tr>
                                                <td>Historical Cases</td>
                                                <td>12,847</td>
                                                <td>Real-time</td>
                                                <td><span class="badge badge-success">High</span></td>
                                            </tr>
                                            <tr>
                                                <td>Market Data</td>
                                                <td>5,632</td>
                                                <td>Daily</td>
                                                <td><span class="badge badge-success">High</span></td>
                                            </tr>
                                            <tr>
                                                <td>Competitor Prices</td>
                                                <td>2,134</td>
                                                <td>Weekly</td>
                                                <td><span class="badge badge-warning">Medium</span></td>
                                            </tr>
                                            <tr>
                                                <td>Economic Indicators</td>
                                                <td>890</td>
                                                <td>Monthly</td>
                                                <td><span class="badge badge-success">High</span></td>
                                            </tr>
                                        </tbody>
                                    </table>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>

                <!-- Competitor Analysis Tab -->
                <div class="tab-content" id="competitor-analysis-tab">
                    <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 20px;">
                        <div>
                            <h3 style="margin-bottom: 16px;">Competitor Pricing</h3>
                            <div class="table-container">
                                <table class="table">
                                    <thead>
                                        <tr>
                                            <th>Competitor</th>
                                            <th>Standard Conv.</th>
                                            <th>Leasehold</th>
                                            <th>Remortgage</th>
                                            <th>Market Share</th>
                                        </tr>
                                    </thead>
                                    <tbody>
                                        <tr>
                                            <td><strong>Domus (Us)</strong></td>
                                            <td style="color: var(--success);">£1,200-1,680</td>
                                            <td style="color: var(--success);">£1,400-1,820</td>
                                            <td style="color: var(--success);">£600-780</td>
                                            <td><span class="badge badge-success">12.3%</span></td>
                                        </tr>
                                        <tr>
                                            <td>Premier Solicitors</td>
                                            <td>£1,450</td>
                                            <td>£1,650</td>
                                            <td>£750</td>
                                            <td><span class="badge badge-warning">8.7%</span></td>
                                        </tr>
                                        <tr>
                                            <td>QuickMove Legal</td>
                                            <td>£950</td>
                                            <td>£1,200</td>
                                            <td>£450</td>
                                            <td><span class="badge badge-info">15.2%</span></td>
                                        </tr>
                                        <tr>
                                            <td>Elite Conveyancing</td>
                                            <td>£1,800</td>
                                            <td>£2,100</td>
                                            <td>£900</td>
                                            <td><span class="badge badge-warning">6.1%</span></td>
                                        </tr>
                                        <tr>
                                            <td>Digital Property Law</td>
                                            <td>£850</td>
                                            <td>£1,050</td>
                                            <td>£400</td>
                                            <td><span class="badge badge-info">18.9%</span></td>
                                        </tr>
                                    </tbody>
                                </table>
                            </div>
                        </div>

                        <div>
                            <h3 style="margin-bottom: 16px;">Competitive Positioning</h3>
                            <div class="chart-container">
                                <canvas style="width: 100%; height: 300px; background: var(--bg); border: 1px solid var(--line); border-radius: 8px; display: flex; align-items: center; justify-content: center; color: var(--muted);">
                                    Price vs Quality Matrix Chart
                                </canvas>
                            </div>

                            <div style="margin-top: 20px;">
                                <h4 style="margin-bottom: 12px;">Market Intelligence</h4>
                                <div style="background: var(--bg); border: 1px solid var(--line); border-radius: 8px; padding: 16px; margin-bottom: 12px;">
                                    <div style="font-weight: 500; margin-bottom: 8px;">🔍 Key Insights</div>
                                    <ul style="margin: 0; padding-left: 20px; color: var(--muted); font-size: 14px;">
                                        <li>We're positioned in premium market segment</li>
                                        <li>28% higher conversion rate than competitors</li>
                                        <li>AI pricing gives us 15-20% revenue advantage</li>
                                        <li>Client satisfaction 23% above market average</li>
                                    </ul>
                                </div>

                                <div style="background: var(--bg); border: 1px solid var(--line); border-radius: 8px; padding: 16px;">
                                    <div style="font-weight: 500; margin-bottom: 8px;">📈 Recommendations</div>
                                    <ul style="margin: 0; padding-left: 20px; color: var(--muted); font-size: 14px;">
                                        <li>Maintain premium positioning with value justification</li>
                                        <li>Target 15-18% market share by Q4 2025</li>
                                        <li>Focus on service differentiation over price competition</li>
                                        <li>Expand into underserved market segments</li>
                                    </ul>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>

                <!-- Revenue Forecasting Tab -->
                <div class="tab-content" id="revenue-forecasting-tab">
                    <div style="display: grid; grid-template-columns: 2fr 1fr; gap: 20px;">
                        <div>
                            <h3 style="margin-bottom: 16px;">Revenue Forecasting</h3>
                            <div class="chart-container" style="height: 400px;">
                                <canvas style="width: 100%; height: 100%; background: var(--bg); border: 1px solid var(--line); border-radius: 8px; display: flex; align-items: center; justify-content: center; color: var(--muted);">
                                    Revenue Forecast Chart - 12 Month Projection
                                </canvas>
                            </div>

                            <div style="margin-top: 20px;">
                                <h4 style="margin-bottom: 12px;">Scenario Analysis</h4>
                                <div style="display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 12px;">
                                    <div style="background: var(--bg); border: 1px solid var(--success); border-radius: 8px; padding: 16px; text-align: center;">
                                        <div style="font-weight: 600; color: var(--success); margin-bottom: 8px;">Optimistic</div>
                                        <div style="font-size: 24px; font-weight: 700; margin-bottom: 4px;">£2.1M</div>
                                        <div style="font-size: 12px; color: var(--muted);">+35% growth</div>
                                    </div>
                                    <div style="background: var(--bg); border: 1px solid var(--warning); border-radius: 8px; padding: 16px; text-align: center;">
                                        <div style="font-weight: 600; color: var(--warning); margin-bottom: 8px;">Realistic</div>
                                        <div style="font-size: 24px; font-weight: 700; margin-bottom: 4px;">£1.8M</div>
                                        <div style="font-size: 12px; color: var(--muted);">+24% growth</div>
                                    </div>
                                    <div style="background: var(--bg); border: 1px solid var(--danger); border-radius: 8px; padding: 16px; text-align: center;">
                                        <div style="font-weight: 600; color: var(--danger); margin-bottom: 8px;">Conservative</div>
                                        <div style="font-size: 24px; font-weight: 700; margin-bottom: 4px;">£1.5M</div>
                                        <div style="font-size: 12px; color: var(--muted);">+15% growth</div>
                                    </div>
                                </div>
                            </div>
                        </div>

                        <div>
                            <h3 style="margin-bottom: 16px;">Key Drivers</h3>
                            
                            <div style="background: var(--bg); border: 1px solid var(--line); border-radius: 8px; padding: 16px; margin-bottom: 16px;">
                                <div style="font-weight: 500; margin-bottom: 12px;">Market Growth</div>
                                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
                                    <span style="font-size: 14px;">Property Market</span>
                                    <span style="color: var(--success);">+12%</span>
                                </div>
                                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
                                    <span style="font-size: 14px;">Remortgage Boom</span>
                                    <span style="color: var(--success);">+28%</span>
                                </div>
                                <div style="display: flex; justify-content: space-between; align-items: center;">
                                    <span style="font-size: 14px;">First-Time Buyers</span>
                                    <span style="color: var(--warning);">+8%</span>
                                </div>
                            </div>

                            <div style="background: var(--bg); border: 1px solid var(--line); border-radius: 8px; padding: 16px; margin-bottom: 16px;">
                                <div style="font-weight: 500; margin-bottom: 12px;">Operational Factors</div>
                                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
                                    <span style="font-size: 14px;">AI Efficiency</span>
                                    <span style="color: var(--success);">+22%</span>
                                </div>
                                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
                                    <span style="font-size: 14px;">Team Expansion</span>
                                    <span style="color: var(--success);">+15%</span>
                                </div>
                                <div style="display: flex; justify-content: space-between; align-items: center;">
                                    <span style="font-size: 14px;">Process Automation</span>
                                    <span style="color: var(--success);">+18%</span>
                                </div>
                            </div>

                            <div style="background: var(--bg); border: 1px solid var(--line); border-radius: 8px; padding: 16px;">
                                <div style="font-weight: 500; margin-bottom: 12px;">Risk Factors</div>
                                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
                                    <span style="font-size: 14px;">Economic Uncertainty</span>
                                    <span style="color: var(--danger);">-8%</span>
                                </div>
                                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
                                    <span style="font-size: 14px;">Competition</span>
                                    <span style="color: var(--warning);">-5%</span>
                                </div>
                                <div style="display: flex; justify-content: space-between; align-items: center;">
                                    <span style="font-size: 14px;">Regulatory Changes</span>
                                    <span style="color: var(--warning);">-3%</span>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    `;
}

// Pricing specific functions
async function optimizePricing() {
    showLoading();
    try {
        const response = await fetch('/api/pricing/optimize', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'}
        });
        const result = await response.json();
        showModal('Pricing Optimization Complete', 
            `<div style="color: var(--success); margin-bottom: 16px;">✅ Pricing optimization completed successfully!</div>
             <div style="margin-bottom: 12px;"><strong>Revenue Impact:</strong> +${result.revenue_impact || '12.3%'}</div>
             <div style="margin-bottom: 12px;"><strong>Cases Affected:</strong> ${result.cases_affected || '23'}</div>
             <div style="margin-bottom: 12px;"><strong>Average Price Change:</strong> +${result.avg_change || '8.5%'}</div>
             <div style="margin-top: 16px;">Updated pricing rules are now active across all service types.</div>`
        );
    } catch (error) {
        showError('Pricing optimization failed: ' + error.message);
    } finally {
        hideLoading();
    }
}
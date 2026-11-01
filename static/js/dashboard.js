// CyberShield AI - Dashboard JavaScript
// Enterprise SOC Dashboard with Animations

(function() {
    'use strict';

    // State
    const state = {
        activeSection: 'dashboard',
        activeModel: 'job',
        isAnalyzing: false
    };

    // Initialize
    document.addEventListener('DOMContentLoaded', function() {
        initNavigation();
        initParticles();
        initDashboard();
        initAnalyzer();
        initTopBarControls();
        animateMetrics();
    });

    // ============================================
    // NAVIGATION
    // ============================================
    function initNavigation() {
        const navItems = document.querySelectorAll('.nav-item');
        const sections = document.querySelectorAll('.content-section');

        navItems.forEach(item => {
            item.addEventListener('click', (e) => {
                e.preventDefault();
                const sectionId = item.dataset.section;
                
                // Update nav
                navItems.forEach(nav => nav.classList.remove('active'));
                item.classList.add('active');
                
                // Update sections
                sections.forEach(section => section.classList.remove('active'));
                document.getElementById(`section-${sectionId}`).classList.add('active');
                
                state.activeSection = sectionId;
            });

        });

        document.querySelectorAll('.jump-to-section').forEach(button => {
            button.addEventListener('click', () => {
                const target = document.querySelector(`.nav-item[data-section="${button.dataset.target}"]`);
                if (target) target.click();
            });
        });
    }

    function initTopBarControls() {
        const settingsBtn = document.getElementById('settingsBtn');
        const popover = document.getElementById('settingsPopover');
        const closeSettings = document.getElementById('closeSettingsBtn');
        const themeToggle = document.getElementById('themeToggle');
        const notificationsBtn = document.getElementById('notificationsBtn');
        const search = document.getElementById('globalSearch');
        const savedTheme = localStorage.getItem('cybershield-theme') || 'dark';

        document.documentElement.dataset.theme = savedTheme;
        if (themeToggle) themeToggle.checked = savedTheme === 'light';
        if (settingsBtn && popover) settingsBtn.addEventListener('click', () => {
            popover.hidden = !popover.hidden;
        });
        if (closeSettings && popover) closeSettings.addEventListener('click', () => {
            popover.hidden = true;
        });
        if (themeToggle) themeToggle.addEventListener('change', () => {
            const theme = themeToggle.checked ? 'light' : 'dark';
            document.documentElement.dataset.theme = theme;
            localStorage.setItem('cybershield-theme', theme);
        });
        if (notificationsBtn) notificationsBtn.addEventListener('click', () => {
            const activity = document.querySelector('.nav-item[data-section="activity"]');
            const filter = document.getElementById('activityFilter');
            if (filter) filter.value = 'threat';
            if (activity) activity.click();
            const badge = document.getElementById('notifBadge');
            if (badge) badge.style.display = 'none';
        });
        if (search) search.addEventListener('keydown', event => {
            if (event.key !== 'Enter') return;
            const value = search.value.trim().toLowerCase();
            const activity = document.querySelector('.nav-item[data-section="activity"]');
            if (!value) {
                if (activity) activity.click();
                return;
            }
            if (activity) activity.click();
            setTimeout(() => filterActivityRows(value), 0);
        });
    }

    function filterActivityRows(query) {
        document.querySelectorAll('#activityTimeline .timeline-item').forEach(item => {
            item.hidden = !item.textContent.toLowerCase().includes(query);
        });
        const status = document.getElementById('activityStatus');
        if (status) {
            const count = [...document.querySelectorAll('#activityTimeline .timeline-item:not([hidden])')].length;
            status.textContent = `${count} matching event${count === 1 ? '' : 's'}`;
        }
    }

    // ============================================
    // PARTICLES BACKGROUND
    // ============================================
    function initParticles() {
        const canvas = document.getElementById('particles');
        if (!canvas) return;
        
        const ctx = canvas.getContext('2d');
        canvas.width = window.innerWidth;
        canvas.height = window.innerHeight;

        const particles = [];
        const particleCount = 50;

        class Particle {
            constructor() {
                this.reset();
            }

            reset() {
                this.x = Math.random() * canvas.width;
                this.y = Math.random() * canvas.height;
                this.vx = (Math.random() - 0.5) * 0.5;
                this.vy = (Math.random() - 0.5) * 0.5;
                this.size = Math.random() * 2;
            }

            update() {
                this.x += this.vx;
                this.y += this.vy;

                if (this.x < 0 || this.x > canvas.width) this.vx *= -1;
                if (this.y < 0 || this.y > canvas.height) this.vy *= -1;
            }

            draw() {
                ctx.fillStyle = 'rgba(0, 229, 255, 0.5)';
                ctx.beginPath();
                ctx.arc(this.x, this.y, this.size, 0, Math.PI * 2);
                ctx.fill();
            }
        }

        for (let i = 0; i < particleCount; i++) {
            particles.push(new Particle());
        }

        function animate() {
            ctx.clearRect(0, 0, canvas.width, canvas.height);
            
            particles.forEach(particle => {
                particle.update();
                particle.draw();
            });

            // Draw connections
            particles.forEach((p1, i) => {
                particles.slice(i + 1).forEach(p2 => {
                    const dx = p1.x - p2.x;
                    const dy = p1.y - p2.y;
                    const distance = Math.sqrt(dx * dx + dy * dy);

                    if (distance < 150) {
                        ctx.strokeStyle = `rgba(0, 229, 255, ${0.15 * (1 - distance / 150)})`;
                        ctx.lineWidth = 1;
                        ctx.beginPath();
                        ctx.moveTo(p1.x, p1.y);
                        ctx.lineTo(p2.x, p2.y);
                        ctx.stroke();
                    }
                });
            });

            requestAnimationFrame(animate);
        }

        animate();

        window.addEventListener('resize', () => {
            canvas.width = window.innerWidth;
            canvas.height = window.innerHeight;
        });
    }

    // ============================================
    // LIVE DATA LAYER
    // ============================================
    const charts = {};
    const esc = (t) => String(t == null ? '' : t).replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
    const getJSON = (u) => fetch(u).then(r => { if (!r.ok) throw new Error(u + ' ' + r.status); return r.json(); });

    function initDashboard() {
        refreshAll();
        setInterval(refreshStats, 15000);
        const f = document.getElementById('activityFilter');
        if (f) f.addEventListener('change', loadActivityTimeline);
        const refreshActivity = document.getElementById('refreshActivityBtn');
        if (refreshActivity) refreshActivity.addEventListener('click', loadActivityTimeline);
        document.querySelectorAll('.nav-item').forEach(n => n.addEventListener('click', () => {
            if (n.dataset.section === 'activity') loadActivityTimeline();
            if (n.dataset.section === 'threats') loadThreats();
            if (n.dataset.section === 'scanner') loadRecentUrls();
        }));
    }

    function refreshAll() {
        refreshStats(); loadActivityFeed(); loadModels(); loadThreats(); loadActivityTimeline(); loadRecentUrls();
    }

    function countTo(el, target) {
        if (!el) return;
        const from = parseInt((el.textContent || '0').replace(/,/g, '')) || 0;
        const t0 = performance.now();
        (function step(t) {
            const p = Math.min((t - t0) / 700, 1);
            el.textContent = Math.round(from + (target - from) * (1 - Math.pow(1 - p, 3))).toLocaleString();
            if (p < 1) requestAnimationFrame(step);
        })(t0);
    }

    function animateMetrics() {}

    async function refreshStats() {
        try {
            const d = await getJSON('/api/stats');
            countTo(document.getElementById('mTotal'), d.total);
            countTo(document.getElementById('mThreats'), d.threats);
            countTo(document.getElementById('mSafe'), d.safe);
            document.getElementById('mThreatsSub').textContent = d.threat_rate + '% threat rate';
            document.getElementById('mSafeSub').textContent = (d.total ? (100 - d.threat_rate).toFixed(1) : '0') + '% verification rate';
            document.getElementById('mRisk').textContent = d.risk_score.toFixed(1);
            document.getElementById('sideRisk').textContent = d.risk_score.toFixed(1);
            document.getElementById('mRiskSub').textContent = d.risk_label + ' threat level';
            const uc = document.getElementById('urlScanCount'); if (uc) uc.textContent = (d.by_module.url || 0);
            const nb = document.getElementById('notifBadge');
            if (nb) { nb.textContent = d.threats; nb.style.display = d.threats ? '' : 'none'; }
            renderThreatChart(d); renderTimelineChart(d);
        } catch (e) { console.error(e); }
    }

    const chartText = '#94A3B8';
    function renderThreatChart(d) {
        const canvas = document.getElementById('threatChart'); if (!canvas) return;
        const tm = d.threat_by_module || {};
        const data = [tm.phishing || 0, tm.job_scam || 0, tm.url || 0, d.safe];
        if (charts.threat) { charts.threat.data.datasets[0].data = data; charts.threat.update(); return; }
        charts.threat = new Chart(canvas.getContext('2d'), {
            type: 'doughnut',
            data: { labels: ['Phishing', 'Job Scams', 'Malicious URLs', 'Safe Content'],
                datasets: [{ data, borderWidth: 2,
                    backgroundColor: ['rgba(239,68,68,.8)', 'rgba(250,204,21,.8)', 'rgba(168,85,247,.8)', 'rgba(34,197,94,.8)'],
                    borderColor: ['#EF4444', '#FACC15', '#A855F7', '#22C55E'] }] },
            options: { responsive: true, plugins: { legend: { position: 'bottom', labels: { color: chartText, font: { family: 'Rajdhani', size: 12 }, padding: 15 } } } }
        });
    }
    function renderTimelineChart(d) {
        const canvas = document.getElementById('timelineChart'); if (!canvas) return;
        const t = d.timeline;
        if (charts.timeline) {
            charts.timeline.data.labels = t.labels; charts.timeline.data.datasets[0].data = t.threats;
            charts.timeline.data.datasets[1].data = t.safe; charts.timeline.update(); return;
        }
        const ds = (label, data, c) => ({ label, data, borderColor: c, backgroundColor: c.replace('1)', '0.1)'), tension: .4, fill: true });
        charts.timeline = new Chart(canvas.getContext('2d'), {
            type: 'line',
            data: { labels: t.labels, datasets: [ds('Threats Detected', t.threats, 'rgba(239,68,68,1)'), ds('Safe Content', t.safe, 'rgba(34,197,94,1)')] },
            options: { responsive: true, scales: {
                y: { beginAtZero: true, ticks: { color: '#64748B', precision: 0 }, grid: { color: 'rgba(148,163,184,.1)' } },
                x: { ticks: { color: '#64748B', maxTicksLimit: 8 }, grid: { color: 'rgba(148,163,184,.1)' } } },
                plugins: { legend: { labels: { color: chartText, font: { family: 'Rajdhani', size: 12 } } } } }
        });
    }

    async function loadActivityFeed() {
        const feed = document.getElementById('activityFeed'); if (!feed) return;
        try {
            const rows = await getJSON('/api/activity?limit=8');
            feed.innerHTML = rows.length ? rows.map(a =>
                `<div class="activity-item"><div>${a.is_threat ? '⚠️' : '✅'} ${esc(a.module)}: ${esc(a.prediction)}${a.is_threat ? '' : ''}</div><div class="activity-time">${esc(a.ago)}</div></div>`
            ).join('') : '<div class="activity-item"><div>No activity yet — run a scan in AI Testing or URL Scan.</div></div>';
            const intel = document.getElementById('dashThreatList');
            if (intel) {
                const th = rows.filter(r => r.is_threat).slice(0, 3);
                intel.innerHTML = th.length ? th.map(a => `<div class="threat-item"><div class="threat-info"><div class="threat-title">${esc(a.prediction).toUpperCase()}</div><div class="threat-desc">${esc(a.excerpt)}</div><div class="threat-meta"><span class="${a.level === 'critical' ? 'badge-red' : 'badge-orange'}">${a.level.toUpperCase()}</span><span class="threat-time">${esc(a.ago)}</span></div></div></div>`).join('')
                    : '<div class="threat-desc" style="padding:12px">No threats detected yet.</div>';
            }
        } catch (e) { console.error(e); }
    }

    async function loadActivityTimeline() {
        const box = document.getElementById('activityTimeline'); if (!box) return;
        const f = (document.getElementById('activityFilter') || {}).value || 'all';
        const status = document.getElementById('activityStatus');
        const refresh = document.getElementById('refreshActivityBtn');
        if (status) status.textContent = 'Loading events...';
        if (refresh) refresh.disabled = true;
        box.innerHTML = '<div class="activity-empty"><strong>Loading activity...</strong><span>Fetching the latest scan results.</span></div>';
        try {
            const rows = await getJSON('/api/activity?limit=50&type=' + f);
            const threats = rows.filter(a => a.is_threat).length;
            const safe = rows.length - threats;
            const visible = document.getElementById('activityVisibleCount');
            const threatCount = document.getElementById('activityThreatCount');
            const safeCount = document.getElementById('activitySafeCount');
            if (visible) visible.textContent = rows.length;
            if (threatCount) threatCount.textContent = threats;
            if (safeCount) safeCount.textContent = safe;
            box.innerHTML = rows.length ? rows.map(a => `
                <div class="timeline-item ${a.level}"><span class="badge ${a.level}">${a.level === 'safe' ? 'SAFE' : a.level.toUpperCase()}</span>
                <div class="timeline-content"><h4>${esc(a.prediction)}</h4>
                <p>${esc(a.module)} | ${a.module.includes('URL') ? 'Risk score' : 'Confidence'}: ${a.confidence}${a.module.includes('URL') ? '/100' : '%'}</p>
                <p style="opacity:.6;font-size:12px">${esc(a.excerpt)}</p>
                <span class="time">${esc(a.ago)}</span></div></div>`).join('')
                : '<div class="activity-empty"><strong>No matching events</strong><span>Try another filter or run a scan to create the first activity record.</span><button class="btn-secondary jump-to-section" data-target="analyzer" type="button">Analyze text</button></div>';
            if (!rows.length) {
                const emptyButton = box.querySelector('.jump-to-section');
                if (emptyButton) emptyButton.addEventListener('click', () => {
                    const target = document.querySelector(`.nav-item[data-section="${emptyButton.dataset.target}"]`);
                    if (target) target.click();
                });
            }
            if (status) status.textContent = `${rows.length} event${rows.length === 1 ? '' : 's'} loaded`;
        } catch (e) {
            console.error(e);
            box.innerHTML = '<div class="activity-empty error"><strong>Could not load activity</strong><span>Refresh the page or try again.</span></div>';
            if (status) status.textContent = 'Activity unavailable';
        } finally {
            if (refresh) refresh.disabled = false;
        }
    }

    async function loadModels() {
        const grid = document.getElementById('modelGrid'); if (!grid) return;
        try {
            const models = await getJSON('/api/models');
            const icons = { job_scam: '💼', phishing: '📧', url: '🔗' };
            grid.innerHTML = models.map(m => {
                const x = m.metrics;
                const stats = x ? `<div><strong>${(x.accuracy * 100).toFixed(1)}%</strong> Accuracy</div><div><strong>${(x.f1_score * 100).toFixed(1)}%</strong> F1</div>
                    <div><strong>${x.dataset_size || (x.train_size + x.test_size)}</strong> Samples</div>` : '<div><strong>Rule-based</strong></div><div><strong>10+</strong> Signals</div>';
                return `<div class="model-card active"><div class="model-icon">${icons[m.key]}</div><h3>${esc(m.name)}</h3><p>${esc(m.algo)}</p><div class="model-stats">${stats}</div><span class="model-status active">ACTIVE</span></div>`;
            }).join('');
            const c = document.getElementById('metricsChart');
            if (c && !charts.metrics) {
                const ms = models.filter(m => m.metrics);
                charts.metrics = new Chart(c.getContext('2d'), {
                    type: 'bar',
                    data: { labels: ['Accuracy', 'Precision', 'Recall', 'F1'],
                        datasets: ms.map((m, i) => ({ label: m.name, backgroundColor: i ? 'rgba(168,85,247,.7)' : 'rgba(0,229,255,.7)',
                            data: [m.metrics.accuracy, m.metrics.precision, m.metrics.recall, m.metrics.f1_score].map(v => +(v * 100).toFixed(1)) })) },
                    options: { scales: { y: { min: 0, max: 100, ticks: { color: '#64748B' }, grid: { color: 'rgba(148,163,184,.1)' } }, x: { ticks: { color: '#64748B' } } },
                        plugins: { legend: { labels: { color: chartText } } } }
                });
            }
        } catch (e) { console.error(e); }
    }

    async function loadThreats() {
        const grid = document.getElementById('threatsGrid'); if (!grid) return;
        try {
            const d = await getJSON('/api/threats');
            const sc = d.severity_counts || {};
            document.getElementById('threatStats').innerHTML = [['critical', 'Critical'], ['high', 'High'], ['medium', 'Medium']]
                .map(([k, l]) => `<div class="threat-stat"><span class="stat-number ${k}">${sc[k] || 0}</span><span class="stat-label">${l} Categories</span></div>`).join('')
                + `<div class="threat-stat"><span class="stat-number blocked">${d.total_detections}</span><span class="stat-label">Detections</span></div>`;
            grid.innerHTML = d.items.map(t => `<div class="threat-item ${t.severity}"><h4>${esc(t.name)}</h4><p>${esc(t.desc)}</p>
                <div class="threat-tags"><span class="tag">MITRE: ${esc(t.mitre)}</span><span class="tag">${esc(t.tactic)}</span><span class="tag">${t.detections} detected</span></div></div>`).join('');
        } catch (e) { console.error(e); }
    }

    async function loadRecentUrls() {
        const body = document.getElementById('recentUrlBody'); if (!body) return;
        try {
            const rows = (await getJSON('/api/activity?limit=100&type=url')).slice(0, 8);
            if (!rows.length) return;
            body.innerHTML = rows.map(r => {
                const cls = r.level === 'critical' ? 'high' : r.level === 'warning' ? 'medium' : 'safe';
                const st = r.level === 'critical' ? ['blocked', 'BLOCKED'] : r.level === 'warning' ? ['warning', 'FLAGGED'] : ['safe', 'VERIFIED'];
                return `<tr><td class="url-cell">${esc(r.excerpt)}</td><td><span class="risk-badge ${cls}">${esc(r.prediction)}</span></td>
                    <td><span class="status-badge ${st[0]}">${st[1]}</span></td><td class="time-cell">${esc(r.ago)}</td>
                    <td><button class="btn-table-action" data-url="${esc(r.excerpt)}">Rescan</button></td></tr>`;
            }).join('');
            body.querySelectorAll('[data-url]').forEach(b => b.addEventListener('click', () => {
                document.getElementById('urlInput').value = b.dataset.url; runUrlScan();
            }));
        } catch (e) { console.error(e); }
    }

    // ============================================
    // URL SCANNER
    // ============================================
    async function runUrlScan() {
        const input = document.getElementById('urlInput'), btn = document.getElementById('scanUrlBtn');
        const feedback = document.getElementById('urlFeedback');
        const url = input.value.trim();
        if (!url) {
            feedback.textContent = 'Paste a URL first, then choose DEEP SCAN.';
            feedback.className = 'input-feedback error';
            input.focus();
            return;
        }
        feedback.textContent = '';
        feedback.className = 'input-feedback';
        btn.disabled = true; btn.querySelector('span').textContent = 'SCANNING...';
        try {
            const r = await fetch('/api/scan-url', { method: 'POST', headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ url, check_ssl: !!(document.getElementById('optSsl') || {}).checked }) });
            const d = await r.json();
            if (!r.ok) { alert(d.error || 'Scan failed'); return; }
            document.getElementById('urlEmptyState').style.display = 'none';
            document.getElementById('urlScanResult').style.display = 'block';
            document.getElementById('riskScore').textContent = d.risk_score;
            const colors = { safe: '#22C55E', warning: '#FACC15', critical: '#EF4444' };
            document.getElementById('riskScoreCircle').style.borderColor = colors[d.level];
            document.getElementById('riskScore').style.color = colors[d.level];
            document.getElementById('urlVerdict').textContent = d.verdict;
            document.getElementById('urlVerdictDesc').textContent = d.level === 'safe' ? 'No significant risk signals found.' : `${d.indicators.length} risk signal(s) found on ${d.host}`;
            document.getElementById('domainEntropy').textContent = d.domain_entropy;
            document.getElementById('pathLength').textContent = d.path_length;
            document.getElementById('sslStatus').textContent = d.ssl_status;
            document.getElementById('specialChars').textContent = d.special_chars;
            const sev = { high: '#EF4444', medium: '#FACC15', low: '#00E5FF', info: '#22C55E' };
            document.getElementById('threatIndicators').innerHTML = d.indicators.map(i =>
                `<div class="indicator-item" style="border-left:3px solid ${sev[i.severity]};padding:8px 12px;margin:6px 0;background:rgba(255,255,255,.03)"><strong style="color:${sev[i.severity]}">${i.severity.toUpperCase()}</strong> &nbsp;${esc(i.text)}</div>`).join('');
            loadRecentUrls(); refreshStats(); loadActivityFeed();
        } catch (e) { alert('Scan failed. Please try again.'); }
        finally { btn.disabled = false; btn.querySelector('span').textContent = 'DEEP SCAN'; }
    }

    // ============================================
    // ANALYZER
    // ============================================
    function initAnalyzer() {
        const modelBtns = document.querySelectorAll('.model-btn');
        const analyzeBtn = document.getElementById('analyzeBtn');
        const input = document.getElementById('analyzerInput');
        const feedback = document.getElementById('analyzerFeedback');

        document.querySelectorAll('.example-btn').forEach(button => {
            button.addEventListener('click', () => {
                const examples = {
                    job: 'Congratulations! You have been selected for a work-from-home job. Pay a registration fee to confirm your position.',
                    phishing: 'Your account will be suspended today. Verify your password immediately by clicking the secure link below.'
                };
                const model = button.dataset.example;
                input.value = examples[model];
                modelBtns.forEach(b => b.classList.toggle('active', b.dataset.model === model));
                state.activeModel = model;
                feedback.textContent = 'Example loaded. Review it, then select ANALYZE.';
                feedback.className = 'input-feedback';
                input.focus();
            });
        });

        // Model selection
        modelBtns.forEach(btn => {
            btn.addEventListener('click', () => {
                modelBtns.forEach(b => b.classList.remove('active'));
                btn.classList.add('active');
                state.activeModel = btn.dataset.model;
            });
        });

        const sb = document.getElementById('scanUrlBtn');
        if (sb) sb.addEventListener('click', runUrlScan);
        const ui = document.getElementById('urlInput');
        if (ui) ui.addEventListener('keydown', e => { if (e.key === 'Enter') runUrlScan(); });
        const cb = document.getElementById('clearBtn');
        if (cb) cb.addEventListener('click', () => {
            input.value = '';
            document.getElementById('resultDisplay').style.display = 'none';
            const ss = document.getElementById('scanningState');
            ss.style.display = ''; ss.querySelector('.scan-text').textContent = 'AWAITING INPUT';
        });
        // Analyze button
        if (analyzeBtn) {
            analyzeBtn.addEventListener('click', () => {
                const text = input.value.trim();
                if (text && !state.isAnalyzing) {
                    runAnalysis(text);
                } else if (!text) {
                    feedback.textContent = 'Paste an email, message, or job offer first.';
                    feedback.className = 'input-feedback error';
                    input.focus();
                }
            });
        }
    }

    async function runAnalysis(text) {
        state.isAnalyzing = true;
        
        const scanningState = document.getElementById('scanningState');
        const resultDisplay = document.getElementById('resultDisplay');
        const analyzeBtn = document.getElementById('analyzeBtn');
        
        // Show scanning animation
        scanningState.querySelector('.scan-text').textContent = 'ANALYZING...';
        resultDisplay.style.display = 'none';
        
        analyzeBtn.disabled = true;
        analyzeBtn.innerHTML = '<span>ANALYZING...</span>';
        
        try {
            const endpoint = state.activeModel === 'job' ? '/predict/job' : '/predict/phishing';
            const response = await fetch(endpoint, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ text })
            });
            
            const data = await response.json();
            
            // Wait a bit for effect
            await new Promise(resolve => setTimeout(resolve, 1000));
            
            // Show results
            if (data.error) { alert(data.error); document.getElementById('scanningState').querySelector('.scan-text').textContent = 'AWAITING INPUT'; return; }
            displayResults(data);
            refreshStats(); loadActivityFeed();
            
        } catch (error) {
            console.error('Analysis error:', error);
            alert('Analysis failed. Please try again.');
        } finally {
            state.isAnalyzing = false;
            analyzeBtn.disabled = false;
            analyzeBtn.innerHTML = '<span>ANALYZE</span><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="9 18 15 12 9 6"/></svg>';
        }
    }

    function displayResults(data) {
        const scanningState = document.getElementById('scanningState');
        const resultDisplay = document.getElementById('resultDisplay');
        const verdictBadge = document.getElementById('verdictBadge');
        const gaugeValue = document.getElementById('gaugeValue');
        const threatLevel = document.getElementById('threatLevel');
        const legitLevel = document.getElementById('legitLevel');
        const threatValue = document.getElementById('threatValue');
        const legitValue = document.getElementById('legitValue');
        const termCloud = document.getElementById('termCloud');
        const explanationText = document.getElementById('explanationText');
        
        // Hide scanning, show results
        scanningState.style.display = 'none';
        resultDisplay.style.display = 'flex';

        // Update verdict
        if (data.is_threat) {
            verdictBadge.textContent = 'THREAT DETECTED';
            verdictBadge.classList.add('threat');
        } else {
            verdictBadge.textContent = 'SAFE';
            verdictBadge.classList.remove('threat');
        }
        if (data.top_terms && data.top_terms.length) { /* terms rendered below */ }
        
        // Update confidence gauge
        gaugeValue.textContent = data.confidence + '%';
        drawConfidenceGauge(data.confidence, data.is_threat);
        
        // Update risk bars
        const probs = data.probabilities || {};
        const isJob = state.activeModel === 'job';
        const threatPercent = probs[isJob ? 'Fraudulent Job Offer' : 'Phishing Email'] || 0;
        const legitPercent = probs[isJob ? 'Genuine Job Offer' : 'Legitimate Email'] || 0;

        setTimeout(() => {
            threatLevel.style.width = threatPercent + '%';
            legitLevel.style.width = legitPercent + '%';
            threatValue.textContent = Math.round(threatPercent) + '%';
            legitValue.textContent = Math.round(legitPercent) + '%';
        }, 100);
        
        // Update term cloud
        termCloud.innerHTML = '';
        if (data.top_terms && data.top_terms.length) {
            data.top_terms.forEach(term => {
                const tag = document.createElement('span');
                tag.className = 'term-tag';
                tag.textContent = term;
                termCloud.appendChild(tag);
            });
        }
        
        // Update explanation
        let explanation = `The AI model analyzed the content and detected `;
        if (data.is_threat) {
            explanation += `malicious patterns with ${data.confidence}% confidence. `;
            explanation += `Top contributing terms: ${(data.top_terms||[]).join(', ') || 'n/a'}. These are commonly associated with ${state.activeModel === 'job' ? 'fraudulent job offers' : 'phishing attacks'}.`;
        } else {
            explanation += `legitimate content with ${data.confidence}% confidence. `;
            explanation += `The language patterns and structure align with genuine ${state.activeModel === 'job' ? 'job postings' : 'email communications'}.`;
        }
        explanationText.textContent = explanation;
    }

    function drawConfidenceGauge(confidence, isThreat) {
        const canvas = document.getElementById('confidenceGauge');
        if (!canvas) return;
        
        const ctx = canvas.getContext('2d');
        const centerX = canvas.width / 2;
        const centerY = canvas.height / 2;
        const radius = 80;
        const lineWidth = 12;
        
        // Clear canvas
        ctx.clearRect(0, 0, canvas.width, canvas.height);
        
        // Background circle
        ctx.beginPath();
        ctx.arc(centerX, centerY, radius, 0, 2 * Math.PI);
        ctx.strokeStyle = 'rgba(0, 0, 0, 0.3)';
        ctx.lineWidth = lineWidth;
        ctx.stroke();
        
        // Progress arc
        const startAngle = -Math.PI / 2;
        const endAngle = startAngle + (confidence / 100) * 2 * Math.PI;
        
        const gradient = ctx.createLinearGradient(0, 0, canvas.width, 0);
        if (isThreat) {
            gradient.addColorStop(0, '#EF4444');
            gradient.addColorStop(1, '#FACC15');
        } else {
            gradient.addColorStop(0, '#22C55E');
            gradient.addColorStop(1, '#00E5FF');
        }
        
        ctx.beginPath();
        ctx.arc(centerX, centerY, radius, startAngle, endAngle);
        ctx.strokeStyle = gradient;
        ctx.lineWidth = lineWidth;
        ctx.lineCap = 'round';
        ctx.stroke();
        
        // Glow effect
        ctx.shadowBlur = 20;
        ctx.shadowColor = isThreat ? '#EF4444' : '#00E5FF';
        ctx.stroke();
    }

})();

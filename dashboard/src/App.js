import React, { useState, useEffect, useRef, useCallback } from 'react';
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, LineChart, Line, CartesianGrid } from 'recharts';

const API_BASE = process.env.REACT_APP_API_URL || '';
const WS_URL = process.env.REACT_APP_WS_URL || `ws://${window.location.host}/ws`;

const css = `
  :root {
    --bg: #050a0f;
    --surface: #0d1821;
    --surface2: #142232;
    --border: #1e3a52;
    --accent: #00d4ff;
    --accent2: #ff3366;
    --accent3: #00ff88;
    --text: #e0f0ff;
    --muted: #4a7a9b;
    --font-mono: 'JetBrains Mono', monospace;
    --font-display: 'Syne', sans-serif;
  }

  * { box-sizing: border-box; margin: 0; padding: 0; }

  body {
    background: var(--bg);
    color: var(--text);
    font-family: var(--font-mono);
    min-height: 100vh;
    overflow-x: hidden;
  }

  .app { max-width: 1400px; margin: 0 auto; padding: 24px; }

  .header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-bottom: 32px;
    padding-bottom: 20px;
    border-bottom: 1px solid var(--border);
  }

  .logo { display: flex; align-items: center; gap: 14px; }

  .logo-icon {
    width: 44px; height: 44px;
    background: linear-gradient(135deg, var(--accent2), #ff6b35);
    border-radius: 10px;
    display: flex; align-items: center; justify-content: center;
    font-size: 22px;
  }

  .logo-text h1 {
    font-family: var(--font-display);
    font-size: 20px;
    font-weight: 800;
    letter-spacing: -0.5px;
    color: var(--text);
  }

  .logo-text p { font-size: 11px; color: var(--muted); margin-top: 2px; }

  .status-badge {
    display: flex; align-items: center; gap: 8px;
    padding: 8px 16px;
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 20px;
    font-size: 12px;
  }

  .pulse {
    width: 8px; height: 8px;
    border-radius: 50%;
    background: var(--accent3);
    animation: pulse 2s infinite;
  }

  .pulse.offline { background: var(--accent2); animation: none; }

  @keyframes pulse {
    0%, 100% { opacity: 1; transform: scale(1); }
    50% { opacity: 0.4; transform: scale(0.8); }
  }

  .stats-grid {
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 16px;
    margin-bottom: 24px;
  }

  .stat-card {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 12px;
    padding: 20px;
    position: relative;
    overflow: hidden;
    transition: border-color 0.2s;
  }

  .stat-card:hover { border-color: var(--accent); }

  .stat-card::before {
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0;
    height: 2px;
  }

  .stat-card.blue::before { background: var(--accent); }
  .stat-card.red::before { background: var(--accent2); }
  .stat-card.green::before { background: var(--accent3); }
  .stat-card.orange::before { background: #ff8c00; }

  .stat-label {
    font-size: 10px;
    color: var(--muted);
    text-transform: uppercase;
    letter-spacing: 1.5px;
    margin-bottom: 10px;
  }

  .stat-value {
    font-family: var(--font-display);
    font-size: 32px;
    font-weight: 800;
    line-height: 1;
  }

  .stat-value.blue { color: var(--accent); }
  .stat-value.red { color: var(--accent2); }
  .stat-value.green { color: var(--accent3); }
  .stat-value.orange { color: #ff8c00; }

  .stat-sub { font-size: 11px; color: var(--muted); margin-top: 6px; }

  .main-grid {
    display: grid;
    grid-template-columns: 1fr 420px;
    gap: 16px;
    margin-bottom: 16px;
  }

  .card {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 12px;
    padding: 20px;
  }

  .card-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-bottom: 16px;
  }

  .card-title {
    font-family: var(--font-display);
    font-size: 14px;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 1px;
  }

  .count-badge {
    padding: 3px 10px;
    background: var(--surface2);
    border: 1px solid var(--border);
    border-radius: 10px;
    font-size: 11px;
    color: var(--muted);
  }

  .alert-feed { max-height: 480px; overflow-y: auto; }
  .alert-feed::-webkit-scrollbar { width: 4px; }
  .alert-feed::-webkit-scrollbar-track { background: var(--surface); }
  .alert-feed::-webkit-scrollbar-thumb { background: var(--border); border-radius: 2px; }

  .alert-item {
    padding: 14px;
    margin-bottom: 8px;
    background: var(--surface2);
    border: 1px solid var(--border);
    border-left: 3px solid var(--accent2);
    border-radius: 8px;
    animation: slideIn 0.3s ease;
    transition: border-color 0.2s;
  }

  .alert-item:hover { border-color: var(--accent2); }

  @keyframes slideIn {
    from { opacity: 0; transform: translateX(-10px); }
    to   { opacity: 1; transform: translateX(0); }
  }

  .alert-top {
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-bottom: 8px;
  }

  .alert-user { font-size: 13px; font-weight: 600; color: var(--text); }
  .alert-amount { font-size: 16px; font-weight: 700; color: var(--accent2); }

  .alert-mid {
    display: flex;
    gap: 8px;
    flex-wrap: wrap;
    margin-bottom: 8px;
  }

  .tag {
    padding: 2px 8px;
    border-radius: 4px;
    font-size: 10px;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.5px;
  }

  .tag.category { background: rgba(0,212,255,0.1); color: var(--accent); border: 1px solid rgba(0,212,255,0.2); }
  .tag.country  { background: rgba(255,140,0,0.1); color: #ff8c00; border: 1px solid rgba(255,140,0,0.2); }
  .tag.risk     { background: rgba(255,51,102,0.15); color: var(--accent2); border: 1px solid rgba(255,51,102,0.3); }

  .alert-reasons { font-size: 10px; color: var(--muted); }

  .risk-bar {
    height: 4px;
    background: var(--surface);
    border-radius: 2px;
    margin-top: 10px;
    overflow: hidden;
  }

  .risk-fill {
    height: 100%;
    border-radius: 2px;
    background: linear-gradient(90deg, #ff8c00, var(--accent2));
    transition: width 0.5s ease;
  }

  .empty-state {
    text-align: center;
    padding: 60px 20px;
    color: var(--muted);
  }

  .empty-state .icon { font-size: 40px; margin-bottom: 12px; }
  .empty-state p { font-size: 13px; }

  .recharts-cartesian-grid-horizontal line,
  .recharts-cartesian-grid-vertical line { stroke: var(--border); }

  @media (max-width: 1100px) {
    .stats-grid { grid-template-columns: repeat(2, 1fr); }
    .main-grid { grid-template-columns: 1fr; }
  }
`;

const CustomTooltip = ({ active, payload, label }) => {
  if (!active || !payload?.length) return null;
  return (
    <div style={{background:'#0d1821',border:'1px solid #1e3a52',borderRadius:8,padding:'10px 14px'}}>
      <p style={{color:'#4a7a9b',fontSize:10,marginBottom:4}}>{label}</p>
      <p style={{color:'#00d4ff',fontWeight:700}}>{payload[0]?.value?.toLocaleString()}</p>
    </div>
  );
};

function AlertCard({ alert }) {
  const riskPct = Math.round(alert.risk_score * 100);
  return (
    <div className="alert-item">
      <div className="alert-top">
        <span className="alert-user">👤 {alert.user_id}</span>
        <span className="alert-amount">${alert.amount?.toFixed(2)}</span>
      </div>
      <div className="alert-mid">
        <span className="tag category">{alert.merchant_category}</span>
        <span className="tag country">📍 {alert.country}</span>
        <span className="tag risk">⚠️ {riskPct}% risk</span>
      </div>
      <div className="alert-reasons">{(alert.reasons || []).join(' · ')}</div>
      <div className="risk-bar">
        <div className="risk-fill" style={{width: `${riskPct}%`}} />
      </div>
    </div>
  );
}

export default function App() {
  const [connected, setConnected] = useState(false);
  const [stats, setStats] = useState({ total_transactions: 0, fraud_detected: 0, fraud_rate: 0, total_volume_usd: 0 });
  const [alerts, setAlerts] = useState([]);
  const [categoryData, setCategoryData] = useState([]);
  const [trendData, setTrendData] = useState([]);
  const wsRef = useRef(null);
  const trendRef = useRef([]);

  const fetchFullStats = useCallback(async () => {
    try {
      const [statsRes, alertsRes] = await Promise.all([
        fetch(`${API_BASE}/api/stats`),
        fetch(`${API_BASE}/api/alerts?limit=30`),
      ]);
      const statsData = await statsRes.json();
      const alertsData = await alertsRes.json();

      setStats(statsData);
      setAlerts(alertsData.alerts || []);

      if (statsData.category_breakdown) {
        const cats = Object.entries(statsData.category_breakdown)
          .map(([name, count]) => ({ name: name.replace('_', ' '), count }))
          .sort((a, b) => b.count - a.count)
          .slice(0, 8);
        setCategoryData(cats);
      }
    } catch (err) {
      console.log('Fetch error:', err.message);
    }
  }, []);

  useEffect(() => {
    let reconnectTimer;

    function connect() {
      const ws = new WebSocket(WS_URL);
      wsRef.current = ws;

      ws.onopen = () => {
        setConnected(true);
        const pingInterval = setInterval(() => {
          if (ws.readyState === WebSocket.OPEN) ws.send('ping');
        }, 25000);
        ws._pingInterval = pingInterval;
      };

      ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          if (data.type === 'update') {
            setStats(data.stats);
            trendRef.current = [
              ...trendRef.current.slice(-59),
              {
                t: new Date().toLocaleTimeString('en', {hour12:false,hour:'2-digit',minute:'2-digit',second:'2-digit'}),
                tx: data.stats.total_transactions,
                fraud: data.stats.fraud_detected,
              }
            ];
            setTrendData([...trendRef.current]);

            if (data.latest_alerts?.length) {
              setAlerts(prev => {
                const ids = new Set(prev.map(a => a.transaction_id));
                const newOnes = data.latest_alerts.filter(a => !ids.has(a.transaction_id));
                return [...newOnes, ...prev].slice(0, 50);
              });
            }
          }
        } catch (e) {}
      };

      ws.onclose = () => {
        setConnected(false);
        clearInterval(ws._pingInterval);
        reconnectTimer = setTimeout(connect, 3000);
      };

      ws.onerror = () => ws.close();
    }

    fetchFullStats();
    connect();
    const restInterval = setInterval(fetchFullStats, 10000);

    return () => {
      clearTimeout(reconnectTimer);
      clearInterval(restInterval);
      wsRef.current?.close();
    };
  }, [fetchFullStats]);

  const formatVolume = (v) => {
    if (v >= 1_000_000) return `$${(v/1_000_000).toFixed(2)}M`;
    if (v >= 1_000) return `$${(v/1_000).toFixed(1)}K`;
    return `$${v.toFixed(0)}`;
  };

  return (
    <>
      <style>{css}</style>
      <div className="app">
        <div className="header">
          <div className="logo">
            <div className="logo-icon">🛡️</div>
            <div className="logo-text">
              <h1>FraudShield</h1>
              <p>Kafka · Spark · Real-time Detection</p>
            </div>
          </div>
          <div className="status-badge">
            <div className={`pulse ${connected ? '' : 'offline'}`} />
            <span style={{color: connected ? '#00ff88' : '#ff3366', fontSize: 12}}>
              {connected ? 'LIVE' : 'RECONNECTING'}
            </span>
          </div>
        </div>

        <div className="stats-grid">
          <div className="stat-card blue">
            <div className="stat-label">Total Transactions</div>
            <div className="stat-value blue">{stats.total_transactions?.toLocaleString()}</div>
            <div className="stat-sub">processed by Spark</div>
          </div>
          <div className="stat-card red">
            <div className="stat-label">Fraud Detected</div>
            <div className="stat-value red">{stats.fraud_detected?.toLocaleString()}</div>
            <div className="stat-sub">flagged alerts</div>
          </div>
          <div className="stat-card orange">
            <div className="stat-label">Fraud Rate</div>
            <div className="stat-value orange">{stats.fraud_rate?.toFixed(2)}%</div>
            <div className="stat-sub">of all transactions</div>
          </div>
          <div className="stat-card green">
            <div className="stat-label">Total Volume</div>
            <div className="stat-value green">{formatVolume(stats.total_volume_usd || 0)}</div>
            <div className="stat-sub">processed USD</div>
          </div>
        </div>

        <div className="main-grid">
          <div className="card">
            <div className="card-header">
              <span className="card-title">Transaction Trend</span>
              <span className="count-badge">Last 60s</span>
            </div>
            {trendData.length > 1 ? (
              <ResponsiveContainer width="100%" height={200}>
                <LineChart data={trendData}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="t" tick={{fontSize:9,fill:'#4a7a9b'}} interval="preserveStartEnd" />
                  <YAxis tick={{fontSize:9,fill:'#4a7a9b'}} />
                  <Tooltip content={<CustomTooltip />} />
                  <Line type="monotone" dataKey="tx" stroke="#00d4ff" dot={false} strokeWidth={2} />
                  <Line type="monotone" dataKey="fraud" stroke="#ff3366" dot={false} strokeWidth={2} />
                </LineChart>
              </ResponsiveContainer>
            ) : (
              <div className="empty-state" style={{padding:'40px 0'}}>
                <div className="icon">📡</div>
                <p>Waiting for data stream...</p>
              </div>
            )}

            <div className="card-header" style={{marginTop:20}}>
              <span className="card-title">By Category</span>
            </div>
            {categoryData.length > 0 ? (
              <ResponsiveContainer width="100%" height={180}>
                <BarChart data={categoryData} layout="vertical" margin={{left:20}}>
                  <XAxis type="number" tick={{fontSize:9,fill:'#4a7a9b'}} />
                  <YAxis type="category" dataKey="name" tick={{fontSize:9,fill:'#4a7a9b'}} width={90} />
                  <Tooltip content={<CustomTooltip />} />
                  <Bar dataKey="count" fill="#00d4ff" fillOpacity={0.7} radius={[0,4,4,0]} />
                </BarChart>
              </ResponsiveContainer>
            ) : (
              <div style={{height:180,display:'flex',alignItems:'center',justifyContent:'center',color:'#4a7a9b',fontSize:12}}>
                Loading categories...
              </div>
            )}
          </div>

          <div className="card">
            <div className="card-header">
              <span className="card-title">🚨 Fraud Alerts</span>
              <span className="count-badge">{alerts.length} alerts</span>
            </div>
            <div className="alert-feed">
              {alerts.length === 0 ? (
                <div className="empty-state">
                  <div className="icon">✅</div>
                  <p>No alerts yet. Stream starting...</p>
                </div>
              ) : (
                alerts.map((alert, i) => (
                  <AlertCard key={alert.transaction_id || i} alert={alert} />
                ))
              )}
            </div>
          </div>
        </div>
      </div>
    </>
  );
}

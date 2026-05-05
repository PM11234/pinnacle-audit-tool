const { useState, useEffect } = React;

const API_BASE = "http://localhost:8000/api";

function ConnectAccounts({ onComplete }) {
  const [connectingMeta, setConnectingMeta] = useState(false);
  const [connectingGoogle, setConnectingGoogle] = useState(false);
  const [metaConnected, setMetaConnected] = useState(false);
  const [googleConnected, setGoogleConnected] = useState(false);

  const handleConnect = async (platform) => {
    if (platform === 'meta') setConnectingMeta(true);
    if (platform === 'google') setConnectingGoogle(true);

    try {
      const res = await fetch(`${API_BASE}/connect/${platform}`, { method: 'POST' });
      if (res.ok) {
        if (platform === 'meta') setMetaConnected(true);
        if (platform === 'google') setGoogleConnected(true);
      }
    } catch (error) {
      console.error("Connection failed", error);
    } finally {
      if (platform === 'meta') setConnectingMeta(false);
      if (platform === 'google') setConnectingGoogle(false);
    }
  };

  // Auto-proceed when both connected
  useEffect(() => {
    if (metaConnected && googleConnected) {
      setTimeout(onComplete, 1000);
    }
  }, [metaConnected, googleConnected, onComplete]);

  return (
    <div className="connect-container">
      <h2>Connect Your Ad Accounts</h2>
      <p className="subtitle">Securely connect your platforms to generate your One-Click Audit.</p>
      
      <button 
        className="btn btn-meta" 
        onClick={() => handleConnect('meta')}
        disabled={connectingMeta || metaConnected}
      >
        {connectingMeta ? <span className="loader"></span> : metaConnected ? '✓ Meta Connected' : 'Connect Meta Ads'}
      </button>

      <button 
        className="btn btn-google" 
        onClick={() => handleConnect('google')}
        disabled={connectingGoogle || googleConnected}
      >
        {connectingGoogle ? <span className="loader"></span> : googleConnected ? '✓ Google Connected' : 'Connect Google Ads'}
      </button>

      {(metaConnected && googleConnected) && (
        <p style={{ color: 'var(--green-color)', marginTop: '1rem' }}>All accounts connected! Generating audit...</p>
      )}
    </div>
  );
}

function Dashboard() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch(`${API_BASE}/audit`)
      .then(res => res.json())
      .then(result => {
        setData(result.data);
        setLoading(false);
      })
      .catch(err => {
        console.error("Failed to fetch audit data", err);
        setLoading(false);
      });
  }, []);

  if (loading) {
    return (
      <div className="connect-container">
        <span className="loader" style={{ width: '40px', height: '40px', borderWidth: '4px' }}></span>
        <p>Analyzing cross-channel performance...</p>
      </div>
    );
  }

  if (!data) return <div>Failed to load data. Is the backend running?</div>;

  return (
    <div className="dashboard">
      {/* RED - STOP LEAKAGE */}
      <div className="card red">
        <div className="card-header">
          <div className="icon-wrapper">!</div>
          <div>
            <h2>Stop Leakage</h2>
            <p className="subtitle" style={{ fontSize: '0.85rem' }}>Urgent money-wasting issues</p>
          </div>
        </div>
        {data.red.map((item, idx) => (
          <div key={idx} className="insight-item">
            <h3>{item.title}</h3>
            <p>{item.description}</p>
            {item.tip && <p style={{marginTop: '0.5rem', color: 'var(--red-color)', fontSize: '0.9rem'}}><strong>Senior Buyer's Tip:</strong> {item.tip}</p>}
          </div>
        ))}
      </div>

      {/* YELLOW - OPTIMIZE */}
      <div className="card yellow">
        <div className="card-header">
          <div className="icon-wrapper">⚠</div>
          <div>
            <h2>Optimize</h2>
            <p className="subtitle" style={{ fontSize: '0.85rem' }}>Opportunities to improve</p>
          </div>
        </div>
        {data.yellow.map((item, idx) => (
          <div key={idx} className="insight-item">
            <h3>{item.title}</h3>
            <p>{item.description}</p>
            {item.tip && <p style={{marginTop: '0.5rem', color: 'var(--yellow-color)', fontSize: '0.9rem'}}><strong>Senior Buyer's Tip:</strong> {item.tip}</p>}
          </div>
        ))}
      </div>

      {/* GREEN - SCALE */}
      <div className="card green">
        <div className="card-header">
          <div className="icon-wrapper">↑</div>
          <div>
            <h2>Scale</h2>
            <p className="subtitle" style={{ fontSize: '0.85rem' }}>What's working best</p>
          </div>
        </div>
        {data.green.map((item, idx) => (
          <div key={idx} className="insight-item">
            <h3>{item.title}</h3>
            <p>{item.description}</p>
            {item.tip && <p style={{marginTop: '0.5rem', color: 'var(--green-color)', fontSize: '0.9rem'}}><strong>Senior Buyer's Tip:</strong> {item.tip}</p>}
          </div>
        ))}
      </div>
    </div>
  );
}

function App() {
  const [step, setStep] = useState('connect'); // 'connect' or 'dashboard'

  return (
    <div className="container">
      <header>
        <h1>AdAudit SaaS</h1>
        <p className="subtitle">One-Click AI Audit for Modern Agencies</p>
      </header>

      {step === 'connect' && (
        <ConnectAccounts onComplete={() => setStep('dashboard')} />
      )}
      
      {step === 'dashboard' && (
        <Dashboard />
      )}
    </div>
  );
}

const root = ReactDOM.createRoot(document.getElementById('root'));
root.render(<App />);

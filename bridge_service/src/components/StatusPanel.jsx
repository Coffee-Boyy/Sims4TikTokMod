import React, { useState, useEffect, useCallback } from 'react';

const StatusPanel = ({ isConnected, currentConfig }) => {
  const [clientCount, setClientCount] = useState(0);
  const [currentUser, setCurrentUser] = useState(null);

  const updateStatus = useCallback(async () => {
    try {
      const status = await window.electronAPI.getBridgeStatus();
      setClientCount(status.clientCount);
    } catch (error) {
      console.error('Failed to update status:', error);
    }
  }, []);

  useEffect(() => {
    updateStatus();
    const statusInterval = setInterval(updateStatus, 2000);
    return () => clearInterval(statusInterval);
  }, [updateStatus]);

  useEffect(() => {
    if (currentConfig && currentConfig.username) {
      setCurrentUser(currentConfig.username);
    } else {
      setCurrentUser(null);
    }
  }, [currentConfig]);

  const handleCurrentUserClick = (e) => {
    if (!currentUser) {
      e.preventDefault();
      return;
    }
    e.preventDefault();
    const clean = currentUser.replace(/^@/, '');
    const url = `https://www.tiktok.com/@${encodeURIComponent(clean)}/live`;
    if (window.electronAPI && window.electronAPI.openExternal) {
      window.electronAPI.openExternal(url);
    } else {
      window.open(url, '_blank');
    }
  };

  const getStatusDisplay = () => {
    if (isConnected) {
      return { text: 'Running', className: 'status-value status-running' };
    } else {
      return { text: 'Stopped', className: 'status-value status-stopped' };
    }
  };

  const { text: statusText, className: statusClassName } = getStatusDisplay();

  return (
    <section className="panel">
      <div className="panel-header-standard">
        <h2 className="panel-title">Status</h2>
      </div>
      <div className="status-grid">
        <div className="status-item">
          <span className="status-label">Status:</span>
          <span className={statusClassName}>{statusText}</span>
        </div>
        <div className="status-item">
          <span className="status-label">Sims 4 Clients:</span>
          <span className="status-value">{clientCount}</span>
        </div>
        <div className="status-item">
          <span className="status-label">Current User:</span>
          {currentUser ? (
            <a 
              className="status-value" 
              href="#" 
              target="_blank" 
              rel="noopener"
              onClick={handleCurrentUserClick}
              title={`Open @${currentUser.replace(/^@/, '')}'s TikTok LIVE`}
            >
              {currentUser.replace(/^@/, '')}
            </a>
          ) : (
            <span className="status-value">None</span>
          )}
        </div>
      </div>
    </section>
  );
};

export default StatusPanel;

import React, { useState, useEffect, useCallback } from 'react';
import Header from './components/Header';
import ConnectionPanel from './components/ConnectionPanel';
import StatusPanel from './components/StatusPanel';
import GiftConfigPanel from './components/GiftConfigPanel';
import LogPanel from './components/LogPanel';
import Footer from './components/Footer';
import './App.css';

function App() {
  const [isConnected, setIsConnected] = useState(false);
  const [currentConfig, setCurrentConfig] = useState(null);
  const [simsInteractions, setSimsInteractions] = useState(null);
  const [tiktokGifts, setTiktokGifts] = useState(null);
  const [logEntries, setLogEntries] = useState([
    {
      type: 'info',
      message: 'Welcome to Sims 4 TikTok Bridge! Configure your settings above and click "Start Bridge".',
      timestamp: new Date().toISOString()
    }
  ]);
  const [autoScroll, setAutoScroll] = useState(true);

  // Initialize app
  useEffect(() => {
    // Check if electronAPI is available
    if (!window.electronAPI) {
      console.error('Electron API not available - preload script failed to load');
      addLogEntry({
        type: 'error',
        message: 'Electron API not available - application may not function properly',
        timestamp: new Date().toISOString(),
        stack: 'Preload script (preload.js) failed to load or contextBridge.exposeInMainWorld failed'
      });
      return;
    }
    
    console.log('Electron API loaded successfully');

    // Load interactions and gifts
    window.electronAPI.getInteractions().then(interactions => {
      setSimsInteractions(interactions);
    });
    window.electronAPI.getGifts().then(gifts => {
      setTiktokGifts(gifts);
    });
    
    // Load saved username
    loadSavedUsername();
    
    // Start status polling
    const statusInterval = setInterval(updateStatus, 2000);
    
    // Listen for log messages from main process
    window.electronAPI.onLogMessage((logMessage) => {
      addLogEntry(logMessage);
    });

    return () => {
      clearInterval(statusInterval);
      window.electronAPI.removeAllListeners('log-message');
    };
  }, []);

  const addLogEntry = useCallback((logMessage) => {
    setLogEntries(prev => {
      const newEntries = [...prev, logMessage];
      // Limit log entries to prevent memory issues
      const maxEntries = 1000;
      return newEntries.length > maxEntries ? newEntries.slice(-maxEntries) : newEntries;
    });
  }, []);

  const updateStatus = useCallback(async () => {
    try {
      const status = await window.electronAPI.getBridgeStatus();
      setIsConnected(status.connected);
    } catch (error) {
      console.error('Failed to update status:', error);
    }
  }, []);

  const loadSavedUsername = useCallback(async () => {
    try {
      const result = await window.electronAPI.getLastTikTokUsername();
      if (result.success && result.username) {
        addLogEntry({
          type: 'info',
          message: `Loaded saved username: ${result.username}`,
          timestamp: new Date().toISOString()
        });
      }
    } catch (error) {
      console.error('Failed to load saved username:', error);
      addLogEntry({
        type: 'warning',
        message: 'Could not load saved username from previous session',
        timestamp: new Date().toISOString()
      });
    }
  }, [addLogEntry]);

  const clearLog = useCallback(() => {
    setLogEntries([
      {
        type: 'info',
        message: 'Log cleared',
        timestamp: new Date().toISOString()
      }
    ]);
  }, []);

  return (
    <div className="container">
      <Header />
      <main className="main-content">
        <ConnectionPanel 
          isConnected={isConnected}
          onConnectionChange={setIsConnected}
          onConfigChange={setCurrentConfig}
          addLogEntry={addLogEntry}
        />
        <StatusPanel 
          isConnected={isConnected}
          currentConfig={currentConfig}
        />
        <GiftConfigPanel 
          simsInteractions={simsInteractions}
          tiktokGifts={tiktokGifts}
          addLogEntry={addLogEntry}
        />
        <LogPanel 
          logEntries={logEntries}
          autoScroll={autoScroll}
          onAutoScrollChange={setAutoScroll}
          onClearLog={clearLog}
        />
      </main>
      <Footer />
    </div>
  );
}

export default App;

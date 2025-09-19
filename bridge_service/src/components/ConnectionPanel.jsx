import React, { useState, useCallback } from 'react';

const ConnectionPanel = ({ isConnected, onConnectionChange, onConfigChange, addLogEntry }) => {
  const [username, setUsername] = useState('');
  const [isStarting, setIsStarting] = useState(false);
  const [isStopping, setIsStopping] = useState(false);

  const loadSavedUsername = useCallback(async () => {
    try {
      const result = await window.electronAPI.getLastTikTokUsername();
      if (result.success && result.username) {
        setUsername(result.username);
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

  React.useEffect(() => {
    loadSavedUsername();
  }, [loadSavedUsername]);

  const startBridge = async () => {
    const usernameValue = username.trim();
    const port = 8765; // Default port, configurable via config.json
    const manualMode = false;
    
    if (!usernameValue && !manualMode) {
      showError('TikTok username is required unless using manual mode');
      return;
    }
    
    setIsStarting(true);
    
    try {
      const config = { username: usernameValue, port, manualMode };
      const result = await window.electronAPI.startBridge(config);
      
      if (result.success) {
        onConnectionChange(true);
        onConfigChange(config);
        
        addLogEntry({
          type: 'success',
          message: result.message,
          timestamp: new Date().toISOString()
        });
        
        showSuccess(result.message);
      } else {
        throw new Error(result.message || 'Failed to start bridge');
      }
    } catch (error) {
      addLogEntry({
        type: 'error',
        message: `Failed to start bridge: ${error.message}`,
        timestamp: new Date().toISOString(),
        stack: error.stack
      });
      
      showError(`Failed to start bridge: ${error.message}`);
    } finally {
      setIsStarting(false);
    }
  };

  const stopBridge = async () => {
    setIsStopping(true);
    
    try {
      const result = await window.electronAPI.stopBridge();
      
      if (result.success) {
        onConnectionChange(false);
        onConfigChange(null);
        
        addLogEntry({
          type: 'success',
          message: result.message,
          timestamp: new Date().toISOString()
        });
        
        showSuccess(result.message);
      } else {
        throw new Error(result.message || 'Failed to stop bridge');
      }
    } catch (error) {
      addLogEntry({
        type: 'error',
        message: `Failed to stop bridge: ${error.message}`,
        timestamp: new Date().toISOString(),
        stack: error.stack
      });
      
      showError(`Failed to stop bridge: ${error.message}`);
    } finally {
      setIsStopping(false);
    }
  };

  const showSuccess = (message) => {
    console.log('SUCCESS:', message);
  };

  const showError = (message) => {
    console.error('ERROR:', message);
    window.electronAPI.showErrorDialog({
      title: 'Error',
      message: message
    });
  };

  return (
    <section className="panel">
      <div className="panel-header-standard">
        <h2 className="panel-title">Connection Settings</h2>
      </div>
      <div className="form-group">
        <label htmlFor="username">TikTok Username:</label>
        <input 
          type="text" 
          id="username" 
          placeholder="Enter TikTok username (without @)" 
          value={username}
          onChange={(e) => setUsername(e.target.value)}
        />
      </div>

      <div className="button-group">
        {!isConnected ? (
          <button 
            className="btn btn-primary" 
            onClick={startBridge}
            disabled={isStarting}
          >
            {isStarting ? (
              <>Starting... <span className="loading"></span></>
            ) : (
              'Start Bridge'
            )}
          </button>
        ) : (
          <button 
            className="btn btn-danger" 
            onClick={stopBridge}
            disabled={isStopping}
          >
            {isStopping ? (
              <>Stopping... <span className="loading"></span></>
            ) : (
              'Stop Bridge'
            )}
          </button>
        )}
      </div>
    </section>
  );
};

export default ConnectionPanel;

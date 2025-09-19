import React, { useState, useEffect, useRef } from 'react';
import LogEntry from './LogEntry';

const LogPanel = ({ logEntries, autoScroll, onAutoScrollChange, onClearLog }) => {
  const logContainerRef = useRef(null);

  useEffect(() => {
    if (autoScroll && logContainerRef.current) {
      logContainerRef.current.scrollTop = logContainerRef.current.scrollHeight;
    }
  }, [logEntries, autoScroll]);

  return (
    <section className="panel log-panel">
      <div className="panel-header-with-controls">
        <div className="panel-header-content">
          <h2 className="panel-title">Activity Log</h2>
        </div>
        <div className="log-controls">
          <button 
            className="btn btn-small"
            onClick={onClearLog}
          >
            Clear Log
          </button>
          <label className="checkbox-label" htmlFor="auto-scroll">
            <input 
              type="checkbox" 
              id="auto-scroll" 
              checked={autoScroll}
              onChange={(e) => onAutoScrollChange(e.target.checked)}
            />
            <span className="checkmark"></span>
            <span className="checkbox-text">Auto-scroll</span>
          </label>
        </div>
      </div>
      <div 
        ref={logContainerRef}
        className="log-container"
      >
        {logEntries.map((entry, index) => (
          <LogEntry key={index} entry={entry} />
        ))}
      </div>
    </section>
  );
};

export default LogPanel;

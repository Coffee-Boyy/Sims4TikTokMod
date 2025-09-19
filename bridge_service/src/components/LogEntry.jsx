import React, { useState } from 'react';

const LogEntry = ({ entry }) => {
  const [showStackTrace, setShowStackTrace] = useState(false);
  const [copyFeedback, setCopyFeedback] = useState('');

  // Determine log type based on message content
  let logType = entry.type;
  
  // Check if this should be a blue info message
  if (entry.type === 'manual' || entry.type === 'ai') {
    const messageText = entry.message;
    if (messageText.includes('🎮 Manually triggering sim creation') ||
        messageText.includes('🤖 AI enabled - analyzing appearance') ||
        messageText.includes('🎨 Starting appearance analysis') ||
        messageText.includes('🔍 Analyzing profile picture') ||
        messageText.includes('📤 Sending sim creation event')) {
      logType = 'info-blue';
    }
  }

  const handleToggleStackTrace = (e) => {
    e.stopPropagation();
    setShowStackTrace(!showStackTrace);
  };

  const handleCopyStackTrace = async (e) => {
    e.stopPropagation();
    try {
      const fullErrorText = `${entry.message}\n\nStack Trace:\n${entry.stack}`;
      await navigator.clipboard.writeText(fullErrorText);
      
      // Show feedback
      setCopyFeedback('Copied!');
      setTimeout(() => {
        setCopyFeedback('');
      }, 2000);
    } catch (err) {
      console.error('Failed to copy to clipboard:', err);
      setCopyFeedback('Copy Failed');
      setTimeout(() => {
        setCopyFeedback('');
      }, 2000);
    }
  };

  // Handle invalid or missing timestamps
  let timeString;
  try {
    const date = entry.timestamp ? new Date(entry.timestamp) : new Date();
    timeString = date.toLocaleTimeString();
  } catch (error) {
    timeString = new Date().toLocaleTimeString();
  }

  return (
    <div className={`log-entry log-${logType}`}>
      <span className="log-timestamp">[{timeString}]</span>
      
      <div className="log-message-container">
        <span className="log-message">{entry.message}</span>
        
        {/* Add stack trace toggle if available */}
        {entry.stack && entry.type === 'error' && (
          <div className="stack-controls">
            <button 
              className="stack-toggle"
              onClick={handleToggleStackTrace}
            >
              {showStackTrace ? 'Hide Details' : 'Show Details'}
            </button>
            
            {showStackTrace && (
              <button 
                className="stack-copy"
                onClick={handleCopyStackTrace}
              >
                {copyFeedback || 'Copy'}
              </button>
            )}
            
            {showStackTrace && (
              <pre className="stack-trace">
                {entry.stack}
              </pre>
            )}
          </div>
        )}
      </div>
    </div>
  );
};

export default LogEntry;

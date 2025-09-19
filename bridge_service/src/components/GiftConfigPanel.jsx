import React, { useState, useEffect, useCallback } from 'react';
import GiftItem from './GiftItem';

const GiftConfigPanel = ({ simsInteractions, tiktokGifts, addLogEntry }) => {
  const [currentGiftMappings, setCurrentGiftMappings] = useState({});
  const [hasUnsavedChanges, setHasUnsavedChanges] = useState(false);
  const [changedGifts, setChangedGifts] = useState(new Set());
  const [searchTerm, setSearchTerm] = useState('');

  useEffect(() => {
    if (tiktokGifts && simsInteractions) {
      loadGiftConfiguration();
    }
  }, [tiktokGifts, simsInteractions]);

  const loadGiftConfiguration = useCallback(async () => {
    try {
      // Try to load from backend service first
      if (window.electronAPI && window.electronAPI.loadGiftMappings) {
        const result = await window.electronAPI.loadGiftMappings();
        if (result && result.success && result.mappings) {
          setCurrentGiftMappings(result.mappings);
          addLogEntry({
            type: 'info',
            message: '📁 Gift configuration loaded from backend',
            timestamp: new Date().toISOString()
          });
          
          // Mark as saved since we just loaded from backend
          markConfigurationAsSaved();
          return;
        }
      }

      // Mark as saved since we just loaded from disk
      markConfigurationAsSaved();
    } catch (error) {
      console.error('Failed to load gift configuration:', error);
      setCurrentGiftMappings({});
      markConfigurationAsSaved();
      
      addLogEntry({
        type: 'error',
        message: `❌ Failed to load gift configuration: ${error.message}`,
        timestamp: new Date().toISOString()
      });
    }
  }, [addLogEntry]);

  const markConfigurationAsUnsaved = useCallback((giftId = null) => {
    setHasUnsavedChanges(true);
    if (giftId) {
      setChangedGifts(prev => new Set([...prev, giftId]));
    }
  }, []);

  const markConfigurationAsSaved = useCallback(() => {
    setHasUnsavedChanges(false);
    setChangedGifts(new Set());
  }, []);

  const saveGiftConfiguration = useCallback(async (silent = false) => {
    try {
      // Save to backend service
      if (window.electronAPI && window.electronAPI.saveGiftMappings) {
        const result = await window.electronAPI.saveGiftMappings(currentGiftMappings);
        if (result && !result.success) {
          throw new Error(result.error || 'Bridge service failed to save gift mappings');
        }
      }
      
      // Mark as saved and update UI
      markConfigurationAsSaved();
      
      // Only log if not silent
      if (!silent) {
        addLogEntry({
          type: 'info',
          message: '💾 Gift configuration saved',
          timestamp: new Date().toISOString()
        });
      }
    } catch (error) {
      console.error('Failed to save gift configuration:', error);
      showError(`Failed to save gift configuration: ${error.message}`);
    }
  }, [currentGiftMappings, markConfigurationAsSaved, addLogEntry]);

  const resetGiftConfiguration = useCallback(async () => {
    const result = await window.electronAPI.resetGiftMappings();
    setCurrentGiftMappings(result);
    // Mark all gifts as changed since we reset everything
    const allGiftIds = new Set(tiktokGifts.map(gift => gift.id));
    setChangedGifts(allGiftIds);
    markConfigurationAsUnsaved();
    addLogEntry({
      type: 'info',
      message: '🔄 Gift configuration reset to defaults (unsaved)',
      timestamp: new Date().toISOString()
    });
  }, [tiktokGifts, markConfigurationAsUnsaved, addLogEntry]);

  const handleSaveConfig = useCallback(async () => {
    if (!hasUnsavedChanges) {
      showInfo('No changes to save.');
      return;
    }
    
    await saveGiftConfiguration();
    showSuccess('Gift configuration saved successfully!');
  }, [hasUnsavedChanges, saveGiftConfiguration]);

  const handleResetConfig = useCallback(async () => {
    if (confirm('Are you sure you want to reset all gift mappings to defaults? This cannot be undone.')) {
      await resetGiftConfiguration();
      showSuccess('Gift configuration reset to defaults!');
    }
  }, [resetGiftConfiguration]);

  const handleGiftMappingChange = useCallback((giftId, selectedInteraction) => {
    setCurrentGiftMappings(prev => ({
      ...prev,
      [giftId]: selectedInteraction
    }));
    
    // Log the change (but don't save yet)
    const gift = tiktokGifts.find(g => g.id === giftId);
    const interaction = simsInteractions.find(i => i.value === selectedInteraction);
    
    addLogEntry({
      type: 'info',
      message: `🎁 Gift mapping updated: ${gift?.name} → ${interaction?.icon || ''} ${interaction?.label || 'Unknown'} (unsaved)`,
      timestamp: new Date().toISOString()
    });
    
    // Mark configuration as having unsaved changes
    markConfigurationAsUnsaved(giftId);
  }, [tiktokGifts, simsInteractions, addLogEntry, markConfigurationAsUnsaved]);

  const showInfo = (message) => {
    console.log('INFO:', message);
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

  // Filter gifts based on search term
  const filteredGifts = tiktokGifts?.filter(gift => {
    if (!searchTerm.trim()) return true;
    
    const searchLower = searchTerm.toLowerCase();
    
    // Search by gift name
    if (gift.name.toLowerCase().includes(searchLower)) {
      return true;
    }
    
    // Search by selected interaction
    const currentMapping = currentGiftMappings[gift.id];
    if (currentMapping && currentMapping !== 'none') {
      const interaction = simsInteractions.find(i => i.value === currentMapping);
      if (interaction && interaction.label.toLowerCase().includes(searchLower)) {
        return true;
      }
    }
    
    return false;
  });

  if (!tiktokGifts || !simsInteractions) {
    return (
      <section className="panel" id="gift-config-panel">
        <div className="panel-header-with-controls">
          <div className="panel-header-content">
            <h2 className="panel-title">Gift Interaction Configuration</h2>
          </div>
        </div>
        <div>Loading gift configuration...</div>
      </section>
    );
  }

  return (
    <section className="panel" id="gift-config-panel">
      <div className="panel-header-with-controls">
        <div className="panel-header-content">
          <h2 className="panel-title">Gift Interaction Configuration</h2>
        </div>
        <div className="config-controls">
          {hasUnsavedChanges && changedGifts.size > 0 && (
            <span className="unsaved-changes-label">
              {changedGifts.size} unsaved change{changedGifts.size !== 1 ? 's' : ''}
            </span>
          )}
          <button 
            className="btn btn-secondary btn-small"
            onClick={handleSaveConfig}
          >
            Save Configuration
          </button>
          <button 
            className="btn btn-danger btn-small"
            onClick={handleResetConfig}
          >
            Reset to Defaults
          </button>
        </div>
      </div>

      <div className="search-box">
        <input
          type="text"
          placeholder="Search gifts by name or interaction..."
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
          className="search-input"
        />
        {searchTerm && (
          <button
            className="search-clear"
            onClick={() => setSearchTerm('')}
            title="Clear search"
          >
            ✕
          </button>
        )}
      </div>

      <div className="gift-grid" id="gift-grid">
        {filteredGifts.map(gift => (
          <GiftItem
            key={gift.id}
            gift={gift}
            simsInteractions={simsInteractions}
            currentMapping={currentGiftMappings[gift.id]}
            onMappingChange={handleGiftMappingChange}
            addLogEntry={addLogEntry}
          />
        ))}
      </div>
    </section>
  );
};

export default GiftConfigPanel;

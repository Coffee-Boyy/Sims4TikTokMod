import React from 'react';

const GiftItem = ({ gift, simsInteractions, currentMapping, onMappingChange, addLogEntry }) => {
  const handleMappingChange = (e) => {
    const selectedInteraction = e.target.value;
    onMappingChange(gift.id, selectedInteraction);
  };

  const handleTestGift = async (e) => {
    e.preventDefault();
    
    // Check if bridge is connected
    const isConnected = await window.electronAPI.getBridgeStatus().then(status => status.connected);
    if (!isConnected) {
      showError('Bridge is not connected. Please start the bridge first.');
      return;
    }
    
    // Generate a test username
    const testUsername = `testuser_${Math.random().toString(36).substring(2, 8)}`;
    
    // Create the gift data in the same format as the manual gift system
    const giftData = {
      username: testUsername,
      giftName: gift.name,
      giftId: gift.id,
      diamondCount: gift.cost,
      giftDisplayName: gift.name,
      tier: gift.tier,
      icon: gift.icon
    };
    
    // Get the mapped Sims interaction for this gift
    const simsInteraction = currentMapping || 'none';
    if (simsInteraction && simsInteraction !== 'none') {
      const interaction = simsInteractions.find(i => i.value === simsInteraction);
      if (interaction) {
        giftData.simsInteraction = simsInteraction;
        giftData.simsInteractionLabel = interaction.label;
      }
    }
    
    try {
      const result = await window.electronAPI.sendManualGift(giftData);
      
      if (result.success) {
        const interactionText = giftData.simsInteractionLabel ? 
          ` → ${giftData.simsInteractionLabel}` : '';
        
        addLogEntry({
          type: 'success',
          message: `🧪 Test gift sent: ${testUsername} -> ${gift.name} (${gift.cost} 💎)${interactionText}`,
          timestamp: new Date().toISOString()
        });
        
        showSuccess(`Test gift sent: ${gift.name}`);
      } else {
        throw new Error(result.message || 'Failed to send test gift');
      }
    } catch (error) {
      addLogEntry({
        type: 'error',
        message: `Failed to send test gift: ${error.message}`,
        timestamp: new Date().toISOString(),
        stack: error.stack
      });
      
      showError(`Failed to send test gift: ${error.message}`);
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
    <div className="gift-item">
      <div className="gift-header">
        <div className="gift-icon">
          <img 
            src={gift.icon} 
            alt={gift.name} 
            onError={(e) => {
              e.target.style.display = 'none';
              e.target.nextElementSibling.style.display = 'inline';
            }}
          />
          <span className="fallback-icon" style={{display: 'none'}}>🎁</span>
        </div>
        <div className="gift-info">
          <h4 className="gift-name">
            {gift.name} 
            <span className={`gift-tier tier-${gift.tier}`}>{gift.tier}</span>
          </h4>
          <div className="gift-cost">
            <span className="diamond-icon">💎</span>
            <span>{gift.cost} diamonds</span>
          </div>
        </div>
        <div className="gift-actions">
          <button 
            className="btn btn-test btn-small" 
            onClick={handleTestGift}
            title="Test this gift"
          >
            🧪 Test
          </button>
        </div>
      </div>
      <div className="gift-mapping">
        <label htmlFor={`mapping-${gift.id}`}>Sims 4 Interaction:</label>
        <select 
          id={`mapping-${gift.id}`}
          value={currentMapping || ''}
          onChange={handleMappingChange}
        >
          {simsInteractions.map(interaction => (
            <option key={interaction.value} value={interaction.value}>
              {interaction.icon} {interaction.label}
            </option>
          ))}
        </select>
      </div>
    </div>
  );
};

export default GiftItem;

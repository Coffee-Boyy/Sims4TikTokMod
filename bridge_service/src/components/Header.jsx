import React, { useState, useEffect } from 'react';

const Header = () => {
  const [currentTheme, setCurrentTheme] = useState('system');

  useEffect(() => {
    // Load saved theme preference
    const savedTheme = localStorage.getItem('theme-preference') || 'system';
    setCurrentTheme(savedTheme);
    
    // Apply the theme
    applyTheme(savedTheme);
    
    // Check for system dark mode preference
    const prefersDarkMode = window.matchMedia('(prefers-color-scheme: dark)');
    
    // Listen for system theme changes (only relevant when in system mode)
    const handleSystemThemeChange = (e) => {
      if (currentTheme === 'system') {
        updateThemeToggleIcon();
      }
    };
    
    prefersDarkMode.addEventListener('change', handleSystemThemeChange);
    
    return () => {
      prefersDarkMode.removeEventListener('change', handleSystemThemeChange);
    };
  }, [currentTheme]);

  const toggleTheme = () => {
    // Cycle through: system -> light -> dark -> system
    let newTheme;
    switch (currentTheme) {
      case 'system':
        newTheme = 'light';
        break;
      case 'light':
        newTheme = 'dark';
        break;
      case 'dark':
        newTheme = 'system';
        break;
      default:
        newTheme = 'system';
    }
    
    setCurrentTheme(newTheme);
    applyTheme(newTheme);
    updateThemeToggleIcon();
    
    // Save preference
    localStorage.setItem('theme-preference', newTheme);
  };

  const applyTheme = (theme) => {
    const root = document.documentElement;
    
    if (theme === 'system') {
      // Remove data-theme attribute to let CSS media queries handle it
      root.removeAttribute('data-theme');
    } else {
      // Set explicit theme
      root.setAttribute('data-theme', theme);
    }
  };

  const getEffectiveTheme = () => {
    if (currentTheme === 'system') {
      return window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
    }
    return currentTheme;
  };

  const updateThemeToggleIcon = () => {
    const effectiveTheme = getEffectiveTheme();
    
    // Update icon and tooltip based on current theme and mode
    let icon, title;
    if (currentTheme === 'system') {
      icon = effectiveTheme === 'dark' ? '🌙' : '☀️';
      title = `Theme: System (${effectiveTheme}) - Click to switch to Light mode`;
    } else if (currentTheme === 'light') {
      icon = '☀️';
      title = 'Theme: Light - Click to switch to Dark mode';
    } else {
      icon = '🌙';
      title = 'Theme: Dark - Click to switch to System mode';
    }
    
    return { icon, title };
  };

  const { icon, title } = updateThemeToggleIcon();

  return (
    <header className="header">
      <div className="header-content">
        <h1 className="title">The Sims 4 - TikTok</h1>
        <button 
          className="theme-toggle" 
          title={title}
          onClick={toggleTheme}
        >
          <span className="theme-icon">{icon}</span>
        </button>
      </div>
    </header>
  );
};

export default Header;

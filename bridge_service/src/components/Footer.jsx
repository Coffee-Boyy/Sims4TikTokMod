import React from 'react';

const Footer = () => {
  const handleGitHubClick = (e) => {
    e.preventDefault();
    if (window.electronAPI && window.electronAPI.openExternal) {
      window.electronAPI.openExternal('https://github.com/ConnorChristie/Sims4TikTokMod');
    }
  };

  return (
    <footer className="footer">
      <div className="footer-content">
        <span>Built by Coffee Boy</span>
        <a 
          href="#" 
          id="github-link" 
          className="github-link"
          onClick={handleGitHubClick}
        >
          GitHub Repository
        </a>
      </div>
    </footer>
  );
};

export default Footer;

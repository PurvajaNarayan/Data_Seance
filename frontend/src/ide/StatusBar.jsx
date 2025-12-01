import React from 'react';
import { GitBranch, AlertCircle, Bell } from 'lucide-react';

export function StatusBar() {
  // Styles
  const containerStyle = {
    height: '24px',
    backgroundColor: '#007acc',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingLeft: '8px',
    paddingRight: '8px',
    fontSize: '12px',
    color: '#ffffff',
  };

  const leftSectionStyle = {
    display: 'flex',
    alignItems: 'center',
    gap: '16px',
  };

  const rightSectionStyle = {
    display: 'flex',
    alignItems: 'center',
    gap: '16px',
  };

  const itemStyle = {
    display: 'flex',
    alignItems: 'center',
    gap: '4px',
  };

  return (
    <div style={containerStyle}>
      <div style={leftSectionStyle}>
        <div style={itemStyle}>
          <GitBranch size={14} />
          <span>main</span>
        </div>
        <div style={itemStyle}>
          <AlertCircle size={14} />
          <span>0</span>
        </div>
      </div>
      
      <div style={rightSectionStyle}>
        <span>Python 3.10.0</span>
        <span>UTF-8</span>
        <span>LF</span>
        <span>Ln 24, Col 16</span>
        <Bell size={14} />
      </div>
    </div>
  );
}
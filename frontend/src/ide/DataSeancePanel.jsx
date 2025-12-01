import React from 'react';
import { X, ShieldCheck } from 'lucide-react';
import { ProblemsPanel } from './ProblemsPanel';

export function DataSeancePanel({ onClose, selectedFile, fileContents }) {
  const containerStyle = {
    width: '384px', // 96 * 4 = 384px (w-96)
    backgroundColor: '#252526',
    borderLeft: '1px solid #3e3e42',
    display: 'flex',
    flexDirection: 'column',
    height: '100%',
  };

  const headerStyle = {
    height: '36px', 
    backgroundColor: '#2d2d30',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingLeft: '12px',
    paddingRight: '12px',
    borderBottom: '1px solid #3e3e42',
  };

  const headerLeftStyle = {
    display: 'flex',
    alignItems: 'center',
    gap: '8px',
  };

  const titleStyle = {
    fontSize: '14px',
    color: '#cccccc',
  };

  const closeButtonStyle = {
    backgroundColor: 'transparent',
    border: 'none',
    borderRadius: '4px',
    padding: '4px',
    cursor: 'pointer',
    color: '#cccccc',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    transition: 'background-color 0.2s ease',
  };

  const contentStyle = {
    flex: 1,
    overflow: 'hidden',
  };

  return (
    <div style={containerStyle}>
      {/* Header */}
      <div style={headerStyle}>
        <div style={headerLeftStyle}>
          <ShieldCheck size={16} color="#4CAF50" />
          <span style={titleStyle}>Data Seance</span>
        </div>
        <button
          onClick={onClose}
          style={closeButtonStyle}
          onMouseEnter={(e) => {
            e.currentTarget.style.backgroundColor = '#2a2d2e';
          }}
          onMouseLeave={(e) => {
            e.currentTarget.style.backgroundColor = 'transparent';
          }}
        >
          <X size={16} />
        </button>
      </div>

      {/* Content */}
      <div style={contentStyle}>
        <ProblemsPanel 
          selectedFile={selectedFile}
          fileContents={fileContents}
        />
      </div>
    </div>
  );
}
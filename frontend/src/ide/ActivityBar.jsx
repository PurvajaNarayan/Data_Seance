import React from 'react';
import { Files, Search, Package, ShieldCheck } from 'lucide-react';

export function ActivityBar({ 
  activeView, 
  onViewChange, 
  dataSciencePanelOpen, 
  onToggleDataScience 
}) {
  const items = [
    { id: 'explorer', icon: Files, label: 'Explorer' },
    { id: 'search', icon: Search, label: 'Search' },
    { id: 'extensions', icon: Package, label: 'Extensions' },
    { id: 'datascience', icon: ShieldCheck, label: 'Data Science', isDataScience: true },
  ];

  const containerStyle = {
    width: '48px',
    backgroundColor: '#333333',
    display: 'flex',
    flexDirection: 'column',
    alignItems: 'center',
    paddingTop: '8px',
    paddingBottom: '8px',
    gap: '8px',
  };

  const buttonStyle = (isActive) => ({
    width: '48px',
    height: '48px',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    position: 'relative',
    backgroundColor: 'transparent',
    border: 'none',
    cursor: 'pointer',
    color: isActive ? '#ffffff' : '#858585',
    transition: 'color 0.2s ease',
  });

  const activeIndicatorStyle = (isDataScience) => ({
    position: 'absolute',
    left: 0,
    width: '2px',
    height: '48px',
    backgroundColor: isDataScience ? '#4CAF50' : '#ffffff',
  });

  return (
    <div style={containerStyle}>
      {items.map((item) => {
        const Icon = item.icon;
        const isActive = item.isDataScience ? dataSciencePanelOpen : activeView === item.id;
        
        return (
          <button
            key={item.id}
            onClick={() => item.isDataScience ? onToggleDataScience() : onViewChange(item.id)}
            style={buttonStyle(isActive)}
            title={item.label}
            onMouseEnter={(e) => {
              if (!isActive) {
                e.currentTarget.style.color = '#ffffff';
              }
            }}
            onMouseLeave={(e) => {
              if (!isActive) {
                e.currentTarget.style.color = '#858585';
              }
            }}
          >
            <Icon size={24} />
            {isActive && (
              <div style={activeIndicatorStyle(item.isDataScience)} />
            )}
          </button>
        );
      })}
    </div>
  );
}
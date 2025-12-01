import React, { useState } from 'react';

export function TopMenuBar() {
  const menuItems = ['File', 'Edit', 'Selection', 'View', 'Go', 'Run', 'Terminal', 'Help'];
  const [hoveredItem, setHoveredItem] = useState(null);

  // Styles
  const containerStyle = {
    height: '36px',
    backgroundColor: '#323233',
    display: 'flex',
    alignItems: 'center',
    paddingLeft: '8px',
    paddingRight: '8px',
    gap: '4px',
  };

  const buttonStyle = (isHovered) => ({
    padding: '4px 8px',
    backgroundColor: isHovered ? '#2a2d2e' : 'transparent',
    border: 'none',
    borderRadius: '4px',
    fontSize: '14px',
    color: '#cccccc',
    cursor: 'pointer',
    transition: 'background-color 0.2s ease',
  });

  return (
    <div style={containerStyle}>
      {menuItems.map((item) => (
        <button
          key={item}
          style={buttonStyle(hoveredItem === item)}
          onMouseEnter={() => setHoveredItem(item)}
          onMouseLeave={() => setHoveredItem(null)}
        >
          {item}
        </button>
      ))}
    </div>
  );
}
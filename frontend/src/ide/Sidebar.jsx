import React, { useState, useRef } from 'react';
import { ChevronRight, ChevronDown, FileCode, FileJson, FolderOpen, Folder, Upload, FileText } from 'lucide-react';

export function Sidebar({ activeView, onFileSelect, selectedFile, onFileUpload }) {
  const [expandedFolders, setExpandedFolders] = useState(new Set(['boston_housing']));
  const [uploadedFiles, setUploadedFiles] = useState([]);
  const fileInputRef = useRef(null);

  const toggleFolder = (folder) => {
    const newExpanded = new Set(expandedFolders);
    if (newExpanded.has(folder)) {
      newExpanded.delete(folder);
    } else {
      newExpanded.add(folder);
    }
    setExpandedFolders(newExpanded);
  };

  const handleImportClick = () => {
    fileInputRef.current?.click();
  };

  const handleFileUpload = async (event) => {
    const files = event.target.files;
    if (files && files.length > 0) {
      const newFiles = [];
      
      for (let i = 0; i < files.length; i++) {
        const file = files[i];
        const fileExtension = file.name.split('.').pop().toLowerCase();
        
        // Check if it's a binary file
        if (fileExtension === 'pkl') {
          newFiles.push({
            name: file.name,
            content: `# Binary file: ${file.name}\n# Size: ${(file.size / 1024).toFixed(2)} KB\n# Type: Python Pickle File\n\n# This is a binary file and cannot be displayed as text.\n# To use this file, you would need to:\n# 1. Download it to your local machine\n# 2. Load it in Python using pickle.load()\n\n# Example:\n# import pickle\n# with open('${file.name}', 'rb') as f:\n#     data = pickle.load(f)`,
            type: 'binary',
            binaryData: file
          });
        } else {
          // Read text files normally
          const content = await readFileContent(file);
          newFiles.push({
            name: file.name,
            content: content,
            type: getFileType(file.name)
          });
        }
      }
      
      setUploadedFiles([...uploadedFiles, ...newFiles]);
      
      // Notify parent component
      if (onFileUpload) {
        onFileUpload(newFiles);
      }
      
      console.log('Files uploaded:', newFiles.map(f => f.name));
    }
    
    // Reset input
    event.target.value = '';
  };

  const readFileContent = (file) => {
    return new Promise((resolve, reject) => {
      const reader = new FileReader();
      reader.onload = (e) => resolve(e.target.result);
      reader.onerror = reject;
      reader.readAsText(file);
    });
  };

  const getFileType = (filename) => {
    const ext = filename.split('.').pop().toLowerCase();
    if (['py', 'js', 'jsx', 'ts', 'tsx'].includes(ext)) return 'code';
    if (['json', 'csv', 'txt', 'md'].includes(ext)) return 'data';
    if (ext === 'pkl') return 'binary';
    return 'file';
  };

  const getFileIcon = (filename) => {
    const ext = filename.split('.').pop().toLowerCase();
    if (ext === 'py') {
      return { Icon: FileCode, color: '#3b8dd8' };
    }
    if (ext === 'csv') {
      return { Icon: FileJson, color: 'rgb(76, 175, 80)' };
    }
    if (ext === 'pkl') {
      return { Icon: FileCode, color: '#9b59b6' };
    }
    if (ext === 'md') {
      return { Icon: FileText, color: '#858585' };
    }
    return { Icon: FileCode, color: '#cccccc' };
  };

  // Search View
  if (activeView === 'search') {
    return (
      <div style={sidebarStyle}>
        <div style={searchContainerStyle}>
          <h2 style={{ ...titleStyle, marginBottom: '16px' }}>Search</h2>
          <input
            type="text"
            placeholder="Search"
            style={searchInputStyle}
          />
        </div>
      </div>
    );
  }

  // Extensions View
  if (activeView === 'extensions') {
    const [hoveredExtension, setHoveredExtension] = useState(null);

    return (
      <div style={sidebarStyle}>
        <div style={extensionsContainerStyle}>
          <h2 style={{ ...titleStyle, marginBottom: '16px' }}>Extensions</h2>
          <input
            type="text"
            placeholder="Search Extensions"
            style={{ ...searchInputStyle, marginBottom: '16px' }}
          />
          <div style={extensionsListStyle}>
            <div
              style={extensionItemStyle(hoveredExtension === 'python')}
              onMouseEnter={() => setHoveredExtension('python')}
              onMouseLeave={() => setHoveredExtension(null)}
            >
              <div style={extensionNameStyle}>Python</div>
              <div style={extensionAuthorStyle}>Microsoft</div>
            </div>
            <div
              style={extensionItemStyle(hoveredExtension === 'jupyter')}
              onMouseEnter={() => setHoveredExtension('jupyter')}
              onMouseLeave={() => setHoveredExtension(null)}
            >
              <div style={extensionNameStyle}>Jupyter</div>
              <div style={extensionAuthorStyle}>Microsoft</div>
            </div>
          </div>
        </div>
      </div>
    );
  }

  // Explorer View (Default)
  const FolderButton = ({ folder, label, children }) => {
    const [isHovered, setIsHovered] = useState(false);
    const isExpanded = expandedFolders.has(folder);

    return (
      <>
        <button
          onClick={() => toggleFolder(folder)}
          style={folderButtonStyle(isHovered)}
          onMouseEnter={() => setIsHovered(true)}
          onMouseLeave={() => setIsHovered(false)}
        >
          {isExpanded ? <ChevronDown size={16} /> : <ChevronRight size={16} />}
          {isExpanded ? <FolderOpen size={16} /> : <Folder size={16} />}
          <span>{label}</span>
        </button>
        {isExpanded && <div style={indentStyle}>{children}</div>}
      </>
    );
  };

  const FileButton = ({ file, icon: Icon, iconColor }) => {
    const [isHovered, setIsHovered] = useState(false);
    const isSelected = selectedFile === file;

    return (
      <button
        onClick={() => onFileSelect(file)}
        style={fileButtonStyle(isSelected, isHovered)}
        onMouseEnter={() => setIsHovered(true)}
        onMouseLeave={() => setIsHovered(false)}
      >
        <Icon size={16} color={iconColor} />
        <span>{file}</span>
      </button>
    );
  };

  const [uploadBtnHovered, setUploadBtnHovered] = useState(false);

  // Styles
  const sidebarStyle = {
    width: '256px',
    backgroundColor: '#252526',
    borderRight: '1px solid #3e3e42',
    display: 'flex',
    flexDirection: 'column',
  };

  const headerStyle = {
    padding: '8px',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'space-between',
  };

  const titleStyle = {
    textTransform: 'uppercase',
    letterSpacing: '0.05em',
    fontSize: '12px',
    paddingLeft: '8px',
    paddingRight: '8px',
    color: '#cccccc',
  };

  const uploadButtonStyle = {
    padding: '6px',
    backgroundColor: 'transparent',
    border: 'none',
    borderRadius: '4px',
    color: '#858585',
    cursor: 'pointer',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    transition: 'background-color 0.2s ease, color 0.2s ease',
  };

  const hiddenInputStyle = {
    display: 'none',
  };

  const contentStyle = {
    flex: 1,
    overflowY: 'auto',
  };

  const contentInnerStyle = {
    padding: '0 8px',
  };

  const folderButtonStyle = (isHovered) => ({
    width: '100%',
    display: 'flex',
    alignItems: 'center',
    gap: '4px',
    padding: '4px 8px',
    backgroundColor: isHovered ? '#2a2d2e' : 'transparent',
    border: 'none',
    borderRadius: '4px',
    fontSize: '14px',
    color: '#cccccc',
    cursor: 'pointer',
    transition: 'background-color 0.2s ease',
  });

  const fileButtonStyle = (isSelected, isHovered) => ({
    width: '100%',
    display: 'flex',
    alignItems: 'center',
    gap: '4px',
    padding: '4px 8px',
    backgroundColor: isSelected ? '#37373d' : (isHovered ? '#2a2d2e' : 'transparent'),
    border: 'none',
    borderRadius: '4px',
    fontSize: '14px',
    color: '#cccccc',
    cursor: 'pointer',
    transition: 'background-color 0.2s ease',
  });

  const indentStyle = {
    marginLeft: '16px',
  };

  const spacerStyle = {
    marginBottom: '4px',
  };

  const searchContainerStyle = {
    padding: '16px',
  };

  const searchInputStyle = {
    width: '100%',
    backgroundColor: '#3c3c3c',
    border: '1px solid #3e3e42',
    padding: '4px 12px',
    borderRadius: '4px',
    fontSize: '14px',
    color: '#cccccc',
    outline: 'none',
  };

  const extensionsContainerStyle = {
    padding: '16px',
  };

  const extensionsListStyle = {
    display: 'flex',
    flexDirection: 'column',
    gap: '8px',
  };

  const extensionItemStyle = (isHovered) => ({
    padding: '8px',
    backgroundColor: isHovered ? '#2a2d2e' : 'transparent',
    borderRadius: '4px',
    cursor: 'pointer',
    transition: 'background-color 0.2s ease',
  });

  const extensionNameStyle = {
    color: '#cccccc',
    fontSize: '14px',
  };

  const extensionAuthorStyle = {
    fontSize: '12px',
    color: '#858585',
  };

  return (
    <div style={sidebarStyle}>
      <div style={headerStyle}>
        <h2 style={titleStyle}>Explorer</h2>
        <button
          onClick={handleImportClick}
          style={uploadButtonStyle}
          title="Import Files"
          onMouseEnter={(e) => {
            setUploadBtnHovered(true);
            e.currentTarget.style.backgroundColor = '#2a2d2e';
            e.currentTarget.style.color = '#ffffff';
          }}
          onMouseLeave={(e) => {
            setUploadBtnHovered(false);
            e.currentTarget.style.backgroundColor = 'transparent';
            e.currentTarget.style.color = '#858585';
          }}
        >
          <Upload size={16} />
        </button>
        <input
          ref={fileInputRef}
          type="file"
          multiple
          style={hiddenInputStyle}
          onChange={handleFileUpload}
          accept=".py,.csv,.json,.txt,.md,.js,.jsx,.pkl"
        />
      </div>
      
      <div style={contentStyle}>
        <div style={contentInnerStyle}>
          {/* Test Files */}
          <div style={spacerStyle}>
            <FileButton 
              file="PIIdata.csv" 
              icon={FileJson} 
              iconColor="rgb(76, 175, 80)" 
            />
          </div>

          {/* Boston Housing folder */}
          <div style={spacerStyle}>
            <FolderButton folder="boston_housing" label="boston_housing">
              <FileButton 
                file="boston_housing/boston_housing.py" 
                icon={FileCode} 
                iconColor="#3b8dd8" 
              />
              <FileButton 
                file="boston_housing/boston_housing.pkl" 
                icon={FileCode} 
                iconColor="#9b59b6" 
              />
              <FileButton 
                file="boston_housing/README.md" 
                icon={FileText} 
                iconColor="#858585" 
              />
            </FolderButton>
          </div>

          {/* Uploaded Files Section */}
          {uploadedFiles.length > 0 && (
            <div style={spacerStyle}>
              <FolderButton folder="uploaded" label="Uploaded Files">
                {uploadedFiles.map((file, index) => {
                  const { Icon, color } = getFileIcon(file.name);
                  return (
                    <FileButton
                      key={index}
                      file={file.name}
                      icon={Icon}
                      iconColor={color}
                    />
                  );
                })}
              </FolderButton>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

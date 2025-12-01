import React, { useState } from 'react';
import { ActivityBar } from './ide/ActivityBar';
import { Sidebar } from './ide/Sidebar';
import { EditorArea } from './ide/EditorArea';
import { DataSeancePanel } from './ide/DataSeancePanel';
import { StatusBar } from './ide/StatusBar';
import { TopMenuBar } from './ide/TopMenuBar';

export default function App() {
  const [activeView, setActiveView] = useState('explorer');
  const [openFile, setOpenFile] = useState('analysis.py');
  const [dataSciencePanelOpen, setDataSciencePanelOpen] = useState(true);
  const [fileContents, setFileContents] = useState({});
  const [uploadedFileContents, setUploadedFileContents] = useState({});

  const handleFileUpload = (newFiles) => {
    // Add uploaded files to uploadedFileContents
    const updatedContents = { ...uploadedFileContents };
    newFiles.forEach(file => {
      updatedContents[file.name] = file.content;
    });
    setUploadedFileContents(updatedContents);
    
    // Optionally open the first uploaded file
    if (newFiles.length > 0) {
      setOpenFile(newFiles[0].name);
    }
  };

  const appContainerStyle = {
    height: '100vh',
    display: 'flex',
    flexDirection: 'column',
    backgroundColor: '#1e1e1e',
    color: '#cccccc',
    fontFamily: '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif',
  };

  const mainContentStyle = {
    display: 'flex',
    flex: 1,
    overflow: 'hidden',
  };


  return (
    <div style={appContainerStyle}>
      <TopMenuBar />
      
      <div style={mainContentStyle}>
        <ActivityBar 
          activeView={activeView} 
          onViewChange={setActiveView}
          dataSciencePanelOpen={dataSciencePanelOpen}
          onToggleDataScience={() => setDataSciencePanelOpen(!dataSciencePanelOpen)}
        />
        
        <Sidebar 
          activeView={activeView} 
          onFileSelect={setOpenFile}
          selectedFile={openFile}
          onFileUpload={handleFileUpload}
        />
        
        <EditorArea 
          openFile={openFile}
          dataSciencePanelOpen={dataSciencePanelOpen}
          onFileContentsChange={setFileContents}
          externalFileContents={uploadedFileContents}
        />
        
        {dataSciencePanelOpen && (
          <DataSeancePanel 
            onClose={() => setDataSciencePanelOpen(false)}
            selectedFile={openFile}
            fileContents={{ ...fileContents, ...uploadedFileContents }}
          />
        )}
      </div>
      
      <StatusBar />
    </div>
  );
}
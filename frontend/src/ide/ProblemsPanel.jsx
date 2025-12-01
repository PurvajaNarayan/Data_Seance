import React, { useState } from 'react';
import { Play, AlertCircle, AlertTriangle, Info, FileText, X, ChevronDown, ChevronRight } from 'lucide-react';

export function ProblemsPanel({ selectedFile, fileContents }) {
  const [problems, setProblems] = useState([]);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [hasAnalyzed, setHasAnalyzed] = useState(false);
  const [hoveredIndex, setHoveredIndex] = useState(null);
  const [expandedIndex, setExpandedIndex] = useState(null);
  const [fullAnalysis, setFullAnalysis] = useState('');
  const [showFullReport, setShowFullReport] = useState(false);
  const [isControlsCollapsed, setIsControlsCollapsed] = useState(false);

  const extractSummary = (description) => {
    // Get first sentence or first part before bullet points
    const sentences = description.split(/\.\s+/);
    return sentences[0] + (sentences.length > 1 ? '.' : '');
  };

  const extractEvidence = (description) => {
    // Extract bullet points that look like evidence
    const bullets = description.match(/\*[^*]+\*/g) || [];
    return bullets.join(' ');
  };

  const handleStartAnalysis = async () => {
    if (!selectedFile || !fileContents[selectedFile]) {
      return;
    }

    setIsAnalyzing(true);
    
    try {
      const response = await fetch('http://localhost:5001/api/analyze', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          file_name: selectedFile,
          file_content: fileContents[selectedFile],
          project_description: 'Data Science Project Analysis'
        })
      });

      const data = await response.json();
      
      console.log('=== API RESPONSE ===', data);

      if (data.success) {
        // Map the new structured format
        const mappedIssues = (data.issues || []).map(issue => ({
          line: 1,
          severity: issue.issue_severity,
          name: issue.issue_name,
          summary: extractSummary(issue.issue_description),
          evidence: issue.issue_description,
          remedies: issue.possible_remedies || []
        }));
        
        console.log('Mapped Issues:', mappedIssues);
        
        setProblems(mappedIssues);
        setFullAnalysis(data.full_analysis || '');
        setHasAnalyzed(true);
      } else {
        console.error('Backend analysis failed:', data.error);
        alert('Analysis failed: ' + data.error);
      }
    } catch (error) {
      console.error('Error calling backend:', error);
      alert('Could not connect to backend. Make sure the server is running on port 5001.');
    } finally {
      setIsAnalyzing(false);
    }
  };

  const downloadAnalysis = () => {
    const blob = new Blob([fullAnalysis], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `ethics-analysis-${selectedFile}.txt`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  const formatText = (text) => {
    if (!text) return text;
    
    // Replace **text** with styled spans
    const parts = text.split(/(\*\*[^*]+\*\*)/g);
    return parts.map((part, i) => {
      if (part.startsWith('**') && part.endsWith('**')) {
        return <strong key={i} style={{ color: '#eab308' }}>{part.slice(2, -2)}</strong>;
      }
      return part;
    });
  };

  const formatAnalysis = (text) => {
    if (!text) return null;

    const lines = text.split('\n');
    const elements = [];
    let key = 0;

    lines.forEach((line) => {
      const trimmed = line.trim();
      
      if (trimmed.startsWith('###')) {
        elements.push(
          <div key={key++} style={{ 
            fontSize: '18px', 
            fontWeight: 'bold', 
            color: '#4CAF50',
            marginTop: '16px',
            marginBottom: '8px'
          }}>
            {trimmed.replace(/^###\s*/, '')}
          </div>
        );
      }
      else if (trimmed.startsWith('####')) {
        elements.push(
          <div key={key++} style={{ 
            fontSize: '16px', 
            fontWeight: 'bold', 
            color: '#3b82f6',
            marginTop: '12px',
            marginBottom: '6px'
          }}>
            {trimmed.replace(/^####\s*/, '')}
          </div>
        );
      }
      else if (trimmed.includes('**')) {
        elements.push(
          <div key={key++} style={{ marginBottom: '4px', lineHeight: '1.6' }}>
            {formatText(trimmed)}
          </div>
        );
      }
      else if (trimmed.startsWith('-')) {
        elements.push(
          <div key={key++} style={{ 
            marginLeft: '16px', 
            marginBottom: '4px',
            display: 'flex',
            gap: '8px',
            lineHeight: '1.6'
          }}>
            <span style={{ color: '#4CAF50' }}>•</span>
            <span>{trimmed.substring(1).trim()}</span>
          </div>
        );
      }
      else if (trimmed === '---') {
        elements.push(
          <hr key={key++} style={{ 
            border: 'none', 
            borderTop: '1px solid #3e3e42',
            margin: '16px 0'
          }} />
        );
      }
      else if (trimmed.length > 0) {
        elements.push(
          <div key={key++} style={{ 
            marginBottom: '8px',
            lineHeight: '1.6',
            color: '#cccccc'
          }}>
            {trimmed}
          </div>
        );
      }
      else {
        elements.push(<div key={key++} style={{ height: '8px' }} />);
      }
    });

    return elements;
  };

  const getSeverityIcon = (severity) => {
    switch (severity) {
      case 'error':
        return <AlertCircle size={16} color="#ef4444" />;
      case 'warning':
        return <AlertTriangle size={16} color="#eab308" />;
      case 'info':
        return <Info size={16} color="#3b82f6" />;
      default:
        return null;
    }
  };

  const getSeverityColor = (severity) => {
    switch (severity) {
      case 'error':
        return '#ef4444';
      case 'warning':
        return '#eab308';
      case 'info':
        return '#3b82f6';
      default:
        return '#cccccc';
    }
  };

  const errorCount = problems.filter(p => p.severity === 'error').length;
  const warningCount = problems.filter(p => p.severity === 'warning').length;
  const infoCount = problems.filter(p => p.severity === 'info').length;

  // Styles
  const containerStyle = {
    display: 'flex',
    flexDirection: 'column',
    height: '100%',
  };

  const analysisControlStyle = {
    borderBottom: '1px solid #3e3e42',
    overflow: 'hidden',
    transition: 'max-height 0.3s ease, padding 0.3s ease',
    maxHeight: isControlsCollapsed ? '0' : '500px',
    padding: isControlsCollapsed ? '0 16px' : '16px',
  };

  const fileInfoStyle = {
    marginBottom: '12px',
  };

  const labelStyle = {
    fontSize: '12px',
    color: '#858585',
    marginBottom: '4px',
  };

  const fileNameStyle = {
    fontSize: '14px',
    paddingLeft: '8px',
    paddingRight: '8px',
    paddingTop: '4px',
    paddingBottom: '4px',
    backgroundColor: '#1e1e1e',
    borderRadius: '4px',
    color: '#cccccc',
  };

  const buttonStyle = (disabled, color = '#4CAF50') => ({
    width: '100%',
    padding: '8px 16px',
    backgroundColor: disabled ? '#3e3e42' : color,
    color: disabled ? '#858585' : '#ffffff',
    border: 'none',
    borderRadius: '4px',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    gap: '8px',
    cursor: disabled ? 'not-allowed' : 'pointer',
    fontSize: '14px',
    transition: 'background-color 0.2s ease',
    marginBottom: '8px',
  });

  const summaryStyle = {
    padding: '12px 16px',
    borderBottom: '1px solid #3e3e42',
    display: 'flex',
    alignItems: 'center',
    gap: '16px',
    fontSize: '14px',
    color: '#cccccc',
  };

  const summaryItemStyle = {
    display: 'flex',
    alignItems: 'center',
    gap: '4px',
  };

  const problemsListStyle = {
    flex: 1,
    overflowY: 'auto',
  };

  const emptyStateStyle = {
    padding: '16px',
    textAlign: 'center',
    color: '#858585',
    fontSize: '14px',
  };

  const successStateStyle = {
    padding: '16px',
    textAlign: 'center',
    color: '#4CAF50',
    fontSize: '14px',
  };

  const problemsContainerStyle = {
    padding: '8px',
  };

  const problemItemStyle = (isHovered, isExpanded) => ({
    marginBottom: '8px',
    backgroundColor: isHovered || isExpanded ? '#2a2d2e' : '#1e1e1e',
    borderRadius: '4px',
    border: isExpanded ? '1px solid #4CAF50' : '1px solid transparent',
    cursor: 'pointer',
    transition: 'all 0.2s ease',
    overflow: 'hidden',
  });

  const problemContentStyle = {
    display: 'flex',
    alignItems: 'flex-start',
    gap: '8px',
  };

  const problemDetailsStyle = {
    flex: 1,
  };

  const problemHeaderStyle = {
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'space-between',
    marginBottom: '6px',
  };

  const problemMessageStyle = (severity) => ({
    fontSize: '15px',
    fontWeight: 'bold',
    color: getSeverityColor(severity),
  });

  const problemDescriptionStyle = {
    fontSize: '13px',
    color: '#cccccc',
    lineHeight: '1.5',
  };

  const modalOverlayStyle = {
    position: 'fixed',
    top: 0,
    left: 0,
    right: 0,
    bottom: 0,
    backgroundColor: 'rgba(0, 0, 0, 0.8)',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    zIndex: 1000,
  };

  const modalContentStyle = {
    backgroundColor: '#1e1e1e',
    borderRadius: '8px',
    width: '90%',
    maxWidth: '900px',
    maxHeight: '90vh',
    display: 'flex',
    flexDirection: 'column',
    border: '1px solid #3e3e42',
  };

  const modalHeaderStyle = {
    padding: '16px',
    borderBottom: '1px solid #3e3e42',
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
  };

  const modalTitleStyle = {
    fontSize: '18px',
    fontWeight: 'bold',
    color: '#4CAF50',
  };

  const modalBodyStyle = {
    padding: '16px',
    overflowY: 'auto',
    flex: 1,
    fontSize: '14px',
    color: '#cccccc',
  };

  const modalCloseButtonStyle = {
    backgroundColor: 'transparent',
    border: 'none',
    color: '#cccccc',
    cursor: 'pointer',
    padding: '4px',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    borderRadius: '4px',
  };

  const collapseHeaderStyle = {
    padding: '12px 16px',
    borderBottom: '1px solid #3e3e42',
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    cursor: 'pointer',
    backgroundColor: isControlsCollapsed ? '#1e1e1e' : '#2a2d2e',
    transition: 'background-color 0.2s ease',
  };

  const collapseHeaderTitleStyle = {
    fontSize: '14px',
    fontWeight: 'bold',
    color: '#cccccc',
    display: 'flex',
    alignItems: 'center',
    gap: '8px',
  };

  return (
    <div style={containerStyle}>
      <div 
        style={collapseHeaderStyle}
        onClick={() => setIsControlsCollapsed(!isControlsCollapsed)}
        onMouseEnter={(e) => e.currentTarget.style.backgroundColor = '#2a2d2e'}
        onMouseLeave={(e) => e.currentTarget.style.backgroundColor = isControlsCollapsed ? '#1e1e1e' : '#2a2d2e'}
      >
        <div style={collapseHeaderTitleStyle}>
          {isControlsCollapsed ? <ChevronRight size={16} /> : <ChevronDown size={16} />}
          <span>Analysis Controls</span>
        </div>
        {selectedFile && (
          <div style={{ fontSize: '12px', color: '#858585' }}>
            {selectedFile}
          </div>
        )}
      </div>
      {/* Analysis control */}
      <div style={analysisControlStyle}>
        <div style={fileInfoStyle}>
          <div style={labelStyle}>Selected File:</div>
          <div style={fileNameStyle}>
            {selectedFile || 'No file selected'}
          </div>
        </div>
        
        <button
          onClick={handleStartAnalysis}
          disabled={!selectedFile || isAnalyzing}
          style={buttonStyle(!selectedFile || isAnalyzing)}
          onMouseEnter={(e) => {
            if (!(!selectedFile || isAnalyzing)) {
              e.currentTarget.style.backgroundColor = '#45a049';
            }
          }}
          onMouseLeave={(e) => {
            if (!(!selectedFile || isAnalyzing)) {
              e.currentTarget.style.backgroundColor = '#4CAF50';
            }
          }}
        >
          <Play size={16} />
          {isAnalyzing ? 'Analyzing...' : 'Start Analysing'}
        </button>

        {hasAnalyzed && fullAnalysis && (
          <>
            <button
              onClick={() => setShowFullReport(true)}
              style={buttonStyle(false, '#007acc')}
              onMouseEnter={(e) => e.currentTarget.style.backgroundColor = '#005a9e'}
              onMouseLeave={(e) => e.currentTarget.style.backgroundColor = '#007acc'}
            >
              <FileText size={16} />
              View Full Report
            </button>

            <button
              onClick={downloadAnalysis}
              style={buttonStyle(false, '#6b7280')}
              onMouseEnter={(e) => e.currentTarget.style.backgroundColor = '#4b5563'}
              onMouseLeave={(e) => e.currentTarget.style.backgroundColor = '#6b7280'}
            >
              📥 Download Report
            </button>
          </>
        )}
      </div>

      {/* Problems summary */}
      {hasAnalyzed && (
        <div style={summaryStyle}>
          <div style={summaryItemStyle}>
            <AlertCircle size={14} color="#ef4444" />
            <span>{errorCount}</span>
          </div>
          <div style={summaryItemStyle}>
            <AlertTriangle size={14} color="#eab308" />
            <span>{warningCount}</span>
          </div>
          <div style={summaryItemStyle}>
            <Info size={14} color="#3b82f6" />
            <span>{infoCount}</span>
          </div>
        </div>
      )}

      {/* Problems list */}
      <div style={problemsListStyle}>
        {!hasAnalyzed ? (
          <div style={emptyStateStyle}>
            Select a file and click "Start Analysing" to find potential issues
          </div>
        ) : problems.length === 0 ? (
          <div style={successStateStyle}>
            ✓ No problems found! Code looks good.
          </div>
        ) : (
          <div style={problemsContainerStyle}>
            {problems.map((problem, index) => {
              const isExpanded = expandedIndex === index;
              
              return (
                <div
                  key={index}
                  style={problemItemStyle(hoveredIndex === index, isExpanded)}
                  onMouseEnter={() => setHoveredIndex(index)}
                  onMouseLeave={() => setHoveredIndex(null)}
                >
                  {/* Card Header - Always Visible */}
                  <div 
                    onClick={() => setExpandedIndex(isExpanded ? null : index)}
                    style={{ padding: '12px' }}
                  >
                    <div style={problemContentStyle}>
                      {getSeverityIcon(problem.severity)}
                      <div style={problemDetailsStyle}>
                        <div style={problemHeaderStyle}>
                          <span style={problemMessageStyle(problem.severity)}>
                            {problem.name}
                          </span>
                          {isExpanded ? <ChevronDown size={16} /> : <ChevronRight size={16} />}
                        </div>
                        <div style={problemDescriptionStyle}>
                          {formatText(problem.summary)}
                        </div>
                      </div>
                    </div>
                  </div>

                  {/* Expanded Content */}
                  {isExpanded && (
                    <div style={{
                      padding: '0 12px 12px 40px',
                      borderTop: '1px solid #3e3e42',
                      marginTop: '8px',
                      paddingTop: '12px'
                    }}>
                      {problem.evidence && (
                        <div style={{ marginBottom: '12px' }}>
                          <div style={{
                            fontSize: '13px',
                            fontWeight: 'bold',
                            color: '#eab308',
                            marginBottom: '6px'
                          }}>
                            📋 Evidence:
                          </div>
                          <div style={{
                            fontSize: '12px',
                            color: '#cccccc',
                            lineHeight: '1.6',
                            paddingLeft: '12px',
                            borderLeft: '2px solid #3e3e42',
                          }}>
                            {formatText(problem.evidence)}
                          </div>
                        </div>
                      )}

                      {problem.remedies && problem.remedies.length > 0 && (
                        <div>
                          <div style={{
                            fontSize: '13px',
                            fontWeight: 'bold',
                            color: '#4CAF50',
                            marginBottom: '6px'
                          }}>
                            💡 Recommendations:
                          </div>
                          <div style={{
                            fontSize: '12px',
                            color: '#cccccc',
                            paddingLeft: '12px'
                          }}>
                            {problem.remedies.map((remedy, i) => (
                              <div key={i} style={{
                                display: 'flex',
                                gap: '8px',
                                marginBottom: '6px',
                                lineHeight: '1.5'
                              }}>
                                <span style={{ color: '#4CAF50', fontWeight: 'bold' }}>•</span>
                                <span>{remedy}</span>
                              </div>
                            ))}
                          </div>
                        </div>
                      )}
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        )}
      </div>

      {/* Full Report Modal */}
      {showFullReport && (
        <div style={modalOverlayStyle} onClick={() => setShowFullReport(false)}>
          <div style={modalContentStyle} onClick={(e) => e.stopPropagation()}>
            <div style={modalHeaderStyle}>
              <div style={modalTitleStyle}>
                Ethics Compliance Report - {selectedFile}
              </div>
              <button
                onClick={() => setShowFullReport(false)}
                style={modalCloseButtonStyle}
                onMouseEnter={(e) => e.currentTarget.style.backgroundColor = '#2a2d2e'}
                onMouseLeave={(e) => e.currentTarget.style.backgroundColor = 'transparent'}
              >
                <X size={20} />
              </button>
            </div>
            <div style={modalBodyStyle}>
              {formatAnalysis(fullAnalysis)}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
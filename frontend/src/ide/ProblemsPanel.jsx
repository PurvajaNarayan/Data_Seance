import React, { useState, useEffect } from 'react';
import { Play, AlertCircle, AlertTriangle, Info, FileText, X, ChevronDown, ChevronRight, ThumbsUp, ThumbsDown, Lightbulb, Loader } from 'lucide-react';

export function ProblemsPanel({ selectedFile, fileContents, onFileSelect }) {
  const [problems, setProblems] = useState([]);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [hasAnalyzed, setHasAnalyzed] = useState(false);
  const [hoveredIndex, setHoveredIndex] = useState(null);
  const [expandedIndex, setExpandedIndex] = useState(null);
  const [fullAnalysis, setFullAnalysis] = useState('');
  const [showFullReport, setShowFullReport] = useState(false);
  const [isControlsCollapsed, setIsControlsCollapsed] = useState(false);
  const [localSelectedFile, setLocalSelectedFile] = useState(selectedFile);
  const [cacheKey, setCacheKey] = useState(null);

  // Feedback state
  const [feedback, setFeedback] = useState({});
  const [loadingClarity, setLoadingClarity] = useState({});
  const [reportClarity, setReportClarity] = useState(null);
  const [loadingReportClarity, setLoadingReportClarity] = useState(false);

  const availableFiles = Object.keys(fileContents);

  useEffect(() => {
    if (selectedFile) {
      setLocalSelectedFile(selectedFile);
    }
  }, [selectedFile]);

  const handleFileChange = (e) => {
    const newFile = e.target.value;
    setLocalSelectedFile(newFile);
    if (onFileSelect) {
      onFileSelect(newFile);
    }
  };

  const extractSummary = (description) => {
    const sentences = description.split(/\.\s+/);
    return sentences[0] + (sentences.length > 1 ? '.' : '');
  };

  const handleStartAnalysis = async () => {
    const fileToAnalyze = localSelectedFile || selectedFile;
    if (!fileToAnalyze || !fileContents[fileToAnalyze]) {
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
          file_name: fileToAnalyze,
          file_content: fileContents[fileToAnalyze],
          project_description: 'Data Science Project Analysis'
        })
      });

      const data = await response.json();

      console.log('=== API RESPONSE ===', data);

      if (data.success) {
        const mappedIssues = (data.issues || []).map(issue => ({
          line: 1,
          severity: issue.issue_severity,
          name: issue.issue_name,
          summary: extractSummary(issue.issue_description),
          evidence: issue.issue_evidence,
          remedies: issue.possible_remedies || [],
          rawIssue: issue // Store original for attribute expansion
        }));

        console.log('Mapped Issues:', mappedIssues);

        setProblems(mappedIssues);
        setFullAnalysis(data.full_analysis || '');
        setCacheKey(data.cache_key); // Store cache key for attribute expansion
        setHasAnalyzed(true);
        setFeedback({});
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

  const parseIssuesFromAnalysis = (text) => {
    if (!text) return [];

    const issues = [];
    const lines = text.split('\n');
    let currentIssue = null;
    let currentSection = null;

    for (let i = 0; i < lines.length; i++) {
      const line = lines[i].trim();

      // Detect issue headers (look for patterns like "1. Issue Name" or "#### Issue Name")
      if (line.match(/^\d+\.\s+\*\*.*\*\*/) || line.match(/^####\s+\d+\./)) {
        if (currentIssue) {
          issues.push(currentIssue);
        }
        currentIssue = {
          name: line.replace(/^\d+\.\s+\*\*|\*\*|^####\s+\d+\.\s+/g, '').trim(),
          severity: 'info',
          description: '',
          evidence: '',
          remedies: '',
          fullContent: line + '\n'
        };
        currentSection = 'name';
      }
      // Detect sections within an issue
      else if (currentIssue && line.match(/^\*\*(Severity|Description|Evidence|Recommendation|Remediation).*:\*\*/)) {
        const sectionName = line.match(/^\*\*(Severity|Description|Evidence|Recommendation|Remediation)/)[1].toLowerCase();
        currentSection = sectionName === 'recommendation' || sectionName === 'remediation' ? 'remedies' : sectionName;
        currentIssue.fullContent += line + '\n';

        // Extract severity level
        if (sectionName === 'Severity' && line.includes('🔴')) {
          currentIssue.severity = 'error';
        } else if (sectionName === 'Severity' && line.includes('🟡')) {
          currentIssue.severity = 'warning';
        }
      }
      // Add content to current section
      else if (currentIssue && line.length > 0 && currentSection) {
        currentIssue.fullContent += line + '\n';
        if (currentSection === 'description' || currentSection === 'evidence') {
          currentIssue[currentSection] += (currentIssue[currentSection] ? '\n' : '') + line;
        } else if (currentSection === 'remedies' && line.startsWith('-')) {
          currentIssue[currentSection] += (currentIssue[currentSection] ? '\n' : '') + line;
        }
      }
    }

    if (currentIssue) {
      issues.push(currentIssue);
    }

    return issues;
  };

  const renderFullReportWithExpansion = () => {
    if (!problems || problems.length === 0) {
      return formatAnalysis(fullAnalysis);
    }

    return problems.map((problem, index) => (
      <div key={index} style={{
        border: '1px solid #3e3e42',
        borderRadius: '6px',
        padding: '16px',
        marginBottom: '16px',
        backgroundColor: '#1a1a1a'
      }}>
        {/* Issue Title */}
        <div style={{
          fontSize: '16px',
          fontWeight: 'bold',
          color: '#3b82f6',
          marginBottom: '12px'
        }}>
          {problem.name}
        </div>

        {/* Status */}
        <div style={{ marginBottom: '8px' }}>
          <strong style={{ color: '#eab308' }}>Status:</strong>{' '}
          <span style={{ color: '#cccccc' }}>
            {problem.rawIssue?.issue_status ||
              (problem.severity === 'error' ? 'Violation' :
                problem.severity === 'warning' ? 'Possible Concern' : 'Not Assessable')}
          </span>
        </div>

        {/* Description */}
        {(problem.rawIssue?.issue_description || problem.summary) && (
          <div style={{ marginBottom: '8px' }}>
            <strong style={{ color: '#eab308' }}>Description:</strong>{' '}
            <span style={{ color: '#cccccc', lineHeight: '1.6' }}>
              {problem.rawIssue?.issue_description || problem.summary}
            </span>
          </div>
        )}

        {/* Evidence */}
        {problem.evidence && (
          <div style={{ marginBottom: '8px' }}>
            <strong style={{ color: '#eab308' }}>Evidence:</strong>
            <div style={{
              marginTop: '4px',
              paddingLeft: '12px',
              borderLeft: '2px solid #3e3e42',
              color: '#cccccc',
              lineHeight: '1.6'
            }}>
              {problem.evidence.split('\n').map((line, i) => (
                line.trim().startsWith('-') ? (
                  <div key={i} style={{ display: 'flex', gap: '8px', marginBottom: '4px' }}>
                    <span style={{ color: '#4CAF50' }}>•</span>
                    <span>{line.trim().substring(1).trim()}</span>
                  </div>
                ) : (
                  <div key={i} style={{ marginBottom: '4px' }}>{line}</div>
                )
              ))}
            </div>
          </div>
        )}

        {/* Recommendation */}
        {problem.remedies && problem.remedies.length > 0 && (
          <div style={{ marginBottom: '8px' }}>
            <strong style={{ color: '#eab308' }}>Recommendation:</strong>
            <div style={{
              marginTop: '4px',
              paddingLeft: '12px',
              color: '#cccccc',
              lineHeight: '1.6'
            }}>
              {problem.remedies.map((remedy, i) => (
                <div key={i} style={{ display: 'flex', gap: '8px', marginBottom: '4px' }}>
                  <span style={{ color: '#4CAF50' }}>•</span>
                  <span>{remedy}</span>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Expanded Details - Only show if reportClarity is true and issue has clarity */}
        {reportClarity && problem.structuredExpansion && (
          <div style={{
            marginTop: '16px',
            paddingTop: '16px',
            borderTop: '2px solid rgb(76, 175, 80)'
          }}>
            <div style={{
              fontSize: '14px',
              fontWeight: 'bold',
              color: 'rgb(76, 175, 80)',
              marginBottom: '12px',
              display: 'flex',
              alignItems: 'center',
              gap: '8px'
            }}>
              <Lightbulb size={18} />
              Additional Clarity & Guidance
            </div>
            {renderStructuredExpansion(problem.structuredExpansion)}
          </div>
        )}
      </div>
    ));
  };

  const handleGiveClarity = async (index) => {
    const problem = problems[index];
    const fileToUse = localSelectedFile || selectedFile;
    setLoadingClarity(prev => ({ ...prev, [index]: true }));

    try {
      // Prepare the request payload
      const requestPayload = {
        issue_name: problem.name,
        issue_description: problem.evidence || problem.summary || 'No description available',
        issue_evidence: problem.rawIssue?.issue_evidence || problem.evidence || '',
        file_name: fileToUse,
        file_content: fileContents[fileToUse],
        cache_key: cacheKey // Pass cache key for better context
      };

      console.log('📤 Sending clarity request:', {
        issue_name: requestPayload.issue_name,
        has_cache_key: !!cacheKey,
        has_evidence: !!requestPayload.issue_evidence
      });

      const response = await fetch('http://localhost:5001/api/request-details', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(requestPayload)
      });

      const data = await response.json();

      if (data.success) {
        // Parse the structured expansion
        const parsedExpansion = parseAttributeExpansion(data.additional_details);

        // Update the problem with structured details
        setProblems(prev => {
          const updated = [...prev];
          updated[index] = {
            ...updated[index],
            clarityDetails: data.additional_details,
            structuredExpansion: parsedExpansion,
            hasClarity: true
          };
          return updated;
        });

        setFeedback(prev => ({
          ...prev,
          [index]: { ...prev[index], hasClarity: true }
        }));
      } else {
        console.error('Backend returned error:', data.error);
        alert(`Failed to get clarity: ${data.error}`);
      }
    } catch (error) {
      console.error('Error requesting clarity:', error);
      alert('Could not get clarity. Please try again.');
    } finally {
      setLoadingClarity(prev => ({ ...prev, [index]: false }));
    }
  };

  const parseAttributeExpansion = (text) => {
    // Parse the structured markdown response
    const sections = {};
    const lines = text.split('\n');
    let currentSection = null;
    let currentContent = [];

    for (const line of lines) {
      const trimmed = line.trim();

      // Detect section headers
      if (trimmed.startsWith('- Expanded Rationale:') || trimmed.startsWith('**Expanded Rationale**')) {
        if (currentSection) sections[currentSection] = currentContent.join('\n').trim();
        currentSection = 'rationale';
        currentContent = [trimmed.replace(/^-\s*Expanded Rationale:\s*|^\*\*Expanded Rationale\*\*:?\s*/i, '')];
      } else if (trimmed.startsWith('- Impact & Stakeholders:') || trimmed.startsWith('**Impact & Stakeholders**')) {
        if (currentSection) sections[currentSection] = currentContent.join('\n').trim();
        currentSection = 'impact';
        currentContent = [trimmed.replace(/^-\s*Impact & Stakeholders:\s*|^\*\*Impact & Stakeholders\*\*:?\s*/i, '')];
      } else if (trimmed.startsWith('- Root Cause Hypotheses:') || trimmed.startsWith('**Root Cause Hypotheses**')) {
        if (currentSection) sections[currentSection] = currentContent.join('\n').trim();
        currentSection = 'rootCause';
        currentContent = [trimmed.replace(/^-\s*Root Cause Hypotheses:\s*|^\*\*Root Cause Hypotheses\*\*:?\s*/i, '')];
      } else if (trimmed.startsWith('- Diagnostics to Run:') || trimmed.startsWith('**Diagnostics to Run**')) {
        if (currentSection) sections[currentSection] = currentContent.join('\n').trim();
        currentSection = 'diagnostics';
        currentContent = [trimmed.replace(/^-\s*Diagnostics to Run:\s*|^\*\*Diagnostics to Run\*\*:?\s*/i, '')];
      } else if (trimmed.startsWith('**Detailed Remediation Plan**') || trimmed.startsWith('- Detailed Remediation Plan')) {
        if (currentSection) sections[currentSection] = currentContent.join('\n').trim();
        currentSection = 'remediation';
        currentContent = [];
      } else if (currentSection) {
        currentContent.push(line);
      }
    }

    if (currentSection) {
      sections[currentSection] = currentContent.join('\n').trim();
    }

    return sections;
  };

  const renderStructuredExpansion = (expansion) => {
    if (!expansion) return null;

    const sectionConfig = [
      { key: 'rationale', title: '🎯 Expanded Rationale', color: '#3b82f6' },
      { key: 'impact', title: '👥 Impact & Stakeholders', color: '#ef4444' },
      { key: 'rootCause', title: '🔍 Root Cause Hypotheses', color: '#eab308' },
      { key: 'diagnostics', title: '🔬 Diagnostics to Run', color: '#8b5cf6' },
      { key: 'remediation', title: '🛠️ Detailed Remediation Plan', color: '#10b981' }
    ];

    return (
      <div style={{ marginTop: '12px' }}>
        {sectionConfig.map(({ key, title, color }) =>
          expansion[key] && (
            <div key={key} style={{ marginBottom: '16px' }}>
              <div style={{
                fontSize: '13px',
                fontWeight: 'bold',
                color: color,
                marginBottom: '8px',
                paddingBottom: '4px',
                borderBottom: `2px solid ${color}40`
              }}>
                {title}
              </div>
              <div style={{
                fontSize: '12px',
                color: '#cccccc',
                lineHeight: '1.6',
                paddingLeft: '12px',
                paddingTop: '8px',
                paddingBottom: '8px',
                paddingRight: '8px',
                borderLeft: `3px solid ${color}`,
                backgroundColor: `${color}10`,
                borderRadius: '4px',
                whiteSpace: 'pre-wrap'
              }}>
                {formatText(expansion[key])}
              </div>
            </div>
          )
        )}
      </div>
    );
  };

  const handleThumbsUp = (index) => {
    setFeedback(prev => ({
      ...prev,
      [index]: {
        ...prev[index],
        rating: prev[index]?.rating === 'up' ? null : 'up'
      }
    }));
  };

  const handleThumbsDown = (index) => {
    setFeedback(prev => ({
      ...prev,
      [index]: {
        ...prev[index],
        rating: prev[index]?.rating === 'down' ? null : 'down'
      }
    }));
  };

  const handleGiveReportClarity = async () => {
    const fileToUse = localSelectedFile || selectedFile;
    setLoadingReportClarity(true);

    try {
      // Prepare all issues for batch request
      const issuesForBatch = problems.map(problem => ({
        issue_name: problem.name,
        issue_description: problem.rawIssue?.issue_description || problem.summary || 'No description available',
        issue_evidence: problem.rawIssue?.issue_evidence || problem.evidence || ''
      }));

      console.log(`📦 Sending batch request for ${issuesForBatch.length} issues`);

      // Single batch API call for ALL issues
      const response = await fetch('http://localhost:5001/api/request-details-batch', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          issues: issuesForBatch,
          file_name: fileToUse,
          file_content: fileContents[fileToUse],
          cache_key: cacheKey
        })
      });

      const data = await response.json();

      if (data.success) {
        console.log(`✅ Received batch response with ${Object.keys(data.issue_details).length} expansions`);

        // Parse and update all issues with their expansions
        setProblems(prev => {
          const updated = [...prev];
          updated.forEach((problem, index) => {
            const expansion = data.issue_details[problem.name];
            if (expansion) {
              const parsedExpansion = parseAttributeExpansion(expansion);
              updated[index] = {
                ...updated[index],
                clarityDetails: expansion,
                structuredExpansion: parsedExpansion,
                hasClarity: true
              };
            }
          });
          return updated;
        });

        setReportClarity(true);
      } else {
        console.error('Backend returned error:', data.error);
        alert(`Failed to get clarity: ${data.error}`);
      }
    } catch (error) {
      console.error('Error requesting batch clarity:', error);
      alert('Could not get clarity for all issues. Please try again.');
    } finally {
      setLoadingReportClarity(false);
    }
  };

  const downloadAnalysis = () => {
    const fileName = localSelectedFile || selectedFile || 'analysis';
    const blob = new Blob([fullAnalysis], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `ethics-analysis-${fileName}.txt`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  const formatText = (text) => {
    if (!text) return text;

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
    let currentIssue = [];
    let isInIssue = false;

    const renderIssueBox = (issueElements, boxKey) => {
      return (
        <div key={boxKey} style={{
          border: '1px solid #3e3e42',
          borderRadius: '6px',
          padding: '16px',
          marginBottom: '16px',
          backgroundColor: '#1a1a1a'
        }}>
          {issueElements}
        </div>
      );
    };

    lines.forEach((line, index) => {
      const trimmed = line.trim();

      // Detect the start of an issue (numbered headers like "1. Issue Name" or "#### 1.")
      const isIssueStart = trimmed.match(/^\d+\.\s+[A-Z]/) && !isInIssue;

      // Detect separator or major section (not an issue)
      const isSeparator = trimmed === '---';
      const isMajorSection = trimmed.startsWith('###') && !trimmed.match(/###\s*\d+\./);

      if (isIssueStart) {
        // Save previous issue if exists
        if (currentIssue.length > 0) {
          elements.push(renderIssueBox(currentIssue, key++));
          currentIssue = [];
        }
        isInIssue = true;
      } else if (isSeparator && isInIssue) {
        // End current issue when we hit a separator
        if (currentIssue.length > 0) {
          elements.push(renderIssueBox(currentIssue, key++));
          currentIssue = [];
          isInIssue = false;
        }
        // Don't render the separator itself
        return;
      } else if (isMajorSection) {
        // End current issue and render the major section outside boxes
        if (currentIssue.length > 0) {
          elements.push(renderIssueBox(currentIssue, key++));
          currentIssue = [];
          isInIssue = false;
        }
      }

      // Build the formatted line element
      let lineElement = null;

      if (trimmed.startsWith('###')) {
        lineElement = (
          <div key={key++} style={{
            fontSize: '18px',
            fontWeight: 'bold',
            color: '#4CAF50',
            marginTop: isInIssue ? '0' : '16px',
            marginBottom: '8px'
          }}>
            {trimmed.replace(/^###\s*/, '')}
          </div>
        );
      }
      else if (trimmed.startsWith('####')) {
        lineElement = (
          <div key={key++} style={{
            fontSize: '16px',
            fontWeight: 'bold',
            color: '#3b82f6',
            marginTop: isInIssue ? '0' : '12px',
            marginBottom: '6px'
          }}>
            {trimmed.replace(/^####\s*/, '')}
          </div>
        );
      }
      else if (trimmed.includes('**')) {
        lineElement = (
          <div key={key++} style={{ marginBottom: '4px', lineHeight: '1.6' }}>
            {formatText(trimmed)}
          </div>
        );
      }
      else if (trimmed.startsWith('-')) {
        lineElement = (
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
        lineElement = (
          <hr key={key++} style={{
            border: 'none',
            borderTop: '1px solid #3e3e42',
            margin: '16px 0'
          }} />
        );
      }
      else if (trimmed.length > 0) {
        lineElement = (
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
        lineElement = <div key={key++} style={{ height: '8px' }} />;
      }

      // Add to current issue or directly to elements
      if (isInIssue && lineElement) {
        currentIssue.push(lineElement);
      } else if (lineElement) {
        elements.push(lineElement);
      }
    });

    // Don't forget the last issue
    if (currentIssue.length > 0) {
      elements.push(renderIssueBox(currentIssue, key++));
    }

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

  // Styles (keeping original styles)
  const containerStyle = {
    display: 'flex',
    flexDirection: 'column',
    height: '100%',
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

  const fileDropdownStyle = {
    width: '100%',
    fontSize: '14px',
    padding: '8px 12px',
    backgroundColor: '#1e1e1e',
    border: '1px solid #3e3e42',
    borderRadius: '4px',
    color: '#cccccc',
    cursor: 'pointer',
    outline: 'none',
    appearance: 'none',
    backgroundImage: `url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='12' height='12' viewBox='0 0 12 12'%3E%3Cpath fill='%23cccccc' d='M6 9L1 4h10z'/%3E%3C/svg%3E")`,
    backgroundRepeat: 'no-repeat',
    backgroundPosition: 'right 8px center',
    paddingRight: '32px',
    transition: 'border-color 0.2s ease',
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

  const feedbackButtonStyle = (active = false, color = '#6b7280') => ({
    padding: '6px 12px',
    backgroundColor: active ? color : 'transparent',
    color: active ? '#ffffff' : '#858585',
    border: `1px solid ${active ? color : '#3e3e42'}`,
    borderRadius: '4px',
    fontSize: '13px',
    cursor: 'pointer',
    display: 'flex',
    alignItems: 'center',
    gap: '6px',
    transition: 'all 0.2s ease',
  });

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
        {(localSelectedFile || selectedFile) && (
          <div style={{ fontSize: '12px', color: '#858585' }}>
            {localSelectedFile || selectedFile}
          </div>
        )}
      </div>

      <div style={analysisControlStyle}>
        <div style={fileInfoStyle}>
          <div style={labelStyle}>Selected File:</div>
          <select
            value={localSelectedFile || ''}
            onChange={handleFileChange}
            style={fileDropdownStyle}
          >
            <option value="" disabled>Choose a file...</option>
            {availableFiles.map((file) => (
              <option key={file} value={file}>
                {file}
              </option>
            ))}
          </select>
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
              Download Report
            </button>
          </>
        )}
      </div>

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
              const rating = feedback[index]?.rating;

              return (
                <div
                  key={index}
                  style={problemItemStyle(hoveredIndex === index, isExpanded)}
                  onMouseEnter={() => setHoveredIndex(index)}
                  onMouseLeave={() => setHoveredIndex(null)}
                >
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
                        <div style={{ marginBottom: '12px' }}>
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

                      {problem.structuredExpansion && renderStructuredExpansion(problem.structuredExpansion)}

                      <div style={{
                        display: 'flex',
                        gap: '8px',
                        flexWrap: 'wrap',
                        alignItems: 'center',
                        marginTop: '12px',
                        paddingTop: '12px',
                        borderTop: '1px solid #3e3e42'
                      }}>
                        <button
                          onClick={(e) => {
                            e.stopPropagation();
                            handleGiveClarity(index);
                          }}
                          disabled={loadingClarity[index] || problem.hasClarity}
                          style={{
                            ...feedbackButtonStyle(problem.hasClarity, '#3b82f6'),
                            opacity: (loadingClarity[index] || problem.hasClarity) ? 0.6 : 1,
                            cursor: (loadingClarity[index] || problem.hasClarity) ? 'not-allowed' : 'pointer'
                          }}
                          onMouseEnter={(e) => {
                            if (!loadingClarity[index] && !problem.hasClarity) {
                              e.currentTarget.style.borderColor = '#3b82f6';
                              e.currentTarget.style.backgroundColor = '#1e293b';
                            }
                          }}
                          onMouseLeave={(e) => {
                            if (!loadingClarity[index] && !problem.hasClarity) {
                              e.currentTarget.style.borderColor = '#3e3e42';
                              e.currentTarget.style.backgroundColor = 'transparent';
                            }
                          }}
                        >
                          {loadingClarity[index] ? (
                            <Loader size={16} style={{ animation: 'spin 1s linear infinite' }} />
                          ) : (
                            <Lightbulb size={16} />
                          )}
                          {loadingClarity[index] ? 'Getting Clarity...' : problem.hasClarity ? 'Clarity Added' : 'Give Clarity'}
                        </button>

                        <div style={{ marginLeft: 'auto', display: 'flex', gap: '8px' }}>
                          <button
                            onClick={(e) => {
                              e.stopPropagation();
                              handleThumbsUp(index);
                            }}
                            style={feedbackButtonStyle(rating === 'up', '#4CAF50')}
                            title="Helpful"
                            onMouseEnter={(e) => {
                              if (rating !== 'up') {
                                e.currentTarget.style.borderColor = '#4CAF50';
                                e.currentTarget.style.backgroundColor = '#1a2e1a';
                              }
                            }}
                            onMouseLeave={(e) => {
                              if (rating !== 'up') {
                                e.currentTarget.style.borderColor = '#3e3e42';
                                e.currentTarget.style.backgroundColor = 'transparent';
                              }
                            }}
                          >
                            <ThumbsUp size={16} />
                          </button>
                          <button
                            onClick={(e) => {
                              e.stopPropagation();
                              handleThumbsDown(index);
                            }}
                            style={feedbackButtonStyle(rating === 'down', '#ef4444')}
                            title="Not helpful"
                            onMouseEnter={(e) => {
                              if (rating !== 'down') {
                                e.currentTarget.style.borderColor = '#ef4444';
                                e.currentTarget.style.backgroundColor = '#2e1a1a';
                              }
                            }}
                            onMouseLeave={(e) => {
                              if (rating !== 'down') {
                                e.currentTarget.style.borderColor = '#3e3e42';
                                e.currentTarget.style.backgroundColor = 'transparent';
                              }
                            }}
                          >
                            <ThumbsDown size={16} />
                          </button>
                        </div>
                      </div>
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        )}
      </div>

      {showFullReport && (
        <div style={modalOverlayStyle} onClick={() => setShowFullReport(false)}>
          <div style={modalContentStyle} onClick={(e) => e.stopPropagation()}>
            <div style={modalHeaderStyle}>
              <div style={modalTitleStyle}>
                Ethics Compliance Report - {localSelectedFile || selectedFile}
              </div>
              <div style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
                <button
                  onClick={(e) => {
                    e.stopPropagation();
                    handleGiveReportClarity();
                  }}
                  disabled={loadingReportClarity || reportClarity}
                  style={{
                    padding: '6px 12px',
                    backgroundColor: reportClarity ? 'rgb(76, 175, 80)' : 'transparent',
                    color: reportClarity ? '#ffffff' : '#858585',
                    border: `1px solid ${reportClarity ? 'rgb(76, 175, 80)' : '#3e3e42'}`,
                    borderRadius: '4px',
                    fontSize: '13px',
                    cursor: (loadingReportClarity || reportClarity) ? 'not-allowed' : 'pointer',
                    display: 'flex',
                    alignItems: 'center',
                    gap: '6px',
                    transition: 'all 0.2s ease',
                    opacity: (loadingReportClarity || reportClarity) ? 0.6 : 1,
                  }}
                  onMouseEnter={(e) => {
                    if (!loadingReportClarity && !reportClarity) {
                      e.currentTarget.style.borderColor = 'rgb(76, 175, 80)';
                      e.currentTarget.style.backgroundColor = '#1a2e1a';
                    }
                  }}
                  onMouseLeave={(e) => {
                    if (!loadingReportClarity && !reportClarity) {
                      e.currentTarget.style.borderColor = '#3e3e42';
                      e.currentTarget.style.backgroundColor = 'transparent';
                    }
                  }}
                >
                  {loadingReportClarity ? (
                    <Loader size={16} style={{ animation: 'spin 1s linear infinite' }} />
                  ) : (
                    <Lightbulb size={16} />
                  )}
                  {loadingReportClarity ? 'Getting...' : reportClarity ? 'Added' : 'Give Clarity'}
                </button>
                <button
                  onClick={() => {
                    setShowFullReport(false);
                    setReportClarity(null);
                  }}
                  style={modalCloseButtonStyle}
                  onMouseEnter={(e) => e.currentTarget.style.backgroundColor = '#2a2d2e'}
                  onMouseLeave={(e) => e.currentTarget.style.backgroundColor = 'transparent'}
                >
                  <X size={20} />
                </button>
              </div>
            </div>
            <div style={modalBodyStyle}>
              {renderFullReportWithExpansion()}
            </div>
          </div>
        </div>
      )}

      <style>{`
        @keyframes spin {
          from { transform: rotate(0deg); }
          to { transform: rotate(360deg); }
        }
      `}</style>
    </div>
  );
}
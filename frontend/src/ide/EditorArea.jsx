import React, { useState, useEffect, useRef } from 'react';
import { X } from 'lucide-react';

const initialFileContents = {
  'analysis.py': `import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier

# Load dataset
df = pd.read_csv('data/dataset.csv')

# Display basic information
print(f"Dataset shape: {df.shape}")
print(df.head())

# Data preprocessing
X = df.drop('target', axis=1)
y = df['target']

# Split the data
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42
)

# Train model
model = RandomForestClassifier(n_estimators=100, random_state=42)
model.fit(X_train, y_train)

# Evaluate
train_score = model.score(X_train, y_train)
test_score = model.score(X_test, y_test)

print(f"Training accuracy: {train_score:.4f}")
print(f"Testing accuracy: {test_score:.4f}")

# Feature importance
feature_importance = pd.DataFrame({
    'feature': X.columns,
    'importance': model.feature_importances_
}).sort_values('importance', ascending=False)

print("\\nTop 5 important features:")
print(feature_importance.head())`,

  'model.py': `from sklearn.base import BaseEstimator, TransformerMixin
import numpy as np

class CustomPreprocessor(BaseEstimator, TransformerMixin):
    """Custom preprocessor for data transformation"""
    
    def __init__(self, normalize=True):
        self.normalize = normalize
        self.mean_ = None
        self.std_ = None
    
    def fit(self, X, y=None):
        if self.normalize:
            self.mean_ = np.mean(X, axis=0)
            self.std_ = np.std(X, axis=0)
        return self
    
    def transform(self, X):
        if self.normalize and self.mean_ is not None:
            X_transformed = (X - self.mean_) / (self.std_ + 1e-8)
            return X_transformed
        return X`,

  'utils.py': `import pandas as pd
import numpy as np

def load_and_clean_data(filepath):
    """Load and perform basic cleaning on dataset"""
    df = pd.read_csv(filepath)
    
    # Remove duplicates
    df = df.drop_duplicates()
    
    # Handle missing values
    df = df.fillna(df.mean(numeric_only=True))
    
    return df

def calculate_statistics(data):
    """Calculate basic statistics"""
    stats = {
        'mean': np.mean(data),
        'median': np.median(data),
        'std': np.std(data),
        'min': np.min(data),
        'max': np.max(data)
    }
    return stats`,

  'requirements.txt': `pandas==2.0.0
numpy==1.24.0
matplotlib==3.7.0
scikit-learn==1.2.2
jupyter==1.0.0
seaborn==0.12.0`,

  'dataset.csv': `feature1,feature2,feature3,target
0.5,1.2,3.4,0
1.2,0.8,2.1,1
0.9,1.5,4.2,0
1.8,0.5,1.9,1
0.7,1.1,3.8,0`
};

export function EditorArea({ openFile, dataSciencePanelOpen, onFileContentsChange, externalFileContents }) {
  const [fileContents, setFileContents] = useState(initialFileContents);
  const [content, setContent] = useState('');
  const textareaRef = useRef(null);
  const lineNumbersRef = useRef(null);

  // Merge initial files with external uploaded files
  useEffect(() => {
    if (externalFileContents) {
      setFileContents(prev => ({
        ...prev,
        ...externalFileContents
      }));
    }
  }, [externalFileContents]);

  useEffect(() => {
    if (openFile) {
      setContent(fileContents[openFile] || '// File not found');
    } else {
      setContent('');
    }
  }, [openFile, fileContents]);

  useEffect(() => {
    onFileContentsChange(fileContents);
  }, [fileContents, onFileContentsChange]);

  const handleContentChange = (e) => {
    const newContent = e.target.value;
    setContent(newContent);
    if (openFile) {
      setFileContents(prev => ({
        ...prev,
        [openFile]: newContent
      }));
    }
  };

  const handleScroll = (e) => {
    if (lineNumbersRef.current) {
      lineNumbersRef.current.scrollTop = e.currentTarget.scrollTop;
    }
  };

  const lineCount = content.split('\n').length;
  const lineNumbers = Array.from({ length: lineCount }, (_, i) => i + 1);

  // Styles
  const containerStyle = {
    flex: 1,
    display: 'flex',
    flexDirection: 'column',
    backgroundColor: '#1e1e1e',
  };

  const tabsContainerStyle = {
    height: '36px',
    backgroundColor: '#252526',
    display: 'flex',
    alignItems: 'center',
    borderBottom: '1px solid #3e3e42',
  };

  const tabStyle = {
    display: 'flex',
    alignItems: 'center',
    gap: '8px',
    paddingLeft: '12px',
    paddingRight: '12px',
    paddingTop: '4px',
    paddingBottom: '4px',
    backgroundColor: '#1e1e1e',
    borderRight: '1px solid #3e3e42',
  };

  const tabTextStyle = {
    fontSize: '14px',
    color: '#cccccc',
  };

  const closeButtonStyle = {
    backgroundColor: 'transparent',
    border: 'none',
    borderRadius: '4px',
    padding: '2px',
    cursor: 'pointer',
    color: '#cccccc',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    transition: 'background-color 0.2s ease',
  };

  const editorContentStyle = {
    flex: 1,
    display: 'flex',
    overflow: 'hidden',
  };

  const lineNumbersStyle = {
    backgroundColor: '#1e1e1e',
    color: '#858585',
    textAlign: 'right',
    paddingTop: '16px',
    paddingBottom: '16px',
    paddingRight: '16px',
    paddingLeft: '8px',
    fontFamily: 'monospace',
    fontSize: '14px',
    overflow: 'hidden',
    userSelect: 'none',
    minWidth: '3rem',
  };

  const lineNumberStyle = {
    lineHeight: '1.5rem',
  };

  const textareaStyle = {
    flex: 1,
    backgroundColor: '#1e1e1e',
    color: '#cccccc',
    padding: '16px',
    fontFamily: 'monospace',
    fontSize: '14px',
    resize: 'none',
    outline: 'none',
    overflow: 'auto',
    border: 'none',
    lineHeight: '1.5rem',
    tabSize: 4,
  };

  return (
    <div style={containerStyle}>
      {/* Tabs */}
      <div style={tabsContainerStyle}>
        {openFile && (
          <div style={tabStyle}>
            <span style={tabTextStyle}>{openFile}</span>
            <button
              style={closeButtonStyle}
              onMouseEnter={(e) => {
                e.currentTarget.style.backgroundColor = '#2a2d2e';
              }}
              onMouseLeave={(e) => {
                e.currentTarget.style.backgroundColor = 'transparent';
              }}
            >
              <X size={14} />
            </button>
          </div>
        )}
      </div>

      {/* Editor content */}
      <div style={editorContentStyle}>
        {/* Line numbers */}
        <div ref={lineNumbersRef} style={lineNumbersStyle}>
          {lineNumbers.map((num) => (
            <div key={num} style={lineNumberStyle}>
              {num}
            </div>
          ))}
        </div>

        {/* Editable text area */}
        <textarea
          ref={textareaRef}
          value={content}
          onChange={handleContentChange}
          onScroll={handleScroll}
          spellCheck={false}
          style={textareaStyle}
        />
      </div>
    </div>
  );
}
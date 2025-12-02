"""
Flask API for Ethics Compliance Analysis

This provides REST API endpoints for the frontend to call backend analysis functions.

Author: User
Date: November 30, 2025
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
import traceback
import pandas as pd
from io import StringIO
import re

from backend.main import analyze_ethics

app = Flask(__name__)
CORS(app)  # Enable CORS for frontend requests


@app.route('/api/analyze', methods=['POST'])
def analyze_code():
    """
    Analyze code/data for ethics compliance issues using LLM.
    
    Expects JSON payload:
    {
        "file_name": "analysis.py",
        "file_content": "import pandas...",
        "project_description": "Data science project"
    }
    
    Returns:
    {
        "success": true,
        "project_name": "PIIdata.csv",
        "project_description": "Data Science Project Analysis",
        "issues": [
            {
                "issue_name": "Privacy Violation - PII Exposure",
                "issue_description": "Dataset contains PII without anonymization",
                "issue_severity": "error",
                "possible_remedies": ["Anonymize customer names", "Hash phone numbers"]
            }
        ],
        "full_analysis": "Complete LLM response..."
    }
    """
    try:
        data = request.get_json()
        
        file_name = data.get('file_name', 'unknown_file')
        file_content = data.get('file_content', '')
        project_description = data.get('project_description', 'Data Science Project Analysis')
        
        print(f"\n{'='*60}")
        print(f"🔍 Analyzing: {file_name}")
        print(f"📝 Project: {project_description}")
        print(f"{'='*60}\n")
        
        # Determine file type
        file_ext = file_name.split('.')[-1].lower()
        
        if file_ext == 'csv':
            # Parse CSV and pass to analyze_ethics
            df = pd.read_csv(StringIO(file_content))
            print(f"📊 DataFrame: {df.shape[0]} rows × {df.shape[1]} columns")
            
            # Use your main function
            result = analyze_ethics(
                data=df,
                project_description=project_description,
                prompt_style="structured"
            )
            
        else:
            # For code files
            df = pd.DataFrame({'code_line': file_content.split('\n')})
            
            result = analyze_ethics(
                data=df,
                project_description=f"{project_description} - Code file: {file_name}",
                prompt_style="structured"
            )
        
        # Extract the LLM response
        llm_response = result['llm_response']
        
        # Parse into structured format
        structured_response = parse_llm_to_structured_issues(
            llm_response,
            file_name,
            project_description
        )
        
        print(f"✅ Analysis complete. Found {len(structured_response['issues'])} issues.\n")
        
        return jsonify(structured_response)
    
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': str(e),
            'traceback': traceback.format_exc()
        }), 500


# def parse_llm_to_structured_issues(llm_response, file_name, project_description):
#     """
#     Parse LLM response into structured format.
#     Handles multiple formats: **1. Name** or #### **1. Name**
#     """
#     issues = []
    
#     # Try pattern 1: #### **1. Name**
#     pattern1 = r'####\s+\*\*(\d+)\.\s+(.+?)\*\*(.+?)(?=####|\n###|\Z)'
#     matches = list(re.finditer(pattern1, llm_response, re.DOTALL))
    
#     # Try pattern 2: **1. Name** (without ####)
#     if not matches:
#         pattern2 = r'\*\*(\d+)\.\s+(.+?)\*\*(.+?)(?=\n\*\*\d+\.|\n---|\n###|\Z)'
#         matches = list(re.finditer(pattern2, llm_response, re.DOTALL))
    
#     # Extract recommendations once
#     all_remedies = extract_remedies(llm_response)
    
#     for match in matches:
#         section_num = match.group(1)
#         section_name = match.group(2).strip()
#         section_content = match.group(3).strip()
        
#         # Skip recommendations and missing info sections
#         if any(skip in section_name.lower() for skip in ['missing information', 'recommendation', 'key evidence']):
#             continue
        
#         # Extract details
#         severity = extract_severity(section_content)
#         description = extract_clean_description(section_content)
        
#         # Use section-specific remedies if available, otherwise use all
#         section_remedies = extract_section_remedies(section_content) or all_remedies
        
#         issues.append({
#             'issue_name': f"{section_num}. {section_name}",
#             'issue_description': description,
#             'issue_severity': severity,
#             'possible_remedies': section_remedies[:5]
#         })
    
#     # If still no issues, use fallback
#     if not issues:
#         issues = extract_fallback_issues(llm_response, all_remedies)
    
#     return {
#         'success': True,
#         'project_name': file_name,
#         'project_description': project_description,
#         'issues': issues,
#         'full_analysis': llm_response
#     }

def parse_llm_to_structured_issues(llm_response, file_name, project_description):
    """Parse structured LLM response with consistent format."""
    issues = []
    
    # Pattern: #### **1. Category Name**
    # **Status**: Violation
    # **Issue**: ...
    # **Data Observations**:
    # - observation 1
    # **Recommendation**:
    # - remedy 1
    
    pattern = r'####\s+\*\*(\d+)\.\s+(.+?)\*\*\s*\n\*\*Status\*\*:\s*(.+?)\n\*\*Issue\*\*:\s*(.+?)\n\*\*Data Observations\*\*:\s*\n(.+?)\n\*\*Recommendation\*\*:\s*\n(.+?)(?=\n---|####|\Z)'
    
    matches = re.finditer(pattern, llm_response, re.DOTALL)
    
    for match in matches:
        section_num = match.group(1)
        section_name = match.group(2).strip()
        status = match.group(3).strip()
        issue = match.group(4).strip()
        observations = match.group(5).strip()
        recommendations = match.group(6).strip()
        
        # Determine severity from status
        if 'violation' in status.lower():
            severity = 'error'
        elif 'concern' in status.lower():
            severity = 'warning'
        else:
            severity = 'info'
        
        # Extract remedy bullet points
        remedies = [
            line.strip().lstrip('- ').strip() 
            for line in recommendations.split('\n') 
            if line.strip().startswith('-')
        ]
        
        issues.append({
            'issue_name': f"{section_num}. {section_name}",
            'issue_description': issue,
            'issue_severity': severity,
            'issue_evidence': observations,  # This is now "Data Observations"
            'possible_remedies': remedies[:5]
        })
    
    return {
        'success': True,
        'project_name': file_name,
        'project_description': project_description,
        'issues': issues,
        'full_analysis': llm_response
    }


def extract_severity(content):
    """Determine severity from content."""
    content_lower = content.lower()
    
    # Check for explicit severity markers
    if '**violation**:' in content_lower or '**clear violation**' in content_lower:
        return 'error'
    elif '**violation' in content_lower and 'not assessable' not in content_lower:
        return 'error'
    elif '**possible concern' in content_lower or '**concern' in content_lower:
        return 'warning'
    elif '**risk' in content_lower or 'warning' in content_lower:
        return 'warning'
    elif '**not assessable' in content_lower or 'not assessable' in content_lower:
        return 'info'
    
    # Default based on keywords
    if any(word in content_lower for word in ['critical', 'severe', 'pii exposure', 'violat']):
        return 'error'
    elif any(word in content_lower for word in ['concern', 'risk', 'should']):
        return 'warning'
    else:
        return 'info'


def extract_clean_description(content):
    """Extract clean description from section content."""
    lines = content.split('\n')
    description_parts = []
    
    # Look for main violation/concern statement
    for line in lines:
        line = line.strip()
        
        # Skip empty lines and markers
        if not line or line in ['---', '**Evidence**:', '**Evidence Gaps**:']:
            continue
        
        # Get violation/concern statement
        if line.startswith('**Violation') or line.startswith('**Possible Concern') or line.startswith('**Not Assessable'):
            continue
        
        # Get bullet points with evidence
        if line.startswith('-'):
            clean_line = line.lstrip('- ').strip()
            if len(clean_line) > 20 and '**' in clean_line:
                # Extract text between ** markers
                clean_line = re.sub(r'\*\*(.+?)\*\*:', r'\1:', clean_line)
            description_parts.append(clean_line)
    
    # Combine first 2-3 meaningful points
    return ' '.join(description_parts[:3]) if description_parts else content[:200]


def extract_remedies(llm_response):
    """Extract recommendations from the full response."""
    remedies = []
    
    # Find the Recommendations section
    if '### **Recommendations**' in llm_response:
        rec_section = llm_response.split('### **Recommendations**')[1].split('###')[0]
    elif '### Recommendations' in llm_response:
        rec_section = llm_response.split('### Recommendations')[1].split('###')[0]
    else:
        return ['See full analysis for recommendations']
    
    # Extract numbered recommendations
    numbered_pattern = r'\d+\.\s+\*\*(.+?)\*\*:?\s*\n\s*-\s+(.+?)(?=\n\d+\.|\n\n|\Z)'
    matches = re.finditer(numbered_pattern, rec_section, re.DOTALL)
    
    for match in matches:
        category = match.group(1).strip()
        items = match.group(2).strip()
        
        # Split by bullet points
        for line in items.split('\n'):
            line = line.strip()
            if line.startswith('-'):
                remedy = line.lstrip('- ').strip()
                if len(remedy) > 10:
                    remedies.append(remedy)
    
    # Fallback: just get all bullet points from recommendations
    if not remedies:
        for line in rec_section.split('\n'):
            if line.strip().startswith('-'):
                remedy = line.strip().lstrip('- ').strip()
                if len(remedy) > 10:
                    remedies.append(remedy)
    
    return remedies[:6] if remedies else ['Review full analysis for remediation steps']


def extract_section_remedies(section_content):
    """Extract remedies specific to a section."""
    remedies = []
    
    # Look for **Recommendation**: pattern
    if '**Recommendation' in section_content:
        rec_parts = section_content.split('**Recommendation')
        if len(rec_parts) > 1:
            rec_text = rec_parts[1].split('\n')[0]
            for line in rec_parts[1].split('\n'):
                if line.strip().startswith('-'):
                    remedy = line.strip().lstrip('- ').strip()
                    if len(remedy) > 10:
                        remedies.append(remedy)
    
    return remedies


def extract_fallback_issues(llm_response, all_remedies):
    """Improved fallback parser."""
    issues = []
    
    # Look for numbered sections manually
    lines = llm_response.split('\n')
    current_section = None
    current_content = []
    
    for line in lines:
        # Check if this is a section header
        if re.match(r'\*\*\d+\.\s+', line.strip()):
            # Save previous section
            if current_section and current_content:
                section_text = '\n'.join(current_content)
                severity = extract_severity(section_text)
                description = extract_clean_description(section_text)
                
                issues.append({
                    'issue_name': current_section,
                    'issue_description': description,
                    'issue_severity': severity,
                    'possible_remedies': all_remedies[:5]
                })
            
            # Start new section
            current_section = line.strip().replace('**', '').strip()
            current_content = []
        elif current_section:
            current_content.append(line)
    
    # Save last section
    if current_section and current_content:
        section_text = '\n'.join(current_content)
        severity = extract_severity(section_text)
        description = extract_clean_description(section_text)
        
        # Skip if it's recommendations or missing info
        if not any(skip in current_section.lower() for skip in ['recommendation', 'missing information', 'key evidence']):
            issues.append({
                'issue_name': current_section,
                'issue_description': description,
                'issue_severity': severity,
                'possible_remedies': all_remedies[:5]
            })
    
    return issues if issues else [{
        'issue_name': 'Ethics Compliance Analysis',
        'issue_description': 'Analysis completed. See full report for details.',
        'issue_severity': 'info',
        'possible_remedies': ['Review the complete analysis report']
    }]


@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'service': 'Ethics Compliance API',
        'version': '1.0.0'
    })


if __name__ == '__main__':
    print("\n" + "="*60)
    print("🚀 DATA SEANCE - Ethics Compliance API")
    print("="*60)
    print(f"📍 Server: http://localhost:5001")
    print(f"💚 Health: http://localhost:5001/api/health")
    print(f"🔍 Analyze: POST http://localhost:5001/api/analyze")
    print("="*60 + "\n")
    print("✨ Ready to analyze files from frontend!")
    print("Press Ctrl+C to stop\n")
    
    app.run(debug=True, port=5001, host='0.0.0.0')
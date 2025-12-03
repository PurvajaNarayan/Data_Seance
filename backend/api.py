# """
# Flask API for Ethics Compliance Analysis

# This provides REST API endpoints for the frontend to call backend analysis functions.

# Author: User
# Date: November 30, 2025
# """

# from flask import Flask, request, jsonify
# from flask_cors import CORS
# import traceback
# import pandas as pd
# from io import StringIO
# import re

# from backend.main import analyze_ethics, elaborate_attribute
# from backend.llm_helpers import describe_pandas_dataset

# app = Flask(__name__)
# CORS(app)  # Enable CORS for frontend requests

# # Cache for storing analysis context
# analysis_cache = {}


# @app.route('/api/analyze', methods=['POST'])
# def analyze_code():
#     """
#     Analyze code/data for ethics compliance issues using LLM.
    
#     Expects JSON payload:
#     {
#         "file_name": "analysis.py",
#         "file_content": "import pandas...",
#         "project_description": "Data science project"
#     }
    
#     Returns:
#     {
#         "success": true,
#         "project_name": "PIIdata.csv",
#         "project_description": "Data Science Project Analysis",
#         "cache_key": "file_hash_12345",  # NEW: for attribute expansion
#         "issues": [
#             {
#                 "issue_name": "Privacy Violation - PII Exposure",
#                 "issue_description": "Dataset contains PII without anonymization",
#                 "issue_severity": "error",
#                 "issue_evidence": "Column 'email' contains 1000 email addresses",
#                 "possible_remedies": ["Anonymize customer names", "Hash phone numbers"]
#             }
#         ],
#         "full_analysis": "Complete LLM response..."
#     }
#     """
#     try:
#         data = request.get_json()
        
#         file_name = data.get('file_name', 'unknown_file')
#         file_content = data.get('file_content', '')
#         project_description = data.get('project_description', 'Data Science Project Analysis')
        
#         print(f"\n{'='*60}")
#         print(f"🔍 Analyzing: {file_name}")
#         print(f"📝 Project: {project_description}")
#         print(f"{'='*60}\n")
        
#         # Determine file type
#         file_ext = file_name.split('.')[-1].lower()
        
#         if file_ext == 'csv':
#             # Parse CSV and pass to analyze_ethics
#             df = pd.read_csv(StringIO(file_content))
#             print(f"📊 DataFrame: {df.shape[0]} rows × {df.shape[1]} columns")
            
#             # Use your main function
#             result = analyze_ethics(
#                 data=df,
#                 project_description=project_description,
#                 prompt_style="structured"
#             )
            
#             # Generate and cache context for attribute expansion
#             cache_key = f"{file_name}_{hash(file_content)}"
#             data_desc = describe_pandas_dataset(df)
            
#             analysis_cache[cache_key] = {
#                 'df': df,
#                 'data_desc': data_desc,
#                 'model_desc': None,  # No model in dataset-only analysis
#                 'guidelines': result.get('guidelines', ''),
#                 'project_description': project_description,
#                 'file_name': file_name
#             }
#             print(f"💾 Cached context with key: {cache_key}")
            
#         else:
#             # For code files
#             df = pd.DataFrame({'code_line': file_content.split('\n')})
            
#             result = analyze_ethics(
#                 data=df,
#                 project_description=f"{project_description} - Code file: {file_name}",
#                 prompt_style="structured"
#             )
            
#             # Cache for code files too
#             cache_key = f"{file_name}_{hash(file_content)}"
#             data_desc = describe_pandas_dataset(df)
            
#             analysis_cache[cache_key] = {
#                 'df': df,
#                 'data_desc': data_desc,
#                 'model_desc': None,
#                 'guidelines': result.get('guidelines', ''),
#                 'project_description': project_description,
#                 'file_name': file_name
#             }
        
#         # Extract the LLM response
#         llm_response = result['llm_response']
        
#         # Parse into structured format
#         structured_response = parse_llm_to_structured_issues(
#             llm_response,
#             file_name,
#             project_description
#         )
        
#         # Add cache_key to response
#         structured_response['cache_key'] = cache_key
        
#         print(f"✅ Analysis complete. Found {len(structured_response['issues'])} issues.\n")
        
#         return jsonify(structured_response)
    
#     except Exception as e:
#         print(f"❌ Error: {str(e)}")
#         traceback.print_exc()
#         return jsonify({
#             'success': False,
#             'error': str(e),
#             'traceback': traceback.format_exc()
#         }), 500


# @app.route('/api/request-details', methods=['POST'])
# def request_attribute_details():
#     """
#     Enhanced endpoint that uses elaborate_attribute() for richer expansion.
#     This is called when user clicks "Give Clarity" on an issue.
    
#     Expects JSON payload:
#     {
#         "issue_name": "1. Protected Attributes",
#         "issue_description": "Description of the issue...",
#         "file_name": "data.csv",
#         "file_content": "csv content...",
#         "cache_key": "file_hash_12345"  # Optional: uses cached context if available
#     }
    
#     Returns:
#     {
#         "success": true,
#         "additional_details": "Structured markdown with expansion sections..."
#     }
#     """
#     try:
#         data = request.get_json()
#         issue_name = data.get('issue_name', 'Unknown Issue')
#         issue_description = data.get('issue_description', '')
#         issue_evidence = data.get('issue_evidence', '')
#         file_name = data.get('file_name', 'unknown')
#         file_content = data.get('file_content', '')
#         cache_key = data.get('cache_key')
        
#         print(f"\n{'='*60}")
#         print(f"💡 Expanding attribute: {issue_name}")
#         print(f"📂 File: {file_name}")
#         print(f"🔑 Cache key: {cache_key}")
#         print(f"{'='*60}\n")
        
#         # Reconstruct the attribute response block from the issue
#         # This mimics the structured format the LLM expects
#         attr_response = f"""**{issue_name}**
# **Description**: {issue_description}

# **Evidence**: 
# {issue_evidence if issue_evidence else 'See analysis for details'}"""
        
#         # Get or create context
#         if cache_key and cache_key in analysis_cache:
#             print("✅ Using cached context")
#             context = analysis_cache[cache_key]
#             data_desc = context['data_desc']
#             model_desc = context.get('model_desc', 'No model provided (dataset-only analysis)')
#             guidelines = context['guidelines']
#             proj_desc = context['project_description']
#         else:
#             print("⚠️ No cache found, regenerating context...")
#             # Parse file content and regenerate context
#             file_ext = file_name.split('.')[-1].lower()
            
#             if file_ext == 'csv':
#                 df = pd.read_csv(StringIO(file_content))
#             else:
#                 df = pd.DataFrame({'code_line': file_content.split('\n')})
            
#             # Load default guidelines
#             from pathlib import Path
#             guidelines_path = Path(__file__).parent.parent / 'assets' / 'guidelines' / 'guidelines_shorter.txt'
            
#             if guidelines_path.exists():
#                 with open(guidelines_path, 'r') as f:
#                     guidelines = f.read()
#             else:
#                 print("⚠️ Guidelines file not found, using empty guidelines")
#                 guidelines = "Ethical AI guidelines not available."
            
#             data_desc = describe_pandas_dataset(df)
#             model_desc = "No model provided (dataset-only analysis)"
#             proj_desc = "Data Science Project"
        
#         print("🤖 Calling elaborate_attribute()...")
        
#         # Call elaborate_attribute for rich expansion
#         expanded_details = elaborate_attribute(
#             proj_desc=proj_desc,
#             data_desc=data_desc,
#             model_desc=model_desc,
#             attr_response=attr_response,
#             guidelines=guidelines,
#             temperature=0.7,
#             model_id=None
#         )
        
#         print("✅ Attribute expansion complete\n")
        
#         return jsonify({
#             'success': True,
#             'additional_details': expanded_details
#         })
        
#     except Exception as e:
#         print(f"❌ Error expanding attribute: {str(e)}")
#         traceback.print_exc()
#         return jsonify({
#             'success': False,
#             'error': str(e),
#             'traceback': traceback.format_exc()
#         }), 500


# def parse_llm_to_structured_issues(llm_response, file_name, project_description):
#     """Parse structured LLM response - handles multiple format variations."""
#     issues = []
    
#     # STEP 1: Clean up the response
#     llm_response = llm_response.strip()
#     if llm_response.startswith('```'):
#         llm_response = llm_response[3:].lstrip()
#         if llm_response.endswith('```'):
#             llm_response = llm_response[:-3].rstrip()
    
#     # STEP 2: Use fallback parser directly (more reliable for varied formats)
#     issues = parse_fallback(llm_response)
    
#     print(f"📊 Parsed {len(issues)} issues successfully")
#     return {
#         'success': True,
#         'project_name': file_name,
#         'project_description': project_description,
#         'issues': issues,
#         'full_analysis': llm_response
#     }


# def parse_fallback(llm_response):
#     """Robust fallback parser that handles various formats."""
#     issues = []
    
#     # Split by numbered sections (handles "1. Name" and "1. **Name**")
#     # Use lookahead to keep the number in the split
#     parts = re.split(r'\n(?=\d+\.\s+)', llm_response)
    
#     for part in parts:
#         part = part.strip()
#         if not part:
#             continue
            
#         # Check if this part starts with a number
#         number_match = re.match(r'^(\d+)\.\s+', part)
#         if not number_match:
#             continue
            
#         try:
#             section_num = number_match.group(1)
            
#             # Extract section name (first line, remove markdown)
#             first_line_match = re.match(r'^\d+\.\s+\*{0,2}(.+?)\*{0,2}\s*\n', part)
#             section_name = first_line_match.group(1).strip() if first_line_match else 'Unknown'
            
#             # Extract status (case-insensitive, handle bold)
#             status_match = re.search(r'Status:\s*\*{0,2}(.+?)\*{0,2}\s*\n', part, re.IGNORECASE)
#             status = status_match.group(1).strip() if status_match else 'Unknown'
            
#             # Determine severity
#             status_lower = status.lower()
#             if 'violation' in status_lower:
#                 severity = 'error'
#             elif 'concern' in status_lower:
#                 severity = 'warning'
#             else:
#                 severity = 'info'
            
#             # Extract description
#             desc_match = re.search(r'Description:\s*(.+?)(?=\n\s*Evidence:|\Z)', part, re.DOTALL | re.IGNORECASE)
#             description = desc_match.group(1).strip() if desc_match else 'No description available'
            
#             # Extract evidence bullets (stop at Recommendation or ---)
#             evidence_match = re.search(
#                 r'Evidence:\s*\n(.+?)(?=\n\s*\*{0,2}Recommendation|\n\s*---|\Z)', 
#                 part, 
#                 re.DOTALL | re.IGNORECASE
#             )
#             if evidence_match:
#                 evidence_text = evidence_match.group(1)
#                 evidence_lines = []
#                 for line in evidence_text.split('\n'):
#                     line = line.strip()
#                     # Include lines starting with '-' and exclude Coherence/Recommendation lines
#                     if line.startswith('-') and not any(
#                         skip in line.lower() 
#                         for skip in ['coherence', 'recommendation', 'cross-cutting']
#                     ):
#                         evidence_lines.append(line.lstrip('- ').strip())
#                 evidence = '\n'.join(evidence_lines) if evidence_lines else evidence_text.strip()
#             else:
#                 evidence = 'No evidence provided'
            
#             # Extract recommendations (handle **Recommendation**: format)
#             rec_match = re.search(
#                 r'\*{0,2}Recommendation\*{0,2}:\s*(.+?)(?=\n\s*---|\n\d+\.|\Z)', 
#                 part, 
#                 re.DOTALL | re.IGNORECASE
#             )
#             if rec_match:
#                 rec_text = rec_match.group(1).strip()
#                 remedies = []
                
#                 # Look for bullet points first
#                 for line in rec_text.split('\n'):
#                     line = line.strip()
#                     if line.startswith('-'):
#                         remedies.append(line.lstrip('- ').strip())
                
#                 # If no bullets, check for priority-prefixed recommendations
#                 if not remedies:
#                     # Match patterns like: (Immediate) Do this. (Short-term) Do that.
#                     priority_pattern = r'\((?:Immediate|Short-term|Long-term)\)\s*([^(]+?)(?=\((?:Immediate|Short-term|Long-term)\)|\Z)'
#                     priority_matches = re.finditer(priority_pattern, rec_text, re.DOTALL | re.IGNORECASE)
#                     for match in priority_matches:
#                         remedy = match.group(1).strip()
#                         if remedy:
#                             remedies.append(remedy)
                
#                 # If still no remedies, use whole text (cleaned)
#                 if not remedies and rec_text:
#                     # Clean up and take first meaningful sentence
#                     cleaned = rec_text.replace('\n', ' ').strip()
#                     if len(cleaned) > 10:
#                         remedies = [cleaned[:200]]  # Limit length
                        
#             else:
#                 remedies = []
            
#             if not remedies:
#                 remedies = ['See full analysis for recommendations']
            
#             issues.append({
#                 'issue_name': f"{section_num}. {section_name}",
#                 'issue_description': description,
#                 'issue_severity': severity,
#                 'issue_evidence': evidence,
#                 'possible_remedies': remedies[:5]
#             })
            
#         except Exception as e:
#             print(f"❌ Error parsing section {section_num}: {e}")
#             import traceback
#             traceback.print_exc()
#             continue
    
#     if not issues:
#         print("⚠️ Parser found no issues. Returning generic issue.")
#         return [{
#             'issue_name': 'Analysis Complete',
#             'issue_description': 'Ethics analysis completed. See full report for details.',
#             'issue_severity': 'info',
#             'issue_evidence': 'Analysis was performed but could not be parsed into structured format.',
#             'possible_remedies': ['Review the complete analysis report']
#         }]
    
#     return issues


# @app.route('/api/health', methods=['GET'])
# def health_check():
#     """Health check endpoint"""
#     return jsonify({
#         'status': 'healthy',
#         'service': 'Ethics Compliance API',
#         'version': '1.1.0',  # Updated version
#         'features': [
#             'ethics_analysis',
#             'attribute_expansion',
#             'context_caching'
#         ]
#     })


# @app.route('/api/cache/status', methods=['GET'])
# def cache_status():
#     """Check cache status - useful for debugging"""
#     return jsonify({
#         'cached_analyses': len(analysis_cache),
#         'cache_keys': list(analysis_cache.keys())
#     })


# @app.route('/api/cache/clear', methods=['POST'])
# def clear_cache():
#     """Clear the analysis cache - useful for development"""
#     global analysis_cache
#     cache_size = len(analysis_cache)
#     analysis_cache = {}
#     return jsonify({
#         'success': True,
#         'message': f'Cleared {cache_size} cached analyses'
#     })


# if __name__ == '__main__':
#     print("\n" + "="*60)
#     print("🚀 DATA SEANCE - Ethics Compliance API v1.1")
#     print("="*60)
#     print(f"📍 Server: http://localhost:5001")
#     print(f"💚 Health: http://localhost:5001/api/health")
#     print(f"🔍 Analyze: POST http://localhost:5001/api/analyze")
#     print(f"💡 Expand: POST http://localhost:5001/api/request-details")
#     print(f"📊 Cache Status: GET http://localhost:5001/api/cache/status")
#     print("="*60 + "\n")
#     print("✨ Ready to analyze files from frontend!")
#     print("🔑 Context caching enabled for attribute expansion")
#     print("Press Ctrl+C to stop\n")
    
#     app.run(debug=True, port=5001, host='0.0.0.0')

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

from backend.main import analyze_ethics, elaborate_attribute
from backend.llm_helpers import describe_pandas_dataset

app = Flask(__name__)
CORS(app)  # Enable CORS for frontend requests

# Cache for storing analysis context
analysis_cache = {}


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
        "cache_key": "file_hash_12345",  # NEW: for attribute expansion
        "issues": [
            {
                "issue_name": "Privacy Violation - PII Exposure",
                "issue_description": "Dataset contains PII without anonymization",
                "issue_severity": "error",
                "issue_evidence": "Column 'email' contains 1000 email addresses",
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
            
            # Generate and cache context for attribute expansion
            cache_key = f"{file_name}_{hash(file_content)}"
            data_desc = describe_pandas_dataset(df)
            
            analysis_cache[cache_key] = {
                'df': df,
                'data_desc': data_desc,
                'model_desc': None,  # No model in dataset-only analysis
                'guidelines': result.get('guidelines', ''),
                'project_description': project_description,
                'file_name': file_name
            }
            print(f"💾 Cached context with key: {cache_key}")
            
        else:
            # For code files
            df = pd.DataFrame({'code_line': file_content.split('\n')})
            
            result = analyze_ethics(
                data=df,
                project_description=f"{project_description} - Code file: {file_name}",
                prompt_style="structured"
            )
            
            # Cache for code files too
            cache_key = f"{file_name}_{hash(file_content)}"
            data_desc = describe_pandas_dataset(df)
            
            analysis_cache[cache_key] = {
                'df': df,
                'data_desc': data_desc,
                'model_desc': None,
                'guidelines': result.get('guidelines', ''),
                'project_description': project_description,
                'file_name': file_name
            }
        
        # Extract the LLM response
        llm_response = result['llm_response']
        
        # Parse into structured format
        structured_response = parse_llm_to_structured_issues(
            llm_response,
            file_name,
            project_description
        )
        
        # Add cache_key to response
        structured_response['cache_key'] = cache_key
        
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


@app.route('/api/request-details', methods=['POST'])
def request_attribute_details():
    """
    Enhanced endpoint that uses elaborate_attribute() for richer expansion.
    This is called when user clicks "Give Clarity" on an issue.
    
    Expects JSON payload:
    {
        "issue_name": "1. Protected Attributes",
        "issue_description": "Description of the issue...",
        "file_name": "data.csv",
        "file_content": "csv content...",
        "cache_key": "file_hash_12345"  # Optional: uses cached context if available
    }
    
    Returns:
    {
        "success": true,
        "additional_details": "Structured markdown with expansion sections..."
    }
    """
    try:
        data = request.get_json()
        issue_name = data.get('issue_name', 'Unknown Issue')
        issue_description = data.get('issue_description', '')
        issue_evidence = data.get('issue_evidence', '')
        file_name = data.get('file_name', 'unknown')
        file_content = data.get('file_content', '')
        cache_key = data.get('cache_key')
        
        print(f"\n{'='*60}")
        print(f"💡 Expanding attribute: {issue_name}")
        print(f"📂 File: {file_name}")
        print(f"🔑 Cache key: {cache_key}")
        print(f"{'='*60}\n")
        
        # Reconstruct the attribute response block from the issue
        # This mimics the structured format the LLM expects
        attr_response = f"""**{issue_name}**
**Description**: {issue_description}

**Evidence**: 
{issue_evidence if issue_evidence else 'See analysis for details'}"""
        
        # Get or create context
        if cache_key and cache_key in analysis_cache:
            print("✅ Using cached context")
            context = analysis_cache[cache_key]
            data_desc = context.get('data_desc', 'Dataset information not available')
            model_desc = context.get('model_desc') or 'No model provided (dataset-only analysis)'
            guidelines = context.get('guidelines', 'Ethical AI guidelines not available')
            proj_desc = context.get('project_description', 'Data Science Project')
        else:
            print("⚠️ No cache found, regenerating context...")
            # Parse file content and regenerate context
            file_ext = file_name.split('.')[-1].lower()
            
            if file_ext == 'csv':
                df = pd.read_csv(StringIO(file_content))
            else:
                df = pd.DataFrame({'code_line': file_content.split('\n')})
            
            # Load default guidelines
            from pathlib import Path
            guidelines_path = Path(__file__).parent.parent / 'assets' / 'guidelines' / 'guidelines_shorter.txt'
            
            if guidelines_path.exists():
                with open(guidelines_path, 'r') as f:
                    guidelines = f.read()
            else:
                print("⚠️ Guidelines file not found, using empty guidelines")
                guidelines = "Ethical AI guidelines not available."
            
            data_desc = describe_pandas_dataset(df) or "Dataset information not available"
            model_desc = "No model provided (dataset-only analysis)"
            proj_desc = "Data Science Project"
        
        # Ensure all parameters are strings, not None
        data_desc = str(data_desc) if data_desc else "Dataset information not available"
        model_desc = str(model_desc) if model_desc else "No model provided (dataset-only analysis)"
        guidelines = str(guidelines) if guidelines else "Ethical AI guidelines not available"
        proj_desc = str(proj_desc) if proj_desc else "Data Science Project"
        attr_response = str(attr_response) if attr_response else "Issue information not available"
        
        # Debug logging
        print("📋 Parameters for elaborate_attribute:")
        print(f"  - proj_desc length: {len(proj_desc)} chars")
        print(f"  - data_desc length: {len(data_desc)} chars")
        print(f"  - model_desc length: {len(model_desc)} chars")
        print(f"  - guidelines length: {len(guidelines)} chars")
        print(f"  - attr_response length: {len(attr_response)} chars")
        
        print("🤖 Calling elaborate_attribute()...")
        
        # Call elaborate_attribute for rich expansion
        expanded_details = elaborate_attribute(
            proj_desc=proj_desc,
            data_desc=data_desc,
            model_desc=model_desc,
            attr_response=attr_response,
            guidelines=guidelines,
            temperature=0.7,
            model_id=None
        )
        
        print("✅ Attribute expansion complete\n")
        
        return jsonify({
            'success': True,
            'additional_details': expanded_details
        })
        
    except Exception as e:
        print(f"❌ Error expanding attribute: {str(e)}")
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': str(e),
            'traceback': traceback.format_exc()
        }), 500


def parse_llm_to_structured_issues(llm_response, file_name, project_description):
    """Parse structured LLM response - handles multiple format variations."""
    issues = []
    
    # STEP 1: Clean up the response
    llm_response = llm_response.strip()
    if llm_response.startswith('```'):
        llm_response = llm_response[3:].lstrip()
        if llm_response.endswith('```'):
            llm_response = llm_response[:-3].rstrip()
    
    # STEP 2: Use fallback parser directly (more reliable for varied formats)
    issues = parse_fallback(llm_response)
    
    print(f"📊 Parsed {len(issues)} issues successfully")
    return {
        'success': True,
        'project_name': file_name,
        'project_description': project_description,
        'issues': issues,
        'full_analysis': llm_response
    }


def parse_fallback(llm_response):
    """Robust fallback parser that handles various formats."""
    issues = []
    
    # Split by numbered sections (handles "1. Name" and "1. **Name**")
    # Use lookahead to keep the number in the split
    parts = re.split(r'\n(?=\d+\.\s+)', llm_response)
    
    for part in parts:
        part = part.strip()
        if not part:
            continue
            
        # Check if this part starts with a number
        number_match = re.match(r'^(\d+)\.\s+', part)
        if not number_match:
            continue
            
        try:
            section_num = number_match.group(1)
            
            # Extract section name (first line, remove markdown)
            first_line_match = re.match(r'^\d+\.\s+\*{0,2}(.+?)\*{0,2}\s*\n', part)
            section_name = first_line_match.group(1).strip() if first_line_match else 'Unknown'
            
            # Extract status (case-insensitive, handle bold)
            status_match = re.search(r'Status:\s*\*{0,2}(.+?)\*{0,2}\s*\n', part, re.IGNORECASE)
            status = status_match.group(1).strip() if status_match else 'Unknown'
            
            # Determine severity
            status_lower = status.lower()
            if 'violation' in status_lower:
                severity = 'error'
            elif 'concern' in status_lower:
                severity = 'warning'
            else:
                severity = 'info'
            
            # Extract description
            desc_match = re.search(r'Description:\s*(.+?)(?=\n\s*Evidence:|\Z)', part, re.DOTALL | re.IGNORECASE)
            description = desc_match.group(1).strip() if desc_match else 'No description available'
            
            # Extract evidence bullets (stop at Recommendation or ---)
            evidence_match = re.search(
                r'Evidence:\s*\n(.+?)(?=\n\s*\*{0,2}Recommendation|\n\s*---|\Z)', 
                part, 
                re.DOTALL | re.IGNORECASE
            )
            if evidence_match:
                evidence_text = evidence_match.group(1)
                evidence_lines = []
                for line in evidence_text.split('\n'):
                    line = line.strip()
                    # Include lines starting with '-' and exclude Coherence/Recommendation lines
                    if line.startswith('-') and not any(
                        skip in line.lower() 
                        for skip in ['coherence', 'recommendation', 'cross-cutting']
                    ):
                        evidence_lines.append(line.lstrip('- ').strip())
                evidence = '\n'.join(evidence_lines) if evidence_lines else evidence_text.strip()
            else:
                evidence = 'No evidence provided'
            
            # Extract recommendations (handle **Recommendation**: format)
            rec_match = re.search(
                r'\*{0,2}Recommendation\*{0,2}:\s*(.+?)(?=\n\s*---|\n\d+\.|\Z)', 
                part, 
                re.DOTALL | re.IGNORECASE
            )
            if rec_match:
                rec_text = rec_match.group(1).strip()
                remedies = []
                
                # Look for bullet points first
                for line in rec_text.split('\n'):
                    line = line.strip()
                    if line.startswith('-'):
                        remedies.append(line.lstrip('- ').strip())
                
                # If no bullets, check for priority-prefixed recommendations
                if not remedies:
                    # Match patterns like: (Immediate) Do this. (Short-term) Do that.
                    priority_pattern = r'\((?:Immediate|Short-term|Long-term)\)\s*([^(]+?)(?=\((?:Immediate|Short-term|Long-term)\)|\Z)'
                    priority_matches = re.finditer(priority_pattern, rec_text, re.DOTALL | re.IGNORECASE)
                    for match in priority_matches:
                        remedy = match.group(1).strip()
                        if remedy:
                            remedies.append(remedy)
                
                # If still no remedies, use whole text (cleaned)
                if not remedies and rec_text:
                    # Clean up and take first meaningful sentence
                    cleaned = rec_text.replace('\n', ' ').strip()
                    if len(cleaned) > 10:
                        remedies = [cleaned[:200]]  # Limit length
                        
            else:
                remedies = []
            
            if not remedies:
                remedies = ['See full analysis for recommendations']
            
            issues.append({
                'issue_name': f"{section_num}. {section_name}",
                'issue_description': description,
                'issue_severity': severity,
                'issue_evidence': evidence,
                'possible_remedies': remedies[:5]
            })
            
        except Exception as e:
            print(f"❌ Error parsing section {section_num}: {e}")
            import traceback
            traceback.print_exc()
            continue
    
    if not issues:
        print("⚠️ Parser found no issues. Returning generic issue.")
        return [{
            'issue_name': 'Analysis Complete',
            'issue_description': 'Ethics analysis completed. See full report for details.',
            'issue_severity': 'info',
            'issue_evidence': 'Analysis was performed but could not be parsed into structured format.',
            'possible_remedies': ['Review the complete analysis report']
        }]
    
    return issues


@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'service': 'Ethics Compliance API',
        'version': '1.1.0',  # Updated version
        'features': [
            'ethics_analysis',
            'attribute_expansion',
            'context_caching'
        ]
    })


@app.route('/api/cache/status', methods=['GET'])
def cache_status():
    """Check cache status - useful for debugging"""
    return jsonify({
        'cached_analyses': len(analysis_cache),
        'cache_keys': list(analysis_cache.keys())
    })


@app.route('/api/cache/clear', methods=['POST'])
def clear_cache():
    """Clear the analysis cache - useful for development"""
    global analysis_cache
    cache_size = len(analysis_cache)
    analysis_cache = {}
    return jsonify({
        'success': True,
        'message': f'Cleared {cache_size} cached analyses'
    })


if __name__ == '__main__':
    print("\n" + "="*60)
    print("🚀 DATA SEANCE - Ethics Compliance API v1.1")
    print("="*60)
    print(f"📍 Server: http://localhost:5001")
    print(f"💚 Health: http://localhost:5001/api/health")
    print(f"🔍 Analyze: POST http://localhost:5001/api/analyze")
    print(f"💡 Expand: POST http://localhost:5001/api/request-details")
    print(f"📊 Cache Status: GET http://localhost:5001/api/cache/status")
    print("="*60 + "\n")
    print("✨ Ready to analyze files from frontend!")
    print("🔑 Context caching enabled for attribute expansion")
    print("Press Ctrl+C to stop\n")
    
    app.run(debug=True, port=5001, host='0.0.0.0')
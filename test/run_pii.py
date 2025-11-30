"""
Run Ethics Compliance Analysis on PII Dataset

This script runs the ethics compliance pipeline on PIIdata.csv to detect
privacy and ethical issues in the dataset.

Author: User
Date: November 30, 2025
"""

import sys
from pathlib import Path

# Add the parent directory to the path so we can import backend
sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.main import analyze_ethics

def main():
    """
    Run ethics compliance analysis on PIIdata.csv.
    
    This performs dataset-only analysis (no model) to identify:
    - PII (Personally Identifiable Information)
    - Privacy concerns
    - Data governance issues
    - Protected attributes
    """
    
    print("=" * 80)
    print("ETHICS COMPLIANCE ANALYSIS - PII DATASET")
    print("=" * 80)
    print()
    
    # Path to the CSV file
    data_path = Path("test/PIIdata.csv")
    
    # Check if file exists
    if not data_path.exists():
        print(f"❌ Error: File not found: {data_path}")
        print(f"   Please ensure PIIdata.csv is in the current directory.")
        return
    
    # Metadata describing the columns
    metadata = {
        "Customer_name": "Full name of the customer (PII)",
        "Customer_phone_number": "Customer's phone number (PII)",
        "Customer_landmark": "Landmark near customer's address (potentially PII/location data)"
    }
    
    # Project description
    project_description = """
    Customer database containing personal information for service delivery.
    Used for customer identification, contact, and location-based services.
    """
    
    print(f"📁 Analyzing file: {data_path}")
    print(f"   Project: Customer PII Database Analysis")
    print()
    print("🔍 Starting analysis...")
    print("-" * 80)
    print()
    
    try:
        # Run the analysis (dataset only, no model)
        result = analyze_ethics(
            data=data_path,
            metadata=metadata,
            project_description=project_description,
            prompt_style="detailed",  # Use detailed analysis
            model_id=None,  # Use default model
            temperature=0.7
        )
        
        print("✅ Analysis completed successfully!")
        print()
        print("=" * 80)
        print("ETHICS COMPLIANCE REPORT")
        print("=" * 80)
        print()
        print(result['llm_response'])
        print()
        print("=" * 80)
        print()
        
        # Save the report
        output_dir = Path("./ethics_reports")
        output_dir.mkdir(parents=True, exist_ok=True)
        
        report_path = output_dir / "pii_dataset_analysis.txt"
        with open(report_path, 'w') as f:
            f.write("=" * 80 + "\n")
            f.write("ETHICS COMPLIANCE ANALYSIS - PII DATASET\n")
            f.write("=" * 80 + "\n\n")
            f.write(f"Project: {project_description.strip()}\n\n")
            f.write("=" * 80 + "\n")
            f.write("DATASET DESCRIPTION\n")
            f.write("=" * 80 + "\n\n")
            f.write(result['data_description'])
            f.write("\n\n")
            f.write("=" * 80 + "\n")
            f.write("ETHICS ANALYSIS\n")
            f.write("=" * 80 + "\n\n")
            f.write(result['llm_response'])
        
        print(f"💾 Report saved to: {report_path}")
        print()
        
        # Print summary of issues found
        print("=" * 80)
        print("QUICK SUMMARY")
        print("=" * 80)
        print()
        print("Analysis Type: Dataset Only (No Model)")
        print(f"Dataset: {data_path}")
        print(f"Columns Analyzed: {len(metadata)}")
        print()
        print("Key Areas Evaluated:")
        print("  ✓ Protected Attributes & PII Detection")
        print("  ✓ Privacy & Data Governance")
        print("  ✓ Data Fairness & Bias")
        print("  ✓ Transparency & Documentation")
        print()
        
    except FileNotFoundError as e:
        print(f"❌ Error: {e}")
    except Exception as e:
        print(f"❌ Unexpected error occurred:")
        print(f"   {type(e).__name__}: {e}")
        import traceback
        print()
        print("Full traceback:")
        traceback.print_exc()


if __name__ == "__main__":
    main()
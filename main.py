"""
Main Pipeline
Orchestrates the entire metadata extraction process
"""

import os
import sys
import pandas as pd
import time

from src.text_extractor import extract_text
from src.prompt_builder import build_extraction_prompt
from src.llm_client import LLMClient
from src.post_processor import post_process
from src.evaluate import compute_recall


def find_file(folder: str, file_name_prefix: str) -> str:
    """Find a file in folder matching the prefix"""
    file_name_prefix = str(file_name_prefix).strip()
    
    for f in os.listdir(folder):
        # Try exact prefix match
        if f.startswith(file_name_prefix):
            return os.path.join(folder, f)
    
    # Try matching just the number part
    prefix_number = file_name_prefix.split('-')[0] if '-' in file_name_prefix else file_name_prefix
    for f in os.listdir(folder):
        if f.startswith(prefix_number):
            return os.path.join(folder, f)
    
    # Try partial match
    for f in os.listdir(folder):
        if file_name_prefix.lower() in f.lower():
            return os.path.join(folder, f)
    
    return None


def process_documents(folder: str, file_list: list, llm_client: LLMClient) -> pd.DataFrame:
    """
    Process all documents in a folder
    
    Args:
        folder: Path to folder containing documents
        file_list: List of file name prefixes to process
        llm_client: Initialized LLM client
    
    Returns:
        DataFrame with predictions
    """
    
    results = []
    
    for i, file_prefix in enumerate(file_list):
        print(f"\n{'='*50}")
        print(f" Processing [{i+1}/{len(file_list)}]: {file_prefix}")
        print(f"{'='*50}")
        
        # Find the actual file
        file_path = find_file(folder, file_prefix)
        
        if not file_path:
            print(f"  File not found for prefix: {file_prefix}")
            results.append({
                'File Name': file_prefix,
                'Agreement Value': '',
                'Agreement Start Date': '',
                'Agreement End Date': '',
                'Renewal Notice (Days)': '',
                'Party One': '',
                'Party Two': ''
            })
            continue
        
        # Step 1: Extract text
        print(" Step 1: Extracting text...")
        text = extract_text(file_path)
        
        if not text:
            print("  ⚠️ No text extracted!")
            continue
        
        print(f"  Extracted {len(text)} characters")
        
        # Step 2: Build prompt
        print("  🔧 Step 2: Building prompt...")
        prompt = build_extraction_prompt(text)
        
        # Step 3: Send to LLM
        print("   Step 3: Sending to LLM...")
        raw_metadata = llm_client.extract_metadata(prompt)
        print(f"  Raw metadata: {raw_metadata}")
    
        # Step 4: Post-process
        print("  🧹 Step 4: Post-processing...")
        cleaned_metadata = post_process(raw_metadata)
        cleaned_metadata['File Name'] = file_prefix
        print(f"   Cleaned metadata: {cleaned_metadata}")
        
        results.append(cleaned_metadata)
        
        # Rate limiting - avoid API throttling
        time.sleep(2)
    
    return pd.DataFrame(results)


def main():
    """Main execution"""
    
    print("🚀 Starting Metadata Extraction Pipeline")
    print("=" * 60)
    
    # ===== CONFIGURATION =====
    TRAIN_FOLDER = "data/train"
    TEST_FOLDER = "data/test"
    TRAIN_CSV = "data/train.csv"
    TEST_CSV = "data/test.csv"
    OUTPUT_FILE = "predictions.csv"
    
    # ===== Load Data =====
    print("\nLoading data...")
    
    train_df = pd.read_csv(TRAIN_CSV)
    print(f"  Training samples: {len(train_df)}")
    print(f"  Columns: {list(train_df.columns)}")
    print(f"\n  Training data preview:")
    print(train_df.head())
    
    # ===== Initialize LLM =====
    print("\nInitializing LLM...")
    llm_client = LLMClient()
    
    # ===== Choose mode =====
    mode = input("\nChoose mode:\n  1. Validate on training data\n  2. Predict on test data\n  3. Both\nEnter (1/2/3): ").strip()
    
    # ===== Mode 1: Validate on Training Data =====
    if mode in ['1', '3']:
        print("\n" + "=" * 60)
        print(" VALIDATION ON TRAINING DATA")
        print("=" * 60)
        
        train_files = train_df['File Name'].astype(str).tolist()
        train_predictions = process_documents(
            TRAIN_FOLDER, train_files, llm_client
        )
        
        # Evaluate
        print("\nComputing Recall on Training Data...")
        compute_recall(train_predictions, train_df)
        
        # Save training predictions
        train_predictions.to_csv("train_predictions.csv", index=False)
        print("Training predictions saved to train_predictions.csv")
    
    # ===== Mode 2: Predict on Test Data =====
    if mode in ['2', '3']:
        print("\n" + "=" * 60)
        print(" PREDICTIONS ON TEST DATA")
        print("=" * 60)
        
        # Get test file names
        if os.path.exists(TEST_CSV):
            test_df = pd.read_csv(TEST_CSV)
            test_files = test_df['File Name'].astype(str).tolist()
        else:
            # If no test.csv, just process all files in test folder
            test_files = [
                os.path.splitext(f)[0] 
                for f in os.listdir(TEST_FOLDER)
                if f.endswith(('.docx', '.png', '.jpg'))
            ]
        
        test_predictions = process_documents(
            TEST_FOLDER, test_files, llm_client
        )
        
        # Save predictions
        test_predictions.to_csv(OUTPUT_FILE, index=False)
        print(f"\n Test predictions saved to {OUTPUT_FILE}")
        print(test_predictions)
    
    print("\n Pipeline complete!")


if __name__ == "__main__":
    main()
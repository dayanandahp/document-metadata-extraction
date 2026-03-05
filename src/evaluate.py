"""
Evaluation Module
Computes per-field Recall metric
"""

import pandas as pd
import math


def normalize_value(value) -> str:
    """Normalize a value for comparison"""
    val_str = str(value).strip()
    
    # Handle NaN
    if val_str.lower() == 'nan' or val_str == '':
        return 'nan'
    
    # Handle float numbers like 90.0 → 90
    try:
        num = float(val_str)
        if num == int(num):
            return str(int(num))
        return str(num)
    except ValueError:
        pass
    
    return val_str


def compute_recall(predictions_df: pd.DataFrame, ground_truth_df: pd.DataFrame) -> dict:
    """
    Compute per-field Recall
    """
    
    # Mapping: prediction column name → ground truth column name
    field_mapping = {
        'Agreement Value': None,
        'Agreement Start Date': None,
        'Agreement End Date': None,
        'Renewal Notice (Days)': None,
        'Party One': None,
        'Party Two': None
    }
    
    gt_columns = ground_truth_df.columns.tolist()
    
    for gt_col in gt_columns:
        gt_lower = gt_col.lower()
        if 'value' in gt_lower:
            field_mapping['Agreement Value'] = gt_col
        elif 'start' in gt_lower:
            field_mapping['Agreement Start Date'] = gt_col
        elif 'end' in gt_lower:
            field_mapping['Agreement End Date'] = gt_col
        elif 'renewal' in gt_lower:
            field_mapping['Renewal Notice (Days)'] = gt_col
        elif 'party one' in gt_lower:
            field_mapping['Party One'] = gt_col
        elif 'party two' in gt_lower:
            field_mapping['Party Two'] = gt_col
    
    print("\n Column Mapping:")
    for pred_col, gt_col in field_mapping.items():
        print(f"   {pred_col} ← {gt_col}")
    
    results = {}
    
    print("\n" + "=" * 60)
    print(" EVALUATION RESULTS")
    print("=" * 60)
    
    for pred_field, gt_field in field_mapping.items():
        
        if gt_field is None:
            print(f"\n📌 {pred_field}")
            print(f"    No matching column found in ground truth!")
            results[pred_field] = 0
            continue
        
        true_count = 0
        false_count = 0
        details = []
        
        for idx, gt_row in ground_truth_df.iterrows():
            file_name = str(gt_row['File Name']).strip()
            raw_expected = gt_row[gt_field]
            expected = normalize_value(raw_expected)
            
            # Find matching prediction
            pred_rows = predictions_df[
                predictions_df['File Name'].astype(str).str.strip() == file_name
            ]
            
            if len(pred_rows) == 0:
                false_count += 1
                details.append(f"   {file_name}: NOT FOUND in predictions")
                continue
            
            raw_predicted = pred_rows[pred_field].values[0]
            predicted = normalize_value(raw_predicted)
            
            # Compare
            # Both NaN = match
            if expected == 'nan' and predicted == 'nan':
                true_count += 1
                details.append(f"   {file_name}: (both empty/nan)")
            # Case-insensitive comparison
            elif predicted.lower() == expected.lower():
                true_count += 1
                details.append(f"   {file_name}: '{predicted}'")
            else:
                false_count += 1
                details.append(
                    f"  ❌ {file_name}: expected='{expected}' | got='{predicted}'"
                )
        
        total = true_count + false_count
        recall = true_count / total if total > 0 else 0
        results[pred_field] = recall
        
        print(f"\n📌 {pred_field}")
        print(f"   Recall: {recall:.2%} ({true_count}/{total})")
        for detail in details:
            print(detail)
    
    avg_recall = sum(results.values()) / len(results) if results else 0
    
    print(f"\n{'=' * 60}")
    print(f"🏆 AVERAGE RECALL: {avg_recall:.2%}")
    print(f"{'=' * 60}")
    
    return results
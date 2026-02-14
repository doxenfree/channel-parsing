import csv

def calculate_probability(skill, level, level_gap, hits):
    """
    Calculates the probability of successfully channeling a spell based on azxten methodology.
    Formula: (max(39, min(370, (channeling_skill + 5 + level + level_gap * 3))) / 391) ^ hits
    """
    calc_val = skill + 5 + level + (level_gap * 3)
    clamped_val = max(39, min(370, calc_val))
    
    # Base chance for a single hit
    single_hit_chance = clamped_val / 391.0
    
    # Probability of succeeding all independent checks (one per hit)
    return single_hit_chance ** hits

def validate_model(csv_file):
    total_events = 0
    actual_successes = 0
    expected_successes = 0.0
    brier_score_sum = 0.0
    
    # Dictionary to bin the probabilities for the calibration curve
    # Bins will be 0.0, 0.1, 0.2 ... 1.0
    bins = {} 

    print(f"Reading data from {csv_file}...\n")
    
    with open(csv_file, 'r', encoding='utf-8') as f:
        # Use DictReader to easily access columns by name
        reader = csv.DictReader(f)
        
        for row in reader:
            try:
                # Extract and cast the necessary fields
                skill = int(row['channeling skill'])
                level = int(row['level'])
                hits = int(row['hits'])
                
                # Handle cases where level gap might be empty or missing
                level_gap_str = row.get('level gap', '0')
                level_gap = int(level_gap_str) if level_gap_str.strip() else 0
                
                result = row['result'].strip().lower()
                
            except (ValueError, KeyError) as e:
                # Skip header rows or malformed data
                continue
                
            # 1 for Success, 0 for Failure
            actual_outcome = 1 if result == 'success' else 0
            
            # Predict the probability using the hypothesis formula
            predicted_prob = calculate_probability(skill, level, level_gap, hits)
            
            # Tally metrics
            total_events += 1
            actual_successes += actual_outcome
            expected_successes += predicted_prob
            
            # Brier score calculation: (predicted - actual)^2
            brier_score_sum += (predicted_prob - actual_outcome) ** 2
            
            # Binning for calibration table (round to nearest 10% / 0.1)
            bin_key = round(predicted_prob * 10) / 10.0
            if bin_key not in bins:
                bins[bin_key] = {'actual': 0, 'expected': 0.0, 'count': 0}
            
            bins[bin_key]['actual'] += actual_outcome
            bins[bin_key]['expected'] += predicted_prob
            bins[bin_key]['count'] += 1

    if total_events == 0:
        print("No valid data found to process.")
        return

    # Calculate final averages
    brier_score = brier_score_sum / total_events
    overall_actual_rate = (actual_successes / total_events) * 100
    overall_expected_rate = (expected_successes / total_events) * 100

    # Print Validation Report
    print("=== Model Validation Report ===")
    print(f"Total Events Evaluated: {total_events}")
    print("-" * 31)
    print(f"Actual Successes:       {actual_successes} ({overall_actual_rate:.2f}%)")
    print(f"Expected Successes:     {expected_successes:.2f} ({overall_expected_rate:.2f}%)")
    print(f"Brier Score:            {brier_score:.4f} (Closer to 0 is better)")
    
    print("\n=== Calibration Table ===")
    print("Groups events by their predicted probability. If the model is accurate,")
    print("the 'Actual %' should closely match the 'Pred Prob' bin.\n")
    print(f"{'Pred Prob':<10} | {'Count':<8} | {'Actual %':<10} | {'Expected %':<10}")
    print("-" * 47)
    
    for b in sorted(bins.keys()):
        data = bins[b]
        if data['count'] > 0:
            act_pct = (data['actual'] / data['count']) * 100
            exp_pct = (data['expected'] / data['count']) * 100
            print(f"~ {b:<8.2f} | {data['count']:<8} | {act_pct:>8.2f}% | {exp_pct:>8.2f}%")

if __name__ == '__main__':
    # Update this to match your target CSV file
    INPUT_CSV = "channeling_data_cleaned.csv"
    validate_model(INPUT_CSV)

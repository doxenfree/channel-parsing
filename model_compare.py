import csv

def calc_azxten(skill, level, level_gap, hits):
    """
    Calculates probability based on the azxten methodology.
    Formula: ((max(39, min(370, (skill + 5 + level + level_gap * 3))) / 391) ** hits)
    """
    calc_val = skill + 5 + level + (level_gap * 3)
    clamped_val = max(39, min(370, calc_val))
    single_hit_chance = clamped_val / 391.0
    
    prob = single_hit_chance ** hits
    return max(0.0, min(1.0, prob))

def calc_eqemu(skill, hits):
    """
    Calculates probability based on the EQEmu methodology.
    Formula: (30 + (skill / 400.0 * 100) - (hits * 2)) / 100.0
    """
    chance = (30 + (skill / 400.0 * 100) - (hits * 2)) / 100.0
    return max(0.0, min(1.0, chance))

def print_calibration_table(bins, model_name):
    """Helper to print a calibration table for a specific model's bin data."""
    print(f"\n--- {model_name} Calibration Table ---")
    print("Groups events by their predicted probability.")
    print(f"{'Pred Prob':<10} | {'Count':<8} | {'Actual %':<10} | {'Expected %':<10}")
    print("-" * 47)
    
    for b in sorted(bins.keys()):
        data = bins[b]
        if data['count'] > 0:
            act_pct = (data['actual'] / data['count']) * 100
            exp_pct = (data['expected'] / data['count']) * 100
            print(f"~ {b:<8.2f} | {data['count']:<8} | {act_pct:>8.2f}% | {exp_pct:>8.2f}%")

def compare_models(csv_file):
    total_events = 0
    actual_successes = 0
    
    # Tracking for Model A (Azxten)
    exp_successes_a = 0.0
    brier_sum_a = 0.0
    bins_a = {}
    
    # Tracking for Model B (EQEmu)
    exp_successes_b = 0.0
    brier_sum_b = 0.0
    bins_b = {}

    print(f"Reading data from {csv_file}...\n")
    
    try:
        with open(csv_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            
            for row in reader:
                try:
                    # Map CSV columns to variables
                    skill = int(row['channeling skill'])
                    level = int(row['level'])
                    hits = int(row['hits'])
                    level_gap_str = row.get('level gap', '0')
                    level_gap = int(level_gap_str) if level_gap_str.strip() else 0
                    result = row['result'].strip().lower()
                except (ValueError, KeyError):
                    # Skip malformed rows
                    continue
                    
                actual_outcome = 1 if result == 'success' else 0
                total_events += 1
                actual_successes += actual_outcome
                
                # --- Process Model A (Azxten) ---
                prob_a = calc_azxten(skill, level, level_gap, hits)
                exp_successes_a += prob_a
                brier_sum_a += (prob_a - actual_outcome) ** 2
                
                bin_key_a = round(prob_a * 10) / 10.0
                if bin_key_a not in bins_a:
                    bins_a[bin_key_a] = {'actual': 0, 'expected': 0.0, 'count': 0}
                bins_a[bin_key_a]['actual'] += actual_outcome
                bins_a[bin_key_a]['expected'] += prob_a
                bins_a[bin_key_a]['count'] += 1
                
                # --- Process Model B (EQEmu) ---
                prob_b = calc_eqemu(skill, hits)
                exp_successes_b += prob_b
                brier_sum_b += (prob_b - actual_outcome) ** 2
                
                bin_key_b = round(prob_b * 10) / 10.0
                if bin_key_b not in bins_b:
                    bins_b[bin_key_b] = {'actual': 0, 'expected': 0.0, 'count': 0}
                bins_b[bin_key_b]['actual'] += actual_outcome
                bins_b[bin_key_b]['expected'] += prob_b
                bins_b[bin_key_b]['count'] += 1
                
    except FileNotFoundError:
        print(f"Error: Could not find the file {csv_file}")
        return

    if total_events == 0:
        print("No valid data found to process.")
        return

    # Metrics Calculations
    actual_rate = (actual_successes / total_events) * 100
    
    # Model A Stats
    brier_a = brier_sum_a / total_events
    exp_rate_a = (exp_successes_a / total_events) * 100
    
    # Model B Stats
    brier_b = brier_sum_b / total_events
    exp_rate_b = (exp_successes_b / total_events) * 100

    # Print Final Report
    print(f"Total Events Evaluated:  {total_events}")
    print(f"Actual Successes:        {actual_successes} ({actual_rate:.2f}%)\n")
    
    print("--- Model A: Azxten Formula ---")
    print(f"Expected Successes:      {exp_successes_a:.2f} ({exp_rate_a:.2f}%)")
    print(f"Brier Score:             {brier_a:.4f}")
    print(f"Total Error:             {abs(actual_rate - exp_rate_a):.2f}%")
    print_calibration_table(bins_a, "Model A (Azxten)")
    
    print("\n" + "="*50 + "\n")
    
    print("--- Model B: EQEmu Formula ---")
    print(f"Expected Successes:      {exp_successes_b:.2f} ({exp_rate_b:.2f}%)")
    print(f"Brier Score:             {brier_b:.4f}")
    print(f"Total Error:             {abs(actual_rate - exp_rate_b):.2f}%")
    print_calibration_table(bins_b, "Model B (EQEmu)")

if __name__ == '__main__':
    INPUT_CSV = "channeling_data_cleaned.csv"
    compare_models(INPUT_CSV)

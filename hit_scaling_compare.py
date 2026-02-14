import csv
from collections import defaultdict

def calc_azxten(skill, level, level_gap, hits):
    """Exponential Model: ((skill + 5 + level + level_gap * 3) / 391) ^ hits"""
    calc_val = skill + 5 + level + (level_gap * 3)
    clamped_val = max(39, min(370, calc_val))
    prob = (clamped_val / 391.0) ** hits
    return max(0.0, min(1.0, prob))

def calc_eqemu(skill, hits):
    """Linear Model: (30 + (skill / 400 * 100) - (hits * 2)) / 100"""
    chance = (30 + (skill / 400.0 * 100) - (hits * 2)) / 100.0
    return max(0.0, min(1.0, chance))

def analyze_by_hits(csv_file):
    # hit_data[num_hits] = { 'successes': 0, 'total': 0, 'pred_azxten_sum': 0.0, 'pred_eqemu_sum': 0.0 }
    hit_data = defaultdict(lambda: {'successes': 0, 'total': 0, 'az_sum': 0.0, 'eq_sum': 0.0})

    try:
        with open(csv_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                try:
                    skill = int(row['channeling skill'])
                    level = int(row['level'])
                    hits = int(row['hits'])
                    level_gap = int(row.get('level gap', 0))
                    actual = 1 if row['result'].strip().lower() == 'success' else 0
                    
                    # Predictions
                    p_az = calc_azxten(skill, level, level_gap, hits)
                    p_eq = calc_eqemu(skill, hits)
                    
                    # Store
                    stats = hit_data[hits]
                    stats['total'] += 1
                    stats['successes'] += actual
                    stats['az_sum'] += p_az
                    stats['eq_sum'] += p_eq
                except (ValueError, KeyError):
                    continue
    except FileNotFoundError:
        print(f"File {csv_file} not found.")
        return

    print(f"{'Hits':<5} | {'Count':<6} | {'Actual %':<10} | {'Azxten (Exp) %':<15} | {'EQEmu (Lin) %':<15}")
    print("-" * 65)

    for h in sorted(hit_data.keys()):
        d = hit_data[h]
        actual_pct = (d['successes'] / d['total']) * 100
        az_pct = (d['az_sum'] / d['total']) * 100
        eq_pct = (d['eq_sum'] / d['total']) * 100
        
        print(f"{h:<5} | {d['total']:<6} | {actual_pct:>8.1f}% | {az_pct:>13.1f}% | {eq_pct:>13.1f}%")

if __name__ == "__main__":
    analyze_by_hits("channeling_data_cleaned.csv")

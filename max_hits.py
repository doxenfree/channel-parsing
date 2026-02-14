import os
import re
from collections import defaultdict
from pathlib import Path

def find_max_hits_on_success(directory_path):
    # Maps hit count to a list of (filename, line_number) tuples
    success_records = defaultdict(list)
    
    log_pattern = re.compile(r'^\[.*?\]\s+(.*)')
    attack_pattern = re.compile(r' YOU for \d+ points of damage\.')
    
    for file_path in Path(directory_path).glob('*.txt'):
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as file:
                is_casting = False
                current_hits = 0
                
                # enumerate(..., 1) starts line counting at 1
                for line_num, line in enumerate(file, 1):
                    match = log_pattern.match(line)
                    if not match:
                        continue
                    
                    message = match.group(1).strip()
                    
                    # 1. Cast starts
                    if message.startswith("You begin casting "):
                        is_casting = True
                        current_hits = 0
                        
                    # 2. Tracking during an active cast
                    elif is_casting:
                        if attack_pattern.search(message):
                            current_hits += 1
                            
                        # Cast Succeeds
                        elif message.startswith("You regain your concentration"):
                            if current_hits > 0:
                                success_records[current_hits].append((file_path.name, line_num))
                            is_casting = False 
                            
                        # Cast Fails
                        elif message.startswith("Your spell is interrupted."):
                            is_casting = False
                            
        except Exception as e:
            print(f"Error reading {file_path.name}: {e}")

    return success_records

def print_max_hit_report(success_records):
    print("=== EverQuest Max Hits on Success Report ===\n")
    
    if not success_records:
        print("No successful casts with hits were found in the logs.")
        return
        
    # Find the highest number of hits recorded
    max_hits = max(success_records.keys())
    instances = success_records[max_hits]
    
    print(f"Maximum hits taken during a successful cast: {max_hits}")
    print(f"Total instances of this occurring: {len(instances)}\n")
    
    # Format the output into a clean table
    print(f"{'Filename':<35} | {'Line Number'}")
    print("-" * 50)
    
    for filename, line_num in instances:
        print(f"{filename:<35} | {line_num}")

    #hack, remove later
    instances = success_records[1]
    
    print(f"Maximum hits taken during a successful cast: {max_hits}")
    print(f"Total instances of this occurring: {len(instances)}\n")
    
    # Format the output into a clean table
    print(f"{'Filename':<35} | {'Line Number'}")
    print("-" * 50)
    
    for filename, line_num in instances:
        print(f"{filename:<35} | {line_num}")

if __name__ == "__main__":
    LOG_DIR = "../eqlogs/harcourt_applets/DSR/"
    
    if not os.path.exists(LOG_DIR):
        print(f"Directory not found: {LOG_DIR}. Please update the LOG_DIR variable.")
    else:
        records = find_max_hits_on_success(LOG_DIR)
        print_max_hit_report(records)

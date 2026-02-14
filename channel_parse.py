import os
import re
from collections import Counter
from pathlib import Path

def analyze_eq_casting_logs(directory_path):
    # Counters to tally the frequency of X hits during a success/failure
    success_tally = Counter()
    failure_tally = Counter()

    # Regex to strip the EQ timestamp [Day Mon DD HH:MM:SS YYYY] and grab the message
    log_pattern = re.compile(r'^\[.*?\]\s+(.*)')
    
    # Regex to match the physical damage pattern: "<NPC> <attack> YOU for <damage> points of damage."
    #attack_pattern = re.compile(r' YOU for \d+ points of damage\.')
    attack_pattern = re.compile(r'(?: YOU for \d+ points of damage|You have been \w+)\.')

    # Iterate through all .txt files in the target directory
    # (EverQuest logs are typically formatted as eqlog_Character_server.txt)
    for file_path in Path(directory_path).glob('*.txt'):
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as file:
                is_casting = False
                current_hits = 0

                for line in file:
                    match = log_pattern.match(line)
                    if not match:
                        continue
                    
                    # Extract the log message, stripping trailing spaces/newlines
                    message = match.group(1).strip()

                    # 1. Check if a new cast is starting
                    if message.startswith("You begin casting "):
                        is_casting = True
                        current_hits = 0
                        
                    # 2. If we are currently casting, check for hits, successes, or failures
                    elif is_casting:
                        # Count the hit if it matches the damage pattern
                        if attack_pattern.search(message):
                            current_hits += 1
                            
                        # Resolve cast: Success (channel check passed)
                        elif message.startswith("You regain your concentration"):
                            if current_hits > 0:
                                success_tally[current_hits] += 1
                            is_casting = False # Reset state
                            
                        # Resolve cast: Failure (interrupted)
                        elif message.startswith("Your spell is interrupted."):
                            if current_hits > 0:
                                failure_tally[current_hits] += 1
                            is_casting = False # Reset state
                            
        except Exception as e:
            print(f"Error reading {file_path}: {e}")

    return success_tally, failure_tally


def print_report(success_tally, failure_tally):
    print("=== EverQuest Casting Channel Report ===")
    print(f"Total successful casts (while being hit): {sum(success_tally.values())}")
    print(f"Total interrupted casts (while being hit): {sum(failure_tally.values())}")
    print("-" * 40)
    
    # Get all unique hit counts we observed across both counters
    all_hit_counts = set(success_tally.keys()).union(set(failure_tally.keys()))
    
    if not all_hit_counts:
        print("No hits during casting were found in the logs.")
        return

    print(f"{'Hits Taken':<15} | {'Successful Casts':<20} | {'Failed Casts':<15}")
    print("-" * 55)
    
    for hits in sorted(all_hit_counts):
        successes = success_tally.get(hits, 0)
        failures = failure_tally.get(hits, 0)
        print(f"{hits:<15} | {successes:<20} | {failures:<15}")


if __name__ == "__main__":
    # Point this to your EverQuest logs directory
    LOG_DIR = "../eqlogs/harcourt_applets/DSR/" 
    
    if not os.path.exists(LOG_DIR):
        print(f"Directory not found: {LOG_DIR}. Please update the LOG_DIR variable.")
    else:
        successes, failures = analyze_eq_casting_logs(LOG_DIR)
        print_report(successes, failures)

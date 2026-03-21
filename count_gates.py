import sys
import argparse
import os

def count_successful_gates(filepath):
    successful_gates = 0
    is_casting_gate = False
    
    try:
        with open(filepath, 'r', encoding='utf-8', errors='replace') as f:
            for line in f:
                if is_casting_gate:
                    # 1. Check for failure/interrupt conditions first
                    if "Your spell is interrupted." in line or "You must stand upright and still in order to cast!" in line:
                        is_casting_gate = False
                        
                    # 2. Check for explicit success conditions (zoning or a subsequent fizzle)
                    elif "LOADING, PLEASE WAIT..." in line or "Your spell fizzles!" in line:
                        successful_gates += 1
                        is_casting_gate = False
                        
                    # 3. Check for implicit success (casting any new spell)
                    elif "You begin casting" in line:
                        successful_gates += 1
                        
                        # If the NEW spell they are casting is also Gate, 
                        # we keep the state as True to track this new cast.
                        # Otherwise, they are casting something else, so we reset.
                        if "You begin casting Gate." in line:
                            is_casting_gate = True
                        else:
                            is_casting_gate = False
                            
                else:
                    # If we aren't currently tracking a Gate, look for one to start
                    if "You begin casting Gate." in line:
                        is_casting_gate = True
                        
    except Exception as e:
        print(f"Error reading {filepath}: {e}")
        
    return successful_gates

def main():
    parser = argparse.ArgumentParser(description="Count successful Gate casts in EverQuest log files.")
    parser.add_argument('log_files', nargs='+', help="One or more paths to EQ log files")
    args = parser.parse_args()
    
    total_gates = 0
    
    print(f"{'Log File':<40} | {'Successful Gates'}")
    print("-" * 60)
    
    for log_file in args.log_files:
        if not os.path.exists(log_file):
            print(f"{log_file:<40} | File Not Found")
            continue
            
        count = count_successful_gates(log_file)
        print(f"{os.path.basename(log_file):<40} | {count}")
        total_gates += count
        
    print("-" * 60)
    print(f"{'TOTAL':<40} | {total_gates}")

if __name__ == "__main__":
    main()

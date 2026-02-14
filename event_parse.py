import os
import re
import csv
from pathlib import Path

def analyze_eq_casting_logs(directory_path, output_csv):
    # Core regex patterns for message parsing
    log_pattern = re.compile(r'^\[.*?\]\s+(.*)')
    attack_pattern = re.compile(r'(?: YOU for \d+ points of damage|You have been \w+)\.')
    
    # State-tracking regex patterns
    skill_pattern = re.compile(r'You have become better at Channeling! \((\d+)\)')
    level_pattern = re.compile(r'(?:You have gained a level!|You raise a level!) Welcome to level (\d+)!')
    spell_pattern = re.compile(r'You begin casting (.*?)\.')
    stun_pattern = re.compile(r'You are stunned!')

    if not os.path.exists(directory_path):
        print(f"Directory not found: {directory_path}. Please update the LOG_DIR variable.")
        return

    # Open CSV for writing
    with open(output_csv, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.writer(csvfile)
        
        # Write the header
        writer.writerow(['channeling skill', 'level', 'class', 'spell', 'hits', 'result'])
        
        for file_path in Path(directory_path).glob('*.txt'):
            filename = file_path.name
            
            # Extract character name: a string of letters excluding 'eqlog' and 'txt'
            letter_blocks = re.findall(r'[A-Za-z]+', filename)
            valid_names = [b for b in letter_blocks if b.lower() not in ('eqlog', 'txt')]
            
            if not valid_names:
                continue
            char_name = valid_names[0]
            
            # Who message pattern for the specific character (captures Level and Class)
            # e.g., "[50 Cleric] CharacterName"
            who_pattern = re.compile(r'^\[(\d+)\s+(.*?)\]\s+' + re.escape(char_name) + r'\b', re.IGNORECASE)

            initial_skill = None
            initial_level = None
            char_class = None

            # Pass 1: Scan for initial baseline values (level, skill, and class)
            try:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as file:
                    for line in file:
                        match = log_pattern.match(line)
                        if not match:
                            continue

                        message = match.group(1).strip()

                        if initial_skill is None:
                            s_match = skill_pattern.match(message)
                            if s_match:
                                initial_skill = int(s_match.group(1)) - 1

                        if initial_level is None:
                            l_match = level_pattern.match(message)
                            if l_match:
                                # Level up message gives us the new level, so base is 1 lower
                                initial_level = int(l_match.group(1)) - 1
                                
                        # Check the who message if we are missing class OR level
                        if char_class is None or initial_level is None:
                            w_match = who_pattern.match(message)
                            if w_match:
                                if initial_level is None:
                                    initial_level = int(w_match.group(1))
                                if char_class is None:
                                    char_class = w_match.group(2)
                                    
                        # Stop scanning if we found all baseline data
                        if initial_skill is not None and initial_level is not None and char_class is not None:
                            break
            
            except Exception as e:
                print(f"Error reading {file_path} during baseline pass: {e}")
                continue
            
            # If we don't find a leveling up or channeling message, skip the file entirely
            if initial_skill is None or initial_level is None or char_class is None:
                print(f"Skipping {filename}: Missing initial channeling skill, level, or class data.")
                print(f"initial_skill:{initial_skill}, initial_level:{initial_level}, char_class:{char_class}.")
                continue
                
            # Pass 2: Parse events sequentially and record channeling checks
            try:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as file:
                    current_skill = initial_skill
                    current_level = initial_level
                    
                    is_casting = False
                    current_hits = 0
                    current_spell = ""
                    is_stunned = False
                    
                    for line in file:
                        match = log_pattern.match(line)
                        if not match:
                            continue
                        
                        message = match.group(1).strip()
                        
                        # 1. Check for state updates
                        s_match = skill_pattern.match(message)
                        if s_match:
                            current_skill = int(s_match.group(1))
                            continue
                            
                        l_match = level_pattern.match(message)
                        if l_match:
                            current_level = int(l_match.group(1))
                            continue
                            
                        # 2. Check if a new cast is starting
                        spell_match = spell_pattern.match(message)
                        if spell_match:
                            is_casting = True
                            current_hits = 0
                            is_stunned = False
                            current_spell = spell_match.group(1)
                            continue
                            
                        # 3. Handle casting events, stuns, and resolution
                        if is_casting:
                            if stun_pattern.match(message):
                                is_stunned = True
                                
                            elif attack_pattern.search(message):
                                current_hits += 1
                                
                            elif message.startswith("You regain your concentration"):
                                if current_hits > 0 :
                                    writer.writerow([current_skill, current_level, char_class, current_spell, current_hits, 'Success'])
                                is_casting = False # Reset state
                                
                            elif message.startswith("Your spell is interrupted."):
                                if current_hits > 0 and not is_stunned:
                                    writer.writerow([current_skill, current_level, char_class, current_spell, current_hits, 'Failure'])
                                is_casting = False # Reset state

            except Exception as e:
                print(f"Error reading {file_path} during parsing pass: {e}")

    print(f"\nProcessing complete. Log data compiled into: {output_csv}")


if __name__ == "__main__":
    # Point this to your EverQuest logs directory
    LOG_DIR = "../eqlogs/harcourt_applets/DSR/" 
    OUTPUT_FILE = "channeling_data.csv"
    
    analyze_eq_casting_logs(LOG_DIR, OUTPUT_FILE)

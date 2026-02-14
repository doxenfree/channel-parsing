import csv
import re
import urllib.request
import urllib.parse
from time import sleep

# Class mapping based on the provided table
CLASS_MAPPING = {
    # Bard
    'Bard': 'Bard', 'Minstrel': 'Bard', 'Troubadour': 'Bard', 'Virtuoso': 'Bard',
    # Cleric
    'Cleric': 'Cleric', 'Vicar': 'Cleric', 'Templar': 'Cleric', 'High Priest': 'Cleric',
    # Druid
    'Druid': 'Druid', 'Wanderer': 'Druid', 'Preserver': 'Druid', 'Hierophant': 'Druid',
    # Enchanter
    'Enchanter': 'Enchanter', 'Illusionist': 'Enchanter', 'Beguiler': 'Enchanter', 'Phantasmist': 'Enchanter',
    # Magician
    'Magician': 'Magician', 'Elementalist': 'Magician', 'Conjurer': 'Magician', 'Arch Mage': 'Magician',
    # Monk
    'Monk': 'Monk', 'Disciple': 'Monk', 'Master': 'Monk', 'Grandmaster': 'Monk',
    # Necromancer
    'Necromancer': 'Necromancer', 'Heretic': 'Necromancer', 'Defiler': 'Necromancer', 'Warlock': 'Necromancer',
    # Paladin
    'Paladin': 'Paladin', 'Cavalier': 'Paladin', 'Knight': 'Paladin', 'Crusader': 'Paladin',
    # Ranger
    'Ranger': 'Ranger', 'Pathfinder': 'Ranger', 'Outrider': 'Ranger', 'Warder': 'Ranger',
    # Rogue
    'Rogue': 'Rogue', 'Rake': 'Rogue', 'Blackguard': 'Rogue', 'Assassin': 'Rogue',
    # Shadow Knight
    'Shadow Knight': 'Shadow Knight', 'Reaver': 'Shadow Knight', 'Revenant': 'Shadow Knight', 'Grave Lord': 'Shadow Knight',
    # Shaman
    'Shaman': 'Shaman', 'Mystic': 'Shaman', 'Luminary': 'Shaman', 'Oracle': 'Shaman',
    # Warrior
    'Warrior': 'Warrior', 'Champion': 'Warrior', 'Myrmidon': 'Warrior', 'Warlord': 'Warrior',
    # Wizard
    'Wizard': 'Wizard', 'Channeler': 'Wizard', 'Evoker': 'Wizard', 'Sorcerer': 'Wizard'
}

# Normalize dictionary for case-insensitive lookup
CLASS_MAPPING_LOWER = {k.lower(): v for k, v in CLASS_MAPPING.items()}

# Cache to prevent repeated web requests: {(spell_name, base_class): spell_level}
SPELL_CACHE = {
    ('Wrath of Nature', 'Druid'): 50, #Manually adding epic activatable, not sure if correct
    ('Spirit of Eagle', 'Druid'): 54,
    ('Shield of Thorns', 'Druid'): 49,
}

def get_base_class(title):
    return CLASS_MAPPING_LOWER.get(title.lower(), title)

def fetch_spell_level(spell_name, base_class):
    """Fetches the spell level from the p99 wiki raw markup."""
    cache_key = (spell_name, base_class)
    if cache_key in SPELL_CACHE:
        return SPELL_CACHE[cache_key]

    # Format spell name for wiki URL (spaces to underscores)
    formatted_spell = urllib.parse.quote(spell_name.replace(' ', '_').replace('`','\''))
    url = f"https://wiki.project1999.com/index.php?title={formatted_spell}&action=raw"

    try:
        # Give a tiny delay to be polite to the wiki server
        sleep(0.5)
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req) as response:
            wiki_text = response.read().decode('utf-8')
            
        # Regex to find the specific class line e.g., "* [[Druid]] - Level 53 ... "
        class_pattern = re.compile(r'\*\s*\[\[' + re.escape(base_class) + r'\]\](.*?)(?=\n|$)', re.IGNORECASE)
        match = class_pattern.search(wiki_text)
        
        if not match:
            print(f"  [!] Could not find class '{base_class}' on wiki page for '{spell_name}'.")
            SPELL_CACHE[cache_key] = None
            return None
            
        line = match.group(1)
        
        # Extract all "Level XX" occurrences and the text that immediately follows them
        # e.g., " - Level 53 {{Kunark Era Inline}} - Level 51 {{Velious Era Inline}}"
        level_pattern = re.compile(r'Level\s+(\d+)\s*(.*?)(?=Level|$)', re.IGNORECASE)
        level_matches = level_pattern.findall(line)
        
        if not level_matches:
            SPELL_CACHE[cache_key] = None
            return None
            
        selected_level = int(level_matches[0][0]) # Default to the first found level
        
        # If there are multiple levels, check for Velious Era
        if len(level_matches) > 1:
            for lvl_str, trailing_text in level_matches:
                if 'velious' in trailing_text.lower():
                    selected_level = int(lvl_str)
                    break
                    
        print(f"  [+] Cached {spell_name} for {base_class}: Level {selected_level}")
        SPELL_CACHE[cache_key] = selected_level
        return selected_level

    except Exception as e:
        print(f"  [!] Error fetching {spell_name} from Wiki: {e}")
        SPELL_CACHE[cache_key] = None
        return None

def clean_csv(input_file, output_file):
    print(f"Reading from {input_file}...")
    
    with open(input_file, 'r', encoding='utf-8') as infile, \
         open(output_file, 'w', newline='', encoding='utf-8') as outfile:
        
        reader = csv.reader(infile)
        writer = csv.writer(outfile)
        
        # Read header and append new column
        header = next(reader)
        header.append('level gap')
        writer.writerow(header)
        
        for row_num, row in enumerate(reader, start=2):
            if len(row) < 6:
                continue
                
            skill, char_level, char_class, spell, hits, result = row
            char_level = int(char_level)
            
            # 1. Convert title to base class
            base_class = get_base_class(char_class)
            row[2] = base_class 
            
            # 2. Fetch spell level
            spell_level = fetch_spell_level(spell, base_class)
            
            # 3. Calculate level diff (> 6 rule)
            level_diff = 0
            if spell_level is not None:
                diff = char_level - spell_level
                if diff > 6:
                    level_diff = diff
            
            row.append(level_diff)
            writer.writerow(row)

    print(f"\nCleanup complete. Data saved to: {output_file}")

if __name__ == "__main__":
    INPUT_CSV = "channeling_data.csv"
    OUTPUT_CSV = "channeling_data_cleaned.csv"
    
    clean_csv(INPUT_CSV, OUTPUT_CSV)

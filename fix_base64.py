import os
import re
import glob

# More robust regex matching only base64 characters and whitespace
pattern = re.compile(r'([\'"]data:image/[a-zA-Z]+;base64,)([A-Za-z0-9+/=\s]+)([\'"])')

def process_file(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    matches = pattern.findall(content)
    if not matches:
        print(f"No match found in: {os.path.basename(filepath)}")
        return

    def replacer(match):
        prefix = match.group(1)
        base64_data = match.group(2)
        quote = match.group(3)
        # Remove all whitespace
        clean_base64 = re.sub(r'\s+', '', base64_data)
        return prefix + clean_base64 + quote

    new_content = pattern.sub(replacer, content)

    if new_content != content:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(new_content)
        print(f"Fixed base64 in: {os.path.basename(filepath)}")
    else:
        print(f"No changes in: {os.path.basename(filepath)} (Matches found but no whitespace removed)")

if __name__ == "__main__":
    games_dir = r"C:\Users\Mr Mahmoud Elziadi\.gemini\antigravity\scratch\Thebest_start_repo\games"
    html_files = glob.glob(os.path.join(games_dir, "*.html"))
    for file in html_files:
        process_file(file)

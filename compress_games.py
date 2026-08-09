import os
import re
import glob
import base64
from io import BytesIO
from PIL import Image

def compress_base64_image(b64_string, max_size=(400, 400), quality=60):
    try:
        # Decode base64 to image
        image_data = base64.b64decode(b64_string)
        img = Image.open(BytesIO(image_data))
        
        # Convert to RGB if it's RGBA (for JPEG compatibility)
        if img.mode in ('RGBA', 'P'):
            img = img.convert('RGB')
            
        # Resize image maintaining aspect ratio
        img.thumbnail(max_size, Image.Resampling.LANCZOS)
        
        # Save to buffer as WebP
        buffer = BytesIO()
        img.save(buffer, format="WEBP", quality=quality)
        
        # Encode back to base64
        compressed_b64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
        return f"data:image/webp;base64,{compressed_b64}"
    except Exception as e:
        print(f"Error compressing image: {e}")
        return None

def process_file(filepath):
    print(f"Processing {filepath}...")
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    # Regex to match base64 strings
    pattern = re.compile(r'(data:image/[a-zA-Z]+;base64,)([A-Za-z0-9+/=\s]+)')
    
    def replacer(match):
        prefix = match.group(1)
        base64_data = match.group(2)
        # Remove whitespace
        clean_base64 = re.sub(r'\s+', '', base64_data)
        
        compressed = compress_base64_image(clean_base64)
        if compressed:
            return compressed
        return match.group(0) # Return original if failed

    new_content = pattern.sub(replacer, content)

    if new_content != content:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(new_content)
        print(f"Compressed images in: {os.path.basename(filepath)}")
    else:
        print(f"No compressible images found in: {os.path.basename(filepath)}")

if __name__ == "__main__":
    games_dir = r"C:\Users\Mr Mahmoud Elziadi\.gemini\antigravity\scratch\Thebest_start_repo\games"
    html_files = glob.glob(os.path.join(games_dir, "*.html"))
    for file in html_files:
        process_file(file)

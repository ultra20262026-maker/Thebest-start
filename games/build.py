import os
import base64
import re
import json
from PIL import Image
from io import BytesIO

root_dir = os.path.dirname(os.path.abspath(__file__))
assets_dir = os.path.join(root_dir, 'assets')

def get_base64_image(path):
    basename = os.path.basename(path)
    
    # Exclude submarine.jpg from compression to preserve exact RGB threshold (< 30) for transparency!
    if basename == 'submarine.jpg':
        with open(path, "rb") as f:
            encoded = base64.b64encode(f.read()).decode("utf-8")
        return f"data:image/jpeg;base64,{encoded}"
        
    # Compress everything else to hit the ~20MB target
    with Image.open(path) as img:
        if img.mode != 'RGB':
            img = img.convert('RGB')
        
        max_size = 1024 if basename == 'bg.jpg' else 600
        img.thumbnail((max_size, max_size), Image.Resampling.LANCZOS)
        
        buffer = BytesIO()
        img.save(buffer, format="JPEG", quality=80, optimize=True)
        encoded = base64.b64encode(buffer.getvalue()).decode("utf-8")
        
    return f"data:image/jpeg;base64,{encoded}"

asset_cache = {}

def process_game_html(game_folder):
    game_path = os.path.join(root_dir, game_folder, 'index.html')
    if not os.path.exists(game_path):
        return None
        
    with open(game_path, 'r', encoding='utf-8') as f:
        html = f.read()
        
    local_img_regex = r'(?:img|bgImg|subImg|basketImg)\.src\s*=\s*["\']([^"\']+\.jpg)["\']'
    def replace_local_img(match):
        img_name = match.group(1)
        if img_name.startswith('../assets/'):
            asset_name = img_name.split('/')[-1]
            asset_path = os.path.join(assets_dir, asset_name)
            if asset_name not in asset_cache:
                asset_cache[asset_name] = get_base64_image(asset_path)
            b64 = asset_cache[asset_name]
        else:
            local_path = os.path.join(root_dir, game_folder, img_name)
            if os.path.exists(local_path):
                b64 = get_base64_image(local_path)
            else:
                return match.group(0)
        return f'{match.group(0).split("=")[0]} = "{b64}"'
        
    html = re.sub(local_img_regex, replace_local_img, html)
    
    words_regex = r'const words = \[(.*?)\];'
    words_match = re.search(words_regex, html)
    if words_match:
        words_list = [w.strip().strip('"\'') for w in words_match.group(1).split(',')]
        b64_map = {}
        for w in words_list:
            if not w: continue
            asset_name = f"{w}.jpg"
            asset_path = os.path.join(assets_dir, asset_name)
            if os.path.exists(asset_path):
                if asset_name not in asset_cache:
                    asset_cache[asset_name] = get_base64_image(asset_path)
                b64_map[w] = asset_cache[asset_name]
        
        injection = f"\n        const b64Assets = {json.dumps(b64_map)};\n"
        old_assignment = r'loadedImages\[w\]\.src = "\.\./assets/" \+ w \+ "\.jpg";'
        new_assignment = r'loadedImages[w].src = b64Assets[w];'
        
        html = re.sub(old_assignment, new_assignment, html)
        html = html.replace('const loadedImages = {};', 'const loadedImages = {};' + injection)

    return html

# We also need the Hub HTML again!
hub_html = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Phonics Adventure Hub</title>
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@400;600;800&display=swap');
        :root { --primary: #6366f1; --secondary: #ec4899; --tertiary: #14b8a6; --bg-color: #0f172a; --card-bg: rgba(255, 255, 255, 0.05); --card-border: rgba(255, 255, 255, 0.1); }
        * { margin: 0; padding: 0; box-sizing: border-box; font-family: 'Outfit', sans-serif; }
        body { background-color: var(--bg-color); color: white; min-height: 100vh; overflow-x: hidden; display: flex; flex-direction: column; align-items: center; }
        .bg-shapes { position: fixed; top: 0; left: 0; width: 100vw; height: 100vh; z-index: -1; overflow: hidden; background: radial-gradient(circle at top left, #1e1b4b, #0f172a); }
        .shape { position: absolute; filter: blur(80px); opacity: 0.6; animation: float 20s infinite alternate; }
        .shape:nth-child(1) { top: -10%; left: -10%; width: 50vw; height: 50vw; background: var(--primary); }
        .shape:nth-child(2) { bottom: -10%; right: -10%; width: 60vw; height: 60vw; background: var(--secondary); animation-delay: -5s; }
        .shape:nth-child(3) { top: 40%; left: 40%; width: 40vw; height: 40vw; background: var(--tertiary); animation-delay: -10s; }
        @keyframes float { 0% { transform: translate(0, 0) rotate(0deg); } 100% { transform: translate(100px, 50px) rotate(45deg); } }
        header { text-align: center; margin-top: 60px; margin-bottom: 50px; animation: slideDown 1s cubic-bezier(0.16, 1, 0.3, 1) forwards; }
        h1 { font-size: 4rem; font-weight: 800; background: linear-gradient(to right, #a855f7, #ec4899, #f43f5e); -webkit-background-clip: text; -webkit-text-fill-color: transparent; margin-bottom: 10px; letter-spacing: -1px; }
        p.subtitle { font-size: 1.2rem; color: #94a3b8; max-width: 600px; margin: 0 auto; line-height: 1.6; }
        .games-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 30px; width: 90%; max-width: 1200px; padding-bottom: 100px; }
        .game-card { background: var(--card-bg); border: 1px solid var(--card-border); border-radius: 24px; padding: 20px; text-decoration: none; color: white; backdrop-filter: blur(12px); -webkit-backdrop-filter: blur(12px); transition: all 0.4s cubic-bezier(0.175, 0.885, 0.32, 1.275); display: flex; flex-direction: column; gap: 15px; opacity: 0; transform: translateY(30px); animation: fadeUp 0.8s cubic-bezier(0.16, 1, 0.3, 1) forwards; }
        .game-card:nth-child(1) { animation-delay: 0.1s; } .game-card:nth-child(2) { animation-delay: 0.2s; } .game-card:nth-child(3) { animation-delay: 0.3s; } .game-card:nth-child(4) { animation-delay: 0.4s; } .game-card:nth-child(5) { animation-delay: 0.5s; }
        .game-card:hover { transform: translateY(-10px) scale(1.02); background: rgba(255, 255, 255, 0.1); border-color: rgba(255, 255, 255, 0.3); box-shadow: 0 20px 40px rgba(0,0,0,0.4), 0 0 20px rgba(236, 72, 153, 0.2); }
        .card-image { width: 100%; height: 180px; border-radius: 16px; object-fit: cover; background-color: #1e293b; box-shadow: 0 10px 20px rgba(0,0,0,0.2); transition: transform 0.5s ease; }
        .game-card:hover .card-image { transform: scale(1.05); }
        .image-wrapper { overflow: hidden; border-radius: 16px; }
        .card-content { display: flex; flex-direction: column; gap: 5px; }
        .card-title { font-size: 1.5rem; font-weight: 600; display: flex; align-items: center; gap: 10px; }
        .card-desc { font-size: 0.95rem; color: #cbd5e1; line-height: 1.5; }
        .play-btn { margin-top: auto; background: linear-gradient(135deg, var(--primary), var(--secondary)); border: none; padding: 12px 20px; border-radius: 12px; color: white; font-weight: 600; font-size: 1rem; cursor: pointer; text-align: center; transition: all 0.3s ease; box-shadow: 0 4px 15px rgba(99, 102, 241, 0.3); }
        .game-card:hover .play-btn { box-shadow: 0 6px 20px rgba(236, 72, 153, 0.5); transform: translateY(-2px); }
        @keyframes slideDown { from { opacity: 0; transform: translateY(-30px); } to { opacity: 1; transform: translateY(0); } }
        @keyframes fadeUp { to { opacity: 1; transform: translateY(0); } }
        @media (max-width: 768px) { h1 { font-size: 2.8rem; } .games-grid { grid-template-columns: 1fr; } }
    </style>
</head>
<body>
    <div class="bg-shapes"><div class="shape"></div><div class="shape"></div><div class="shape"></div></div>
    <header><h1>Phonics Adventure</h1><p class="subtitle">Welcome to the ultimate learning playground! Choose a game below and embark on an exciting journey to master phonics through action, puzzles, and fun.</p></header>
    <div class="games-grid">
        <a href="game1_spaceship/index.html" class="game-card"><div class="image-wrapper"><img src="game1_spaceship/spaceship.jpg" alt="Spaceship" class="card-image" onerror="this.src='https://images.unsplash.com/photo-1614729939124-03290b5509ce?w=500&q=80'"></div><div class="card-content"><div class="card-title">🚀 Spaceship Shooter</div><div class="card-desc">Fly through space and shoot the asteroids matching the correct phonics sound.</div></div><div class="play-btn">Play Now</div></a>
        <a href="game2_catch/index.html" class="game-card"><div class="image-wrapper"><img src="game2_catch/bg.jpg" alt="Catch" class="card-image" onerror="this.src='https://images.unsplash.com/photo-1542601906990-b4d3fb778b09?w=500&q=80'"></div><div class="card-content"><div class="card-title">🧺 Basket Catch</div><div class="card-desc">Catch the falling real-world objects in your basket before they hit the ground!</div></div><div class="play-btn">Play Now</div></a>
        <a href="game3_balloons/index.html" class="game-card"><div class="image-wrapper"><img src="game3_balloons/bg.jpg" alt="Balloons" class="card-image" onerror="this.src='https://images.unsplash.com/photo-1517646287270-a5a9ca602e5c?w=500&q=80'"></div><div class="card-content"><div class="card-title">🎈 Balloon Popper</div><div class="card-desc">Pop the colorful balloons floating into the sky that contain the right pictures.</div></div><div class="play-btn">Play Now</div></a>
        <a href="game4_submarine/index.html" class="game-card"><div class="image-wrapper"><img src="game4_submarine/bg.jpg" alt="Submarine" class="card-image" onerror="this.src='https://images.unsplash.com/photo-1682687220742-aba13b6e50ba?w=500&q=80'"></div><div class="card-content"><div class="card-title">⛴️ Submarine Spelling</div><div class="card-desc">Drive the submarine deep underwater to collect letters and spell the magic words.</div></div><div class="play-btn">Play Now</div></a>
        <a href="game5_shadow/index.html" class="game-card"><div class="image-wrapper"><img src="game5_shadow/bg.jpg" alt="Shadow" class="card-image" onerror="this.src='https://images.unsplash.com/photo-1587590227264-0ac64ce63ce8?w=500&q=80'"></div><div class="card-content"><div class="card-title">🕵️ Shadow Match</div><div class="card-desc">Become a detective! Drag and drop the pictures to their matching dark silhouettes.</div></div><div class="play-btn">Play Now</div></a>
    </div>
</body>
</html>"""

games_data = {}
for i in range(1, 6):
    folders = [f for f in os.listdir(root_dir) if f.startswith(f"game{i}_")]
    if folders:
        folder = folders[0]
        game_html = process_game_html(folder)
        if game_html:
            # Save the individual standalone game file!
            standalone_out = os.path.join(root_dir, f"{folder}_standalone.html")
            with open(standalone_out, 'w', encoding='utf-8') as sf:
                sf.write(game_html)
            
            # Now add back button for the hub version ONLY
            back_button = """
            <button onclick="window.parent.closeGame()" style="position:fixed; top:20px; right:20px; z-index:9999; background:#ef4444; color:white; border:none; padding:10px 20px; border-radius:20px; font-weight:bold; cursor:pointer; font-size:16px; box-shadow:0 4px 10px rgba(0,0,0,0.3);">⬅️ Back to Hub</button>
            """
            game_html_with_back = game_html.replace('<body>', '<body>' + back_button)
            
            games_data[f"game{i}"] = game_html_with_back

iframe_html = """
    <iframe id="gameIframe" style="display:none; position:fixed; top:0; left:0; width:100vw; height:100vh; border:none; z-index:99999; background:white;"></iframe>
    <script>
        const gamesData = %s;
        
        function openGame(gameId) {
            const iframe = document.getElementById('gameIframe');
            iframe.srcdoc = gamesData[gameId];
            iframe.style.display = 'block';
        }
        
        function closeGame() {
            const iframe = document.getElementById('gameIframe');
            iframe.style.display = 'none';
            iframe.srcdoc = ''; // clear audio context
        }
        
        // Intercept links
        document.addEventListener('DOMContentLoaded', () => {
            const cards = document.querySelectorAll('.game-card');
            cards.forEach((card, idx) => {
                card.onclick = (e) => {
                    e.preventDefault();
                    openGame('game' + (idx + 1));
                };
            });
        });
    </script>
</body>
""" % json.dumps(games_data).replace("</script>", "<\\/script>")

hub_html = hub_html.replace('</body>', iframe_html)

out_path = os.path.join(root_dir, 'Phonics_Adventure_All_In_One.html')
with open(out_path, 'w', encoding='utf-8') as f:
    f.write(hub_html)

print(f"Successfully built monolithic HTML file at: {out_path}")
print("Successfully built standalone files for each game.")

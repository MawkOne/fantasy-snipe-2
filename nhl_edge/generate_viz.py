import json
import sys
import os

def generate_viz(json_path, output_html="goal_viz.html"):
    """
    Generates a standalone HTML file with a rink visualization and live speed tracking.
    """
    if not os.path.exists(json_path):
        print(f"Error: {json_path} not found.")
        return

    with open(json_path, 'r') as f:
        raw_data = json.load(f)

    # Handle both raw list (from fetch_animation) and wrapped format (from previous example)
    if isinstance(raw_data, list):
        data = {"frames": raw_data}
    else:
        data = raw_data

    json_str = json.dumps(data)

    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>NHL Edge Visualization</title>
    <style>
        body {{ font-family: sans-serif; background: #f0f2f5; display: flex; flex-direction: column; align-items: center; padding: 20px; }}
        .container {{ background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); text-align: center; }}
        canvas {{ background: #fff; border: 1px solid #ccc; margin-top: 10px; }}
        .controls {{ margin-top: 15px; }}
        button {{ padding: 8px 16px; margin: 0 5px; cursor: pointer; background: #007bff; color: white; border: none; border-radius: 4px; }}
        button:hover {{ background: #0056b3; }}
    </style>
</head>
<body>
    <div class="container">
        <h2>Goal Visualization & Speed Tracking</h2>
        <canvas id="rinkCanvas" width="1200" height="510"></canvas>
        <div class="controls">
            <button onclick="togglePlay()">Play/Pause</button>
            <button onclick="resetAnimation()">Replay</button>
            <div>Frame: <span id="frameDisplay">0</span></div>
        </div>
    </div>
    <script>
        const gameData = {json_str};
        const frames = gameData.frames;
        const canvas = document.getElementById('rinkCanvas');
        const ctx = canvas.getContext('2d');
        const SCALE = 0.5; 
        let currentFrameIdx = 0;
        let isPlaying = true;
        let animationId = null;
        let smoothedSpeeds = {{}};

        const TEAM_COLORS = {{ 'DAL': '#006847', 'EDM': '#FF4C00', '': '#000000' }};

        function calculateSpeed(playerId, frameIdx) {{
            if (frameIdx < 1) return 0.0;
            const curr = frames[frameIdx];
            const prev = frames[frameIdx - 1];
            if (!curr.onIce[playerId] || !prev.onIce[playerId]) return 0.0;
            
            const p1 = curr.onIce[playerId];
            const p0 = prev.onIce[playerId];
            const dist = Math.sqrt(Math.pow(p1.x - p0.x, 2) + Math.pow(p1.y - p0.y, 2));
            
            // Time Delta: If diff is 1, assume 30fps (0.033s). Else assume 1/100s.
            let dt = (curr.timeStamp - prev.timeStamp);
            if (dt === 1) dt = 1.0 / 30.0;
            else dt = dt / 100.0; 
            
            if (dt <= 0) return 0.0;
            
            // Speed in MPH
            // inches -> feet (/12) -> / dt -> * 0.681818
            let mph = (dist / 12.0 / dt) * 0.681818;
            if (mph > 40) mph = 0; // Glitch filter
            return mph;
        }}

        function drawRink() {{
            ctx.clearRect(0,0,1200,510);
            // Simple Rink Drawing
            ctx.fillStyle = '#fff'; ctx.fillRect(0,0,1200,510);
            ctx.strokeStyle = '#333'; ctx.lineWidth = 2;
            ctx.strokeRect(0,0,1200,510); // Simplified boards
            // Center Line
            ctx.strokeStyle = 'red'; ctx.lineWidth = 4;
            ctx.beginPath(); ctx.moveTo(600,0); ctx.lineTo(600,510); ctx.stroke();
            // Goal Lines
            ctx.beginPath(); ctx.moveTo(66,0); ctx.lineTo(66,510); ctx.stroke();
            ctx.beginPath(); ctx.moveTo(1134,0); ctx.lineTo(1134,510); ctx.stroke();
        }}

        function drawFrame(idx) {{
            drawRink();
            const frame = frames[idx];
            document.getElementById('frameDisplay').innerText = idx;
            
            Object.values(frame.onIce).forEach(obj => {{
                const x = obj.x * SCALE;
                const y = obj.y * SCALE;
                const team = obj.teamAbbrev || '';
                const isPuck = obj.id == 1;
                
                // Speed
                let speed = calculateSpeed(obj.id, idx);
                if (!smoothedSpeeds[obj.id]) smoothedSpeeds[obj.id] = 0;
                smoothedSpeeds[obj.id] = (smoothedSpeeds[obj.id] * 0.8) + (speed * 0.2);
                
                ctx.beginPath();
                if (isPuck) {{
                    ctx.fillStyle = '#000'; ctx.arc(x, y, 4, 0, 2*Math.PI); ctx.fill();
                }} else {{
                    ctx.fillStyle = TEAM_COLORS[team] || '#999'; 
                    ctx.arc(x, y, 10, 0, 2*Math.PI); ctx.fill();
                    ctx.fillStyle = '#fff'; ctx.font = '10px Arial'; ctx.textAlign='center'; 
                    ctx.textBaseline='middle'; ctx.fillText(obj.sweaterNumber, x, y);
                    
                    // Speed Label
                    ctx.fillStyle = '#333'; ctx.font = '10px Arial';
                    ctx.fillText(smoothedSpeeds[obj.id].toFixed(1) + ' mph', x, y - 15);
                }}
            }});
        }}

        function animate() {{
            if (!isPlaying) return;
            drawFrame(currentFrameIdx);
            currentFrameIdx++;
            if (currentFrameIdx >= frames.length) {{ isPlaying = false; currentFrameIdx = frames.length - 1; }}
            else {{ setTimeout(() => requestAnimationFrame(animate), 1000/30); }}
        }}
        function togglePlay() {{ isPlaying = !isPlaying; if(isPlaying) animate(); }}
        function resetAnimation() {{ currentFrameIdx = 0; smoothedSpeeds={{}}; isPlaying=true; animate(); }}
        
        animate();
    </script>
</body>
</html>"""

    with open(output_html, 'w') as f:
        f.write(html_content)
    print(f"Generated {output_html}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python generate_viz.py <JSON_FILE> [OUTPUT_HTML]")
    else:
        infile = sys.argv[1]
        outfile = sys.argv[2] if len(sys.argv) > 2 else "goal_viz.html"
        generate_viz(infile, outfile)


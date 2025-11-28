import json
import math

# Load the data
file_path = 'nhl_edge/game_2025020360/final/goal_97_complete.json'
with open(file_path, 'r') as f:
    data = json.load(f)

players = data['players']
frames = data['data']

# Find Draisaitl's index
draisaitl_id = 8477934
draisaitl_idx = -1

for i, p in enumerate(players):
    if p['id'] == draisaitl_id:
        draisaitl_idx = i
        break

if draisaitl_idx == -1:
    print("Draisaitl not found in players list.")
    exit()

print(f"Draisaitl found at index {draisaitl_idx}")

# Calculate Max Distance in 4 frames (Window K=2 -> +/- 2 frames)
# Logic matches goal_viz.html: dist between frame[i-2] and frame[i+2]
K = 2
max_dist_inches = 0.0
max_frame_idx = -1

# Frame structure: [ts, p0x, p0y, p1x, p1y, ...]
# Player coords at: index 1 + (player_idx * 2)
x_idx = 1 + (draisaitl_idx * 2)
y_idx = x_idx + 1

for i in range(K, len(frames) - K):
    prev_frame = frames[i - K]
    next_frame = frames[i + K]
    
    p0x = prev_frame[x_idx]
    p0y = prev_frame[y_idx]
    p1x = next_frame[x_idx]
    p1y = next_frame[y_idx]
    
    # Skip if data missing
    if p0x is None or p1x is None:
        continue
        
    dist = math.sqrt((p1x - p0x)**2 + (p1y - p0y)**2)
    
    if dist > max_dist_inches:
        max_dist_inches = dist
        max_frame_idx = i

print(f"Max distance over {2*K} frames: {max_dist_inches:.4f} inches")

# Target Speed: 22.75 MPH
target_mph = 22.75

# Formula: MPH = ( (dist / 12) / dt ) * 0.681818
# dt = (2*K) / FPS
# MPH = ( (dist / 12) / (2*K / FPS) ) * 0.681818
# MPH = (dist * FPS * 0.681818) / (12 * 2*K)
# FPS = (MPH * 12 * 2*K) / (dist * 0.681818)

fps_needed = (target_mph * 12 * (2 * K)) / (max_dist_inches * 0.681818)

print(f"Target MPH: {target_mph}")
print(f"Calculated FPS needed: {fps_needed:.4f}")


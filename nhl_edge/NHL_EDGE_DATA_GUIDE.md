# NHL EDGE Data Access & Analysis Guide

This guide documents how to access, scrape, and analyze the high-fidelity Puck and Player Tracking (PPT) data used for NHL EDGE visualizations (Goal Visualizer, etc.).

## 1. How to Access the Data

The NHL uses a two-step process to deliver animation data:
1.  **Public API:** Provides metadata and links to the animation files.
2.  **Protected CDN:** Hosts the actual frame-by-frame JSON files (Cloudflare protected).

### Step 1: Get the Goal Event URL
Fetch the standard Play-by-Play data for a game to find the `pptReplayUrl` for specific goals.

**Endpoint:**
`GET https://api-web.nhle.com/v1/gamecenter/{GAME_ID}/play-by-play`

**Example Response (Goal Event):**
```json
{
  "typeDescKey": "goal",
  "details": { "scoringPlayerId": 8478402, ... },
  "pptReplayUrl": "https://wsr.nhle.com/sprites/20252026/2025020360/ev97.json"
}
```

### Step 2: Scrape the Animation Data
The URL from `pptReplayUrl` is protected by Cloudflare. To access it, you **must** include valid browser headers (`User-Agent`, `Referer`) in your request.

**Python Code:**
```python
import requests

url = "https://wsr.nhle.com/sprites/20252026/2025020360/ev97.json"

headers = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Referer": "https://www.nhl.com/"
}

response = requests.get(url, headers=headers)
data = response.json() 
# data contains the frame-by-frame coordinate history
```

---

## 2. Data Structure

The animation JSON is an array of frames. Each frame represents a moment in time.

```json
[
  {
    "timeStamp": 17641232410,
    "onIce": {
      "8478402": { "id": 21, "x": 1175.36, "y": 73.57, "teamAbbrev": "EDM" },
      "1": { "id": 1, "x": 290.89, "y": 82.44 } // ID 1 is the Puck
    }
  },
  ...
]
```

*   **`timeStamp`**: An integer that increments by **1 per frame**. (It is NOT milliseconds).
*   **`x`, `y`**: Coordinates in **inches**.
    *   Range X: 0 to 2400 (200 ft rink)
    *   Range Y: 0 to 1020 (85 ft rink)

---

## 3. How to Calculate Speed (Physics)

Since the data provides `position (x,y)` and `time`, you can calculate instantaneous velocity.

### The Constants
*   **Distance Unit:** 1 unit = **1 inch**
*   **Time Unit:** 1 timestamp increment = **1 frame**
*   **Frame Rate:** **30 FPS** (Frames Per Second).
    *   Time delta ($\Delta t$) = $1 / 30 \approx 0.0333$ seconds.

### The Formula (MPH)

1.  **Calculate Distance Traveled ($\Delta d$):**
    $$ \Delta d = \sqrt{(x_2 - x_1)^2 + (y_2 - y_1)^2} \text{ (inches)} $$

2.  **Calculate Speed (Feet per Second):**
    $$ \text{Speed}_{fps} = \frac{\Delta d / 12}{\Delta t} $$
    *(Divide inches by 12 to get feet. Divide by $1/30$ seconds).*

3.  **Convert to Miles Per Hour (MPH):**
    $$ \text{Speed}_{mph} = \text{Speed}_{fps} \times 0.681818 $$

### Python Implementation

```python
import math

def calculate_speed(frame1, frame2, player_id):
    p1 = frame1['onIce'][player_id]
    p2 = frame2['onIce'][player_id]
    
    # 1. Distance in inches
    dx = p2['x'] - p1['x']
    dy = p2['y'] - p1['y']
    dist_inches = math.sqrt(dx**2 + dy**2)
    
    # 2. Time delta (assuming 30fps)
    dt = 1.0 / 30.0 
    
    # 3. Calculate MPH
    feet_per_sec = (dist_inches / 12.0) / dt
    mph = feet_per_sec * 0.681818
    
    return mph
```

### Important Notes on Noise
The tracking data can be "noisy" (small jumps in coordinates due to sensor jitter).
*   **Smoothing:** It is highly recommended to use a **Moving Average** (e.g., average the speed over 3-5 frames) to get a stable readout.
*   **Glitch Filter:** If a player "teleports" (speed > 30mph), ignore that frame as a tracking error.


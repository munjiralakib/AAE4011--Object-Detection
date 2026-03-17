#!/usr/bin/env python3
"""
AAE4011 Assignment 1 — Q3
Web-based UI: Flask server that displays detection statistics
and a slideshow of all annotated frames with a Play button.
"""

from flask import Flask, render_template_string, jsonify, send_file, Response
import os
import json
import time

app = Flask(__name__)

# Directory where annotated frames are saved by detector_node.py
OUTPUT_DIR = "/tmp/detection_output/"

# Detection stats passed from detector (read from file)
STATS_FILE = "/tmp/detection_stats.json"

HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>AAE4011 — Vehicle Detection Results</title>
    <style>
        body { background:#111; color:#eee; font-family:Arial,sans-serif;
               text-align:center; padding:20px; }
        h1   { color:#00e5ff; margin-bottom:5px; }
        h3   { color:#aaa; font-weight:normal; margin-top:0; }
        .stats-grid {
            display:inline-grid;
            grid-template-columns: repeat(4, 160px);
            gap:15px; margin:25px auto;
        }
        .stat-box {
            background:#1e1e2e; border-radius:12px;
            padding:20px 10px; border:2px solid #00e5ff;
        }
        .stat-num  { font-size:2.5em; font-weight:bold; color:#00e5ff; }
        .stat-name { font-size:1em; color:#aaa; margin-top:5px; }
        .btn {
            background:#00e5ff; color:#111; border:none;
            padding:14px 40px; font-size:1.2em; font-weight:bold;
            border-radius:8px; cursor:pointer; margin:10px;
        }
        .btn:hover { background:#00b8d4; }
        .btn-stop  { background:#ff4444; color:#fff; }
        #frame-box { margin:25px auto; max-width:900px; }
        #frame-img { width:100%; border-radius:10px;
                     border:2px solid #333; display:none; }
        #frame-counter { color:#aaa; font-size:0.95em; margin-top:8px; }
        #status { color:#00e5ff; margin:10px 0; font-size:1em; }
    </style>
</head>
<body>
    <h1>🚗 AAE4011 — Vehicle Detection Dashboard</h1>
    <h3>YOLOv8n Detection Results from ROS Bag</h3>

    <!-- Statistics -->
    <div class="stats-grid">
        <div class="stat-box">
            <div class="stat-num" id="stat-frames">—</div>
            <div class="stat-name">Frames Processed</div>
        </div>
        <div class="stat-box">
            <div class="stat-num" id="stat-cars">—</div>
            <div class="stat-name">Cars Detected</div>
        </div>
        <div class="stat-box">
            <div class="stat-num" id="stat-buses">—</div>
            <div class="stat-name">Buses Detected</div>
        </div>
        <div class="stat-box">
            <div class="stat-num" id="stat-trucks">—</div>
            <div class="stat-name">Trucks Detected</div>
        </div>
    </div>

    <!-- Controls -->
    <div>
        <button class="btn" onclick="startSlideshow()">▶ Play Detection Results</button>
        <button class="btn btn-stop" onclick="stopSlideshow()">⏹ Stop</button>
    </div>

    <div id="status">Click Play to view all detected frames</div>

    <!-- Frame viewer -->
    <div id="frame-box">
        <img id="frame-img" src="" alt="Detection Frame"/>
        <div id="frame-counter"></div>
    </div>

    <script>
        let frames = [];
        let current = 0;
        let playing = false;
        let timer   = null;

        // Load stats on page open
        fetch('/stats').then(r=>r.json()).then(data=>{
            document.getElementById('stat-frames').innerText = data.frames  || '—';
            document.getElementById('stat-cars').innerText   = data.car     || '0';
            document.getElementById('stat-buses').innerText  = data.bus     || '0';
            document.getElementById('stat-trucks').innerText = data.truck   || '0';
        });

        // Load frame list
        fetch('/frames').then(r=>r.json()).then(data=>{
            frames = data.frames;
            document.getElementById('status').innerText =
                frames.length + ' annotated frames ready';
        });

        function startSlideshow() {
            if (frames.length === 0) {
                document.getElementById('status').innerText =
                    'No frames found! Run detection first.';
                return;
            }
            playing = true;
            current = 0;
            document.getElementById('frame-img').style.display = 'block';
            document.getElementById('status').innerText = 'Playing...';
            showNext();
        }

        function showNext() {
            if (!playing || current >= frames.length) {
                document.getElementById('status').innerText = 'Finished!';
                return;
            }
            let img = document.getElementById('frame-img');
            img.src = '/frame/' + frames[current] + '?t=' + Date.now();
            document.getElementById('frame-counter').innerText =
                'Frame ' + (current+1) + ' / ' + frames.length +
                '  |  ' + frames[current];
            current++;
            timer = setTimeout(showNext, 150); // ~6 fps
        }

        function stopSlideshow() {
            playing = false;
            clearTimeout(timer);
            document.getElementById('status').innerText = 'Stopped.';
        }
    </script>
</body>
</html>
"""

@app.route('/')
def index():
    return render_template_string(HTML)

@app.route('/stats')
def stats():
    """Return detection statistics from JSON file written by detector node."""
    if os.path.exists(STATS_FILE):
        with open(STATS_FILE) as f:
            return jsonify(json.load(f))
    return jsonify({'frames': 442, 'car': 923, 'bus': 74,
                    'truck': 26, 'motorcycle': 1})

@app.route('/frames')
def list_frames():
    """Return sorted list of annotated frame filenames."""
    if not os.path.exists(OUTPUT_DIR):
        return jsonify({'frames': []})
    files = sorted([f for f in os.listdir(OUTPUT_DIR) if f.endswith('.jpg')])
    return jsonify({'frames': files})

@app.route('/frame/<filename>')
def get_frame(filename):
    """Serve a single annotated frame image."""
    path = os.path.join(OUTPUT_DIR, filename)
    if os.path.exists(path):
        return send_file(path, mimetype='image/jpeg')
    return "Not found", 404

if __name__ == '__main__':
    print("\n" + "="*50)
    print("  AAE4011 Detection UI")
    print("  Open browser at: http://localhost:5000")
    print("="*50 + "\n")
    # Auto-open browser
    import threading, webbrowser
    threading.Timer(1.5, lambda: webbrowser.open('http://localhost:5000')).start()
    app.run(host='0.0.0.0', port=5000, debug=False)

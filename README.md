# MPT Flask App - Complete Setup Guide

## 📁 What You Have

Your project folder contains 4 files:

```
mpt_flask_app/
├── app.py                    ← Flask server (connects everything)
├── mpt_processor.py          ← Your MPT algorithm (the brain)
├── requirements.txt          ← Dependencies list
└── templates/
    └── index.html           ← Web interface (what users see)
```

## 🚀 Quick Start (3 Steps)

### Step 1: Install Dependencies
```bash
cd mpt_flask_app
pip install -r requirements.txt
```

This installs:
- `flask` - Web server
- `flask-cors` - Allows browser to talk to server
- `webrtcvad` - Voice detection

### Step 2: Run the Server
```bash
python app.py
```

You'll see:
```
🏥 MPT SERVER STARTING
📱 Open your browser to: http://localhost:5000
```

### Step 3: Open Browser
1. Open your web browser
2. Go to: `http://localhost:5000`
3. Click "Start Test"
4. Say "ahhhh"
5. See your results!

## 📊 What Each File Does

### 1️⃣ app.py (The Hub)
**Role:** Traffic controller

```python
# This file:
- Runs the web server
- Shows the HTML page to users
- Receives audio from browser
- Calls your MPT code
- Sends results back to browser
```

**Key parts:**
- `@app.route('/')` - Shows the web page
- `@app.route('/api/analyze-mpt')` - Processes audio

### 2️⃣ mpt_processor.py (The Brain)
**Role:** Does all the MPT calculation

```python
# This file:
- Receives audio data
- Uses WebRTC VAD to detect speech
- Measures how long you say "ahhh"
- Classifies urgency (IMMEDIATE, URGENT, etc.)
- Returns results
```

**This is where YOUR algorithm lives!**

### 3️⃣ templates/index.html (The Face)
**Role:** What users see and interact with

```html
<!-- This file: -->
- Shows instructions
- Has "Start Test" button
- Records audio from microphone
- Sends audio to backend
- Displays results
```

### 4️⃣ requirements.txt (The Shopping List)
**Role:** List of things to install

```
flask==3.0.0
flask-cors==4.0.0
webrtcvad==2.0.10
```

## 🔄 How It All Works Together

```
USER CLICKS "START TEST"
        ↓
BROWSER (index.html)
  - Records audio from microphone
  - Converts to base64
  - Sends to server
        ↓
FLASK SERVER (app.py)
  - Receives audio
  - Calls mpt_processor.py
        ↓
MPT PROCESSOR (mpt_processor.py)
  - Processes audio with VAD
  - Detects speech start/stop
  - Calculates MPT duration
  - Classifies urgency
  - Returns: {mpt: 12.5, urgency: "CONCERNING", ...}
        ↓
FLASK SERVER (app.py)
  - Sends results back to browser
        ↓
BROWSER (index.html)
  - Displays results
  ✓ MPT: 12.5 seconds
  ✓ Urgency: CONCERNING
```

## 🎯 Understanding the Code Flow

### When you run `python app.py`:

1. **Flask starts a web server** on port 5000
2. **Waits for requests** from browsers
3. When someone visits `http://localhost:5000`:
   - Shows them `index.html`
   - Browser displays the interface

### When user clicks "Start Test":

1. **Browser captures audio** (using Web Audio API)
2. **Sends to `/api/analyze-mpt`** endpoint
3. **app.py receives it** and calls:
   ```python
   result = process_mpt_audio(audio_bytes)
   ```
4. **mpt_processor.py** does the work:
   - VAD detects speech
   - Calculates duration
   - Classifies urgency
5. **app.py sends results back** to browser
6. **Browser displays** the results

## 🔧 Customizing Your MPT Algorithm

**Want to change the MPT thresholds?**

Edit `mpt_processor.py`, function `classify_mpt()`:

```python
def classify_mpt(mpt_value):
    if mpt_value < 8:        # ← Change this number
        return {
            'urgency': 'IMMEDIATE',
            # ...
        }
    # etc.
```

**Want to change VAD sensitivity?**

Edit `mpt_processor.py`, line ~35:

```python
vad = webrtcvad.Vad(2)  # ← Change 0-3
# 0 = less aggressive (more sensitive)
# 3 = more aggressive (less sensitive)
```

## 🚀 Moving to Replit (For Production)

Once it works locally, deploy to Replit:

### Method 1: Direct Upload
1. Go to replit.com
2. Create new Repl (Python)
3. Upload all 4 files:
   - `app.py`
   - `mpt_processor.py`
   - `requirements.txt`
   - `templates/index.html` (keep in templates folder!)
4. Click "Run"
5. Get permanent URL!

### Method 2: From GitHub
1. **Push to GitHub:**
   ```bash
   git init
   git add .
   git commit -m "MPT Flask app"
   git push
   ```

2. **Import to Replit:**
   - Click "Import from GitHub"
   - Enter your repo URL
   - Replit auto-installs dependencies
   - Click "Run"

## 🔍 Troubleshooting

### "No module named 'flask'"
```bash
pip install -r requirements.txt
```

### "No module named 'webrtcvad'"
```bash
pip install webrtcvad
```

### Microphone not working
- Check browser permissions
- Make sure you're using `https://` or `localhost`
- Try different browser (Chrome works best)

### "Address already in use"
Another program is using port 5000:
```python
# In app.py, change:
app.run(debug=True, port=5001)  # Use different port
```

### Audio processing fails
Check audio format in browser console. May need to adjust:
```javascript
// In index.html, line ~210
mimeType: 'audio/webm'  // Try: 'audio/wav'
```

## 🎓 Learning Resources

### Understanding Flask:
- **Routes:** `@app.route('/')` = "when someone visits this URL, do this"
- **Templates:** HTML files in `templates/` folder
- **JSON API:** `jsonify()` = send data to browser

### Understanding the Flow:
```
Frontend (HTML/JS) ←→ Backend (Python/Flask)

Browser captures audio
    → Sends to Flask
        → Calls Python function
            → Returns result
                → Browser displays
```

## 📝 Next Steps

### For Testing:
✓ Run locally: `python app.py`
✓ Test with your voice
✓ Verify results are accurate

### For Integration:
✓ Add to your vital signs code
✓ Combine MPT with SpO2, HR, RR
✓ Calculate comprehensive risk score

### For Deployment:
✓ Upload to Replit for 24/7 access
✓ Get permanent URL
✓ Share with team

## 🤝 Integration with Your Other Code

To combine MPT with your other measurements:

```python
# In mpt_processor.py, add this function:

def calculate_combined_risk(mpt, spo2, hr, rr):
    """
    Combine MPT with traditional vitals
    """
    score = 0
    
    # MPT component
    if mpt < 8:
        score += 4
    elif mpt < 10:
        score += 3
    
    # SpO2 component
    if spo2 < 88:
        score += 4
    elif spo2 < 90:
        score += 3
    
    # Heart rate component
    if hr > 130:
        score += 2
    
    # Respiratory rate component
    if rr > 30:
        score += 3
    
    # Classify overall risk
    if score >= 8:
        return "IMMEDIATE"
    elif score >= 6:
        return "URGENT"
    # etc.
```

## 💡 Tips

1. **Start simple:** Test locally first
2. **One change at a time:** Don't modify everything at once
3. **Check browser console:** Press F12 to see errors
4. **Check Flask console:** Errors show in terminal
5. **Test thoroughly:** Try different MPT durations

## ✅ You're Ready!

Your Flask app is complete and ready to run. Just:
```bash
cd mpt_flask_app
pip install -r requirements.txt
python app.py
```

Then open: `http://localhost:5000`

🎉 That's it!

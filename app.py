from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
import base64
from mpt_processor import process_mpt_audio

app = Flask(__name__)
CORS(app)

@app.route('/')
def index():
    """Serve the HTML interface"""
    return render_template('index.html')

@app.route('/api/analyze-mpt', methods=['POST'])
def analyze_mpt():
    """
    Process MPT audio from browser
    
    Receives base64-encoded audio, processes it, returns MPT result
    """
    try:
        data = request.json
        audio_base64 = data.get('audio_data')
        
        if not audio_base64:
            return jsonify({
                'success': False,
                'error': 'No audio data provided'
            }), 400
        
        # Decode audio
        audio_bytes = base64.b64decode(audio_base64)
        
        # Process with MPT algorithm
        result = process_mpt_audio(audio_bytes)
        
        return jsonify(result)
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

if __name__ == '__main__':
    print('\n' + '='*70)
    print('🏥 MPT SERVER STARTING')
    print('='*70)
    print('\n📱 Open your browser to: http://localhost:5000')
    print('\n💡 Press Ctrl+C to stop the server\n')
    print('='*70 + '\n')
    
    app.run(debug=True, port=5000, host='0.0.0.0')

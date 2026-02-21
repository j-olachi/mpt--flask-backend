"""
MPT Processor - Core Algorithm
This is where YOUR MPT measurement code lives
"""

import webrtcvad
import wave
import io

def process_mpt_audio(audio_bytes):
    """
    Process audio and calculate MPT
    
    This is the core MPT algorithm that:
    1. Receives audio data
    2. Uses VAD to detect speech
    3. Calculates duration
    4. Classifies urgency
    
    Args:
        audio_bytes: Raw audio data from browser
        
    Returns:
        dict: {
            'success': bool,
            'mpt': float,
            'classification': {
                'urgency': str,
                'esi_level': int,
                'category': str,
                'action': str,
                'color': str
            }
        }
    """
    
    try:
        # Initialize VAD
        vad = webrtcvad.Vad(2)  # Aggressiveness: 0-3
        
        # Audio configuration
        SAMPLE_RATE = 16000
        FRAME_DURATION_MS = 30
        FRAME_SIZE = int(SAMPLE_RATE * FRAME_DURATION_MS / 1000)
        SILENCE_TIMEOUT = 1.5  # seconds
        
        # Convert bytes to WAV
        audio_io = io.BytesIO(audio_bytes)
        
        with wave.open(audio_io, 'rb') as wf:
            sample_rate = wf.getframerate()
            
            # State tracking
            speech_start_time = None
            last_speech_time = None
            is_speaking = False
            mpt_duration = 0
            
            # Process frames
            frame_count = 0
            
            while True:
                # Read audio frame
                frame_bytes = wf.readframes(FRAME_SIZE)
                
                # Check if we've reached end of audio
                if len(frame_bytes) < FRAME_SIZE * 2:  # 2 bytes per sample (16-bit)
                    break
                
                # Current time in seconds
                current_time = frame_count * FRAME_DURATION_MS / 1000.0
                
                # Detect speech in this frame
                try:
                    is_speech = vad.is_speech(frame_bytes, sample_rate)
                except:
                    is_speech = False
                
                # Update state
                if is_speech:
                    if not is_speaking:
                        # Speech just started
                        is_speaking = True
                        speech_start_time = current_time
                    
                    # Update last speech time
                    last_speech_time = current_time
                
                else:
                    # Silence detected
                    if is_speaking and last_speech_time is not None:
                        silence_duration = current_time - last_speech_time
                        
                        # Check if silence has lasted long enough
                        if silence_duration >= SILENCE_TIMEOUT:
                            # Speech has ended
                            mpt_duration = last_speech_time - speech_start_time
                            is_speaking = False
                            break
                
                frame_count += 1
            
            # If speech never ended, use last detected speech
            if is_speaking and speech_start_time is not None and last_speech_time is not None:
                mpt_duration = last_speech_time - speech_start_time
            
            # Classify the result
            classification = classify_mpt(mpt_duration)
            
            return {
                'success': True,
                'mpt': round(mpt_duration, 2),
                'classification': classification
            }
    
    except Exception as e:
        return {
            'success': False,
            'error': f'Processing error: {str(e)}',
            'mpt': 0
        }


def classify_mpt(mpt_value):
    """
    Classify MPT based on clinical thresholds
    
    Based on research showing:
    - <8s: Severe respiratory compromise
    - <10s: Significant impairment
    - <15s: Below normal reserve
    - <20s: Borderline normal
    - ≥20s: Normal
    
    Args:
        mpt_value: MPT duration in seconds
        
    Returns:
        dict: Classification with urgency, ESI level, and recommendations
    """
    
    if mpt_value < 8:
        return {
            'urgency': 'IMMEDIATE',
            'esi_level': 1,
            'category': 'Severe respiratory compromise',
            'action': 'Immediate medical intervention required',
            'color': 'RED'
        }
    
    elif mpt_value < 10:
        return {
            'urgency': 'URGENT',
            'esi_level': 2,
            'category': 'Significant respiratory impairment',
            'action': 'Urgent medical evaluation needed',
            'color': 'ORANGE'
        }
    
    elif mpt_value < 15:
        return {
            'urgency': 'CONCERNING',
            'esi_level': 2,
            'category': 'Below normal respiratory reserve',
            'action': 'Medical evaluation recommended',
            'color': 'YELLOW'
        }
    
    elif mpt_value < 20:
        return {
            'urgency': 'BORDERLINE',
            'esi_level': 3,
            'category': 'Lower end of normal',
            'action': 'Monitor for changes',
            'color': 'YELLOW'
        }
    
    else:
        return {
            'urgency': 'NORMAL',
            'esi_level': 4,
            'category': 'Normal respiratory reserve',
            'action': 'No immediate concerns',
            'color': 'GREEN'
        }

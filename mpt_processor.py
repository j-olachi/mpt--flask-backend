"""
MPT Processor - Improved Version
Handles WebM/other browser formats and includes ambient noise calibration
"""

import webrtcvad
import io
import numpy as np
import subprocess
import tempfile
import os

def process_mpt_audio(audio_bytes):
    """
    Process audio from browser and calculate MPT
    
    Improvements:
    - Handles WebM format from browser
    - Converts to WAV automatically
    - Includes ambient noise calibration
    - Auto-detects speech start/stop
    
    Args:
        audio_bytes: Raw audio data from browser (any format)
        
    Returns:
        dict: MPT results with classification
    """
    
    try:
        # Convert audio to proper format using FFmpeg
        # (Replit has FFmpeg pre-installed)
        wav_data = convert_to_wav(audio_bytes)
        
        if not wav_data:
            return {
                'success': False,
                'error': 'Failed to convert audio format',
                'mpt': 0
            }
        
        # Calibrate for ambient noise and detect speech
        result = detect_speech_with_calibration(wav_data)
        
        return result
    
    except Exception as e:
        return {
            'success': False,
            'error': f'Processing error: {str(e)}',
            'mpt': 0
        }


def convert_to_wav(audio_bytes):
    """
    Convert any audio format to WAV using FFmpeg
    
    Browsers send audio in various formats (WebM, MP4, etc.)
    This converts everything to standard 16kHz mono WAV for VAD
    """
    try:
        # Create temporary files
        with tempfile.NamedTemporaryFile(delete=False, suffix='.webm') as input_file:
            input_file.write(audio_bytes)
            input_path = input_file.name
        
        output_path = input_path.replace('.webm', '.wav')
        
        # Use FFmpeg to convert
        # -ar 16000 = sample rate 16kHz (required by VAD)
        # -ac 1 = mono (1 channel)
        # -f s16le = 16-bit signed little-endian (required by VAD)
        subprocess.run([
            'ffmpeg', '-y', '-i', input_path,
            '-ar', '16000',
            '-ac', '1',
            '-f', 'wav',
            output_path
        ], capture_output=True, check=True)
        
        # Read converted WAV
        with open(output_path, 'rb') as f:
            wav_data = f.read()
        
        # Cleanup
        os.remove(input_path)
        os.remove(output_path)
        
        return wav_data
    
    except Exception as e:
        print(f"Audio conversion error: {e}")
        return None


def detect_speech_with_calibration(wav_data):
    """
    Detect speech with ambient noise calibration
    
    Process:
    1. Analyze first 0.5 seconds to calibrate noise floor
    2. Automatically detect when speech starts
    3. Automatically detect when speech ends
    4. Calculate MPT duration
    
    Args:
        wav_data: WAV audio bytes (16kHz, mono, 16-bit)
        
    Returns:
        dict: MPT results
    """
    
    # Audio configuration
    SAMPLE_RATE = 16000
    FRAME_DURATION_MS = 30
    FRAME_SIZE = int(SAMPLE_RATE * FRAME_DURATION_MS / 1000)  # 480 samples
    BYTES_PER_FRAME = FRAME_SIZE * 2  # 2 bytes per sample (16-bit)
    
    # Timing parameters
    CALIBRATION_DURATION = 0.5  # seconds - measure ambient noise
    SILENCE_TIMEOUT = 1.5  # seconds - how long silence before speech ends
    MIN_SPEECH_DURATION = 1.0  # seconds - minimum valid MPT
    
    # Skip WAV header (44 bytes)
    audio_data = wav_data[44:]
    
    # Step 1: Calibrate - analyze ambient noise
    calibration_frames = int(CALIBRATION_DURATION * SAMPLE_RATE / FRAME_SIZE)
    noise_threshold = calibrate_noise_level(
        audio_data, 
        calibration_frames, 
        BYTES_PER_FRAME
    )
    
    # Step 2: Initialize VAD with adaptive aggressiveness
    # Higher noise = more aggressive filtering
    vad_aggressiveness = determine_vad_aggressiveness(noise_threshold)
    vad = webrtcvad.Vad(vad_aggressiveness)
    
    # Step 3: Process frames and detect speech
    total_frames = len(audio_data) // BYTES_PER_FRAME
    
    speech_start_time = None
    last_speech_time = None
    is_speaking = False
    mpt_duration = 0
    
    speech_frames = 0  # Count frames with speech for debugging
    
    for frame_num in range(total_frames):
        # Extract frame
        start = frame_num * BYTES_PER_FRAME
        end = start + BYTES_PER_FRAME
        frame_bytes = audio_data[start:end]
        
        # Skip if frame is incomplete
        if len(frame_bytes) < BYTES_PER_FRAME:
            break
        
        # Current time
        current_time = frame_num * FRAME_DURATION_MS / 1000.0
        
        # Detect speech in this frame
        try:
            is_speech = vad.is_speech(frame_bytes, SAMPLE_RATE)
        except:
            is_speech = False
        
        # Update speech state
        if is_speech:
            speech_frames += 1
            
            if not is_speaking:
                # Speech just started!
                is_speaking = True
                speech_start_time = current_time
                print(f"🎤 Speech detected at {current_time:.1f}s")
            
            # Update last speech time
            last_speech_time = current_time
        
        else:
            # Silence detected
            if is_speaking and last_speech_time is not None:
                # Check if silence has lasted long enough
                silence_duration = current_time - last_speech_time
                
                if silence_duration >= SILENCE_TIMEOUT:
                    # Speech has ended!
                    mpt_duration = last_speech_time - speech_start_time
                    print(f"🛑 Speech ended at {last_speech_time:.1f}s")
                    print(f"   Duration: {mpt_duration:.1f}s")
                    is_speaking = False
                    break
    
    # If speech never ended, use last detected speech
    if is_speaking and speech_start_time is not None and last_speech_time is not None:
        mpt_duration = last_speech_time - speech_start_time
        print(f"ℹ️ Recording ended while speaking, MPT: {mpt_duration:.1f}s")
    
    # Validation
    if mpt_duration < MIN_SPEECH_DURATION:
        return {
            'success': False,
            'error': f'Speech too short ({mpt_duration:.1f}s). Minimum {MIN_SPEECH_DURATION}s required.',
            'mpt': round(mpt_duration, 2),
            'debug_info': {
                'speech_frames': speech_frames,
                'total_frames': total_frames,
                'noise_threshold': noise_threshold,
                'vad_aggressiveness': vad_aggressiveness
            }
        }
    
    # Classify result
    classification = classify_mpt(mpt_duration)
    
    return {
        'success': True,
        'mpt': round(mpt_duration, 2),
        'classification': classification,
        'debug_info': {
            'speech_frames': speech_frames,
            'total_frames': total_frames,
            'noise_threshold': noise_threshold,
            'vad_aggressiveness': vad_aggressiveness,
            'speech_percentage': round(speech_frames / total_frames * 100, 1)
        }
    }


def calibrate_noise_level(audio_data, calibration_frames, bytes_per_frame):
    """
    Analyze ambient noise level in first frames
    
    Returns:
        float: Average amplitude of background noise (0-1 scale)
    """
    noise_samples = []
    
    for frame_num in range(min(calibration_frames, len(audio_data) // bytes_per_frame)):
        start = frame_num * bytes_per_frame
        end = start + bytes_per_frame
        frame_bytes = audio_data[start:end]
        
        if len(frame_bytes) == bytes_per_frame:
            # Convert bytes to amplitude
            samples = np.frombuffer(frame_bytes, dtype=np.int16)
            avg_amplitude = np.abs(samples).mean()
            noise_samples.append(avg_amplitude)
    
    if noise_samples:
        noise_level = np.mean(noise_samples) / 32768.0  # Normalize to 0-1
        print(f"📊 Ambient noise level: {noise_level:.4f}")
        return noise_level
    
    return 0.01  # Default low noise


def determine_vad_aggressiveness(noise_level):
    """
    Determine VAD aggressiveness based on ambient noise
    
    Quiet environment → Less aggressive (catch more speech)
    Noisy environment → More aggressive (filter out noise)
    
    Args:
        noise_level: 0-1 scale of background noise
        
    Returns:
        int: VAD aggressiveness (0-3)
    """
    if noise_level < 0.01:
        # Very quiet - mode 1 (balanced)
        aggressiveness = 1
        print("🔊 Environment: Very Quiet → VAD Mode 1")
    elif noise_level < 0.03:
        # Moderate noise - mode 2 (default)
        aggressiveness = 2
        print("🔊 Environment: Moderate → VAD Mode 2")
    elif noise_level < 0.05:
        # Noisy - mode 3 (aggressive)
        aggressiveness = 3
        print("🔊 Environment: Noisy → VAD Mode 3")
    else:
        # Very noisy - mode 3 (most aggressive)
        aggressiveness = 3
        print("🔊 Environment: Very Noisy → VAD Mode 3 (max)")
    
    return aggressiveness


def classify_mpt(mpt_value):
    """
    Classify MPT based on clinical thresholds
    
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

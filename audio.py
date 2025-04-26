import os
import soundfile as sf
from scipy.signal import butter, lfilter
from pydub import AudioSegment
from pydub.playback import play

# Bandpass filter setup (80Hz - 8000Hz)
def butter_bandpass(lowcut, highcut, fs, order=6):
    nyq = 0.5 * fs
    low = max(lowcut / nyq, 0.001)
    high = min(highcut / nyq, 0.999)
    if not (0 < low < high < 1):
        raise ValueError(f"Invalid bandpass frequencies: low={low}, high={high}")
    b, a = butter(order, [low, high], btype="band")
    return b, a

def apply_bandpass_filter(data, sr, lowcut=80.0, highcut=8000.0):
    max_highcut = 0.49 * sr
    highcut = min(highcut, max_highcut)
    b, a = butter_bandpass(lowcut, highcut, sr)
    return lfilter(b, a, data)

# Preprocessing function for vocal separation using pydub
def preprocess_audio(input_path, output_path):
    # Step 1: Load the audio file using pydub
    audio = AudioSegment.from_wav(input_path)

    # Step 2: Split stereo audio into two channels (if applicable)
    if audio.channels == 2:
        # Assuming the first channel contains vocals and the second one has background
        vocals = audio.split_to_mono()[0]  # Take the first channel (vocals)
    else:
        vocals = audio  # If already mono, use the same audio
    
    # Convert to numpy array for further processing
    vocals_samples = vocals.get_array_of_samples()
    sr = vocals.frame_rate

    # Step 3: Apply bandpass filter to retain speech frequencies
    vocals_filtered = apply_bandpass_filter(vocals_samples, sr)

    # Step 4: Normalize volume
    vocals_filtered = vocals_filtered / max(abs(vocals_filtered))

    # Step 5: Save the processed audio
    sf.write(output_path, vocals_filtered, sr)
    return output_path

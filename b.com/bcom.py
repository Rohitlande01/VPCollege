import sys

print("Initializing system environment...")

try:
    import os
    import requests
    import numpy as np
    import sounddevice as sd
    import pyttsx3
    from faster_whisper import WhisperModel
    import openwakeword
    from openwakeword.model import Model
    import scipy.io.wavfile as wav
    print("✓ All libraries imported successfully.")
except Exception as e:
    print("\n[CRITICAL ERROR DURING IMPORT]:")
    print(e)
    print("\nEnsure you ran: pip install faster-whisper openwakeword pyttsx3 requests sounddevice numpy scipy onnxruntime")
    input("\nPress ENTER to close this window...")
    sys.exit(1)

# ==========================================
# 1. INITIALIZE TEXT-TO-SPEECH (TTS ENGINE)
# ==========================================
try:
    engine = pyttsx3.init()
    voices = engine.getProperty('voices')
    engine.setProperty('voice', voices[0].id)
    engine.setProperty('rate', 175)
except Exception as e:
    print(f"TTS Initialization failed: {e}")

def speak(text):
    print(f"\nJ.A.R.V.I.S.: {text}\n")
    try:
        engine.say(text)
        engine.runAndWait()
    except:
        pass

# ==========================================
# 2. MAIN EXECUTION WITH GLOBAL CRASH CATCH
# ==========================================
def main():
    print("Loading Whisper STT on RTX 2050 GPU...")
    stt_model = WhisperModel("base.en", device="cpu")




    print("Loading Wake Word Engine...")
    openwakeword.utils.download_models()
    wakeword_model = Model(wakeword_models=["hey_jarvis"], inference_framework="onnx")

    SAMPLE_RATE = 16000
    CHUNK_SIZE = 1280

    def query_brain(user_input):
        url = "http://127.0.0"
        payload = {
            "model": "llama3.2:3b",
            "prompt": f"System: You are J.A.R.V.I.S. Keep answers short.\nUser: {user_input}\nJ.A.R.V.I.S.:",
            "stream": False,
            "options": {"num_ctx": 2048}
        }
        try:
            return requests.post(url, json=payload).json().get("response", "Error")
        except:
            return "Local brain server offline, Sir."

    def record_and_transcribe(duration=5):
        # Using a universal write path to completely bypass the WindowsApps permission issue
        temp_dir = os.environ.get("TEMP", os.path.expanduser("~"))
        wav_path = os.path.join(temp_dir, "jarvis_temp_prompt.wav")
        
        audio_data = sd.rec(int(duration * SAMPLE_RATE), samplerate=SAMPLE_RATE, channels=1, dtype='float32')
        sd.wait()
        wav.write(wav_path, SAMPLE_RATE, (audio_data * 32767).astype(np.int16))
        
        segments, _ = stt_model.transcribe(wav_path)
        text = "".join([segment.text for segment in segments]).strip()
        
        if os.path.exists(wav_path): 
            try:
                os.remove(wav_path)
            except:
                pass
        return text

    speak("All systems initialized, Sir. Standing by.")
    
    with sd.InputStream(samplerate=SAMPLE_RATE, channels=1, dtype='int16', blocksize=CHUNK_SIZE) as stream:
        while True:
            audio_frame, _ = stream.read(CHUNK_SIZE)
            audio_frame = np.frombuffer(audio_frame, dtype=np.int16)
            wakeword_model.predict(audio_frame)
            
            for model_name, score in wakeword_model.prediction_buffer.items():
                if score[-1] > 0.5:
                    print("\n[Wake Word Detected!]")
                    speak("Yes, Sir?")
                    command = record_and_transcribe(duration=5)
                    if command:
                        speak(query_brain(command))
                    wakeword_model.reset()

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"\n[RUNTIME CRASH]: {e}")
    finally:
        input("\nScript stopped. Press ENTER to close this window...")

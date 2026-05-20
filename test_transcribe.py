import os
import sys
from google import genai
from dotenv import load_dotenv

sys.stdout.reconfigure(encoding='utf-8')
load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "").strip()
TEST_FILE_PATH = r"C:\Users\X1 CARb0N\Downloads\WhatsApp Ptt 2026-05-21 at 1.39.10 AM.ogg"

def test_transcribe_with_gemini():
    print("=== Testing Transcription with Gemini ===")
    
    if not GEMINI_API_KEY:
        print("[Error] GEMINI_API_KEY is not set in .env!")
        return False

    if not os.path.exists(TEST_FILE_PATH):
        print(f"[Error] Test file not found at: {TEST_FILE_PATH}")
        return False

    try:
        # Initialize Google GenAI client (uses modern google-genai package)
        client = genai.Client(api_key=GEMINI_API_KEY)
        
        print("Uploading audio file to Gemini...")
        audio_file = client.files.upload(file=TEST_FILE_PATH)
        print(f"File uploaded. Name: {audio_file.name}")
        
        print("Generating transcription...")
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=[
                audio_file,
                "Please transcribe this voice recording accurately. If the speech is in Urdu or a mix of Urdu and English (Roman Urdu), transcribe it in Urdu script or English depending on how it is spoken."
            ]
        )
        
        print("\n[Success]!")
        print("--------------------------------------------------")
        print("Transcription:")
        print(response.text)
        print("--------------------------------------------------")
        
        # Clean up the file from Gemini
        try:
            client.files.delete(name=audio_file.name)
        except Exception:
            pass
            
        return True

    except Exception as e:
        print(f"[Error] Gemini transcription failed: {e}")
        return False

if __name__ == "__main__":
    test_transcribe_with_gemini()

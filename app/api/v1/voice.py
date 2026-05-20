import os
import tempfile
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status
from google import genai

from app.config import settings
from app.api.v1.deps import get_current_user
from app.models.user import User

router = APIRouter()

@router.post("/transcribe")
async def transcribe_audio(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
):
    """
    Transcribe an audio file using Gemini (FREE & Multilingual).

    - Accepts: multipart/form-data with field `file` (audio blob)
    - Returns: { "text": "transcribed text" }
    - Auto-detects Urdu and English perfectly.
    - Handles raw formats like OGG, M4A, WAV, MP3, etc. natively.
    - Completely FREE via your existing GEMINI_API_KEY.
    """

    if not settings.GEMINI_API_KEY:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Transcription service is not configured. Please set GEMINI_API_KEY.",
        )

    # Read the audio bytes
    audio_bytes = await file.read()
    if not audio_bytes:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Uploaded file is empty.",
        )

    # Determine file extension (fallback to .m4a)
    filename = file.filename or "audio.m4a"
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else "m4a"
    
    # Save the uploaded audio to a temporary file
    tmp_path = None
    try:
        with tempfile.NamedTemporaryFile(suffix=f".{ext}", delete=False) as tmp:
            tmp.write(audio_bytes)
            tmp_path = tmp.name

        # Initialize modern Gemini client
        client = genai.Client(api_key=settings.GEMINI_API_KEY)

        # Upload the temporary file to Gemini Files API
        # This supports all audio formats natively (.ogg, .mp3, .m4a, .wav)
        gemini_file = client.files.upload(file=tmp_path)

        try:
            # Generate the transcription using gemini-2.5-flash
            response = client.models.generate_content(
                model='gemini-2.5-flash',
                contents=[
                    gemini_file,
                    "Please transcribe this voice recording accurately. If the speech is in Urdu or a mix of Urdu and English (Roman Urdu), transcribe it in Urdu script or English depending on how it is spoken."
                ]
            )

            text = response.text.strip() if response.text else ""
            if not text:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Transcription returned empty text.",
                )

            return {"text": text}

        finally:
            # Always clean up the uploaded file from Gemini storage
            try:
                client.files.delete(name=gemini_file.name)
            except Exception:
                pass

    except Exception as e:
        error_msg = str(e)
        if "api_key" in error_msg.lower() or "invalid key" in error_msg.lower():
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Gemini API Key validation failed. Please check GEMINI_API_KEY.",
            )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Transcription failed: {error_msg}",
        )

    finally:
        # Always clean up local temp file
        if tmp_path and os.path.exists(tmp_path):
            os.remove(tmp_path)

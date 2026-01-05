import speech_recognition as sr
from pydub import AudioSegment
import io

def transcribe_audio_bytes(audio_bytes: bytes, filename: str):
    """
    Receives raw audio bytes (from Streamlit uploader), normalizes to WAV 16k mono,
    returns transcribed text using Google Web Speech API (online).
    """
    # save bytes to a temporary file-like object
    ext = filename.split(".")[-1].lower()
    audio = None
    try:
        if ext in ("wav", "wave"):
            audio = AudioSegment.from_file(io.BytesIO(audio_bytes), format="wav")
        elif ext in ("mp3", "mpeg"):
            audio = AudioSegment.from_file(io.BytesIO(audio_bytes), format="mp3")
        else:
            # try generic read
            audio = AudioSegment.from_file(io.BytesIO(audio_bytes))
        # convert to wav 16k mono
        audio = audio.set_frame_rate(16000).set_channels(1)
        wav_io = io.BytesIO()
        audio.export(wav_io, format="wav")
        wav_io.seek(0)

        r = sr.Recognizer()
        with sr.AudioFile(wav_io) as source:
            audio_data = r.record(source)
        # Use Google Web Speech API (no key, usage limits)
        text = r.recognize_google(audio_data)
        return text
    except Exception as e:
        print("Transcription error:", e)
        return ""

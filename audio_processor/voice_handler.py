# audio_processor/voice_handler.py
import streamlit as st
import tempfile
import os
from openai import OpenAI
from config import API_CONFIG


class VoiceInputHandler:
    def __init__(self):
        self.client = OpenAI(api_key=API_CONFIG.get("openai_api_key"))

    def create_voice_input_interface(self, trade_symbol, trade_time):
        """Create Streamlit interface for voice input"""

        st.subheader(f"🎤 Voice Input for {trade_symbol} Trade")
        st.write(f"**Trade Time:** {trade_time}")
        st.write("**Tell us about this trade - why did you enter and exit?**")

        # File upload option (simpler than real-time recording)
        audio_file = st.file_uploader(
            "Upload audio file (MP3, WAV, M4A)",
            type=["mp3", "wav", "m4a"],
            key=f"audio_{trade_symbol}_{trade_time}",
        )

        # Text input as backup
        st.write("**Or type your reasoning:**")
        text_input = st.text_area(
            "Trade reasoning",
            placeholder="I entered because... I exited because... I was feeling...",
            key=f"text_{trade_symbol}_{trade_time}",
            height=100,
        )

        if audio_file is not None:
            st.audio(audio_file)

            if st.button(
                f"Process Audio for {trade_symbol}", key=f"process_{trade_symbol}"
            ):
                with st.spinner("Converting speech to text..."):
                    transcription = self.transcribe_audio(audio_file)
                    if transcription:
                        st.success("Audio transcribed successfully!")
                        st.write("**Transcription:**")
                        st.write(transcription)
                        return transcription
                    else:
                        st.error("Audio transcription failed")
                        return None

        return text_input if text_input.strip() else None

    def transcribe_audio(self, audio_file):
        """Transcribe audio using OpenAI Whisper"""
        try:
            # Save uploaded file temporarily
            with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp_file:
                tmp_file.write(audio_file.getvalue())
                tmp_file_path = tmp_file.name

            # Transcribe with Whisper
            with open(tmp_file_path, "rb") as audio:
                transcript = self.client.audio.transcriptions.create(
                    model="whisper-1", file=audio, response_format="text"
                )

            # Clean up temp file
            os.unlink(tmp_file_path)

            return transcript

        except Exception as e:
            st.error(f"Transcription error: {e}")
            return None

    def create_bulk_voice_interface(self, trades_list):
        """Interface for recording voice input for multiple trades"""

        voice_inputs = {}

        st.header("🎤 Voice Input for All Trades")
        st.write("Record your reasoning for each trade:")

        for i, trade in enumerate(trades_list):
            with st.expander(
                f"Trade {i + 1}: {trade['symbol']} - ${trade['pnl_dollar']:+.2f}"
            ):
                st.write(f"**Entry:** ${trade['entry_price']} at {trade['entry_time']}")
                st.write(f"**Exit:** ${trade['exit_price']} at {trade['exit_time']}")
                st.write(f"**Duration:** {trade['duration_minutes']} minutes")

                voice_input = self.create_voice_input_interface(
                    trade["symbol"], trade["entry_time"]
                )

                if voice_input:
                    voice_inputs[i] = voice_input

        return voice_inputs

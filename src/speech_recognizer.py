
import whisper
import logging
import os
from pathlib import Path

class SpeechRecognizer:
    def __init__(self, config):
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        self.model_name = self.config.get('whisper', {}).get('model', 'small')
        self.language = self.config.get('whisper', {}).get('language')
        self.model = None
        
        # Load model on initialization
        self.load_model()

    def load_model(self):
        """Load the Whisper model with error handling"""
        try:
            self.logger.info(f"Loading Whisper model: {self.model_name}")
            
            # Check if model name is valid
            valid_models = ['tiny', 'base', 'small', 'medium', 'large']
            if self.model_name not in valid_models:
                self.logger.error(f"Invalid model name: {self.model_name}. Valid models: {valid_models}")
                self.model_name = 'small'  # Fallback
                self.logger.info(f"Using fallback model: {self.model_name}")
            
            self.model = whisper.load_model(self.model_name)
            self.logger.info(f"Successfully loaded Whisper model: {self.model_name}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error loading Whisper model '{self.model_name}': {e}")
            self.model = None
            return False

    def transcribe(self, audio_file):
        """Transcribe audio file to text with comprehensive error handling"""
        if not self.model:
            self.logger.error("No Whisper model loaded")
            return None
            
        if not audio_file or not os.path.exists(audio_file):
            self.logger.error(f"Audio file not found: {audio_file}")
            return None

        try:
            self.logger.debug(f"Starting transcription of: {audio_file}")
            
            # Check file size
            file_size = os.path.getsize(audio_file)
            if file_size == 0:
                self.logger.warning("Audio file is empty")
                return None
            
            self.logger.debug(f"Audio file size: {file_size} bytes")
            
            # Transcribe with specified language or auto-detect
            transcribe_options = {
                'language': self.language,
                'task': 'transcribe',
                'verbose': False
            }
            
            # Remove None values
            transcribe_options = {k: v for k, v in transcribe_options.items() if v is not None}
            
            result = self.model.transcribe(audio_file, **transcribe_options)
            
            if result and 'text' in result:
                transcribed_text = result['text'].strip()
                
                if transcribed_text:
                    self.logger.info(f"Transcription successful: {len(transcribed_text)} characters")
                    self.logger.debug(f"Transcribed text: '{transcribed_text[:100]}...'" if len(transcribed_text) > 100 else f"Transcribed text: '{transcribed_text}'")
                    return transcribed_text
                else:
                    self.logger.warning("Transcription resulted in empty text")
                    return None
            else:
                self.logger.error("Invalid transcription result")
                return None
                
        except Exception as e:
            self.logger.error(f"Error during transcription: {e}")
            return None
    
    def is_model_loaded(self):
        """Check if model is loaded and ready"""
        return self.model is not None
    
    def get_model_info(self):
        """Get information about the loaded model"""
        if not self.model:
            return None
            
        return {
            'model_name': self.model_name,
            'language': self.language,
            'loaded': True
        }

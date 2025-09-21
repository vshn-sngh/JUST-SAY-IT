#!/usr/bin/env python3
"""
Voice-to-Text System
Main application entry point that coordinates all components
"""

import os
import sys
import logging
import threading
import time
import argparse
from pathlib import Path

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import our modules
from config_manager import ConfigManager
from speech_recognizer import SpeechRecognizer
from audio_manager import AudioManager
from text_inserter import TextInserter
from hotkey_detector import HotkeyDetector
from service_manager import ServiceManager

class VoiceToTextApp:
    def __init__(self, config_dir=None):
        # Set up config paths
        if config_dir is None:
            config_dir = Path(__file__).parent.parent / 'config'
        else:
            config_dir = Path(config_dir)
        
        self.default_config_path = config_dir / 'default_settings.json'
        self.user_config_path = config_dir / 'user_settings.json'
        
        # Initialize components
        self.config_manager = ConfigManager(
            str(self.default_config_path),
            str(self.user_config_path)
        )
        self.config = self.config_manager.config
        
        # Setup logging
        self._setup_logging()
        self.logger = logging.getLogger(__name__)
        
        # Initialize other components
        self.speech_recognizer = SpeechRecognizer(self.config)
        self.audio_manager = AudioManager(self.config)
        self.text_inserter = TextInserter(self.config)
        self.hotkey_detector = HotkeyDetector(self.config, self.on_hotkey_pressed)
        self.service_manager = ServiceManager(self.config)
        
        # Application state
        self.is_recording = False
        self.recording_thread = None
        self.running = True
        
        self.logger.info("Voice-to-Text application initialized")
    
    def _setup_logging(self):
        """Setup logging configuration"""
        log_level = self.config.get('logging', {}).get('level', 'INFO')
        log_file = self.config.get('logging', {}).get('file')
        
        # Create logs directory if it doesn't exist
        if log_file:
            log_dir = Path(log_file).parent
            log_dir.mkdir(parents=True, exist_ok=True)
        
        # Configure logging
        logging.basicConfig(
            level=getattr(logging, log_level),
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.StreamHandler(),
                logging.FileHandler(log_file) if log_file else logging.NullHandler()
            ]
        )
    
    def on_hotkey_pressed(self):
        """Callback function called when hotkey is pressed"""
        try:
            if not self.is_recording:
                self.start_recording()
            else:
                self.stop_recording()
        except Exception as e:
            self.logger.error(f"Error handling hotkey press: {e}")
    
    def start_recording(self):
        """Start voice recording"""
        if self.is_recording:
            self.logger.warning("Already recording")
            return
        
        self.logger.info("Starting voice recording...")
        self.is_recording = True
        
        # Start recording in a separate thread
        self.recording_thread = threading.Thread(
            target=self._recording_worker,
            daemon=True
        )
        self.recording_thread.start()
    
    def stop_recording(self):
        """Stop voice recording and process the audio"""
        if not self.is_recording:
            self.logger.warning("Not currently recording")
            return
        
        self.logger.info("Stopping voice recording...")
        self.is_recording = False
        
        # The recording worker will handle the rest
    
    def _recording_worker(self):
        """Worker thread that handles the recording process"""
        try:
            # Start audio recording
            self.audio_manager.start_recording()
            
            # Wait while recording (the hotkey callback will set is_recording to False)
            while self.is_recording and self.running:
                time.sleep(0.1)
            
            # Stop recording and get the audio file
            audio_file = self.audio_manager.stop_recording()
            
            if audio_file and os.path.exists(audio_file):
                self.logger.info(f"Audio recorded: {audio_file}")
                
                # Transcribe the audio
                self.logger.info("Starting transcription...")
                transcribed_text = self.speech_recognizer.transcribe(audio_file)
                
                if transcribed_text and transcribed_text.strip():
                    self.logger.info(f"Transcribed: '{transcribed_text}'")
                    
                    # Insert the text
                    success = self.text_inserter.insert_text(transcribed_text)
                    
                    if success:
                        self.logger.info("Text inserted successfully")
                    else:
                        self.logger.error("Failed to insert text")
                        # Try clipboard method as fallback
                        self.logger.info("Trying clipboard method...")
                        self.text_inserter.insert_text_clipboard(transcribed_text)
                else:
                    self.logger.warning("No text transcribed")
                
                # Clean up temporary audio file
                try:
                    os.remove(audio_file)
                    self.logger.debug(f"Cleaned up audio file: {audio_file}")
                except Exception as e:
                    self.logger.error(f"Error cleaning up audio file: {e}")
                    
            else:
                self.logger.error("No audio file recorded")
                
        except Exception as e:
            self.logger.error(f"Error in recording worker: {e}")
        finally:
            self.is_recording = False
    
    def start(self, daemon_mode=False):
        """Start the application"""
        try:
            self.logger.info("Starting Voice-to-Text application...")
            
            # Start hotkey detector
            self.hotkey_detector.start_listening()
            self.logger.info(f"Listening for hotkey: {self.config.get('hotkey')}")
            
            if daemon_mode:
                # Run as daemon service
                self.service_manager.daemonize()
                self.service_manager.start_service(self._main_loop)
            else:
                # Run in foreground
                self._main_loop()
                
        except KeyboardInterrupt:
            self.logger.info("Keyboard interrupt received")
            self.stop()
        except Exception as e:
            self.logger.error(f"Error starting application: {e}")
            self.stop()
            raise
    
    def _main_loop(self):
        """Main application loop"""
        self.logger.info("Voice-to-Text application is running. Press hotkey to record.")
        
        try:
            while self.running:
                time.sleep(1)
                
                # Reload configuration if needed (could add file watching here)
                # self.config_manager.reload_config()
                
        except KeyboardInterrupt:
            self.logger.info("Received interrupt signal")
            self.stop()
    
    def stop(self):
        """Stop the application gracefully"""
        self.logger.info("Stopping Voice-to-Text application...")
        
        self.running = False
        
        # Stop recording if in progress
        if self.is_recording:
            self.stop_recording()
        
        # Stop hotkey detector
        if self.hotkey_detector:
            self.hotkey_detector.stop_listening()
        
        # Stop service manager
        if self.service_manager:
            self.service_manager.stop_service()
        
        self.logger.info("Application stopped")
    
    def get_status(self):
        """Get current application status"""
        return {
            'running': self.running,
            'recording': self.is_recording,
            'hotkey': self.config.get('hotkey'),
            'whisper_model': self.config.get('whisper', {}).get('model'),
            'service_status': self.service_manager.get_service_status()
        }

def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description='Voice-to-Text System with Whisper',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s                    # Run in foreground mode
  %(prog)s --daemon          # Run as daemon
  %(prog)s --status          # Show status
  %(prog)s --stop            # Stop running daemon
  %(prog)s --config /path    # Use custom config directory
"""
    )
    
    parser.add_argument(
        '--daemon', '-d',
        action='store_true',
        help='Run as daemon service'
    )
    
    parser.add_argument(
        '--status', '-s',
        action='store_true',
        help='Show application status'
    )
    
    parser.add_argument(
        '--stop',
        action='store_true',
        help='Stop running daemon'
    )
    
    parser.add_argument(
        '--config', '-c',
        help='Path to configuration directory'
    )
    
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Enable verbose logging'
    )
    
    args = parser.parse_args()
    
    try:
        # Create application instance
        app = VoiceToTextApp(args.config)
        
        # Enable verbose logging if requested
        if args.verbose:
            logging.getLogger().setLevel(logging.DEBUG)
        
        if args.status:
            # Show status
            status = app.get_status()
            print("Voice-to-Text Status:")
            for key, value in status.items():
                print(f"  {key}: {value}")
            return
        
        if args.stop:
            # Stop daemon
            if app.service_manager.is_running():
                print("Stopping Voice-to-Text daemon...")
                # Send termination signal to running process
                with open('/tmp/voice-to-text.pid', 'r') as f:
                    pid = int(f.read().strip())
                os.kill(pid, 15)  # SIGTERM
                print("Stop signal sent")
            else:
                print("Voice-to-Text daemon is not running")
            return
        
        # Start the application
        app.start(daemon_mode=args.daemon)
        
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == '__main__':
    main()
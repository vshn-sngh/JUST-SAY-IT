
import sounddevice as sd
import soundfile as sf
import numpy as np
import os
import logging
import tempfile
from pathlib import Path

class AudioManager:
    def __init__(self, config):
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # Audio parameters
        self.sample_rate = self.config.get('audio', {}).get('sample_rate', 16000)
        self.channels = self.config.get('audio', {}).get('channels', 1)
        self.device_index = self.config.get('audio', {}).get('device_index')
        
        # Recording state
        self.recording = False
        self.frames = []
        self.stream = None
        
        # Validate audio configuration
        self._validate_config()
        
        self.logger.info(f"Audio manager initialized - Rate: {self.sample_rate}Hz, Channels: {self.channels}")
    
    def _validate_config(self):
        """Validate audio configuration parameters"""
        try:
            # Check if specified device exists
            if self.device_index is not None:
                devices = sd.query_devices()
                if self.device_index >= len(devices) or self.device_index < 0:
                    self.logger.warning(f"Invalid device index {self.device_index}, using default")
                    self.device_index = None
                else:
                    device_info = devices[self.device_index]
                    self.logger.info(f"Using audio device: {device_info['name']}")
            
            # Validate sample rate
            if self.sample_rate not in [8000, 16000, 22050, 44100, 48000]:
                self.logger.warning(f"Unusual sample rate: {self.sample_rate}Hz")
            
            # Validate channels
            if self.channels not in [1, 2]:
                self.logger.warning(f"Unusual channel count: {self.channels}")
                
        except Exception as e:
            self.logger.error(f"Error validating audio config: {e}")

    def start_recording(self):
        """Start audio recording with error handling"""
        if self.recording:
            self.logger.warning("Recording is already in progress")
            return False
            
        try:
            self.logger.info("Starting audio recording...")
            
            # Reset frames buffer
            self.frames = []
            self.recording = True
            
            # Create input stream
            self.stream = sd.InputStream(
                samplerate=self.sample_rate,
                channels=self.channels,
                device=self.device_index,
                callback=self.callback,
                dtype=np.float32
            )
            
            # Start the stream
            self.stream.start()
            
            # Play start sound
            self.play_sound('start')
            
            self.logger.info("Audio recording started successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Error starting recording: {e}")
            self.recording = False
            if self.stream:
                try:
                    self.stream.close()
                except:
                    pass
                self.stream = None
            return False

    def stop_recording(self):
        """Stop audio recording and return the recorded file"""
        if not self.recording:
            self.logger.warning("No recording in progress")
            return None
            
        try:
            self.logger.info("Stopping audio recording...")
            
            # Stop and close stream
            if self.stream:
                self.stream.stop()
                self.stream.close()
                self.stream = None
            
            self.recording = False
            
            # Play stop sound
            self.play_sound('stop')
            
            # Save and return recording
            audio_file = self.save_recording()
            
            if audio_file:
                self.logger.info(f"Recording saved: {audio_file}")
            else:
                self.logger.warning("No audio data to save")
                
            return audio_file
            
        except Exception as e:
            self.logger.error(f"Error stopping recording: {e}")
            self.recording = False
            return None

    def callback(self, indata, frames, time, status):
        """Audio input callback function"""
        if status:
            self.logger.debug(f"Audio callback status: {status}")
            
        if self.recording and indata is not None:
            # Append audio data to frames
            self.frames.append(indata.copy())

    def save_recording(self):
        """Save recorded audio to a temporary file"""
        if not self.frames:
            self.logger.warning("No audio frames to save")
            return None
            
        try:
            # Concatenate all audio frames
            recording = np.concatenate(self.frames, axis=0)
            
            # Check if we have actual audio data
            if recording.size == 0:
                self.logger.warning("Empty audio recording")
                return None
            
            # Create temporary file
            temp_file = tempfile.NamedTemporaryFile(
                suffix='.wav',
                delete=False,
                prefix='voice_recording_'
            ).name
            
            # Save audio to file
            sf.write(temp_file, recording, self.sample_rate)
            
            # Verify file was created and has content
            if os.path.exists(temp_file) and os.path.getsize(temp_file) > 0:
                duration = len(recording) / self.sample_rate
                self.logger.info(f"Recording saved: {duration:.2f}s, {len(recording)} samples")
                return temp_file
            else:
                self.logger.error("Failed to create audio file")
                return None
                
        except Exception as e:
            self.logger.error(f"Error saving recording: {e}")
            return None

    def play_sound(self, sound_type):
        """Play feedback sound with error handling"""
        try:
            # Get project root directory
            project_root = Path(__file__).parent.parent
            sound_file = project_root / 'sounds' / f'recording_{sound_type}.wav'
            
            if sound_file.exists():
                try:
                    data, fs = sf.read(str(sound_file), dtype='float32')
                    
                    # Play sound in a separate thread to avoid blocking
                    sd.play(data, fs)
                    # Don't wait for completion to avoid blocking
                    
                    self.logger.debug(f"Playing feedback sound: {sound_type}")
                    
                except Exception as e:
                    self.logger.error(f"Error playing sound {sound_type}: {e}")
            else:
                self.logger.debug(f"Sound file not found: {sound_file}")
                
        except Exception as e:
            self.logger.error(f"Error in play_sound: {e}")

    def get_audio_devices(self):
        """Get list of available audio devices"""
        try:
            devices = sd.query_devices()
            device_list = []
            
            for i, device in enumerate(devices):
                if device['max_input_channels'] > 0:  # Input devices only
                    device_list.append({
                        'index': i,
                        'name': device['name'],
                        'channels': device['max_input_channels'],
                        'sample_rate': device['default_samplerate']
                    })
            
            self.logger.debug(f"Found {len(device_list)} input devices")
            return device_list
            
        except Exception as e:
            self.logger.error(f"Error querying audio devices: {e}")
            return []
    
    def test_audio_device(self, device_index=None):
        """Test if audio device is working"""
        try:
            test_duration = 1.0  # 1 second test
            
            # Record a short test sample
            test_data = sd.rec(
                int(test_duration * self.sample_rate),
                samplerate=self.sample_rate,
                channels=self.channels,
                device=device_index or self.device_index,
                dtype=np.float32
            )
            
            sd.wait()  # Wait for recording to complete
            
            # Check if we got audio data
            if test_data is not None and test_data.size > 0:
                rms = np.sqrt(np.mean(test_data**2))
                self.logger.info(f"Audio device test successful. RMS level: {rms:.6f}")
                return True
            else:
                self.logger.error("Audio device test failed - no data received")
                return False
                
        except Exception as e:
            self.logger.error(f"Audio device test failed: {e}")
            return False

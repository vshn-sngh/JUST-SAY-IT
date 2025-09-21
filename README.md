# Voice-to-Text System

A real-time voice-to-text system using OpenAI Whisper that captures audio via global hotkeys and automatically types the transcribed text into any application.

## Features

- **Real-time Speech Recognition**: Uses OpenAI Whisper for high-quality offline transcription
- **Global Hotkeys**: Start/stop recording with customizable keyboard shortcuts (default: Ctrl+Alt+V)
- **Cross-Application**: Works in any text field across all applications
- **Daemon Support**: Can run as a background service
- **Audio Feedback**: Optional sound notifications for recording start/stop
- **Configurable**: JSON-based configuration with hot-reload support
- **Privacy-First**: Completely offline operation, no data sent to external services

## Requirements

### System Requirements
- Linux (Ubuntu/Debian, CentOS/RHEL, or similar)
- Python 3.8 or higher
- Audio input device (microphone)
- X11 display server (for GUI automation)

### Dependencies
- OpenAI Whisper for speech recognition
- SoundDevice for audio capture
- PyAutoGUI for text insertion
- Pynput for global hotkey detection

## Installation

### Automated Installation (Recommended)

1. Clone or download this repository
2. Run the installation script with root privileges:

```bash
sudo ./install/install.sh
```

The installer will:
- Install system dependencies
- Set up Python virtual environment
- Install Python packages
- Configure systemd service
- Create configuration files
- Set up command-line launcher

### Manual Installation

1. Install system dependencies:

```bash
# Ubuntu/Debian
sudo apt-get install python3-dev python3-pip python3-venv portaudio19-dev libsndfile1 ffmpeg alsa-utils pulseaudio xdotool

# CentOS/RHEL
sudo dnf install python3-devel python3-pip portaudio-devel libsndfile ffmpeg alsa-utils pulseaudio xdotool
```

2. Create Python virtual environment:

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

3. Configure settings in `config/default_settings.json`

## Usage

### Command Line

After installation, use the `voice-to-text` command:

```bash
# Run in foreground
voice-to-text

# Run as daemon
voice-to-text --daemon

# Check status
voice-to-text --status

# Stop daemon
voice-to-text --stop

# Verbose logging
voice-to-text --verbose
```

### Systemd Service

```bash
# Start service
sudo systemctl start voice-to-text

# Stop service
sudo systemctl stop voice-to-text

# Check status
sudo systemctl status voice-to-text

# Enable auto-start
sudo systemctl enable voice-to-text
```

### Basic Workflow

1. Start the application (foreground or daemon mode)
2. Press the hotkey (default: Ctrl+Alt+V) to start recording
3. Speak your message
4. Press the hotkey again to stop recording
5. The transcribed text will be automatically typed at your cursor position

## Configuration

Configuration files are located in `/etc/voice-to-text-system/` (or `config/` for development).

### Main Settings (`default_settings.json`)

```json
{
    \"hotkey\": \"<ctrl>+<alt>+v\",
    \"audio\": {
        \"sample_rate\": 16000,
        \"channels\": 1,
        \"device_index\": null,
        \"noise_reduction_level\": 1,
        \"silence_threshold\": -40
    },
    \"whisper\": {
        \"model\": \"small\",
        \"language\": null
    },
    \"typing\": {
        \"speed\": 0.05
    },
    \"logging\": {
        \"level\": \"INFO\",
        \"file\": \"/var/log/voice-to-text-system/voice-to-text.log\"
    }
}
```

### User Overrides (`user_settings.json`)

You can override any default settings by creating a `user_settings.json` file:

```json
{
    \"hotkey\": \"<ctrl>+<shift>+r\",
    \"whisper\": {
        \"model\": \"base\"
    }
}
```

### Configuration Options

#### Hotkeys
- Format: `<modifier>+<modifier>+<key>`
- Modifiers: `ctrl`, `alt`, `shift`, `cmd`/`super`
- Examples: `<ctrl>+<alt>+v`, `<ctrl>+<shift>+space`

#### Whisper Models
- `tiny`: Fastest, lowest accuracy (~39M parameters)
- `base`: Fast, good for simple speech (~74M parameters)  
- `small`: **Recommended** balance of speed/accuracy (~244M parameters)
- `medium`: Slower but more accurate (~769M parameters)
- `large`: Slowest, highest accuracy (~1550M parameters)

#### Audio Settings
- `sample_rate`: Audio sampling rate (16000 recommended)
- `channels`: 1 for mono, 2 for stereo
- `device_index`: Specific audio device (null for default)
- `noise_reduction_level`: 0-3, higher = more noise reduction
- `silence_threshold`: dB level to detect silence (-40 recommended)

## Troubleshooting

### Common Issues

**1. \"Permission denied\" errors**
- Make sure you're running with appropriate permissions
- Check that audio device is accessible
- Verify hotkey permissions for global capture

**2. No audio captured**
- Test microphone with: `voice-to-text --test-audio`
- Check audio device settings
- Verify PulseAudio/ALSA configuration

**3. Hotkey not working**  
- Ensure no other application is using the same hotkey
- Try running with `--verbose` to see hotkey detection logs
- Check X11 permissions for input capture

**4. Text not being inserted**
- Verify the target application has focus
- Check that PyAutoGUI has necessary permissions
- Try the clipboard insertion method as fallback

**5. Whisper model download fails**
- Check internet connection for initial model download
- Ensure sufficient disk space (~1-10GB depending on model)
- Models are cached in `~/.cache/whisper/`

### Audio Device Testing

```bash
# List available audio devices
python3 -c \"import sounddevice; print(sounddevice.query_devices())\"

# Test specific device
voice-to-text --test-audio --device 0
```

### Log Files

- Application logs: `/var/log/voice-to-text-system/voice-to-text.log`
- Service logs: `journalctl -u voice-to-text -f`

## Development

### Project Structure

```
voice-to-text-system/
├── src/                     # Source code
│   ├── main.py             # Main application entry point
│   ├── config_manager.py   # Configuration management
│   ├── speech_recognizer.py # Whisper integration
│   ├── audio_manager.py    # Audio capture
│   ├── text_inserter.py    # Text insertion
│   ├── hotkey_detector.py  # Global hotkey detection
│   └── service_manager.py  # Daemon functionality
├── config/                 # Configuration files
├── sounds/                 # Audio feedback files  
├── install/                # Installation scripts
├── tests/                  # Test files
└── logs/                   # Log files
```

### Running for Development

```bash
cd src
python3 main.py --config ../config --verbose
```

### Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

This project is open source. Please check the LICENSE file for details.

## Privacy and Security

- **Offline Operation**: All processing happens locally, no data sent to external servers
- **Temporary Files**: Audio recordings are stored temporarily and deleted after processing
- **No Data Collection**: No usage analytics or telemetry
- **Configurable Logging**: Control what information is logged

## Performance Tips

- Use the `small` Whisper model for best speed/accuracy balance
- Ensure adequate CPU resources (Whisper is CPU-intensive)
- Use a good quality microphone for better transcription accuracy
- Speak clearly and avoid background noise
- Consider noise reduction settings for noisy environments

## Support

For issues, questions, or contributions:
- Check the troubleshooting section above
- Review log files for error details
- Test individual components with verbose logging
- Ensure all dependencies are properly installed

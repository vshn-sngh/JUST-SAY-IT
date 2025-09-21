import threading
import logging
from pynput import keyboard
import time

class HotkeyDetector:
    def __init__(self, config, callback=None):
        self.config = config
        self.hotkey_string = config.get('hotkey', '<ctrl>+<alt>+v')
        self.callback = callback
        self.logger = logging.getLogger(__name__)
        
        # Parse hotkey combination
        self.required_keys = self._parse_hotkey(self.hotkey_string)
        self.pressed_keys = set()
        self.listener = None
        self.running = False
        
        # Debounce mechanism
        self.last_trigger_time = 0
        self.debounce_delay = 0.5  # 500ms
    
    def _parse_hotkey(self, hotkey_string):
        """
        Parse hotkey string like '<ctrl>+<alt>+v' into a set of keys
        """
        keys = set()
        parts = hotkey_string.lower().replace('<', '').replace('>', '').split('+')
        
        for part in parts:
            part = part.strip()
            if part == 'ctrl':
                keys.add(keyboard.Key.ctrl_l)
                keys.add(keyboard.Key.ctrl_r)
            elif part == 'alt':
                keys.add(keyboard.Key.alt_l)
                keys.add(keyboard.Key.alt_r)
            elif part == 'shift':
                keys.add(keyboard.Key.shift_l)
                keys.add(keyboard.Key.shift_r)
            elif part == 'cmd' or part == 'super':
                keys.add(keyboard.Key.cmd)
            elif part == 'space':
                keys.add(keyboard.Key.space)
            elif part == 'tab':
                keys.add(keyboard.Key.tab)
            elif part == 'enter':
                keys.add(keyboard.Key.enter)
            elif len(part) == 1:
                keys.add(part)
        
        self.logger.info(f"Parsed hotkey '{hotkey_string}' to keys: {[str(k) for k in keys]}")
        return keys
    
    def _on_press(self, key):
        """Handle key press events"""
        try:
            # Add the pressed key to our set
            if hasattr(key, 'char') and key.char:
                self.pressed_keys.add(key.char.lower())
            else:
                self.pressed_keys.add(key)
            
            # Check if our hotkey combination is pressed
            self._check_hotkey_combination()
            
        except Exception as e:
            self.logger.error(f"Error in key press handler: {e}")
    
    def _on_release(self, key):
        """Handle key release events"""
        try:
            # Remove the released key from our set
            if hasattr(key, 'char') and key.char:
                self.pressed_keys.discard(key.char.lower())
            else:
                self.pressed_keys.discard(key)
                
        except Exception as e:
            self.logger.error(f"Error in key release handler: {e}")
    
    def _check_hotkey_combination(self):
        """Check if the required key combination is pressed"""
        current_time = time.time()
        
        # Check if any of the required keys match what's currently pressed
        matched_keys = set()
        for required_key in self.required_keys:
            if isinstance(required_key, str):
                # Character key
                if required_key in self.pressed_keys:
                    matched_keys.add(required_key)
            else:
                # Special key (like Ctrl, Alt)
                if required_key in self.pressed_keys:
                    matched_keys.add(required_key)
                # For modifier keys, check both left and right variants
                elif (required_key == keyboard.Key.ctrl_l or required_key == keyboard.Key.ctrl_r) and \
                     (keyboard.Key.ctrl_l in self.pressed_keys or keyboard.Key.ctrl_r in self.pressed_keys):
                    matched_keys.add(required_key)
                elif (required_key == keyboard.Key.alt_l or required_key == keyboard.Key.alt_r) and \
                     (keyboard.Key.alt_l in self.pressed_keys or keyboard.Key.alt_r in self.pressed_keys):
                    matched_keys.add(required_key)
                elif (required_key == keyboard.Key.shift_l or required_key == keyboard.Key.shift_r) and \
                     (keyboard.Key.shift_l in self.pressed_keys or keyboard.Key.shift_r in self.pressed_keys):
                    matched_keys.add(required_key)
        
        # Check if we have a reasonable match (accounting for left/right modifier variants)
        required_count = len(self.required_keys)
        matched_count = len(matched_keys)
        
        # For modifier keys, we need special logic since we add both left and right variants
        if 'ctrl' in self.hotkey_string.lower():
            required_count -= 1  # Subtract one because we added both ctrl_l and ctrl_r
        if 'alt' in self.hotkey_string.lower():
            required_count -= 1   # Subtract one because we added both alt_l and alt_r
        if 'shift' in self.hotkey_string.lower():
            required_count -= 1   # Subtract one because we added both shift_l and shift_r
        
        # Simple matching based on the actual keys we need
        ctrl_pressed = keyboard.Key.ctrl_l in self.pressed_keys or keyboard.Key.ctrl_r in self.pressed_keys
        alt_pressed = keyboard.Key.alt_l in self.pressed_keys or keyboard.Key.alt_r in self.pressed_keys
        
        # Check for the default hotkey: Ctrl+Alt+V
        hotkey_lower = self.hotkey_string.lower()
        if 'ctrl' in hotkey_lower and 'alt' in hotkey_lower and 'v' in hotkey_lower:
            if ctrl_pressed and alt_pressed and 'v' in self.pressed_keys:
                self._trigger_callback(current_time)
        
    def _trigger_callback(self, current_time):
        """Trigger the callback with debouncing"""
        if current_time - self.last_trigger_time >= self.debounce_delay:
            self.last_trigger_time = current_time
            self.logger.info(f"Hotkey triggered: {self.hotkey_string}")
            
            if self.callback:
                # Run callback in a separate thread to avoid blocking
                threading.Thread(target=self.callback, daemon=True).start()
    
    def start_listening(self):
        """Start listening for hotkey presses"""
        if self.running:
            self.logger.warning("Hotkey detector is already running")
            return
        
        try:
            self.running = True
            self.listener = keyboard.Listener(
                on_press=self._on_press,
                on_release=self._on_release
            )
            self.listener.start()
            self.logger.info(f"Started listening for hotkey: {self.hotkey_string}")
            
        except Exception as e:
            self.logger.error(f"Error starting hotkey listener: {e}")
            self.running = False
            raise
    
    def stop_listening(self):
        """Stop listening for hotkey presses"""
        if not self.running:
            return
        
        try:
            self.running = False
            if self.listener:
                self.listener.stop()
                self.listener = None
            
            self.pressed_keys.clear()
            self.logger.info("Stopped hotkey detector")
            
        except Exception as e:
            self.logger.error(f"Error stopping hotkey listener: {e}")
    
    def update_hotkey(self, new_hotkey):
        """Update the hotkey combination"""
        self.hotkey_string = new_hotkey
        self.required_keys = self._parse_hotkey(new_hotkey)
        self.logger.info(f"Updated hotkey to: {new_hotkey}")
    
    def set_callback(self, callback):
        """Set or update the callback function"""
        self.callback = callback
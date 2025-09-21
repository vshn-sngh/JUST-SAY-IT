import pyautogui
import time
import logging

class TextInserter:
    def __init__(self, config):
        self.config = config
        self.typing_speed = config.get('typing', {}).get('speed', 0.05)
        self.logger = logging.getLogger(__name__)
        
        # Configure pyautogui
        pyautogui.FAILSAFE = False
        pyautogui.PAUSE = 0
    
    def insert_text(self, text):
        """
        Insert text at current cursor position with typing simulation
        """
        if not text or not text.strip():
            self.logger.warning("No text to insert")
            return False
        
        try:
            # Clean the text
            clean_text = text.strip()
            
            # Type the text with the configured speed
            if self.typing_speed > 0:
                for char in clean_text:
                    pyautogui.write(char)
                    time.sleep(self.typing_speed)
            else:
                pyautogui.write(clean_text)
            
            self.logger.info(f"Successfully inserted text: {len(clean_text)} characters")
            return True
            
        except Exception as e:
            self.logger.error(f"Error inserting text: {e}")
            return False
    
    def insert_text_clipboard(self, text):
        """
        Alternative method using clipboard
        """
        try:
            import pyperclip
            
            # Save current clipboard content
            original_clipboard = pyperclip.paste()
            
            # Copy text to clipboard
            pyperclip.copy(text.strip())
            
            # Paste using Ctrl+V
            pyautogui.hotkey('ctrl', 'v')
            
            # Restore original clipboard after a brief delay
            time.sleep(0.1)
            pyperclip.copy(original_clipboard)
            
            self.logger.info(f"Successfully inserted text via clipboard: {len(text.strip())} characters")
            return True
            
        except Exception as e:
            self.logger.error(f"Error inserting text via clipboard: {e}")
            return False
    
    def set_typing_speed(self, speed):
        """
        Update typing speed
        """
        self.typing_speed = max(0, speed)
        self.logger.info(f"Typing speed set to: {self.typing_speed}")
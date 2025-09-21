import os
import sys
import signal
import logging
import time
import threading
from pathlib import Path

class ServiceManager:
    def __init__(self, config):
        self.config = config
        self.logger = logging.getLogger(__name__)
        self.running = False
        self.pid_file = '/tmp/voice-to-text.pid'
        
        # Signal handlers
        signal.signal(signal.SIGTERM, self._signal_handler)
        signal.signal(signal.SIGINT, self._signal_handler)
    
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals gracefully"""
        self.logger.info(f"Received signal {signum}, shutting down...")
        self.stop_service()
    
    def start_service(self, main_app_callback=None):
        """Start the service as a daemon or regular process"""
        if self.is_running():
            self.logger.error("Service is already running")
            return False
        
        try:
            self.running = True
            self._create_pid_file()
            
            self.logger.info("Voice-to-Text service started")
            
            # If a main app callback is provided, run it
            if main_app_callback:
                main_app_callback()
            else:
                # Default service loop
                self._service_loop()
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error starting service: {e}")
            self.running = False
            return False
    
    def stop_service(self):
        """Stop the service gracefully"""
        if not self.running:
            return
        
        try:
            self.running = False
            self._remove_pid_file()
            self.logger.info("Voice-to-Text service stopped")
            
        except Exception as e:
            self.logger.error(f"Error stopping service: {e}")
    
    def _service_loop(self):
        """Default service loop - just keep running"""
        try:
            while self.running:
                time.sleep(1)
                
        except KeyboardInterrupt:
            self.logger.info("Keyboard interrupt received")
            self.stop_service()
    
    def is_running(self):
        """Check if the service is already running"""
        if not os.path.exists(self.pid_file):
            return False
        
        try:
            with open(self.pid_file, 'r') as f:
                pid = int(f.read().strip())
            
            # Check if process with this PID exists
            try:
                os.kill(pid, 0)  # Send null signal to check if process exists
                return True
            except OSError:
                # Process doesn't exist, remove stale PID file
                self._remove_pid_file()
                return False
                
        except (ValueError, IOError):
            # Invalid or unreadable PID file
            self._remove_pid_file()
            return False
    
    def _create_pid_file(self):
        """Create PID file for the current process"""
        try:
            pid = os.getpid()
            with open(self.pid_file, 'w') as f:
                f.write(str(pid))
            self.logger.debug(f"Created PID file: {self.pid_file} with PID: {pid}")
            
        except IOError as e:
            self.logger.error(f"Error creating PID file: {e}")
    
    def _remove_pid_file(self):
        """Remove the PID file"""
        try:
            if os.path.exists(self.pid_file):
                os.remove(self.pid_file)
                self.logger.debug(f"Removed PID file: {self.pid_file}")
                
        except IOError as e:
            self.logger.error(f"Error removing PID file: {e}")
    
    def restart_service(self, main_app_callback=None):
        """Restart the service"""
        self.logger.info("Restarting service...")
        self.stop_service()
        time.sleep(1)  # Brief pause
        return self.start_service(main_app_callback)
    
    def get_service_status(self):
        """Get current service status"""
        if self.is_running():
            try:
                with open(self.pid_file, 'r') as f:
                    pid = int(f.read().strip())
                return {
                    'status': 'running',
                    'pid': pid,
                    'pid_file': self.pid_file
                }
            except:
                return {'status': 'unknown'}
        else:
            return {'status': 'stopped'}
    
    def daemonize(self):
        """Daemonize the current process (Unix only)"""
        try:
            # First fork
            pid = os.fork()
            if pid > 0:
                sys.exit(0)  # Parent process exits
                
        except OSError as e:
            self.logger.error(f"First fork failed: {e}")
            sys.exit(1)
        
        # Become session leader
        os.setsid()
        
        try:
            # Second fork
            pid = os.fork()
            if pid > 0:
                sys.exit(0)  # Second parent exits
                
        except OSError as e:
            self.logger.error(f"Second fork failed: {e}")
            sys.exit(1)
        
        # Change working directory and file permissions
        os.chdir('/')
        os.umask(0)
        
        # Redirect standard file descriptors
        sys.stdout.flush()
        sys.stderr.flush()
        
        # Close or redirect stdin, stdout, stderr
        with open('/dev/null', 'r') as dev_null:
            os.dup2(dev_null.fileno(), sys.stdin.fileno())
        
        with open('/dev/null', 'w') as dev_null:
            os.dup2(dev_null.fileno(), sys.stdout.fileno())
            os.dup2(dev_null.fileno(), sys.stderr.fileno())
        
        self.logger.info("Process daemonized successfully")
import platform
import subprocess

class AudioController:
    def __init__(self):
        self.system = platform.system()
        self._setup_system_specific()

    def _setup_system_specific(self):
        if self.system == "Windows":
            try:
                from pycaw.pycaw import AudioUtilities, ISimpleAudioVolume
                self.sessions = AudioUtilities.GetAllSessions()
                # Find the microphone session
                for session in self.sessions:
                    if session.Process and "zoom" in session.Process.name().lower():
                        self.zoom_volume = session._ctl.QueryInterface(ISimpleAudioVolume)
                        break
            except ImportError:
                print("Please install pycaw: pip install pycaw")
        elif self.system == "Darwin":  # macOS
            pass  # We'll use osascript for macOS
        else:  # Linux
            pass  # We'll use pactl for Linux

    def mute_mic(self):
        """Mute the microphone"""
        try:
            if self.system == "Windows":
                if hasattr(self, 'zoom_volume'):
                    self.zoom_volume.SetMute(1, None)
            elif self.system == "Darwin":
                subprocess.run(['osascript', '-e', 'set volume input volume 0'])
            else:
                subprocess.run(['pactl', 'set-source-mute', '@DEFAULT_SOURCE@', '1'])
        except Exception as e:
            print(f"Error muting microphone: {e}")

    def unmute_mic(self):
        """Unmute the microphone"""
        try:
            if self.system == "Windows":
                if hasattr(self, 'zoom_volume'):
                    self.zoom_volume.SetMute(0, None)
            elif self.system == "Darwin":
                subprocess.run(['osascript', '-e', 'set volume input volume 100'])
            else:
                subprocess.run(['pactl', 'set-source-mute', '@DEFAULT_SOURCE@', '0'])
        except Exception as e:
            print(f"Error unmuting microphone: {e}") 
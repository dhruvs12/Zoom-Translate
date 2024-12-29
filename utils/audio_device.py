import pyaudio
import platform

class VirtualAudioDevice:
    def __init__(self):
        self.system = platform.system()
        self.p = pyaudio.PyAudio()
        
    def list_virtual_devices(self):
        """List all available virtual audio devices"""
        virtual_devices = []
        for i in range(self.p.get_device_count()):
            device_info = self.p.get_device_info_by_index(i)
            if any(name.lower() in device_info['name'].lower() for name in 
                  ['virtual', 'vb-audio', 'cable', 'soundflower', 'blackhole']):
                virtual_devices.append((i, device_info['name']))
        return virtual_devices
    
    def get_default_virtual_device(self):
        """Get the first available virtual audio device"""
        devices = self.list_virtual_devices()
        return devices[0][0] if devices else None 
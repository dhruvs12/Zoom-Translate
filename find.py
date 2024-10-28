import pyaudio

# Initialize PyAudio
p = pyaudio.PyAudio()

# List only output devices (maxOutputChannels > 0)
print("Available Output Devices:")
for i in range(p.get_device_count()):
    device_info = p.get_device_info_by_index(i)
    if device_info['maxOutputChannels'] > 0:
        print(f"\nDevice ID: {i}")
        print(f"Name: {device_info['name']}")
        print(f"Max Output Channels: {device_info['maxOutputChannels']}")
        print(f"Default Sample Rate: {device_info['defaultSampleRate']}")

p.terminate()
 
import asyncio
from services.translation_service import TranslationService

def main():
    try:
        service = TranslationService()
        print("Starting translation service...")
        print("Available virtual audio devices:")
        for idx, name in service.virtual_device.list_virtual_devices():
            print(f"  {idx}: {name}")
        print("\nAudio Control Setup:")
        print("- Windows: Make sure Zoom is running")
        print("- macOS: Allow Terminal.app in System Preferences > Security & Privacy > Privacy > Accessibility")
        print("- Linux: No additional setup needed")
        print("\nFirst non-English speaker will set the target language.")
        print("Then translations will go back and forth between English and that language.")
        asyncio.run(service.run())
    except ValueError as e:
        print(f"Error: {e}")
        print("\nTo use this application:")
        print("1. Install a virtual audio cable:")
        print("   - Windows: VB-Cable (https://vb-audio.com/Cable/)")
        print("   - macOS: BlackHole (https://existential.audio/blackhole/)")
        print("   - Linux: PulseAudio or JACK")
        print("2. Configure your meeting platform to use the virtual audio device as input")
        print("3. Run this application again")

if __name__ == "__main__":
    main() 
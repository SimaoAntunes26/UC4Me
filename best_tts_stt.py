import speech_recognition as sr
from pynput import keyboard
import threading
import time
import pyaudio
import edge_tts
import asyncio
import pygame
import io

class VoiceAssistant:
    def __init__(self):
        self.recognizer = sr.Recognizer()
        self.is_recording = False
        self.audio_data = None
        self.recording_thread = None
        
        # Simplified key tracking - no counting needed
        self.listener = None
        
        # PyAudio settings
        self.chunk = 1024
        self.format = pyaudio.paInt16
        self.channels = 1
        self.rate = 44100
        
        # Edge TTS settings for European Portuguese
        self.voice = "pt-PT-RaquelNeural"  # European Portuguese female voice
        # Alternative voices: "pt-PT-DuarteNeural" (male)
        
        # Initialize pygame for audio playback
        pygame.mixer.init()
        
        print("Voice assistant initialized with European Portuguese TTS!")

    def speak(self, text):
        """Convert text to speech using Edge TTS"""
        async def _speak():
            try:
                communicate = edge_tts.Communicate(text, self.voice)
                
                # Create audio data in memory
                audio_data = io.BytesIO()
                async for chunk in communicate.stream():
                    if chunk["type"] == "audio":
                        audio_data.write(chunk["data"])
                
                # Reset position to beginning
                audio_data.seek(0)
                
                # Play audio using pygame
                pygame.mixer.music.load(audio_data)
                pygame.mixer.music.play()
                
                # Wait for playback to finish
                while pygame.mixer.music.get_busy():
                    time.sleep(0.1)
            except Exception as e:
                print(f"TTS Error: {e}")
        
        # Run the async function
        try:
            asyncio.run(_speak())
        except Exception as e:
            print(f"Speech synthesis error: {e}")

    def on_key_press(self, key):
        """Handle key press events from pynput"""
        try:
            # Check if 'g' key was pressed
            if hasattr(key, 'char') and key.char and key.char.lower() == 'g':
                self.handle_g_press()
        except AttributeError:
            # Special keys (like ctrl, alt, etc.) don't have char attribute
            pass

    def on_key_release(self, key):
        """Handle key release events from pynput"""
        # Check for Ctrl+C to exit
        if key == keyboard.Key.ctrl_l or key == keyboard.Key.ctrl_r:
            return False  # This will stop the listener

    def handle_g_press(self):
        """Handle G key press - start 5-second recording"""
        if self.is_recording:
            print("⚠️ Already recording, please wait...")
            return
        
        print("🔴 Starting 5-second recording...")
        self.speak("A iniciar gravação de 5 segundos.")
        self._start_5_second_recording()

    def _start_5_second_recording(self):
        """Start recording for exactly 5 seconds"""
        self.is_recording = True
        self.recording_thread = threading.Thread(target=self._record_for_5_seconds)
        self.recording_thread.start()

    def _record_for_5_seconds(self):
        """Record audio for exactly 5 seconds using PyAudio"""
        try:
            audio = pyaudio.PyAudio()
            
            stream = audio.open(
                format=self.format,
                channels=self.channels,
                rate=self.rate,
                input=True,
                frames_per_buffer=self.chunk
            )
            
            frames = []
            
            # Record for exactly 5 seconds
            start_time = time.time()
            recording_duration = 5.0
            
            print("🔴 Recording... ", end="", flush=True)
            
            while time.time() - start_time < recording_duration:
                data = stream.read(self.chunk)
                frames.append(data)
                
                # Show countdown
                elapsed = time.time() - start_time
                remaining = recording_duration - elapsed
                if int(remaining) != int(remaining + 0.1):  # Print once per second
                    print(f"{int(remaining + 1)}... ", end="", flush=True)
            
            print("⏹️")
            
            stream.stop_stream()
            stream.close()
            audio.terminate()
            
            # Convert to speech_recognition AudioData format
            audio_data = b''.join(frames)
            self.audio_data = sr.AudioData(audio_data, self.rate, 2)  # 2 bytes per sample for 16-bit
            
            self.is_recording = False
            print("✅ Recording completed! Processing...")
            self._process_audio()
            
        except Exception as e:
            print(f"Recording error: {e}")
            self.is_recording = False

    def _process_audio(self):
        """Process the recorded audio"""
        if self.audio_data is None:
            print("No audio data to process.")
            return

        try:
            print("🔄 Converting speech to text...")
            # Convert speech to text using European Portuguese
            text = self.recognizer.recognize_google(self.audio_data, language='pt-PT')
            print(f"📝 You said: '{text}'")
            
            # Play back what was said
            self.speak(f"Disseste: {text}")
            
            # Process the command
            result = self._handle_command(text.lower())
            if result == "exit":
                return "exit"
            
        except sr.UnknownValueError:
            print("❌ Sorry, I couldn't understand the audio.")
            self.speak("Desculpa, não consegui perceber o que disseste.")
        except sr.RequestError as e:
            print(f"❌ Speech recognition service error: {e}")
            self.speak("Desculpa, houve um erro com o serviço de reconhecimento de voz.")
        except Exception as e:
            print(f"❌ Unexpected error: {e}")
            self.speak("Desculpa, ocorreu um erro inesperado.")
        
        # Reset audio data
        self.audio_data = None
        print("\n⏳ Ready for next command. Press 'G' to record again...")

    def _handle_command(self, command):
        """Handle voice commands"""
        if any(word in command for word in ["sair", "parar", "terminar", "adeus", "tchau"]):
            self.speak("Adeus!")
            return "exit"
        elif any(word in command for word in ["teu nome", "quem és", "nome", "quem es"]):
            self.speak("Sou o teu assistente de voz em Python.")
        elif any(word in command for word in ["horas", "tempo", "que horas"]):
            from datetime import datetime
            current_time = datetime.now().strftime("%H:%M")
            self.speak(f"São {current_time}")
        elif any(word in command for word in ["olá", "oi", "bom dia", "ola"]):
            self.speak("Olá! Como posso ajudar?")
        elif any(word in command for word in ["obrigado", "obrigada"]):
            self.speak("De nada! Fico feliz em ajudar.")
        elif any(word in command for word in ["como estás", "como estas", "tudo bem"]):
            self.speak("Estou bem, obrigado! E tu?")
        else:
            self.speak("Ouvi-te, mas ainda estou a aprender a responder a esse comando.")

    def start_keyboard_listener(self):
        """Start the keyboard listener"""
        self.listener = keyboard.Listener(
            on_press=self.on_key_press,
            on_release=self.on_key_release
        )
        self.listener.start()
        return self.listener

def main():
    print("\n🎤 Voice Assistant - 5 Second Recording")
    print("=" * 50)
    print("📋 Como funciona:")
    print("  1. Prima 'G' uma vez para iniciar gravação de 5 segundos")
    print("  2. Fale durante os 5 segundos")
    print("  3. O programa processa automaticamente após 5 segundos")
    print("  4. Para dar outro comando, prima 'G' novamente")
    print("  5. Prima 'Ctrl+C' para sair")
    print("\n💡 Comandos de voz disponíveis:")
    print("  • Qual é o teu nome / Quem és")
    print("  • Que horas são")
    print("  • Olá / Oi / Bom dia")
    print("  • Sair / Parar / Terminar")
    print("  • Obrigado/a")
    print("  • Como estás / Tudo bem")
    print("\n⚠️  NOTA IMPORTANTE para SSH:")
    print("   Se estás a usar SSH, podes precisar de X11 forwarding:")
    print("   ssh -X pi@your_raspberry_pi_ip")
    print("\n⏳ Pronto! Prima 'G' para começar...")
    
    try:
        assistant = VoiceAssistant()
        
        # Start keyboard listener
        listener = assistant.start_keyboard_listener()
        
        assistant.speak("Assistente de voz pronto. Prima G para gravar por 5 segundos.")
        
        # Keep the main thread alive
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\n\n👋 A sair do assistente de voz...")
            if assistant.is_recording:
                assistant.is_recording = False
            listener.stop()
            
    except Exception as e:
        print(f"\n❌ Erro fatal: {e}")
        print("💡 Se estás a usar SSH, tenta:")
        print("   ssh -X pi@your_raspberry_pi_ip")
        print("   ou usa a versão com input() simples")

if __name__ == "__main__":
    main()
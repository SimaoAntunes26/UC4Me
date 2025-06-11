import speech_recognition as sr
from pynput import keyboard
import threading
import time
import cv2
import torch
import numpy as np
import sys
import pyaudio
import edge_tts
import asyncio
import pygame
import io

class IntegratedVoiceAssistant:
    def __init__(self):
        self.recognizer = sr.Recognizer()
        self.is_recording = False
        self.audio_data = None
        self.recording_thread = None
        
        # YOLO model
        self.yolo_model = None
        
        # Keyboard listener
        self.listener = None
        
        # PyAudio settings
        self.chunk = 1024
        self.format = pyaudio.paInt16
        self.channels = 1
        self.rate = 44100
        
        # Edge TTS settings for European Portuguese
        self.voice = "pt-PT-RaquelNeural"  # European Portuguese female voice
        
        # Initialize pygame for audio playback
        pygame.mixer.init()
        
        print("🤖 Integrated Voice Assistant with Object Detection initialized!")

    def load_yolo_model(self):
        """Load YOLOv5 nano model"""
        try:
            print("📦 Loading YOLOv5 model...")
            self.speak("A carregar o modelo de deteção de objetos...")
            
            model = torch.hub.load('ultralytics/yolov5', 'yolov5n', pretrained=True)
            model.eval()
            self.yolo_model = model
            
            print("✅ YOLOv5 model loaded successfully!")
            self.speak("Modelo carregado com sucesso!")
            return True
        except Exception as e:
            print(f"❌ Error loading YOLOv5 model: {e}")
            self.speak("Erro ao carregar o modelo de deteção de objetos.")
            return False

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

    def take_photo_and_detect(self):
        """Take a photo using OpenCV and run YOLOv5 object detection with voice output"""
        try:
            print("📸 Taking photo...")
            self.speak("A tirar fotografia...")
            
            # Initialize camera
            cap = cv2.VideoCapture(0)
            if not cap.isOpened():
                print("❌ Error: Could not open camera")
                self.speak("Erro: não consegui aceder à câmara.")
                return
            
            ret, frame = cap.read()
            cap.release()
            
            if not ret:
                print("❌ Error: Could not capture image")
                self.speak("Erro: não consegui capturar a imagem.")
                return
            
            # Save the captured image
            cv2.imwrite('captured_image.jpg', frame)
            print("✅ Photo captured!")
            self.speak("Fotografia capturada!")
            
            # Run inference
            print("🔍 Running object detection...")
            self.speak("A analisar objetos na imagem...")
            results = self.yolo_model(frame)
            
            # Extract detected objects
            detections = results.pandas().xyxy[0]
            
            if len(detections) > 0:
                print(f"\n🎯 Detected {len(detections)} objects:")
                objects = []
                for _, detection in detections.iterrows():
                    obj_name = detection['name']
                    confidence = detection['confidence']
                    objects.append(f"{obj_name} com {confidence:.0%} de confiança")
                    print(f"- {obj_name} ({confidence:.2f})")
                
                # Speak the detected objects
                objects_text = f"Detetei {len(detections)} objetos: " + ", ".join(objects)
                self.speak(objects_text)
            else:
                print("❌ No objects detected")
                self.speak("Não detetei nenhum objeto na imagem.")
                
        except Exception as e:
            print(f"❌ Error in photo capture/detection: {e}")
            self.speak("Erro durante a captura ou análise da imagem.")

    def count_g_presses_and_execute(self):
        """Count G key presses for 5 seconds and perform actions based on count"""
        g_count = 0
        running = True
        listener = None
        
        def on_press(key):
            nonlocal g_count
            if running:
                try:
                    if key.char and key.char.lower() == 'g':
                        g_count += 1
                        print(f"G pressed! Count: {g_count}")
                except AttributeError:
                    # Special keys don't have char attribute
                    pass
        
        def stop_counting():
            nonlocal running, listener
            time.sleep(5)
            running = False
            if listener:
                listener.stop()
        
        print("\n" + "="*50)
        print("🎮 Press the G key as many times as you want!")
        print("⏰ You have 5 seconds starting... NOW!")
        self.speak("Prima a tecla G quantas vezes quiser. Tem 5 segundos a partir de... agora!")
        
        # Set up the key listener
        listener = keyboard.Listener(on_press=on_press)
        listener.start()
        
        # Start the timer thread
        timer_thread = threading.Thread(target=stop_counting)
        timer_thread.start()
        
        # Wait for the timer to finish
        timer_thread.join()
        
        print(f"\nYou pressed the G key {g_count} times in 5 seconds.")
        self.speak(f"Primiu a tecla G {g_count} vezes em 5 segundos.")
        
        # Process based on number of presses
        if g_count == 1:
            print("📸 Taking photo and detecting objects...")
            self.speak("A tirar fotografia e detetar objetos...")
            self.take_photo_and_detect()
        elif 2 <= g_count <= 4:
            print("🎤 Starting voice recording and playback...")
            self.speak("A iniciar gravação de voz...")
            self.is_recording = True
            self.recording_thread = threading.Thread(target=self._record_for_5_seconds)
            self.recording_thread.start()
        elif g_count > 4:
            print("❌ Invalid input! Too many presses (more than 4)")
            self.speak("Entrada inválida! Demasiadas pressões, mais de 4.")
        else:
            print("❌ No G key presses detected")
            self.speak("Não detetei pressões na tecla G.")
        
        # Wait a moment before next round
        print("\nReady for next round. Press 'G' to start again...")
        self.speak("Prima a tecla G para começar novamente.")
        time.sleep(2)

    def on_key_press(self, key):
        """Handle key press events"""
        try:
            if hasattr(key, 'char') and key.char and key.char.lower() == 'g':
                # Start the G-key counting process
                self.count_g_presses_and_execute()
        except AttributeError:
            pass

    def on_key_release(self, key):
        """Handle key release events"""
        # Check for Ctrl+C to exit
        if key == keyboard.Key.ctrl_l or key == keyboard.Key.ctrl_r:
            return False

    def select_mode(self):
        """Let user select between detection mode and voice assistant mode"""
        self.waiting_for_mode_selection = False
        
        print("\n🎯 Mode Selection:")
        print("1️⃣  Press G ONCE for Object Detection Mode")
        print("2️⃣  Press G TWICE for Voice Assistant Mode")
        print("⏰ You have 3 seconds to choose...")
        
        self.speak("Seleção de modo: Prima G uma vez para deteção de objetos, ou duas vezes para assistente de voz. Tem 3 segundos para escolher.")
        
        # Count G presses for mode selection
        g_count = 0
        running = True
        
        def count_presses(key):
            nonlocal g_count
            if running:
                try:
                    if key.char and key.char.lower() == 'g':
                        g_count += 1
                        print(f"Mode selection G press: {g_count}")
                except AttributeError:
                    pass
        
        # Set up temporary listener for mode selection
        temp_listener = keyboard.Listener(on_press=count_presses)
        temp_listener.start()
        
        # Wait 3 seconds
        time.sleep(3)
        running = False
        temp_listener.stop()
        
        # Determine mode based on G presses
        if g_count == 1:
            self.current_mode = "detection"
            print("🎯 Object Detection Mode selected!")
            self.speak("Modo de deteção de objetos selecionado!")
            print("\n📋 Instructions for Object Detection Mode:")
            print("- Press G once: Take photo and detect objects")
            print("- Press G 2-4 times: Just count the presses")
            print("- Press G more than 4 times: Invalid input")
            self.speak("Instruções: Prima G uma vez para fotografar e detetar objetos, 2 a 4 vezes apenas para contar, mais de 4 vezes é entrada inválida.")
        elif g_count == 2:
            self.current_mode = "voice"
            print("🎤 Voice Assistant Mode selected!")
            self.speak("Modo assistente de voz selecionado!")
            print("\n📋 Instructions for Voice Assistant Mode:")
            print("- Press G to start 5-second voice recording")
            print("- Speak your command during the recording")
            self.speak("Prima G para iniciar gravação de 5 segundos e dar comandos de voz.")
        else:
            print("❌ No valid mode selected, defaulting to Object Detection Mode")
            self.speak("Nenhum modo válido selecionado, a usar modo de deteção de objetos por defeito.")
            self.current_mode = "detection"

    def handle_g_press_voice(self):
        """Handle G key press for voice mode - start 5-second recording"""
        if self.is_recording:
            print("⚠️ Already recording, please wait...")
            self.speak("Já estou a gravar, por favor aguarde.")
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
                if int(remaining) != int(remaining + 0.1):
                    print(f"{int(remaining + 1)}... ", end="", flush=True)
            
            print("⏹️")
            
            stream.stop_stream()
            stream.close()
            audio.terminate()
            
            # Convert to speech_recognition AudioData format
            audio_data = b''.join(frames)
            self.audio_data = sr.AudioData(audio_data, self.rate, 2)
            
            self.is_recording = False
            print("✅ Recording completed! Processing...")
            self.speak("Gravação completa! A processar...")
            self._process_audio()
            
        except Exception as e:
            print(f"❌ Recording error: {e}")
            self.speak("Erro durante a gravação.")
            self.is_recording = False

    def _process_audio(self):
        """Process the recorded audio and play it back"""
        if self.audio_data is None:
            print("❌ No audio data to process.")
            return

        try:
            print("🔄 Converting speech to text...")
            self.speak("A converter voz para texto...")
            
            # Convert speech to text using European Portuguese
            text = self.recognizer.recognize_google(self.audio_data, language='pt-PT')
            print(f"📝 You said: '{text}'")
            
            # Play back what was said
            self.speak(f"Disseste: {text}")
            
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

    def start_keyboard_listener(self):
        """Start the keyboard listener"""
        self.listener = keyboard.Listener(
            on_press=self.on_key_press,
            on_release=self.on_key_release
        )
        self.listener.start()
        return self.listener

    def run(self):
        """Main run method"""
        try:
            # Load YOLO model first
            if not self.load_yolo_model():
                print("❌ Failed to load YOLO model. Exiting...")
                return
            
            # Start keyboard listener
            listener = self.start_keyboard_listener()
            
            print("\n🚀 Sistema pronto!")
            print("\n📋 Instructions:")
            print("  • Press G ONCE: Take photo and detect objects")
            print("  • Press G 2-4 TIMES: Record voice and play it back")
            print("  • Press G 5+ TIMES: Invalid input")
            print("  • Press Ctrl+C to exit")

            self.speak("Sistema pronto! Prima G uma vez para deteção de objetos, ou 2 a 4 vezes para gravação de voz.")
            
            print("\n Press 'G' to start...")
            self.speak("Prima a tecla G para começar.")
            
            # Keep the main thread alive
            try:
                while True:
                    time.sleep(1)
            except KeyboardInterrupt:
                print("\n\n👋 Exiting integrated assistant...")
                self.speak("A sair do assistente integrado. Adeus!")
                if self.is_recording:
                    self.is_recording = False
                listener.stop()
                
        except Exception as e:
            print(f"\n❌ Fatal error: {e}")
            self.speak("Erro fatal do sistema.")

def main():
    print("\n🤖 Integrated Voice Assistant with Object Detection")
    print("=" * 60)
    print("🎯 Simple G-Key Controls:")
    print("  • Press G 1 time: Take photo and detect objects with voice feedback")
    print("  • Press G 2-4 times: Record your voice and hear it played back")
    print("  • Press G 5+ times: Invalid input warning")
    print("\n🚀 Starting system...")
    print("⚠️  Make sure your camera and microphone are connected!")
    print("⚠️  For SSH users: Use 'ssh -X' for X11 forwarding")
    
    try:
        assistant = IntegratedVoiceAssistant()
        assistant.run()
        
    except Exception as e:
        print(f"\n❌ Fatal error: {e}")
        print("💡 Required libraries:")
        print("   pip install pynput opencv-python torch torchvision")
        print("   pip install SpeechRecognition pyaudio edge-tts pygame")

if __name__ == "__main__":
    main()
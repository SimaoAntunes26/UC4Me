import pyttsx3
import speech_recognition as sr
import keyboard
from threading import Thread, Event
from queue import Queue

# Initialize TTS engine
tts_engine = pyttsx3.init()
tts_engine.setProperty('rate', 150)
tts_engine.setProperty('volume', 0.9)

def speak(text):
    """Convert text to speech"""
    tts_engine.say(text)
    tts_engine.runAndWait()

def listen(stop_event, result_queue):
    """Convert speech to text while the key is pressed"""
    recognizer = sr.Recognizer()
    
    with sr.Microphone() as source:
        print("Listening... (hold 'G')")
        recognizer.adjust_for_ambient_noise(source)
        
        try:
            audio = recognizer.listen(source, timeout=1, phrase_time_limit=5)
            
            try:
                text = recognizer.recognize_google(audio)
                print(f"You said: {text}")
                result_queue.put(text.lower())
            except sr.UnknownValueError:
                print("Sorry, I didn't catch that.")
                result_queue.put("")
            except sr.RequestError:
                print("Sorry, my speech service is down.")
                result_queue.put("")
                
        except sr.WaitTimeoutError:
            result_queue.put("")

def voice_interaction():
    """Interactive voice conversation with push-to-talk"""
    speak("Hello! Hold the 'G' key to speak to me. Press 'Esc' to exit.")
    
    while True:
        print("\nPress and hold 'G' to speak or 'Esc' to exit...")
        key = keyboard.read_key()
        
        if key == 'esc':
            speak("Goodbye!")
            break
        elif key.lower() == 'g':
            # Create communication objects
            stop_event = Event()
            result_queue = Queue()
            
            # Start listening thread
            listen_thread = Thread(target=listen, args=(stop_event, result_queue))
            listen_thread.start()
            
            # Wait for 'G' key release
            keyboard.wait('g')
            
            # Signal the listening thread to stop (though it should be done by now)
            stop_event.set()
            listen_thread.join()
            
            # Get the recognized text
            command = result_queue.get()
            
            if not command:
                continue
            elif "your name" in command:
                speak("I'm your Python voice assistant.")
            elif "time" in command:
                from datetime import datetime
                current_time = datetime.now().strftime("%H:%M")
                speak(f"The current time is {current_time}")
            elif "exit" in command or "quit" in command or "stop" in command:
                speak("Goodbye!")
                break
            else:
                speak(f"You said: {command}. I'm still learning to respond to that.")

if __name__ == "__main__":
    try:
        import keyboard
        print("Voice Assistant - Hold 'G' to speak, press 'Esc' to exit")
        voice_interaction()
    except ImportError:
        print("Please install the 'keyboard' library first: pip install keyboard")
    except Exception as e:
        print(f"An error occurred: {e}")
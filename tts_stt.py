import pyttsx3
import speech_recognition as sr

tts_engine = pyttsx3.init()
tts_engine.setProperty('rate', 150)
tts_engine.setProperty('volume', 0.9)

def speak(text):
    """Convert text to speech"""
    tts_engine.say(text)
    tts_engine.runAndWait()

def listen():
    """Convert speech to text using microphone input"""
    recognizer = sr.Recognizer()
    
    with sr.Microphone() as source:
        print("Listening...")
        recognizer.adjust_for_ambient_noise(source)  # Reduce background noise
        audio = recognizer.listen(source)
        
    try:
        print("Recognizing...")
        # Using Google Web Speech API (requires internet)
        text = recognizer.recognize_google(audio)
        print(f"You said: {text}")
        return text
    except sr.UnknownValueError:
        print("Sorry, I didn't catch that.")
        return ""
    except sr.RequestError:
        print("Sorry, my speech service is down.")
        return ""

def voice_interaction():
    """Interactive voice conversation"""
    speak("Hello! How can I help you today?")
    
    while True:
        command = listen().lower()
        
        if not command:
            continue
        elif "exit" in command or "quit" in command or "stop" in command:
            speak("Goodbye!")
            break
        elif "your name" in command:
            speak("I'm your Python voice assistant.")
        elif "time" in command:
            from datetime import datetime
            current_time = datetime.now().strftime("%H:%M")
            speak(f"The current time is {current_time}")
        else:
            speak(f"You said: {command}. I'm still learning to respond to that.")

if __name__ == "__main__":
    print("Voice Assistant - Press Ctrl+C to exit")
    print("Available commands: ask my name, ask for time, say exit/quit/stop")
    voice_interaction()
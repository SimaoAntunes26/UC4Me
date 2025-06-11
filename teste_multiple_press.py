from pynput import keyboard
import threading
import time

def count_g_presses():
    """Count G key presses for 3 seconds"""
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
                # Special keys (ctrl, alt, etc.) don't have char attribute
                pass
    
    def stop_counting():
        nonlocal running, listener
        time.sleep(3)
        running = False
        if listener:
            listener.stop()
    
    print("Press the G key as many times as you can!")
    print("You have 3 seconds starting... NOW!")
    
    # Set up the key listener
    listener = keyboard.Listener(on_press=on_press)
    listener.start()
    
    # Start the timer thread
    timer_thread = threading.Thread(target=stop_counting)
    timer_thread.start()
    
    # Wait for the timer to finish
    timer_thread.join()
    
    print(f"\nTime's up! You pressed the G key {g_count} times in 3 seconds.")
    return g_count

if __name__ == "__main__":
    try:
        count_g_presses()
    except KeyboardInterrupt:
        print("\nProgram interrupted by user.")
    except Exception as e:
        print(f"An error occurred: {e}")
        print("Make sure you have the 'pynput' library installed:")
        print("pip install pynput")
        print("\nNote: On Linux, you may need to run this script with administrator privileges.")
        print("Try: sudo python3 your_script.py")
from pynput import keyboard
import threading
import time
import cv2
import torch
import numpy as np
import sys

def load_yolo_model():
    """Load YOLOv5 nano model"""
    try:
        model = torch.hub.load('ultralytics/yolov5', 'yolov5n', pretrained=True)
        model.eval()
        return model
    except Exception as e:
        print(f"Error loading YOLOv5 model: {e}")
        return None

def take_photo_and_detect(model):
    """Take a photo using OpenCV and run YOLOv5 object detection"""
    try:
        # Initialize camera
        cap = cv2.VideoCapture(0)
        if not cap.isOpened():
            print("Error: Could not open camera")
            return
        
        print("Taking photo...")
        ret, frame = cap.read()
        cap.release()
        
        if not ret:
            print("Error: Could not capture image")
            return
        
        # Save the captured image
        cv2.imwrite('captured_image.jpg', frame)
        print("Photo captured!")
        
        # Run inference
        print("Running object detection...")
        results = model(frame)
        
        # Extract detected objects
        detections = results.pandas().xyxy[0]
        
        if len(detections) > 0:
            print("\nDetected objects:")
            objects = []
            for _, detection in detections.iterrows():
                obj_name = detection['name']
                confidence = detection['confidence']
                objects.append(f"{obj_name} ({confidence:.2f})")
            
            for obj in objects:
                print(f"- {obj}")
        else:
            print("No objects detected")
            
    except Exception as e:
        print(f"Error in photo capture/detection: {e}")
        print("Make sure you have opencv-python and torch installed:")
        print("pip install opencv-python torch torchvision")

def count_g_presses(model):
    """Count G key presses for 5 seconds and perform actions based on count"""
    while True:
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
            time.sleep(5)
            running = False
            if listener:
                listener.stop()
        
        print("\n" + "="*50)
        print("Press the G key as many times as you want!")
        print("You have 5 seconds starting... NOW!")
        
        # Set up the key listener
        listener = keyboard.Listener(on_press=on_press)
        listener.start()
        
        # Start the timer thread
        timer_thread = threading.Thread(target=stop_counting)
        timer_thread.start()
        
        # Wait for the timer to finish
        timer_thread.join()
        
        print(f"\nTime's up! You pressed the G key {g_count} times in 5 seconds.")
        
        # Process based on number of presses
        if g_count == 1:
            print("Taking photo and detecting objects...")
            take_photo_and_detect(model)
        elif 2 <= g_count <= 4:
            print(f"G key pressed {g_count} times - just printing count")
        elif g_count > 4:
            print("Invalid input! Too many presses (more than 4)")
        else:
            print("No G key presses detected")
        
        # Ask if user wants to continue
        print("\nPress Ctrl+C to exit or wait for next round...")
        time.sleep(2)

if __name__ == "__main__":
    try:
        print("Advanced G Key Counter with Object Detection")
        print("Loading YOLOv5 model...")
        
        model = load_yolo_model()
        if model is None:
            print("Failed to load YOLOv5 model. Photo detection will not work.")
            sys.exit(1)
        
        print("YOLOv5 model loaded successfully!")
        print("\nInstructions:")
        print("- Press G once: Take photo and detect objects")
        print("- Press G 2-4 times: Just print the count")
        print("- Press G more than 4 times: Invalid input")
        print("\nMake sure your camera is connected!")
        
        count_g_presses(model)
    except KeyboardInterrupt:
        print("\nProgram interrupted by user. Goodbye!")
    except Exception as e:
        print(f"An error occurred: {e}")
        print("Make sure you have the required libraries installed:")
        print("pip install pynput opencv-python torch torchvision")
        print("\nNote: On Linux, you may need to run this script with administrator privileges.")
        print("Try: sudo python3 your_script.py")
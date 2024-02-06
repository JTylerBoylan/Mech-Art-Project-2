import numpy as np
import cv2
import random

# Frame options
GAZE_TRACKING_ENABLED = True
CALIBRATION_ENABLED = True
SHOW_TEXT_MESSAGE = True
SHOW_EYE_POSITIONS = True
SHOW_GAZE_POSITION = True
SHOW_CALIBRATION_POINTS = True
COVER_EYES = False

#########################
## CAMERA FUNCTIONS ##
#########################

cap = cv2.VideoCapture(0)

image_width = 640
image_height = 480
def configure_camera():
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, image_width)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, image_height)

############################
## GAZETRACKING FUNCTIONS ##
############################
from gaze_tracking import GazeTracking

gaze = GazeTracking()

# Gaze calibration
center_point = (0.5, 0.5)
num_samples = 50
def calibrate_gaze():
    global center_point
    input("Look at the center. Press Enter to continue...")

    # Get the average gaze ratio
    horiz_ratio_sum = 0
    verti_ratio_sum = 0
    sample = 0
    while sample < num_samples:
        success, frame = cap.read()
        if success:
            try:
                gaze.refresh(frame)
                horiz_ratio = gaze.horizontal_ratio()
                verti_ratio = gaze.vertical_ratio()
                if (horiz_ratio is not None) and (verti_ratio is not None):
                    horiz_ratio_sum += horiz_ratio
                    verti_ratio_sum += verti_ratio
                    sample += 1
            except:
                print("Gaze refresh error. Skipping frame.")
    
    horiz_ratio_center = horiz_ratio_sum / num_samples
    verti_ratio_center = verti_ratio_sum / num_samples

    # Update the center point
    center_point = (horiz_ratio_center, verti_ratio_center)


# Check if the user is looking at the center
looking_down = False
random_int = 0
enter_threshold = 0.25  # Enter center gaze if ratio difference is less than this
exit_threshold = 0.125   # Exit center gaze if ratio difference is more than this
def is_looking_down(verti_ratio):
    global looking_down, random_int
    verti_delta = verti_ratio - center_point[1]
    if verti_delta > enter_threshold:
        if looking_down is not True:
            random_int = random.randint(0, 1000)
        looking_down = True
    elif verti_delta < exit_threshold:
        looking_down = False
    return looking_down

# Apply low pass filter to the ratio
horiz_ratio_filtered = 0.5
verti_ratio_filtered = 0.5
filter_size = 2
def apply_ratio_filter(horiz_ratio, verti_ratio):
    global horiz_ratio_filtered, verti_ratio_filtered
    horiz_ratio_filtered = (horiz_ratio_filtered * filter_size + horiz_ratio) / (filter_size + 1)
    verti_ratio_filtered = (verti_ratio_filtered * filter_size + verti_ratio) / (filter_size + 1)
    return horiz_ratio_filtered, verti_ratio_filtered

# Create a black frame
def black_frame():
    return np.zeros((image_height, image_width, 3), dtype=np.uint8)

# Print text to the center of the frame
phrases = [
    "Hello there",
    "I see you",
    "What's up?",
    "My eyes are up here",
    "Caught you looking!",
    "Hey, over here!",
    "Eye contact, please",
    "Trying to hide, huh?",
    "Focus, focus!",
    "Looking sharp, but listen too",
    "Eyes front, please",
    "Are we playing peek-a-boo?",
    "This is not a mirror!",
    "Oh, hello self-observer",
    "Got distracted?",
    "Look at me when I'm talking",
    "Admiring the view?",
    "This isn’t a photoshoot",
    "Stop the screen stare",
    "Your attention, please",
    ":("
]
def print_phrase_to_frame(frame, phrase=0):
    text = phrases[phrase % len(phrases)]
    font = cv2.FONT_HERSHEY_SIMPLEX
    text_size = cv2.getTextSize(text, font, 1, 2)[0]
    text_x = (frame.shape[1] - text_size[0]) // 2
    text_y = (frame.shape[0] + text_size[1]) // 2
    cv2.putText(frame, text, (text_x, text_y), font, 1, (255, 255, 255), 2)

# Show gaze location
def show_gaze_location(frame, horiz_ratio, verti_ratio, radius=10, color=(0, 255, 0)):
    x = int(horiz_ratio * frame.shape[1])
    y = int(verti_ratio * frame.shape[0])
    cv2.circle(frame, (x, y), radius, color, 2)
    return frame

def draw_circles_around_eyes(frame, eye_location_left, eye_location_right):
    if eye_location_left is not None:
        cv2.circle(frame, eye_location_left, 5, (0, 0, 255), 20)
    if eye_location_right is not None:
        cv2.circle(frame, eye_location_right, 5, (0, 0, 255), 20)
    return frame

# Show calibration points
def show_calibration_points(frame):
    frame = show_gaze_location(frame, center_point[0], center_point[1], radius=10, color=(0, 0, 255))
    return frame

def process_frame(frame):

    if not GAZE_TRACKING_ENABLED:
        return frame

    frame= cv2.resize(frame, (640, 480))

    # Run gaze detection
    try:
        gaze.refresh(frame)
    except:
        print("Gaze refresh error. Skipping frame.")
        return frame
    
    # Show eye positions
    if SHOW_EYE_POSITIONS:
        frame = gaze.annotated_frame()
    
    # Get gaze ratios
    horiz_ratio = gaze.horizontal_ratio()
    verti_ratio = gaze.vertical_ratio()

    # Proceed only if both gaze ratios are available
    if (horiz_ratio is None or verti_ratio is None):
        return frame

    # Apply low pass filter
    horiz_ratio, verti_ratio = apply_ratio_filter(horiz_ratio, verti_ratio)

    # Show calibration points
    if SHOW_CALIBRATION_POINTS:
        frame = show_calibration_points(frame)

    # Show gaze location
    if SHOW_GAZE_POSITION:
        frame = show_gaze_location(frame, horiz_ratio, verti_ratio)

    # Get eye locations
    if COVER_EYES:
        eye_location_left = gaze.pupil_left_coords()
        eye_location_right = gaze.pupil_right_coords()
        frame = draw_circles_around_eyes(frame, eye_location_left=eye_location_left, eye_location_right=eye_location_right)

    # If the user is gazing at the center, show the message
    if SHOW_TEXT_MESSAGE and is_looking_down(verti_ratio):
        frame = black_frame()
        print_phrase_to_frame(frame, phrase=random_int)

    print(f"HR: {horiz_ratio} |  VR: {verti_ratio}")

    return frame
    

###########################
## FLASK WEB APPLICATION ##
###########################

from flask import Flask, Response, render_template_string

app = Flask(__name__)

@app.route('/')
def index():
    return render_template_string("""
    <html>
    <head>
        <style>
            body, html {
                margin: 0;
                padding: 0;
                overflow: hidden;
            }
            img {
                position: absolute;
                top: 0;
                left: 0;
                width: 100%;
                height: 100%;
            }
        </style>
    </head>
    <body>
        <img src="/video_feed">
    </body>
    </html>
    """)

@app.route('/video_feed')
def video_feed():
    return Response(gen_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

def gen_frames():
    while True:
        
        success, frame = cap.read()

        if success:

            frame = process_frame(frame)

            _, buffer = cv2.imencode('.jpg', frame, [int(cv2.IMWRITE_JPEG_QUALITY), 80])
            frame = buffer.tobytes()
        
            # Yield the frame
            yield (b'--frame\r\n'
                    b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

#################
## ENTRY POINT ##
#################

if __name__ == '__main__':

    # Configure camera
    configure_camera()

    # Calibrate gaze
    if CALIBRATION_ENABLED:
        calibrate_gaze()

    # Run the web application
    app.run(host='0.0.0.0', port=5000)
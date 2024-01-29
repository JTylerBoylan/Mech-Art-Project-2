import numpy as np
import cv2

# Frame options
GAZE_TRACKING_ENABLED = True
CALIBRATION_ENABLED = False
SHOW_TEXT_MESSAGE = False
SHOW_EYE_POSITIONS = True
SHOW_GAZE_POSITION = True
SHOW_CALIBRATION_POINTS = False

############################
## GAZETRACKING FUNCTIONS ##
############################
from gaze_tracking import GazeTracking

gaze = GazeTracking()

# Gaze calibration
center_ratio = None
horiz_ratio_range = None
verti_ratio_range = None
def calibrate_gaze():
    directions = ["center", "left", "right", "up", "down"]
    num_samples = 10  # Number of samples to take for each direction
    ratios = {"horizontal": {}, "vertical": {}}

    for direction in directions:
        horiz_ratios = []
        verti_ratios = []

        print("----------------------------------------")
        input(f"Look {direction} and press Enter.")
        for _ in range(num_samples):
            frame = picam2.capture_array()
            gaze.refresh(frame)

            horiz_ratio = gaze.horizontal_ratio()
            verti_ratio = gaze.vertical_ratio()

            if horiz_ratio is not None and verti_ratio is not None:
                horiz_ratios.append(horiz_ratio)
                verti_ratios.append(verti_ratio)

        # Calculate the average ratio for each direction
        if horiz_ratios and verti_ratios:
            ratios["horizontal"][direction] = sum(horiz_ratios) / len(horiz_ratios)
            ratios["vertical"][direction] = sum(verti_ratios) / len(verti_ratios)
        else:
            print(f"Gaze not properly detected for {direction}. Please retry.")
            return False 

    print("----------------------------------------")

    global center_ratio, horiz_ratio_range, verti_ratio_range

    # Calculate the normalized center ratio
    center_ratio = (ratios["horizontal"]["center"], ratios["vertical"]["center"])

    # Calculate scale factors based on extreme points
    horiz_ratio_range = (ratios["horizontal"]["right"], ratios["horizontal"]["left"])
    verti_ratio_range = (ratios["vertical"]["up"], ratios["vertical"]["down"])

    print("------------ CALIBRATION ------------")
    print(f"Center: {center_ratio}")
    print(f"Horizontal range: {horiz_ratio_range}")
    print(f"Vertical range: {verti_ratio_range}")
    print("-------------------------------------")

    return True

# Adjust the ratio based on the calibration
def get_adjusted_ratio(horiz_ratio, verti_ratio):
    def adjust_ratio(ratio, range, center):
        if ratio < center:
            return 0.5 * (ratio - range[0]) / (center - range[0])
        else:
            return 0.5 * (ratio - center) / (range[1] - center) + 0.5

    horiz_ratio = adjust_ratio(horiz_ratio, horiz_ratio_range, center_ratio[0])
    verti_ratio = adjust_ratio(verti_ratio, verti_ratio_range, center_ratio[1])
    return horiz_ratio, verti_ratio

# Check if the user is looking at the center
is_center_gaze = False
enter_threshold = 0.125  # Enter center gaze if ratio difference is less than this
exit_threshold = 0.25   # Exit center gaze if ratio difference is more than this
def is_looking_center(horiz_ratio, verti_ratio):
    global is_center_gaze
    if abs(horiz_ratio - 0.5) < enter_threshold and abs(verti_ratio - 0.5) < enter_threshold:
        is_center_gaze = True
    elif abs(horiz_ratio - 0.5) > exit_threshold or abs(verti_ratio - 0.5) > exit_threshold:
        is_center_gaze = False
    return is_center_gaze

# Apply low pass filter to the ratio
horiz_ratio_filtered = 0.5
verti_ratio_filtered = 0.5
filter_size = 5
def apply_ratio_filter(horiz_ratio, verti_ratio):
    global horiz_ratio_filtered, verti_ratio_filtered
    horiz_ratio_filtered = (horiz_ratio_filtered * filter_size + horiz_ratio) / (filter_size + 1)
    verti_ratio_filtered = (verti_ratio_filtered * filter_size + verti_ratio) / (filter_size + 1)
    return horiz_ratio_filtered, verti_ratio_filtered

# Create a black frame
def black_frame():
    return np.zeros((image_height, image_width, 3), dtype=np.uint8)

# Print text to the center of the frame
def print_text_to_frame(frame, text):
    font = cv2.FONT_HERSHEY_SIMPLEX
    text_size = cv2.getTextSize(text, font, 1, 2)[0]
    text_x = (frame.shape[1] - text_size[0]) // 2
    text_y = (frame.shape[0] + text_size[1]) // 2
    cv2.putText(frame, text, (text_x, text_y), font, 1, (255, 255, 255), 2)

# Show gaze location
def show_gaze_location(frame, horiz_ratio, verti_ratio, radius=10):
    x = int(horiz_ratio * frame.shape[1])
    y = int(verti_ratio * frame.shape[0])
    cv2.circle(frame, (x, y), radius, (0, 255, 0), 2)
    return frame

# Show calibration points
def show_calibration_points(frame):
    frame = show_gaze_location(frame, center_ratio[0], center_ratio[1], 5)
    frame = show_gaze_location(frame, horiz_ratio_range[0], center_ratio[1], 5)
    frame = show_gaze_location(frame, horiz_ratio_range[1], center_ratio[1], 5)
    frame = show_gaze_location(frame, center_ratio[0], verti_ratio_range[0], 5)
    frame = show_gaze_location(frame, center_ratio[0], verti_ratio_range[1], 5)
    return frame

def process_frame(frame):
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
    (horiz_ratio, verti_ratio) = apply_ratio_filter(horiz_ratio, verti_ratio)

    # Adjust the ratio based on the calibration
    if CALIBRATION_ENABLED:
        (horiz_ratio, verti_ratio) = get_adjusted_ratio(horiz_ratio, verti_ratio)

    # Show gaze location
    if SHOW_GAZE_POSITION:
        frame = show_gaze_location(frame, horiz_ratio, verti_ratio)

    # Show calibration points
    if SHOW_CALIBRATION_POINTS:
        frame = show_calibration_points(frame)

    # If the user is gazing at the center, show the message
    if is_looking_center(horiz_ratio, verti_ratio) and SHOW_TEXT_MESSAGE:
        frame = black_frame()
        print_text_to_frame(frame, "Hello there")

    return frame


#########################
## PICAMERA2 FUNCTIONS ##
#########################

from picamera2 import Picamera2

picam2 = Picamera2()

image_width = 640
image_height = 480
def configure_camera():
    config = picam2.create_video_configuration(main={"format": "RGB888", "size": (image_width, image_height)})
    picam2.configure(config)
    picam2.start()

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
        frame = picam2.capture_array()

        if (GAZE_TRACKING_ENABLED):
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
    if (GAZE_TRACKING_ENABLED and CALIBRATION_ENABLED):
        while (not calibrate_gaze()):
            pass

    # Run the web application
    app.run(host='0.0.0.0', port=5000)
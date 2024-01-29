import numpy as np
import cv2
from flask import Flask, Response, request, render_template_string
from picamera2 import Picamera2
from gaze_tracking import GazeTracking

app = Flask(__name__)
picam2 = Picamera2()
gaze = GazeTracking()

image_width = 640
image_height = 480

def configure_camera():

    config = picam2.create_video_configuration(main={"format": "RGB888", "size": (image_width, image_height)})

    picam2.configure(config)
    picam2.start()

# Gaze calibration
center_horiz = None
center_verti = None
horiz_range = None
verti_range = None
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

    global center_horiz, center_verti, horiz_range, verti_range

    # Calculate the normalized center ratio
    center_horiz = ratios["horizontal"]["center"]
    center_verti = ratios["vertical"]["center"]

    # Calculate scale factors based on extreme points
    horiz_range = (ratios["horizontal"]["right"], ratios["horizontal"]["left"])
    verti_range = (ratios["vertical"]["up"], ratios["vertical"]["down"])

    print(f"Center: {center_horiz}, {center_verti}")
    print(f"Horizontal range: {horiz_range}")
    print(f"Vertical range: {verti_range}")

    return True

def adjust_ratio(ratio, range, center):
    if ratio < center:
        # Scale ratio between 0 and 0.5
        return 0.5 * (ratio - range[0]) / (center - range[0])
    else:
        # Scale ratio between 0.5 and 1
        return 0.5 * (ratio - center) / (range[1] - center) + 0.5


# Global variable to keep track of gaze state
is_center_gaze = False

def process_frame(frame, horiz_ratio, verti_ratio):

    # Thresholds for entering and exiting center gaze state
    enter_threshold = 0.125  # Enter center gaze if ratio difference is less than this
    exit_threshold = 0.25   # Exit center gaze if ratio difference is more than this

    # Check if the gaze is approximately at the center
    global is_center_gaze
    if abs(horiz_ratio - 0.5) < enter_threshold and abs(verti_ratio - 0.5) < enter_threshold:
        is_center_gaze = True
    elif abs(horiz_ratio - 0.5) > exit_threshold or abs(verti_ratio - 0.5) > exit_threshold:
        is_center_gaze = False

    # If the user is gazing at the center, show the message
    if is_center_gaze:
        # Create a black frame
        frame = np.zeros((image_height, image_width, 3), dtype=np.uint8)

        # Set the message
        message = "Hello there"
        font = cv2.FONT_HERSHEY_SIMPLEX
        text_size = cv2.getTextSize(message, font, 1, 2)[0]
        text_x = (frame.shape[1] - text_size[0]) // 2
        text_y = (frame.shape[0] + text_size[1]) // 2

        # Put the message on the frame
        cv2.putText(frame, message, (text_x, text_y), font, 1, (255, 255, 255), 2)

    return frame

def gen_frames():
    # Initialize gaze ratio averages
    horiz_ratio_avg = 0.5
    verti_ratio_avg = 0.5
    rolling_avg_size = 3  # Adjust the size of the rolling average as needed

    while True:
        frame = picam2.capture_array()

        # Run gaze detection
        try:
            gaze.refresh(frame)
        except:
            print("Gaze refresh error. Skipping frame.")
            continue

        # Get gaze ratios
        horiz_ratio = gaze.horizontal_ratio()
        verti_ratio = gaze.vertical_ratio()

        print(f"RAW: (HR: {horiz_ratio} | VR: {verti_ratio})")

        # Proceed only if both gaze ratios are available
        if horiz_ratio is not None and verti_ratio is not None:

            # Update the rolling average
            horiz_ratio_avg = (horiz_ratio_avg * rolling_avg_size + horiz_ratio) / (rolling_avg_size + 1)
            verti_ratio_avg = (verti_ratio_avg * rolling_avg_size + verti_ratio) / (rolling_avg_size + 1)

            # Apply calibration
            horiz_ratio = adjust_ratio(horiz_ratio_avg, horiz_range, center_horiz)
            verti_ratio = adjust_ratio(verti_ratio_avg, verti_range, center_verti)

            print(f"ADJ: (HR: {horiz_ratio} | VR: {verti_ratio})")

            # Process and encode the frame
            frame = process_frame(frame, horiz_ratio, verti_ratio)
            ret, buffer = cv2.imencode('.jpg', frame, [int(cv2.IMWRITE_JPEG_QUALITY), 80])
            frame = buffer.tobytes()
            
            # Yield the frame
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')


@app.route('/video_feed')
def video_feed():
    return Response(gen_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

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

if __name__ == '__main__':
    configure_camera()
    if calibrate_gaze():
        app.run(host='0.0.0.0', port=5000)
    else:
        print("Gaze calibration failed. Exiting.")
        picam2.stop()
        picam2.close()

import numpy as np
import cv2
from flask import Flask, Response, request, render_template_string
from picamera2 import Picamera2
from gaze_tracking import GazeTracking

app = Flask(__name__)

picam2 = Picamera2()

config = picam2.create_video_configuration(main={"format": "RGB888", "size": (640, 480)})
picam2.configure(config)

picam2.start()

rolling_avg_size = 2
horiz_ratio_avg = 0.5
verti_ratio_avg = 0.5

def gen_frames():
    gaze = GazeTracking()
    
    global horiz_ratio_avg, verti_ratio_avg  # Declare these variables as global

    while True:
        frame = picam2.capture_array()
        frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)

        try:
            gaze.refresh(frame)
        except:
            print("Gaze refresh error")

        frame = gaze.annotated_frame()

        horiz_ratio = gaze.horizontal_ratio()
        verti_ratio = gaze.vertical_ratio()

        # Scale the frame to the screen size
        frame = cv2.resize(frame, (1024, 600))

        if horiz_ratio is not None and verti_ratio is not None:
            # Rolling average filter
            horiz_ratio_avg = (horiz_ratio_avg * rolling_avg_size + horiz_ratio) / (rolling_avg_size + 1)
            verti_ratio_avg = (verti_ratio_avg * rolling_avg_size + verti_ratio) / (rolling_avg_size + 1)

            # Draw a circle at the gaze position
            horiz_pixel = int(1024 * horiz_ratio_avg)
            verti_pixel = int(600 * verti_ratio_avg)
            cv2.circle(frame, (horiz_pixel, verti_pixel), 30, (0, 255, 0), 2)

        ret, buffer = cv2.imencode('.jpg', frame, [int(cv2.IMWRITE_JPEG_QUALITY), 80])
        frame = buffer.tobytes()
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

@app.route('/video_feed')
def video_feed():
    return Response(gen_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/')
def index():
    # Use JavaScript to handle screen color change and video display size
    html = """
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
        <script>
            var video = document.createElement("img");
            video.src = '/video_feed';
            document.body.appendChild(video);
        </script>
    </body>
    </html>
    """
    return render_template_string(html)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)

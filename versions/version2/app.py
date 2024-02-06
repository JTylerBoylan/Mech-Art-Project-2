import cv2
from picamera2 import Picamera2

picam2 = Picamera2()

image_width = 1640
image_height = 1232
def configure_camera():
    config = picam2.create_video_configuration(main={"format": "RGB888", "size": (image_width, image_height)})
    picam2.configure(config)
    picam2.start()

from flask import Flask, Response, render_template

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/video_feed')
def video_feed():
    return Response(gen_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

def gen_frames():
    while True:
        frame = picam2.capture_array()

        _, buffer = cv2.imencode('.jpg', frame, [int(cv2.IMWRITE_JPEG_QUALITY), 80])
        frame = buffer.tobytes()
        
        # Yield the frame
        yield (b'--frame\r\n'
                b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

if __name__ == '__main__':

    # Configure camera
    configure_camera()

    # Run the web application
    app.run(host='0.0.0.0', port=5000)
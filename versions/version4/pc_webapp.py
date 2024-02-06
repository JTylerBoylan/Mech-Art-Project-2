from flask import Flask, Response, render_template_string
import cv2
import socket
import numpy as np
from threading import Thread
from threading import Lock
import time

app = Flask(__name__)

# Global frame variable and lock
latest_frame = None
frame_lock = Lock()

frame_rate = 60
frame_interval = 1.0 / frame_rate

def udp_listener():
    global latest_frame

    udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    host_ip = '0.0.0.0'
    host_port = 3000
    buffer_size = 65536
    udp_socket.bind((host_ip, host_port))
    print(f"Listening for video stream on UDP {host_ip}:{host_port}")

    while True:
        frame_data, _ = udp_socket.recvfrom(buffer_size)
        frame = np.frombuffer(frame_data, dtype=np.uint8)
        frame = cv2.imdecode(frame, flags=cv2.IMREAD_COLOR)
        if frame is not None:
            with frame_lock:
                latest_frame = frame
        time.sleep(0.001)

def generate_frames():
    global latest_frame
    last_time = time.time()
    while True:
        current_time = time.time()
        elapsed = current_time - last_time
        
        if elapsed < frame_interval:
            time.sleep(frame_interval - elapsed)

        last_time = current_time

        with frame_lock:
            if latest_frame is not None:
                latest_frame = process_frame(latest_frame)
                video_frame = cv2.imencode('.jpg', latest_frame)[1].tobytes()
                yield (b'--frame\r\nContent-Type: image/jpeg\r\n\r\n' + video_frame + b'\r\n')

from gaze_tracking import GazeTracking
gaze = GazeTracking()

def process_frame(frame):
    
    try:
        gaze.refresh(frame)
        frame = gaze.annotated_frame()
        text = ""
        if gaze.is_blinking():
            text = "Blinking"
        elif gaze.is_right():
            text = "Looking right"
        elif gaze.is_left():
            text = "Looking left"
        elif gaze.is_center():
            text = "Looking center"
        cv2.putText(frame, text, (90, 60), cv2.FONT_HERSHEY_DUPLEX, 1.6, (147, 58, 31), 2)
    except Exception as e:
        print(e)

    return frame


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
    return Response(generate_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

if __name__ == '__main__':
    udp_thread = Thread(target=udp_listener)
    udp_thread.daemon = True
    udp_thread.start()
    app.run(host='0.0.0.0', port=5000, threaded=True, use_reloader=False)
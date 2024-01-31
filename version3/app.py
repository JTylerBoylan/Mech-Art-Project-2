import cv2
import socket
from picamera2 import Picamera2

image_resolution = (1640, 1232)
picam2 = Picamera2()
config = picam2.create_video_configuration(main={"format": "RGB888", "size": image_resolution})
picam2.configure(config)
picam2.start()

# UDP setup
udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
target_address = ('http://10.0.0.10', 3000)

while True:
    frame = picam2.capture_array()
    _, buffer = cv2.imencode('.jpg', frame, [int(cv2.IMWRITE_JPEG_QUALITY), 80])
    frame = buffer.tobytes()
    udp_socket.sendto(frame, target_address)


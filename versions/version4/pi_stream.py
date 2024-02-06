import cv2
import socket

cap = cv2.VideoCapture(0)
# cap.set(cv2.CAP_PROP_FRAME_WIDTH, 680)
# cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

udp = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
addr = ('10.0.0.185', 3000)

jpeg_quality = 80

while True:
    ret, frame = cap.read()
    if ret:
        frame = cv2.resize(frame, (640, 480))
        ret, jpeg = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, jpeg_quality])
        if ret:
            udp.sendto(jpeg.tobytes(), addr)
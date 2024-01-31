import cv2
import socket
from picamera2 import Picamera2

def main():
    image_resolution = (1640, 1232)
    picam2 = Picamera2()
    config = picam2.create_video_configuration(main={"format": "RGB888", "size": image_resolution})
    picam2.configure(config)
    picam2.start()

    # UDP setup
    udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    target_address = ('10.0.0.185', 3000)

    try:
        while True:
            frame = picam2.capture_array()
            frame = cv2.resize(frame, (640, 480))
            _, buffer = cv2.imencode('.jpg', frame, [int(cv2.IMWRITE_JPEG_QUALITY), 80])
            frame = buffer.tobytes()
            udp_socket.sendto(frame, target_address)
    except Exception as e:
        print(f"Error occurred: {e}")
    finally:
        udp_socket.close()
        picam2.stop()

if __name__ == "__main__":
    main()

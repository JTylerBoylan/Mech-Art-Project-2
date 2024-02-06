import cv2
import socket
import numpy as np

def main():
    # UDP setup
    udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    host_ip = '0.0.0.0'  # Listen on all interfaces
    host_port = 3000  # Listening port
    buffer_size = 65536  # Maximum size of a UDP packet

    udp_socket.bind((host_ip, host_port))
    print(f"Listening for video stream on UDP {host_ip}:{host_port}")

    try:
        while True:
            frame_data, _ = udp_socket.recvfrom(buffer_size)
            frame = np.frombuffer(frame_data, dtype=np.uint8)
            frame = cv2.imdecode(frame, flags=cv2.IMREAD_COLOR)

            if frame is not None:
                cv2.imshow("Received Video", frame)
                if cv2.waitKey(1) & 0xFF == ord('q'):  # Press 'q' to quit
                    break
            else:
                print("Frame decode failed")
    finally:
        udp_socket.close()
        cv2.destroyAllWindows()

if __name__ == "__main__":
    main()
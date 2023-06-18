import cv2
from cv2 import aruco
import time
import csv
from datetime import datetime

# Set the dimensions of the table
table_width = 110  # Replace with your table width in centimeters

# Set the time interval for measuring speed (in seconds)
time_interval = 3  # Replace with your desired time interval

# Initialize the video capture
cap = cv2.VideoCapture(1)  # Replace with your camera index if using multiple cameras
# Calculate the pixel-to-centimeter conversion factor
pixel_to_cm = table_width / cap.get(cv2.CAP_PROP_FRAME_WIDTH)

# Initialize variables for speed calculation
prev_center = None
prev_time = None
start_time = time.time()
speeds = []

# Create cv2.aruco dictionary and parameters
dictionary = cv2.aruco.getPredefinedDictionary(cv2.aruco.DICT_4X4_100)
parameters = cv2.aruco.DetectorParameters()

# Specific aruco marker id that we have printed
desired_id = 72

# Create a CSV file for saving the data
csv_file = open("speed_data.csv", "w", newline="")
csv_writer = csv.writer(csv_file)
csv_writer.writerow(["Time", "Speed (cm/s)"])

while True:
    # Read the frame from the video capture
    ret, frame = cap.read()

    # Convert the frame to grayscale for cv2.aruco marker detection
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

    # Detect cv2.aruco markers in the frame
    corners, ids, _ = cv2.aruco.detectMarkers(gray, dictionary, parameters=parameters)

    # Process each detected cv2.aruco marker
    if ids is not None:
        for i in range(len(ids)):
            if ids[i] == desired_id:
                # Calculate the center of the cv2.aruco marker
                center_x = int((corners[i][0][0][0] + corners[i][0][2][0]) / 2)
                center_y = int((corners[i][0][0][1] + corners[i][0][2][1]) / 2)

                # Draw a circle at the center of the cv2.aruco marker
                cv2.circle(frame, (center_x, center_y), 5, (0, 255, 0), -1)

                # Calculate the current time
                current_time = time.time()

                # Calculate the speed if there is a previous center and time
                if prev_center is not None and prev_time is not None:
                    displacement = ((center_x - prev_center[0]) ** 2 + (center_y - prev_center[1]) ** 2) ** 0.5
                    speed = displacement / (current_time - prev_time) * pixel_to_cm
                    speeds.append(speed)

                # Update the previous center and time
                prev_center = (center_x, center_y)
                prev_time = current_time

    # Display the frame
    cv2.imshow("cv2.aruco Marker Speed Measurement", frame)

    # Check if the time interval has elapsed
    current_time2 = time.time()
    elapsed_time = current_time2 - start_time
    if elapsed_time >= time_interval:
        # Collect the speeds and reset the timer
        if len(speeds) > 0:
            average_speed = sum(speeds) / len(speeds)
            now = datetime.now()
            timestamp = now.strftime("%H:%M:%S.%f")[:-3]
            csv_writer.writerow([timestamp, average_speed])
            print(f"Average Speed: {average_speed} cm/s")
        speeds = []
        start_time = time.time()
# Exit if 'q' is pressed
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break
   
# Release the video capture and close the window
cap.release()
cv2.destroyAllWindows()
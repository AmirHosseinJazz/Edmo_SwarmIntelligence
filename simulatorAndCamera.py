import time
import pyautogui
import tqdm
import pandas as pd
import cv2
from cv2 import aruco
import time
import csv
from datetime import datetime

# last

def move_to_position(last,start,end,value,rangeOf,negative=False):
    pyautogui.moveTo(x=last[0], y=last[1])
    new_position=(((end[0]-start[0])/rangeOf)*(value)+start[0],end[1])
    if negative:
        new_position=(((end[0]-start[0])/rangeOf)*(value+90)+start[0],end[1])
    pyautogui.dragTo(x=new_position[0], y=new_position[1])
    return new_position[0]


if __name__=="__main__":

    # Set the dimensions of the table
    table_width = 110  # Replace with your table width in centimeters

    # Set the time interval for measuring speed (in seconds)
    time_interval = 9  # Replace with your desired time interval

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

    wait_time=20
    samples=pd.read_csv('samples.csv',header=None)
    ##
    lastposition_Snelheid = (140,430)
    Snelheid_start_position = (140, 430)
    Snelheid_end_position = (1610, 430)
    Snelheid_range=10
    ###
    lastposition_module0_omvang = (350,620)
    Module0_Omvang_start_position = (350,620)
    Module0_Omvang_end_position =(550,620)
    Module0_Omvang_range=90
    ###
    lastposition_module0_Positie = (350,771)
    Module0_Positie_start_position = (350,771)
    Module0_Positie_end_position =(550,771)
    Module0_Positie_range=180
    ### 
    lastposition_module1_omvang = (1195,650)
    Module1_Omvang_start_position =(1195,650)
    Module1_Omvang_end_position =(1390,650)
    Module1_Omvang_range=90
    ###
    lastposition_module1_Positie =(1197,772)
    Module1_Positie_start_position =(1197,772)
    Module1_Positie_end_position =(1390,772)
    Module1_Positie_range=180
    ###
    lastposition_relatie=(760,910)
    Relatie_start_position=(760,910)
    Relatie_end_position=(950,910)
    Relatie_range=180
    DF=pd.DataFrame(columns=['Timestamp','Snelheid','Omvang1','Positie1','Omvang2','Positie2','Relatie'])
    time.sleep(8)

    
while True:
    # Read the frame from the video capture
    ret, frame = cap.read()

    # Convert the frame to grayscale for cv2.aruco marker detection
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

    # Detect cv2.aruco markers in the frame
    corners, ids, _ = cv2.aruco.detectMarkers(gray, dictionary, parameters=parameters)

    
    for index,row in samples.iloc[:5].iterrows():
        print(index)
        time.sleep(wait_time)
        # Snelheid
        l=move_to_position(lastposition_Snelheid,Snelheid_start_position,Snelheid_end_position,row[0],Snelheid_range)
        lastposition_Snelheid = (l,430)
        #Module0_Omvang
        l=move_to_position(lastposition_module0_omvang,Module0_Omvang_start_position,Module0_Omvang_end_position,row[1],Module0_Omvang_range)
        lastposition_module0_omvang = (l,630)
        #Module0_Positie
        l=move_to_position(lastposition_module0_Positie,Module0_Positie_start_position,Module0_Positie_end_position,row[2],Module0_Positie_range,negative=True)
        lastposition_module0_Positie = (l,770)
        #Module1_Omvang
        l=move_to_position(lastposition_module1_omvang,Module1_Omvang_start_position,Module1_Omvang_end_position,row[3],Module1_Omvang_range)
        lastposition_module1_omvang = (l,630)
        #Module1_Positie
        l=move_to_position(lastposition_module1_Positie,Module1_Positie_start_position,Module1_Positie_end_position,row[4],Module1_Positie_range,negative=True)
        lastposition_module1_Positie = (l,770)
        #Relatie
        l=move_to_position(lastposition_relatie,Relatie_start_position,Relatie_end_position,row[5],Relatie_range,negative=True)
        lastposition_relatie = (l,910)
        DF=pd.concat([DF, pd.DataFrame([{'Timestamp':datetime.now().time(),'Snelheid':row[0],'Omvang1':row[1],'Positie1':row[2],
                      'Omvang2':row[3],'Positie2':row[4],'Relatie':row[5]}])], ignore_index=True)
        # print(row)
        # print(datetime.datetime.now().time())
    # print(DF.head())
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
                time.sleep(time_interval-2)
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
    
    DF.to_csv('NewParameterSamples.csv',index=False)
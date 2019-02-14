# Talk about the different lighting used

import cv2
import numpy as np
import argparse
import imutils
import time
import mysql.connector
import pymysql
import paramiko
import pandas as pd
import os
from paramiko import SSHClient
from sshtunnel import SSHTunnelForwarder
from os.path import expanduser
from dotenv import load_dotenv

load_dotenv()

home = expanduser('~')
mypkey = paramiko.RSAKey.from_private_key_file(home + '/.ssh/id_rsa', password=os.getenv('priv_key_password'))

# Add these to env file
sql_hostname = os.getenv('sql_hostname')
sql_username = os.getenv('sql_username')
sql_password = os.getenv('sql_password')
sql_main_database = os.getenv('sql_main_database')
sql_port = 3306
ssh_host = os.getenv('ssh_host')
ssh_user = os.getenv('ssh_user')
ssh_port = 22

  # query = '''SELECT * FROM tempTable;'''
  # data = pd.read_sql_query(query, conn)
  # print(data)

# Create a VideoCapture object and read from input file
# If the input is the camera, pass 0 instead of the video file name

# cap = cv2.VideoCapture("udp://127.0.0.1:10000")
cap = cv2.VideoCapture('game2.mov')
# cap = cv2.VideoCapture(0)
# cap = cv2.VideoCapture('/Users/dan/Downloads/snooker-game2.mp4')

# Check if camera opened successfully
if (cap.isOpened() == False):
  print("Error opening video stream or file")

tableLower = (47, 100, 100)
tableUpper = (67, 255, 255)
lower = {
#   'red':    (166,84,141),  # Video game colours
#   'red':    (0,176,154), # HSV
  'red':    (0,171,84), # YCrCb
#   'yellow': (23,59,119), # Video game colours
#   'yellow': (11,139,215), # HSV
#   'yellow': (170,145,20), # YCrCb
# # #   'green':  (66,122,129), # Video game colours
# #   'green':  (57,70,89), # HSV 
#   'green':  (91,104,101), # YCrCb
# # #   'brown':  (0,29,0), # Video game colours
# #   'brown':  (0,41,49), # HSV
#   'brown':  (50,132,103), # YCrCb
# # #   'blue':   (97,100,117), # Video game colours
# #   'blue':   (87,122,111), # HSV
#   'blue':   (60,78,147), # YCrCb
# # #   'pink':   (141,40,200), # Video game colours
# #   'pink':   (169,76,149), # HSV
#   'pink':   (96,242,150), # YCrCb
# # #   'black':  (53,26,0), # Video game colours
# #   'black':  (103,56,16), # HSV
#   'black':  (103,56,16), # YCrCb
}

upper = {
#   'red':    (179,255,255), # Video game colours
#   'red':    (35,237,208), # HSV
  'red':    (110,255,255), # YCrCb
#   'yellow': (50,255,255), # Video game colours
#   'yellow': (169,227,255), # HSV
#   'yellow': (254,220,73), # YCrCb
# # #   'green':  (86,255,255), # Video game colours
# #   'green':  (82,96,138), # HSV
#   'green':  (138,115,132), # YCrCb
# # #   'brown':  (48,174,143), # Video game colours
# #   'brown':  (13,204,145), # HSV
#   'brown':  (103,166,122), # YCrCb
# # #   'blue':   (117,255,255), # Video game colours
# #   'blue':   (162,255,255), # HSV
#   'blue':   (126,112,196), # YCrCb
# # #   'pink':   (169,192,255), # Video game colours
# #   'pink':   (176,199,255), # HSV
#   'pink':   (185,242,150), # YCrCb
# # #   'black':  (120,120,75), # Video game colours
# #   'black':  (133,156,88), # HSV
#   'black':  (133,156,88), # YCrCb
}

redCoords = {}

redCoords['red1X'] = 12
redCoords['red1Y'] = 5


colours = {
    'red': (0,0,255),
    'yellow': (0,255,255),
    'green': (0,255,0),
    'brown': (42,255,165),
    'blue': (255,0,0),
    'pink': (180,105,255),
    'black': (0,0,0),
}
balls = [
  ([166,84,141], [186,255,255]), # Red
  # ([175,0,0], [180,255,255]), # Red
  ([23,59,119],   [50,255,255]), # Yellow
  ([66,122,129], [86,255,255]), # Green
  ([0,29,0], [    48,174,143]), # Brown
  ([97,100,117], [117,255,255]), # Blue
  ([141,40,200],  [169,192,255]), # Pink
  ([53,26,0],    [120,120,75]), # Black
  ([22,31,242], [33,76,255]), # White (not working)
  # ([150,84,141], [186,255,255]), # Pink
  # ([22, 0, 0], [60, 255, 255]), # White
  # ([25, 0, 0], [50, 255, 255])
]


finalEdges = 0
finalMask = 0

totalReds = 10
redCount = 0
yellowCount = 0
pinkCount = 0
# initialFrame = 460
initialFrame = 300
# Explain why I check every frames and not any other number
# Run some tests against other numbers
frameCheck = 5
currentBallCount = 0
startBallPottedCheckTimer = False
startTime = 0
elapsedTimeSincePot = 0
numberOfRedsPotted = 0
ballPottedConfidence = 0
previousRedCount = 0
predictedRedCount = 10

cap.set(cv2.CAP_PROP_POS_FRAMES, initialFrame)



# Read until video is completed
while True:
    # Captures the live stream frame-by-frame
    _, frame = cap.read()

    # Width: 600 - Height: 337
    frame = imutils.resize(frame, width=600)
    # Crop video to only check the table and not stuff on surrounding the table
    frame = frame[25:245, 65:535] # Y, X

    # Added some black circles over the pockets so balls are not detected while in the pocket
    cv2.circle(frame, (21,20), 5, (0,0,0), 19) # Top left
    cv2.circle(frame, (237,17), 4, (0,0,0), 19) # Top Middle
    cv2.circle(frame, (450,15), 5, (0,0,0), 19) # Top Right
    cv2.circle(frame, (452,202), 5, (0,0,0), 19) # Bottom Right
    cv2.circle(frame, (239,207), 4, (0,0,0), 19) # Bottom Middle
    cv2.circle(frame, (25,205), 5, (0,0,0), 19) # Bottom left



    finalMask = 0
    finalMaskTable = 0
    finalEdges = 0


    blur = cv2.GaussianBlur(frame, (9,9), 0)
    hsv = cv2.cvtColor(blur, cv2.COLOR_BGR2YCrCb)
    # cv2.imshow('res', hsv)

    currentFrame = cap.get(cv2.CAP_PROP_POS_FRAMES)
    # print(currentFrame)
    checkBallCount = False

    # Every 5 frames, give the system the ability to check the current ball count on the table
    # The first frame to be processed is always 1 + the initial frame and as a result, there will be no inital check of the current red balls
    # And redCount will be set to 0 as a result which also means the if statement to check whether to update the database will also be true (which add a lot of points to the datbase)
    # So check if current frame is 1 + initalFrame will seed the inital redCount and not update the database prematurely
    previousRedCount = redCount
    if((currentFrame == initialFrame + 1) or currentFrame % frameCheck == 0):
        redCount = 0
        yellowCount = 0
        pinkCount = 0
        checkBallCount = True
    else:
        checkBallCount = False
        # previousRedCount = redCount
    
    for key, value in upper.items():
        kernal = np.ones((8,8), np.uint8)
        mask = cv2.inRange(hsv, lower[key], upper[key])
        # mask = cv2.erode(mask, kernal, iterations=1)
        # cv2.imshow('test', mask)
        # mask = cv2.dilate(mask, kernal, iterations=1)
        mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernal)
        # cv2.imshow('mask', mask)

        # Add the blur and the threshold function to get make the results more circular 
        # They are currently not in as they're not needed at this stage and just slow things down
        # mask = cv2.GaussianBlur(mask, (7,7), 0)
        # kernal = np.ones((6,6), np.uint8)
        # mask = cv2.erode(mask, kernal, iterations=1)
        finalMask = mask
        # thresh = cv2.threshold(finalMask, 127, 255, 0)[-1]
        # contours = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)[-2]
        contours = cv2.findContours(finalMask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)[-2]
        # print(key + ': ' + str(len(contours)))
        i = 0
        connectedContours = False
        for c in contours:
            # if(i == len(contours) - 1):
                # previousRedCount = redCount + 1
            # else:

            numberOfBallsConnected = 0
            # The following code is only needed to show what has been detected
            # Can be removed in final version to improve fps
            M = cv2.moments(c)
            if M["m00"] != 0:
                cX = int(M["m10"] / M["m00"])
                cY = int(M["m01"] / M["m00"])
            else:
                cX, cY = 0, 0

            # average perimeter = 38.6685714 (hardcoded for this window width, ball size etc, )
            # print(cv2.arcLength(c, True))
            currentContourSize = cv2.arcLength(c, True)
            # The largest contour size is around 40 so just add a bit more 
            if(currentContourSize > 42):
                cv2.circle(frame, (cX, cY), 5, (255,0,0), -1)
                cv2.putText(frame, str(i), (cX, cY), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0,255,), 2)

                connectedContours = True
                numberOfBallsConnected = currentContourSize / 38.6685714
                # Subtract one as if we don't, we end up counting the one big connected contor plus the actual number of balls
                numberOfBallsConnected = int(round(numberOfBallsConnected)) - 1
            else:
                cv2.circle(frame, (cX, cY), 5, (255,255,255), -1)
                cv2.putText(frame, str(i), (cX, cY), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0,255,0), 2)

                connectedContours = Falsev2.putText(frame, str(key), (cX -25, cY - 25), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255,255,255), 2)

            i += 1
            if(checkBallCount):
                # When counting the number of balls make sure to reset the ball count at the beginning of the while loop
                if(key == 'red'):
                    # Need check if connected contours 
                    if(connectedContours):
                        # print(numberOfBallsConnected)
                        redCount += numberOfBallsConnected
                    redCount += 1
            

        if(checkBallCount):
            # Every 5 frames check if the number of reds detected has changed
            if(redCount != previousRedCount):
                # If it has (and it's not the first frame otherwise the confidence value will be incorrect) increment the confidence
                if(currentFrame != initialFrame + 1):
                    # The higer the number means less confidence in the pot as redCount has changed value a lot 
                    # The constant changing of value means something has temporarly obstructed view of the ball
                    ballPottedConfidence += 1

            # False pot detected (i.e hand cover etc)
            # Predicted red count = 10
            # If the red count ever becomes greater than the number of red the system has found
            # That means a ball has been obscured for a long enough time for it to be detected as potted
            # But obviously wasn't potted and must have just been covered by a player take a shot

            # RENAME predictedRedCount
            if(redCount > predictedRedCount):
                print("false pot detected on " + str(numberOfRedsPotted) + " balls")
                totalReds += numberOfRedsPotted
                # With a false pot been detected, we need to update the database and remove points that were added with that false pot
                with SSHTunnelForwarder( (ssh_host, ssh_port), ssh_username=ssh_user, ssh_pkey=mypkey, remote_bind_address=(sql_hostname, sql_port)) as tunnel:
                    conn = pymysql.connect(host='127.0.0.1', user=sql_username, passwd=sql_password, db=sql_main_database, port=tunnel.local_bind_port)

                    with conn.cursor() as cursor:
                        # Simple query for that just decrements the points count
                        query = '''UPDATE players SET points = points - %s WHERE name = "dan";'''
                        cursor.execute(query, (numberOfRedsPotted))
                    
                    conn.commit()
                    conn.close()
                    
                numberOfRedsPotted = 0
                predictedRedCount = redCount

        # Every 50 frames check if a ball has been potted (checking every 50 frames give some time to get a confidence values)
        if(currentFrame % 50 == 0):
            # redCount < totalReds means a ball has lost detect and so has been potted
            # if the confidence values is less than 2 it means there was little flucation in the redCount so we can be confident a ball may have been potted
            if(redCount < totalReds and ballPottedConfidence <= 2):
                print("red potted")

                numberOfRedsPotted = totalReds - redCount
                totalReds = (totalReds) - (totalReds - redCount)
                predictedRedCount = totalReds
                ballPottedConfidence = 0
                # Connect to database using ssh keys 
                with SSHTunnelForwarder( (ssh_host, ssh_port), ssh_username=ssh_user, ssh_pkey=mypkey, remote_bind_address=(sql_hostname, sql_port)) as tunnel:
                    conn = pymysql.connect(host='127.0.0.1', user=sql_username, passwd=sql_password, db=sql_main_database, port=tunnel.local_bind_port)

                    with conn.cursor() as cursor:
                        # Simple query for that just increments the points count
                        query = '''UPDATE players SET points = points + %s WHERE name = "dan";'''
                        cursor.execute(query, (numberOfRedsPotted))
                    
                    conn.commit()
                    conn.close()
            ballPottedConfidence = 0

    # May not be needed
    # res = cv2.bitwise_and(frame,frame, mask = finalMask)

    # Display test for number of red balls
    cv2.putText(frame, "Total Reds: " + str(totalReds), (250, 20), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0,0,255), 2)
    cv2.putText(frame, "Red Detected: " + str(redCount) + " - " + str(previousRedCount), (10, 20), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0,0,255), 2)


    cv2.imshow('res', frame)
    # cv2.imshow('mask', finalMask)

    if cv2.waitKey(25) & 0xFF == ord('q'):
        break

cv2.destroyAllWindows()

cap.release()


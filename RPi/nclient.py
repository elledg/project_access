import gpxpy
import gpxpy.gpx
import datetime

import io
import os
import subprocess
import math
import time

import asyncio
import websockets
import json

import pysftp
import env

import threading

from multiprocessing import process
import random
import threading
import multiprocessing
import logging
from threading import Thread
from queue import Queue
import time
logging.basicConfig(format='%(levelname)s - %(asctime)s.%(msecs)03d: %(message)s', datefmt='%H:%M:%S', level=logging.DEBUG)

cnopts = pysftp.CnOpts()
cnopts.hostkeys = None

test = True

async def send_notification(trafficID):
    msg = {"trafficID" : trafficID,
            "status" : "sent"}
    msg = json.dumps(msg)
    async with websockets.connect('ws://' + env.SFTP_IP + ':' + env.SFTP_PORT + '/') as websocket:
        await websocket.send(msg)
        response = await websocket.recv()
        print(response)
        # print("SFTP Notification sent")

def send_videos():
    try:
        files = os.listdir()
    except:
        return -1
    files.sort()
    
    for file in files:
        file_split = file.split(".")
        if (len(file_split) < 2):
            continue
        trafficID = file_split[0]
        extension = file_split[1]
        
        if extension == "mp4":
            with pysftp.Connection(host=env.IP, username=env.USER, password=env.PASS, cnopts=cnopts) as sftp:
                try:
                    print("STFP Connection successfully established ... ")
                    print("Sending " + file + " to server")
                    sftp.put(env.LOCAL + file, env.REMOTE + file)
                    print("File sent to SFTP server")
                except Exception as e:
                    print("Error encountered while uploading to SFTP server")
                    print(e)
        

def send_to_sftp(trafficID, ext):
    try: 
        with pysftp.Connection(host=env.IP, username=env.USER, password=env.PASS, cnopts=cnopts) as sftp:
            try:
                print("STFP Connection successfully established ... ")
                sftp.put(env.LOCAL + trafficID + ext, env.REMOTE + trafficID + ext)
                print("File sent to SFTP server")
                asyncio.run(send_notification(trafficID))
            except Exception as e:
                print("Error encountered while uploading to SFTP server")
                print(e)
    except Exception as e:
        print("Cannot connect to SFTP server")
        print(e)

async def server_request():
    # async with websockets.connect("ws://AWS") as websocket: replace with AWS
    async with websockets.connect("ws://" + env.IP + ":" + env.PORT + "/") as websocket:    
        while True:
            data = await websocket.recv()
            print(data)
            if(len(data) > 0):
                return data
            await asyncio.sleep(5)

def is_within_geofence(lat, lon, lat1, lon1, lat2, lon2):
    if (lon1 >= lon and lon2 <= lon) or (lon1 <= lon and lon2 >= lon):
        if (lat1 >= lat and lat2 <= lat) or (lat1 <= lat and lat2 >= lat):
            return True
    return False

def check_gps_time(file_name, start, end, lat1, lon1, lat2, lon2):
    try:
        gpx_file = open(file_name, 'r')
    except:
        return -1

    gpx = gpxpy.parse(gpx_file)
    start_time = datetime.datetime.fromisoformat(start)
    end_time = datetime.datetime.fromisoformat(end)
    #end_time = start_time + datetime.timedelta(minutes=15)
        
    for track in gpx.tracks:
        for segment in track.segments:
            for point in segment.points:
                current_time = point.time.replace(tzinfo=None)
                if start_time <= current_time and end_time >= current_time:
                    gps_found = is_within_geofence(point.latitude, point.longitude, lat1, lon1, lat2, lon2)
                    print("Timestamp:", current_time)
                    print("Enclosed:", gps_found)
                    if gps_found:
                        return current_time
    return 0

def retrieve(start, end):
    date = start.date()
    time_start = start.time()
    time_end = end.time()

    try:
        files = os.listdir("videos")
    except:
        return -1
    files.sort()
    filelist = []
    
    for file in files:
        file_split = file.split(".")
        if (len(file_split) < 2):
            continue
        raw_time = file_split[0]
        extension = file_split[1]

        file_time = raw_time.replace(";", ":")
        time_split = file_time.split("-")
        
        floor = datetime.time.fromisoformat(time_split[0])
        ceiling = datetime.time.fromisoformat(time_split[1])
        
        if(floor <= time_start and time_start < ceiling):
            new_file = compute_splice(start, end, file)
            print("File:", new_file)
            filelist.append(new_file)
        elif(floor < time_end and time_end <= ceiling):
            new_file = compute_splice(start, end, file)
            print("File:", new_file)
            filelist.append(new_file)
        elif(floor > time_start and ceiling < time_end):
            print("File:", file)
            filelist.append(file)
        elif(floor > time_end):
            break
    return filelist

def splice(start, duration, filename):
    name = os.path.splitext(filename)[0]
    newname =  "spliced/" + name + os.path.splitext(filename)[1]
    if not os.path.exists('videos/spliced'):
        os.makedirs('videos/spliced')
    if os.name == "nt":
        command =  "ffmpeg -ss " + str(start) + " -i videos/" + filename + " -c copy -t " + str(duration) +" videos/" + newname + " -y"
    elif os.name == "posix":
        command =  "ffmpeg -ss " + str(start) + " -i 'videos/" + filename + "' -c copy -t " + str(duration) +" 'videos/" + newname + "' -y"
    print(command)
    subprocess.call(command,shell=True)
    return (newname)
    
def compute_splice(start, end, filename):
    name = os.path.splitext(filename)[0]
    file = name.replace(";", ":").split("-")
    time_start = start.strftime("%H:%M:%S")
    time_end = end.strftime("%H:%M:%S")
    FMT = '%H:%M:%S'
    if (file[0] < time_start and time_start < file[1]):
        tdelta = datetime.datetime.strptime(file[1], FMT) - datetime.datetime.strptime(time_start, FMT)
        tstart = datetime.datetime.strptime(time_start, FMT) - datetime.datetime.strptime(file[0], FMT)
        return (splice(tstart, tdelta, filename))
    if (file[0] < time_end and time_end < file[1]):
        tdelta = datetime.datetime.strptime(time_end, FMT) - datetime.datetime.strptime(file[0], FMT)
        tstart = datetime.datetime.strptime(file[1], FMT) - datetime.datetime.strptime(time_end, FMT)
        return (splice(tstart, tdelta, filename))

def merge(filelist, trafficID):
    list = open('list.txt', "w+")
    for file in filelist:
        list.write("file 'videos/" + file + "'\n")
    list.close()
    command = 'ffmpeg -f concat -safe 0 -i list.txt -c copy ' + trafficID + '.mp4 -y'
    subprocess.call(command,shell=True)


def collect_video(gpx, start, end, lat1, lon1, lat2, lon2, trafficID):
    gps_time = check_gps_time(gpx, start, end, lat1, lon1, lat2, lon2)
    if not test: input()
    if (gps_time == 0):
        print("No video found")
        return 0
    elif (gps_time == -1):
        print("GPX file not found")
        return 0
    elif (gps_time != 0):
        end = datetime.datetime.fromisoformat(end)
        filelist = retrieve(gps_time, end)
        if (filelist == -1):
            print("Video folder not found")
            return
        merge(filelist, trafficID)

def processor(json_target):
    target = json.loads(json_target)
    log.write(str(datetime.datetime.now()) + " - " + str(target) + "'\n")
    trafficID = target["trafficID"] 
    start = target["start"]
    stop = target["stop"]
    gps = target["gps"].split(",")

    log.write("Collecting video - " + str(datetime.datetime.now()) +"'\n")
    video = collect_video('test.gpx', start, stop, float(gps[0]), float(gps[1]), float(gps[2]), float(gps[3]), trafficID)
    if (video != 0):
        print("Video created. Sending to server")
        log.write("Sending to server - " + str(datetime.datetime.now()) +"'\n")
        send_to_sftp(trafficID, '.mp4')
        log.write("Sent to server - " + str(datetime.datetime.now()) +"'\n")

def display(msg):
    threadname = threading.current_thread().name
    processname = multiprocessing.current_process().name
    logging.info(f'{processname}\{threadname}: {msg}')

# Producer
def create_work(queue, finished, max):
    finished.put(False)
    for x in range(max):

        v = random.randint(1,100)
        queue.put(v)
        display(f'Producing {x}: {v}')
    finished.put(True)
    display('finished')

# Consumer
def perform_work(work, finished):
    counter = 0
    while True:
        if not work.empty():
            v = work.get() # assume work.get() returns the file location of the video or filename 
            # upload via sftp
            display(f'Consuming {counter}: {v}') # print the file location or filename sa consuming
            counter += 1
        else:
            q = finished.get()
            if q == True:
                break
        display('finished')

if __name__ == "__main__":
    while True:
        print("Project Access")
        
        try:
            data_json = asyncio.run(server_request())
            data = json.loads(data_json)
            incidents = data["data"] 

            log = open('log.txt', "a")
            
            max = int(input("Input maximum amount of worker threads:"))

            work = Queue()
            [work.put(i) for i in incidents]  
            ready = Queue()
            finished = Queue()

            producer = Thread(target=create_work, args=[ready,finished,max], daemon=True)
            consumer = Thread(target=perform_work, args=[ready,finished], daemon=True)
            
            producer.start()
            consumer.start()

            producer.join()
            display('Producer has finished')
            consumer.join()
            display('Consumer has finished')

            display("Finished")

            log.close()
            
            if test: exit()

        except KeyboardInterrupt as error:
            print ("Exiting Program")
            exit()
           
        except ValueError as error:
            print("Invalid JSON")
            exit()
            
        except (asyncio.TimeoutError, ConnectionRefusedError) as error:
            print("Cannot find server. Reconnecting to server.")
            time.sleep(10)


import gpxpy
import gpxpy.gpx
import datetime

import io
import os
import shutil
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
logging.basicConfig(format='%(levelname)s - %(asctime)s.%(msecs)03d: %(message)s', datefmt='%H:%M:%S', level=logging.INFO)

cnopts = pysftp.CnOpts()
cnopts.hostkeys = None

test = True

threads = set()

def display(msg):
    threadname = threading.current_thread().name
    processname = multiprocessing.current_process().name
    logging.info(f'{processname}\{threadname}: {msg}')

def compute_log():
    data_log = open('files/log_timestamp.csv', "a")
    start = log_data['Main'][0]
    data_log.write(str(start.date()) +","+ str(start.time()) + "\n")
    data_log.write(str(p_thread) + " Producer threads, " + str(c_thread) + " Consumer threads, Mode: " + str(mode) + '\n')
    data_log.write("Total, Time Start, Time End\n")
    for trafficID in log_data:
        logs = log_data[trafficID]
        data_log.write(trafficID)
        for i in range(len(logs)):
            delta = logs[i] - start
            data_log.write(", " + str(delta))
        if trafficID == 'Main':
            data_log.write("\nTrafficID, Checked GPS, Recieved by Minion, Retrieved Necessary Videos, Merged Videos, Sending Video, Sent Video")
        data_log.write('\n')


    data_log.close()

def flush():
    for thread in threads:
        if os.path.exists('files/list-' + thread + '.txt'):
            os.remove('files/list-' + thread + '.txt')
        if os.path.exists('files/videos/spliced/' + thread):
            shutil.rmtree('files/videos/spliced/' + thread)

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

#try http @ELLE
def send_to_sftp(filename, ext=False):
    now = datetime.datetime.now()
    log.write(str(now.date()) +","+ str(now.time()) +","+ filename +",Sending video,"+ threading.current_thread().name +"\n")
    trafficID = filename.split(".")[0]
    log_data[trafficID].append(now)
    try: 
        with pysftp.Connection(host=env.IP, username=env.USER, password=env.PASS, cnopts=cnopts) as sftp:
            try:
                print("STFP Connection successfully established ... ")
                if ext:
                    sftp.put(env.LOCAL + "files/output/" + filename + ext, env.REMOTE + filename + ext)
                else:
                    sftp.put(env.LOCAL + "files/output/" + filename, env.REMOTE + filename)
                display("File sent to SFTP server")
                now = datetime.datetime.now()
                log.write(str(now.date()) +","+ str(now.time()) +","+ filename +",Sent video,"+ threading.current_thread().name +"\n")
                log_data[trafficID].append(now)
                asyncio.run(send_notification(filename))
            except Exception as e:
                log.write(",,"+ filename +",Error uploading,"+ threading.current_thread().name +"\n")
                print("Error encountered while uploading to SFTP server")
                print(e)
    except Exception as e:
        log.write(",,"+ filename +",Error SFTP,"+ threading.current_thread().name +"\n")
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
        gpx_file = open('files/'+file_name, 'r')
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
                    # print("Timestamp:", current_time)
                    # print("Enclosed:", gps_found)
                    if gps_found:
                        return current_time
    return 0

def retrieve(start, end):
    date = start.date()
    time_start = start.time()
    time_end = end.time()

    try:
        files = os.listdir("files/videos")
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
            filelist.append(new_file)
        elif(floor < time_end and time_end <= ceiling):
            new_file = compute_splice(start, end, file)
            filelist.append(new_file)
        elif(floor > time_start and ceiling < time_end):
            filelist.append(file)
        elif(floor > time_end):
            break
    return filelist

def merge(filelist, trafficID):
    if not os.path.exists('files/output'):
        os.makedirs('files/output')
    thread = threading.current_thread().name
    list = open('files/list-'+thread+'.txt', "w+")
    for file in filelist:
        list.write("file 'videos/" + file + "'\n")
    list.close()
    command = 'ffmpeg -hide_banner -loglevel error -f concat -safe 0 -i files/list-'+thread+'.txt -c copy files/output/' + trafficID + '.mp4 -y'
    subprocess.call(command,shell=True)

def splice(start, end, filename):
    name = os.path.splitext(filename)[0]
    thread = threading.current_thread().name
    newname =  "spliced/" + thread + "/" + name + os.path.splitext(filename)[1]
    if not os.path.exists('files/videos/spliced/'+thread):
        os.makedirs('files/videos/spliced/'+thread)
    if os.name == "nt":
        command =  "ffmpeg -hide_banner -loglevel error -ss " + str(start) + " -to " + str(end) +" -i files/videos/" + filename + " -c copy files/videos/" + newname + " -y"
    elif os.name == "posix":
        command =  "ffmpeg -hide_banner -loglevel error -ss " + str(start) + " -to " + str(end) +" -i 'files/videos/" + filename + "' -c copy 'files/videos/" + newname + "' -y"
    # print(command)
    subprocess.call(command,shell=True)
    return (newname)
    
def compute_splice(start, end, filename):
    name = os.path.splitext(filename)[0]
    file = name.replace(";", ":").split("-")
    time_start = start.strftime("%H:%M:%S")
    time_end = end.strftime("%H:%M:%S")
    timestamp_start = 0
    result = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "default=noprint_wrappers=1:nokey=1", 
        "files/videos/"+filename], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    duration = float(result.stdout)
    delta = datetime.timedelta(seconds=duration)
    timestamp_end = duration
    
    FMT = '%H:%M:%S'
    if (file[0] < time_start and time_start < file[1]):
        timestamp_start = datetime.datetime.strptime(time_start, FMT) - datetime.datetime.strptime(file[0], FMT)
        return (splice(timestamp_start, timestamp_end, filename))
    if (file[0] < time_end and time_end < file[1]):
        timestamp_end = datetime.datetime.strptime(time_end, FMT) - datetime.datetime.strptime(file[1], FMT) + delta
        return (splice(timestamp_start, timestamp_end, filename))

def collect_video(gpx, start, end, lat1, lon1, lat2, lon2, trafficID):
    gps_time = check_gps_time(gpx, start, end, lat1, lon1, lat2, lon2)

    now = datetime.datetime.now()
    log_data[trafficID].append(now)
    
    if (gps_time == 0):
        print("No video found")
        return 0
    elif (gps_time == -1):
        print("GPX file not found")
        return 0
    elif (gps_time != 0):
        end = datetime.datetime.fromisoformat(end)
        filelist = retrieve(gps_time, end)
        
        now = datetime.datetime.now()
        log_data[trafficID].append(now)
        
        if (filelist == -1):
            print("Video folder not found")
            return
        merge(filelist, trafficID)

def processor(target):
    trafficID = target["trafficID"] 
    start = target["start"]
    stop = target["stop"]
    gps = target["gps"].split(",")

    now = datetime.datetime.now()
    log.write(str(now.date()) +","+ str(now.time()) +","+ trafficID +",Minion Recieved/Collecting Video,"+ threading.current_thread().name +"\n")
    log_data[trafficID].append(now)

    collect_video('test.gpx', start, stop, float(gps[0]), float(gps[1]), float(gps[2]), float(gps[3]), trafficID)

    now = datetime.datetime.now()
    log.write(str(now.date()) +","+ str(now.time()) +","+ trafficID +",Collected Video,"+ threading.current_thread().name +"\n")
    log_data[trafficID].append(now)

    global threads
    threads.add(threading.current_thread().name)

# Producer
def create_work(work, ready, finished):
    while True:
        if not work.empty():
            x = work.get()
            v = x["trafficID"]+".mp4"

            display(f'Producing: {v}')
            processor(x)
            ready.put(v)
            display(f'Produced: {v}')
        else:
            finished.put(True)
            break

# Producer v2
def create_work_with_vp(work): 
    children = []
    while True:
        if not work.empty():
            x = work.get()
            v = x["trafficID"]+".mp4"

            display(f'Producing: {v}')
            processor(x)

            display(f'Sending: {v}')
            sender = Thread(target=send_to_sftp, args=[v], daemon=True) 
            sender.start()
            children.append(sender)

            display(f'Done: {v}')
        else:
            break
    for c in children:
        c.join()

# Consumer
def perform_work(work, finished):
    while True:
        if work.empty() and (finished.qsize() == p_thread):
            break
        v = work.get()
        display(f'Consuming: {v}')
        send_to_sftp(v)
        display(f'Consumed: {v}')

if __name__ == "__main__":
    while True:
        print("Project Access")
        runs = int(input("Input number of runs to execute:")) if test else 1
        p_thread = int(input("Input maximum amount of producer threads: "))
        c_thread = int(input("Input maximum amount of consumer threads: "))
        mode = int(input("Choose mode: Original [0] or Revamped [1]:"))

        try:
            for r in range(runs):    
                data_json = asyncio.run(server_request())
                data = json.loads(data_json)
                incidents = data["data"] 

                if not os.path.exists('files/'):
                    os.makedirs('files/')
                log = open('files/log.csv', "a")
                log.write("Date, Time, TrafficID, Event, Thread\n")
                now = datetime.datetime.now()
                log.write(str(now.date()) +","+ str(now.time()) +",Multiple,Recieved JSON,Main\n")

                log_data = dict()
                log_data["Main"] = [now]
                for i in incidents: log_data[i["trafficID"]] = []

                work = Queue()
                [work.put(i) for i in incidents] 
                finished = Queue()

                # Original mode
                if(mode == 0):
                    ready = Queue()

                    # Set up and start producer processes
                    producers = [Thread(target=create_work, args=[work,ready,finished], daemon=True) for _ in range(p_thread)]
                    for p in producers:
                        p.start()
                    
                    # Set up and start consumer process
                    consumers = [Thread(target=perform_work, args=[ready,finished], daemon=True) for _ in range(c_thread)]
                    for c in consumers:
                        c.start()

                    # Wait for producers to finish
                    for p in producers:
                        p.join()
                        display('Producer has finished')

                    # Wait for consumer to finish
                    for c in consumers:
                        c.join()
                        display('Consumer has finished')
                    
                    log_data["Main"].append(datetime.datetime.now())
                    compute_log()

                # Revamped mode
                elif(mode == 1):
                    producers = [Thread(target=create_work_with_vp, args=[work], daemon=True) for _ in range(p_thread)]
                    for p in producers:
                        p.start()

                    for p in producers:
                        p.join()
                    display('All processes have finished')
                    log_data["Main"].append(datetime.datetime.now())
                    compute_log()

                else:
                    print("Invalid mode")

                flush()

                display("Finished")
                if test: display("Done "+str(r+1)+" run/s")

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


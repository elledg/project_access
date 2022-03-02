#!/usr/bin/env python

import asyncio
import json
import websockets
import sys

from client import *

async def hello(uri, val):
    async with websockets.connect(uri) as websocket:
        await websocket.send("Hello world! " + val)

        while True:
            print("\n---PROJECT ACCESS---\n")
            
            try:
                # target_json = asyncio.run(server_request())
                # target = json.loads(target_json)
                # trafficID = target["trafficID"] 
                # start = target["start"]
                # stop = target["stop"]
                # gps = target["gps"].split(",")

                target = json.loads('{"trafficID":"AKB48", "start":"2021-04-25T10:01:05", "stop":"2021-04-25T10:02:35", "gps":"15,133,12,110"}') 
                trafficID = str(val)
                start = target["start"]
                stop = target["stop"]
                gps = target["gps"].split(",")


                collect_video('test.gpx', start, stop, float(gps[0]), float(gps[1]), float(gps[2]), float(gps[3]), trafficID)

            except KeyboardInterrupt:
                print ("Cannot find server")    

        await websocket.send("Done! " + val)

n = len(sys.argv)
val = sys.argv[1]

asyncio.get_event_loop().run_until_complete(
    hello('ws://localhost:8001', val))
#!/usr/bin/env python
import asyncio
import websockets
from subprocess import Popen

async def handler(websocket):
    while True:
        message = await websocket.recv()

async def main():
    async with websockets.serve(handler, "", 8001):
        await asyncio.Future()  # run forever

if __name__ == "__main__":
    qty = input("Welcome to GRU.\nFour minions will spawn by default. Press ENTER to proceed.")
    qty = 4 
    print(qty)

    for x in range(int(qty)):
        str_id = str(x)
        command = 'python min2.py ' + str_id
        Popen(command)

    asyncio.run(main())
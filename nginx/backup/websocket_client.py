#!/usr/bin/env python3
"""
WebSocket Client for testing E_Platform WebSocket connections
"""

import asyncio
import websockets
import argparse
import sys
import json
import signal

async def connect_and_listen(url, message=None):
    """Connect to WebSocket server and listen for messages"""
    print(f"Connecting to {url}...")
    
    try:
        async with websockets.connect(url) as websocket:
            print(f"Connected to {url}")
            
            # Set up signal handler for graceful exit
            loop = asyncio.get_event_loop()
            loop.add_signal_handler(signal.SIGINT, lambda: loop.stop())
            
            # Send initial message if provided
            if message:
                print(f"Sending message: {message}")
                await websocket.send(message)
            
            # Listen for messages
            while True:
                try:
                    response = await websocket.recv()
                    try:
                        # Try to parse as JSON
                        parsed = json.loads(response)
                        print(f"Received: {json.dumps(parsed, indent=2)}")
                    except json.JSONDecodeError:
                        # Not JSON, print as is
                        print(f"Received: {response}")
                except websockets.exceptions.ConnectionClosed:
                    print("Connection closed")
                    break
    except websockets.exceptions.InvalidStatusCode as e:
        print(f"Error: Invalid status code {e.status_code}")
        print(f"Response headers: {e.headers}")
        print(f"Response body: {e.body}")
    except websockets.exceptions.ConnectionClosed as e:
        print(f"Connection closed: {e}")
    except Exception as e:
        print(f"Error: {e}")

def main():
    """Main function"""
    parser = argparse.ArgumentParser(description='WebSocket Client for E_Platform')
    parser.add_argument('url', help='WebSocket URL (e.g., ws://localhost/ws/notifications/1/)')
    parser.add_argument('--message', '-m', help='Message to send after connecting')
    
    args = parser.parse_args()
    
    try:
        asyncio.run(connect_and_listen(args.url, args.message))
    except KeyboardInterrupt:
        print("\nExiting...")
        sys.exit(0)

if __name__ == "__main__":
    main()

from enum import Enum
from video_processing import State, Event
import time

state = State.STATE_1

wait_time = 5

def run(video=None, frame=None):
    global state
    # Initialize state start time
    state_start_time = time.time()
    # Initialize camera index
    camera_index = 0
    # Initialize last camera switch time
    last_camera_switch_time = time.time()

    while True:
        # Get current event
        event = video.get_event(frames=frame, state=state)
        # Check current state
        if state == State.STATE_1:
            # Check for different events in STATE_1
            if event == Event.EVENT_2:
                # Transition to STATE_2
                state = State.STATE_2
                # Reset state start time
                state_start_time = time.time()
            elif event == Event.EVENT_3:
                # Transition to STATE_3
                state = State.STATE_3
                # Reset state start time
                state_start_time = time.time()
            elif event == Event.EVENT_4:
                # Transition to STATE_4
                state = State.STATE_4
                # Reset state start time
                state_start_time = time.time()
            elif time.time() - last_camera_switch_time >= 5:
                # Switch camera every 5 seconds if nothing happens (only EVENT_1 occurs)
                video.next_camera()
                last_camera_switch_time = time.time()
                # Update camera index
        elif state == State.STATE_2:
            # Check if event 2 has stopped for 10 seconds
            if time.time() - state_start_time >= wait_time:
                # Transition back to STATE_1 after 10 seconds of inactivity
                video.next_camera()
                state = State.STATE_1
                # Reset state start time
                state_start_time = time.time()
            elif event == Event.EVENT_3:
                # Transition to STATE_3
                state = State.STATE_3
                # Reset state start time
                state_start_time = time.time()
            elif event == Event.EVENT_4:
                # Transition to STATE_4
                state = State.STATE_4
                # Reset state start time
                state_start_time = time.time()
        elif state == State.STATE_3:
            # Check if event 3 has stopped for 10 seconds
            if time.time() - state_start_time >= wait_time:
                # Transition back to STATE_1 after 10 seconds of inactivity
                video.next_camera()
                state = State.STATE_1
                # Reset state start time
                state_start_time = time.time()
            elif event == Event.EVENT_4:
                # Transition to STATE_4
                state = State.STATE_4
                # Reset state start time
                state_start_time = time.time()
        elif state == State.STATE_4:
            # Check if event 4 has stopped for 10 seconds
            if time.time() - state_start_time >= wait_time:
                video.next_camera()
                # Transition back to STATE_1 after 10 seconds of inactivity
                state = State.STATE_1
                # Reset state start time
                state_start_time = time.time()

# We treat state 1 and its event 1 as the normal working condition.
# This way, whenever an event has stopped for 10 seconds at their states, we move back to state 1 first

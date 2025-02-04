from __future__ import print_function
import cv2 as cv
import numpy as np
from enum import Enum
import time
import datetime
import imutils

BGVAL = 50
BGLR = 0.01

CLOSEPERCENTAGE = 0.8
AREA_MIN = 20000
MIN_CONFIDENCE = 0.4

last_photo = 0
last_detection = 0

class State(Enum):
    STATE_1 = 1
    STATE_2 = 2
    STATE_3 = 3
    STATE_4 = 4

class Event(Enum):
    EVENT_1 = 1
    EVENT_2 = 2
    EVENT_3 = 3
    EVENT_4 = 4

def get_color_from_state(state: State) -> tuple[int, int, int]:
    match state:
        case State.STATE_1:
            return (0,255,0)
        case State.STATE_2:
            return (255,0,0)
        case State.STATE_3:
            return (0,255,255)
        case State.STATE_4:
            return (0,0,255)

def location_in_fg(fg_mask, location) -> bool:
    """
    Returns true if the given location has a high enough average value in the background mask,
    indicating that the object detected is in the foreground. Uses the constant BGVAL.

    :param fg_mask: backround mask image
    :param location: x,y,w,h integers
    :return bool:
    """
    (x,y,w,h) = location

    val = np.mean(fg_mask[y:y+h, x:x+w])
    return val > BGVAL

def location_close(frame, location):
    """
    Returns true if the given location is close enough to the camera to warrant attention.
    Based on CLOSEPERCENTAGE constant.

    :param frame: image
    :param location: x,y,w,h ints
    :return bool:
    """
    (x,y,w,h) = location
    return y + h > (len(frame) / CLOSEPERCENTAGE)

def size_close(frame, location):
    """
    Returns true if the given location is close enough to the camera to warrant attention.

    :param frame: image
    :param location: x,y,w,h ints
    :return bool:
    """
    (x,y,w,h) = location
    return w*h > AREA_MIN

class VideoProcessor():
    """
    This is the main class of the program, all video processing and interactions with the camera
    happens in this object.
    """

    def __init__(self, num_cams) -> None:
        self.num_cams = num_cams
        self.cam = 0
        self.open_cameras(num_cams)

        self.capture = self.captures[self.cam]
        # keep track of each background individually
        self.backSub = [cv.createBackgroundSubtractorKNN() for x in range(num_cams)]

        #init object detection code
        self.hog = cv.HOGDescriptor()
        self.hog.setSVMDetector(cv.HOGDescriptor_getDefaultPeopleDetector())

    def open_cameras(self, max_cams) -> None:
        # Only keep trying if a maximum of 5 ports were invalid
        non_working_ports = []
        self.captures = []
        x = 0
        while len(self.captures) < max_cams and len(non_working_ports) < 6:
            cam = cv.VideoCapture(x)
            if cam.isOpened():
                cam.set(cv.CAP_PROP_FRAME_WIDTH, 426)
                cam.set(cv.CAP_PROP_FRAME_HEIGHT, 240)
                self.captures.append(cam)
            else:
                non_working_ports.append(x)
            x+=1
        if len(self.captures) < max_cams:
            print(f"Failed to open all cameras, opened: {len(self.captures)}")

    def next_camera(self):
        if self.num_cams > 1:
            self.cam = (self.cam + 1) % self.num_cams
            self.capture = self.captures[self.cam]

    def take_photo(self):
        # Write the first frame to disk
        ret, frame = self.capture.read()
        frame = imutils.resize(frame, width=400)
        timestamp = datetime.datetime.now()
        # Put the timestamp in the photo and filename
        cv.putText(frame, timestamp.strftime(
                "%A %d %B %Y %I:%M:%S%p"), (10, frame.shape[0] - 10),
                cv.FONT_HERSHEY_SIMPLEX, 0.35, (0, 0, 255), 1)
        # Also include the current state in the file name
        cv.imwrite(f"images/user/cam_{self.cam}_t_{timestamp.strftime('%d_%I_%M_%S%p')}.png", frame)


    def get_event(self, max_time=5, frames=None, state=State.STATE_1):
        """
        Return the state machine edge based on detected objects.
        """

        self.detections = 0
        fails = 0

        if not self.capture.isOpened():
            print('Unable to open')
            self.next_camera()
            return Event.EVENT_1
        
        start_time = time.time()

        # Write the first frame to disk
        ret = self.capture.grab()
        if ret:
            ret, frame = self.capture.retrieve()
            timestamp = datetime.datetime.now()
            # Put the timestamp in the photo and filename
            cv.putText(frame, timestamp.strftime(
                    "%A %d %B %Y %I:%M:%S%p"), (10, frame.shape[0] - 10),
                    cv.FONT_HERSHEY_SIMPLEX, 0.35, (0, 0, 255), 1)
            # Also include the current state in the file name
            cv.imwrite(f"images/cam_{self.cam}_s{state.value}_t_{timestamp.strftime('%d_%I_%M_%S%p')}.png", frame)
        else:
            print("failed  getting frame")
            return Event.EVENT_1
        

        while True:
            ret = self.capture.grab()
            if ret:
                ret, frame = self.capture.retrieve()
                frame = imutils.resize(frame, width=400)
                if frame is None:
                    break

                fgMask = self.backSub[self.cam].apply(frame, None, BGLR)

                locations, confidence = self.hog.detectMultiScale(frame, winStride=(4, 4))
                max_confidence = 0
                min_state = Event.EVENT_2

                for i, (x, y, w, h) in enumerate(locations):
                    if(confidence[i] > MIN_CONFIDENCE) and location_in_fg(fgMask, (x,y,w,h)):
                        cv.rectangle(frame, (x, y), (x + w, y + h), get_color_from_state(state), 5)
                        max_confidence = confidence[i] if confidence[i] > max_confidence else max_confidence
                        if size_close(frame, (x,y,w,h)) or location_close(frame, (x,y,w,h)):
                            if size_close(frame, (x,y,w,h)) and \
                                    location_close(frame, (x,y,w,h)):
                                min_state = Event.EVENT_4 
                            else:
                                min_state = Event.EVENT_3

                timestamp = datetime.datetime.now()
                cv.putText(frame, timestamp.strftime(
                    "%A %d %B %Y %I:%M:%S%p"), (10, frame.shape[0] - 10),
                    cv.FONT_HERSHEY_SIMPLEX, 0.35, (0, 0, 255), 1)
                
                cv.putText(frame,
                        f"State {state}",
                        (10, 15),
                        cv.FONT_HERSHEY_SIMPLEX,
                        0.5,
                        get_color_from_state(state),
                        1)
                
                if state == State.STATE_3 or state == State.STATE_4:
                    cv.putText(frame,
                        f"! Warning !",
                        (10, 30),
                        cv.FONT_HERSHEY_SIMPLEX,
                        0.5,
                        (0, 0, 255),
                        1)
                
                frames["out"].set_with_lock(frame.copy())
                frames["bg"].set_with_lock(fgMask.copy())

                if max_confidence > MIN_CONFIDENCE:
                    print(f"{min_state}, {state}")
                    return min_state
                
                if time.time() - start_time > max_time:
                    return Event.EVENT_1
                        
                keyboard = cv.waitKey(30)
                if keyboard == 'q' or keyboard == 27:
                    break
            else:
                print("failed to get frame")
                return Event.EVENT_1

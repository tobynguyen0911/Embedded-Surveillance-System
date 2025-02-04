# import the necessary packages
from flask import Response
from flask import Flask, jsonify
from flask import render_template
import threading
import cv2
from state_machine import run
import os
import glob
from video_processing import VideoProcessor
import argparse


class FrameClass:
    def __init__(self, lock) -> None:
        self.lock = lock
        self.frame = None

    def set_with_lock(self, in_frame):
        with self.lock:
            self.frame = in_frame

    def get_with_lock(self):
        with self.lock:
            return self.frame

    def get(self):
        return self.frame
    
    def get_lock(self):
        return self.lock

# This object is a wrapper around a frame, this will allow the current frame to accessed
# from a single reference across threads, and uses the lock automatically
out_frames = FrameClass(threading.Lock())
bg_frames = FrameClass(threading.Lock())
frames = {
    "out": out_frames,
    "bg": bg_frames
}
video_processor = None

# initialize a flask object
app = Flask(__name__)

@app.route("/")
def index():
    # return the rendered template
    return render_template("index.html")


def generate(feed="out"):
    # grab global references to the output frame and lock variables
    global frames, lock
    # loop over frames from the output stream
    while True:
        # wait until the lock is acquired
        with frames[feed].get_lock():

            # check if the output frame is available, otherwise skip
            # the iteration of the loop
            if frames[feed].get() is None:
                continue
            # encode the frame in JPEG format
            (flag, encodedImage) = cv2.imencode(".jpg", frames[feed].get())
            # ensure the frame was successfully encoded
            if not flag:
                continue
        # yield the output frame in the byte format
        yield (
            b"--frame\r\n"
            b"Content-Type: image/jpeg\r\n\r\n" + bytearray(encodedImage) + b"\r\n"
        )


@app.route("/video_feed")
def video_feed():
    # return the response generated along with the specific media
    # type (mime type)
    return Response(generate("out"), mimetype="multipart/x-mixed-replace; boundary=frame")

@app.route("/bg_feed")
def bg_feed():
    # return the response generated along with the specific media
    # type (mime type)
    return Response(generate("bg"), mimetype="multipart/x-mixed-replace; boundary=frame")

@app.route("/take_photo", methods=['GET', 'POST'])
def take_photo():
    video_processor.take_photo()
    return "Success"

@app.route("/change_cam", methods=['GET', 'POST'])
def change_cam():
    video_processor.next_camera()
    return "Success"


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("-c", "--cams", type=int, required=True,
        help="number of cameras")
    args = vars(ap.parse_args())

    files = glob.glob('images/*.png')
    for f in files:
        os.remove(f)

    video_processor = VideoProcessor(args["cams"])
    # start a thread that will perform motion detection
    t = threading.Thread(target=run, kwargs={"video":video_processor, "frame": frames})
    t.daemon = True
    t.start()
    app.run(host='0.0.0.0', debug=True, threaded=True, use_reloader=False)
    # start the flask app
    # 	app.run(host=args["ip"], port=args["port"], debug=True,
    # 		threaded=True, use_reloader=False)

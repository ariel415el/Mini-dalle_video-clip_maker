import json
import re
from math import sqrt

import cv2

def get_duration(d):
    return d.minutes*60 + d.seconds + d.milliseconds / 1000


def clean_str(str):
    str = str.replace("\n", " ")
    return re.sub(r'[^A-Za-z0-9 ]+', '', str)


def get_sqrt(n):
    """return the smallest number x such that x**2 > n"""
    x = int(sqrt(n))
    while x**2 < n:
        x = int(x + 1)
    return x


def read_and_preprocess_transcript(path, song_name, n_lines=None):
    """
    Read transcription file, prepend the songname at the start (before first lyrice line),
    set the duration of each lyrics line to last until the next one starts
    """

    transcript = json.load(open(path))

    for i in range(len(transcript)):
        if i < len(transcript) - 1:
            transcript[i]['duration'] = transcript[i+1]['start'] - transcript[i]['start']

    transcript = [{'text': song_name, 'start': 0, 'duration':  transcript[0]['start']}] + transcript

    if n_lines is not None:
        transcript = transcript[:int(n_lines)]
    return transcript


def put_subtitles_on_frame(frame, text, resize_factor=1):
    w, h = frame.shape[:2]
    frame = cv2.resize(frame, (w*resize_factor, h*resize_factor))
    w, h = frame.shape[:2]
    kwargs = {
        'thickness':2,
        'fontScale':0.75,
        'fontFace':cv2.FONT_HERSHEY_SIMPLEX
    }
    (tw, th), _ = cv2.getTextSize(text, **kwargs)
    if tw > w:
        words = text.split()
        first_line = " ".join(words[:len(words) // 2:])
        (tw, th), _ = cv2.getTextSize(first_line, **kwargs)
        frame = cv2.putText(frame, first_line, (w//2 - tw // 2, h - int(th * 3)), color=(255, 255, 255), **kwargs)
        second_line = " ".join(words[len(words) // 2:])
        (tw, th), _ = cv2.getTextSize(second_line, **kwargs)
        frame = cv2.putText(frame, second_line, (w//2 - tw // 2, h - int(th * 1.5)), color=(255, 255, 255), **kwargs)
    else:
        frame = cv2.putText(frame, text, (w//2 - tw // 2, h - int(th * 2)), color=(255, 255, 255), **kwargs)
    return frame

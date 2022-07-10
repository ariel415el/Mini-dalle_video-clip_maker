import argparse
import os
import re
from math import sqrt, ceil
import json
import cv2
import pysrt
from tqdm import tqdm

from dall_e import DalleImageGenerator
from download_from_youtube import download_transcription, download_mp3, get_video_name, get_video_id


def get_duration(d):
    return d.minutes*60 + d.seconds + d.milliseconds / 1000


def clean_str(str):
    return re.sub(r'[^A-Za-z0-9 ]+', '', str)


def get_sqrt(n):
    """return the smallest number x such that x**2 > n"""
    x = int(sqrt(n))
    while x**2 < n:
        x = int(x + 1)
    return x


def read_transcript(path, song_name, n_lines=None):
    """Read transcription file into a list with (text, start, end) tuples"""
    if path.endswith(".srt"):
        subs = pysrt.open(path)
        texts_and_durations = [(song_name, 0, get_duration(subs[0].start))]
        for sub in subs:
            texts_and_durations += [(sub.text, get_duration(sub.start), get_duration(sub.end))]
    elif path.endswith(".json"):
        subs = json.load(open(path))
        texts_and_durations = [(song_name, 0, subs[0]['start'])]
        for sub in subs:
            texts_and_durations += [(sub['text'], sub['start'], sub['start'] + sub['duration'])]
    else:
        raise ValueError("transcript file not supported")

    if n_lines is not None:
        texts_and_durations = texts_and_durations[:int(n_lines)]
    return texts_and_durations


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

def main():
    parser = argparse.ArgumentParser(description='Generate a Dall-e video clip from a youtube url')
    parser.add_argument('url', help='URL of the a song to get the audio from')
    parser.add_argument('--token', help='A Replicate API token', required=True, default=None)
    parser.add_argument('--song_name', help='The name of the song / output files', default=None)
    parser.add_argument('--fps', help='FPS higher then 1 / sec_per_img to better control over timing', default=10)
    parser.add_argument('--sec_per_img', help='How long to show each image', default=3)
    parser.add_argument('--n_lines', help='Limit number of generated lines in the video to faster testing', default=None)
    args = parser.parse_args()

    dalle = DalleImageGenerator(token=args.token)
    img_dim = 256
    resize_factor =  2

    if args.song_name is None:
        args.song_name = clean_str(get_video_name(args.url))

    # Set paths
    outputs_dir = f"data/{args.song_name}"
    frames_dir = f"{outputs_dir}/frames"
    os.makedirs(outputs_dir, exist_ok=True)
    os.makedirs(frames_dir, exist_ok=True)
    mp3_path = f"{outputs_dir}/audio.mp3"
    transcript_path = f"{outputs_dir}/transcript.json"
    vid_path = f"{outputs_dir}/frames.avi"
    final_vid_path = f"{outputs_dir}/final.avi"

    print("Getting audio file and transcript from youtube")
    # Download data
    download_transcription(args.url, transcript_path)
    download_mp3(args.url, mp3_path)

    texts_and_durations = read_transcript(transcript_path, args.song_name, args.n_lines)

    print("Building video-clip")
    frames = []
    video_duration = 0
    for (text, start, end) in texts_and_durations:
        text = clean_str(text)
        start = min(video_duration, start)
        duration = end - start

        # Dall-e generatees grid_size**2 images
        grid_size = max(get_sqrt(duration / args.sec_per_img), 1)

        print(f"({start:.1f} - {end:.1f}):")

        print(f"* Generating {grid_size**2} images with prompt: '{text}'")
        # Generate images
        images = dalle.generate_images(text, grid_size, text_adherence=3)
        # import numpy as np
        # images = (np.random.normal(127, 127, (grid_size, 256, 256, 3))*127 + 128).astype(np.uint8)

        # Write frames
        segment_duration = 0
        frames_per_image = int(duration * args.fps) // len(images)
        for j in range(len(images)):
            frame = cv2.cvtColor(images[j], cv2.COLOR_RGBA2BGR)
            frame = put_subtitles_on_frame(frame, text, resize_factor)
            print(f"* Writing image - {j} as {frames_per_image} frames")
            for _ in range(frames_per_image):
                frames.append(frame)
                segment_duration += 1 / args.fps

        # Write more frames from last image to fill the gap
        if segment_duration < duration:
            n_frames = int((duration - segment_duration) * args.fps)
            print(f"* Writing image - {j} for {n_frames} frames")
            for _ in range(n_frames):
                frames.append(frame)
                segment_duration += 1 / args.fps
        video_duration += segment_duration

    # Write video
    video = cv2.VideoWriter(vid_path, 0, args.fps, (img_dim * resize_factor, img_dim * resize_factor))
    for i, frame in enumerate(frames):
        cv2.imwrite(f"{frames_dir}/frame-{i}.png", frame)
        video.write(frame)
    cv2.destroyAllWindows()
    video.release()

    # Mix video clip with audio
    os.system(f"ffmpeg -ss 00:00:00 -t {video_duration} -i '{mp3_path}' -map 0:a -acodec libmp3lame '{f'data/{args.song_name}/tmp.mp3'}'")
    os.system(f"ffmpeg -i '{vid_path}' -i '{f'data/{args.song_name}/tmp.mp3'}' -map 0 -map 1:a -c:v copy -shortest '{final_vid_path}'")
    print(f"Final video available at: {final_vid_path}")

if __name__ == '__main__':
    main()
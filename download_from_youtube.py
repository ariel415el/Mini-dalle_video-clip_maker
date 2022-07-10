import os

from youtube_transcript_api import YouTubeTranscriptApi
import urllib.parse
import youtube_dl
import json


def get_video_id(url):
    url_data = urllib.parse.urlparse(url)
    query = urllib.parse.parse_qs(url_data.query)
    id = query["v"][0]
    return id


def get_video_name(url):
    id = get_video_id(url)
    params = {"format": "json", "url": "https://www.youtube.com/watch?v=%s" % id}
    url = "https://www.youtube.com/oembed"
    query_string = urllib.parse.urlencode(params)
    url = url + "?" + query_string

    with urllib.request.urlopen(url) as response:
        response_text = response.read()
        data = json.loads(response_text.decode())
        return data['title']

def download_transcription(url, output_path):
    if os.path.exists(output_path):
        return

    id = get_video_id(url)

    # Download transcript with  'YouTubeTranscriptApi'
    str = YouTubeTranscriptApi.get_transcript(id, languages=['en'])
    json.dump(str, open(output_path, 'w'))


def download_mp3(url, output_path):
    if os.path.exists(output_path):
        return
    ydl_opts = {
        'outtmpl': output_path,
        'format': 'bestaudio/best',
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
    }
    with youtube_dl.YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])

if __name__ == '__main__':
    url = 'https://www.youtube.com/watch?v=0mYBSayCsH0&ab_channel=SmashMouthVEVO'
    song_name = "I'm a believer"
    out_dir = os.path.join("data", song_name)
    os.makedirs(out_dir, exist_ok=True)
    print(get_transcription(url, out_dir))
    print(get_mp3(url, out_dir))
# Dall-e video clip maker

This small python project uses Dalle-mini, trough Replicate API, to generate a photo-montage video-clip 
from a song.

Given a youtube url the program will extract the audio and transcript of the video and use the lyrics
in the tarnscript as prompts for Dall-e mini.

## Usage
`python3 main.py <youtube url> --token <your replicate API token>`

An out output example for the video in "Here comes the sun" by the beatles":

[!["Here comes the sun"](https://img.youtube.com/vi/wh_cIPiaQJg/0.jpg)](https://youtu.be/wh_cIPiaQJg)

Only works with youtube videos that have transcription.


## Todo
- [ ] Fix subtitles no whitespace problems
- [ ] Better timing of subtitles and sound
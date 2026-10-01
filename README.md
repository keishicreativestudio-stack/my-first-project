# my-first-project

**The Lighthouse Above the Clouds**: a scrolling picture story in 18 illustrated scenes.

Open `index.html` in a browser. The images are in `images/` as `scene-01.jpg` through `scene-18.jpg`, and the captions are in the `story` array in `index.html`.

## Video

`video/lighthouse.mp4` is a 1080p video of about 1 min 43 s with Japanese captions and background music. `video/lighthouse-720p.mp4` is a lighter preview version.
To make it again: `python3 video/make_video.py` (needs ffmpeg and the IPAPGothic font).

### 空に還る灯台

`video/sora_ni_kaeru_todai.mp4` is a 1080p video of about 7 min 20 s. All of the script is shown as captions, and the music changes with each scene.
To make it again: `pip install numpy && python3 video/make_sora_video.py` (the music comes from `video/make_bgm.py`).

#!/usr/bin/env python3
"""Build the picture-story video from images/scene-XX.jpg sources.

Usage: python3 video/make_video.py <dir with original PNGs or images/> [out.mp4]
Each scene gets a slow Ken Burns move, scenes cross-fade, Japanese captions
are burned in via ASS subtitles, and a soft generated pad plays underneath.
"""
import os
import subprocess
import sys
import tempfile
from concurrent.futures import ThreadPoolExecutor

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = sys.argv[1] if len(sys.argv) > 1 else os.path.join(ROOT, "images")
OUT = sys.argv[2] if len(sys.argv) > 2 else os.path.join(ROOT, "video", "lighthouse.mp4")
FPS = 30
W, H = 1920, 1080
XF = 1.2  # cross-fade seconds

# (caption, seconds, camera move)
SCENES = [
    ("毎晩、リンは雲の海の向こうの灯台を見つめていた。\\N百年もの間、一度も灯りがともらない灯台を。", 7, "in"),
    ("工房で、機械仕掛けの小鳥の最後の翼が完成した。\\N琥珀色の瞳が、ふっと光った。", 7, "in_right"),
    ("ふたりは吊り橋を渡る。\\N知っている世界の、その果てへ。", 6, "pan_right"),
    ("小鳥に導かれ、光る灯籠の森の小道を進んでいく。", 6, "out"),
    ("古い桟橋で待っていたのは、\\N帆に羅針盤が描かれた小さな空の舟。", 6, "pan_left"),
    ("月明かりの雲海へ。めざすは、あの灯台。", 6, "in"),
    ("嵐。稲妻が帆を裂いても、\\Nリンは小鳥を離さなかった。", 5, "shake"),
    ("ぼろぼろになりながら、\\Nふたりは塔のふもとへたどり着いた。", 6, "up"),
    ("塔の中は、止まったままの巨大な時計仕掛け。", 6, "up"),
    ("灯りに浮かぶ壁画。すべての浮島と、\\Nその中心に――鳥と鍵。", 7, "in_right"),
    ("リンは気づいた。\\N螺旋階段を、全力で駆けのぼる。", 5, "pan_right"),
    ("頂上。大きなレンズの前に、\\N鳥の形をした空っぽの台座。", 6, "in"),
    ("「鍵は……ずっと、あなただったんだね」", 7, "in_left"),
    ("涙をこらえて、小鳥をそこへ。\\N塔が、静かに目を覚ます。", 7, "in"),
    ("灯台からあふれた光が、\\N翼のように空いっぱいに広がった。", 7, "out"),
    ("どの町でも、人々が空を見上げた。\\N百年ぶりの灯りを。", 6, "pan_left"),
    ("リンの手に残ったのは、光る羽根が一枚だけ。", 7, "in"),
    ("朝日の中、本物のツバメが指先にとまる。\\Nリンは笑った。あの子は、もうどこにでもいる。", 9, "out"),
]
TITLE_D, END_D = 5, 5


def motion(kind, n):
    """zoompan expressions; p goes 0→1 over the clip with ease-in-out."""
    p = f"(0.5-0.5*cos(PI*on/{n}))"
    cx, cy = "iw/2-(iw/zoom/2)", "ih/2-(ih/zoom/2)"
    if kind == "in":
        return f"1+0.15*{p}", cx, cy
    if kind == "out":
        return f"1.15-0.15*{p}", cx, cy
    if kind == "in_left":
        return f"1+0.18*{p}", f"(iw-iw/zoom)*0.35", cy
    if kind == "in_right":
        return f"1+0.18*{p}", f"(iw-iw/zoom)*0.6", cy
    if kind == "pan_right":
        return "1.15", f"(iw-iw/zoom)*{p}", cy
    if kind == "pan_left":
        return "1.15", f"(iw-iw/zoom)*(1-{p})", cy
    if kind == "up":
        return "1.15", cx, f"(ih-ih/zoom)*(1-{p})"
    if kind == "shake":
        return (f"1.12+0.05*{p}",
                f"{cx}+18*sin(on*1.7)*sin(on*0.31)",
                f"{cy}+12*sin(on*2.3)*cos(on*0.27)")
    raise ValueError(kind)


def run(cmd):
    r = subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, text=True)
    if r.returncode:
        sys.exit(r.stderr[-3000:])


def render_scene(i, tmp):
    _, d, kind = SCENES[i]
    n = int(d * FPS)
    z, x, y = motion(kind, n)
    src = os.path.join(SRC, f"scene-{i + 1:02d}.jpg")
    out = os.path.join(tmp, f"clip{i + 1:02d}.mp4")
    vf = (f"scale=3840:2160:flags=lanczos,setsar=1,"
          f"zoompan=z='{z}':x='{x}':y='{y}':d={n}:s={W}x{H}:fps={FPS},format=yuv420p")
    run(["ffmpeg", "-y", "-loop", "1", "-i", src, "-vf", vf, "-frames:v", str(n),
         "-c:v", "libx264", "-crf", "16", "-preset", "fast", out])
    return out


def ts(t):
    h, rem = divmod(t, 3600)
    m, s = divmod(rem, 60)
    return f"{int(h)}:{int(m):02d}:{s:05.2f}"


def build_ass(path, durations):
    style_cap = "Cap,IPAPGothic,50,&H00F4EBDD,&H00000000,&H64000000,&H96000000,0,0,0,0,100,100,2,0,1,2.5,2,2,80,80,70,1"
    style_title = "Title,IPAPGothic,96,&H00F4EBDD,&H00000000,&H50000000,&H00000000,1,0,0,0,100,100,8,0,1,0,4,5,80,80,0,1"
    style_sub = "Sub,IPAPGothic,40,&H005CB6E7,&H00000000,&H00000000,&H00000000,0,0,0,0,100,100,4,0,1,0,0,5,80,80,0,1"
    lines = [
        "[Script Info]", "ScriptType: v4.00+", f"PlayResX: {W}", f"PlayResY: {H}", "",
        "[V4+ Styles]",
        "Format: Name,Fontname,Fontsize,PrimaryColour,SecondaryColour,OutlineColour,BackColour,"
        "Bold,Italic,Underline,StrikeOut,ScaleX,ScaleY,Spacing,Angle,BorderStyle,Outline,Shadow,"
        "Alignment,MarginL,MarginR,MarginV,Encoding",
        f"Style: {style_cap}", f"Style: {style_title}", f"Style: {style_sub}", "",
        "[Events]", "Format: Layer,Start,End,Style,Name,MarginL,MarginR,MarginV,Effect,Text",
        f"Dialogue: 0,{ts(0.6)},{ts(TITLE_D - 0.5)},Title,,0,0,0,,{{\\fad(900,700)\\pos(960,500)}}雲の上の灯台",
        f"Dialogue: 0,{ts(1.3)},{ts(TITLE_D - 0.5)},Sub,,0,0,0,,{{\\fad(900,700)\\pos(960,610)}}― 少女と機械仕掛けの小鳥の物語 ―",
    ]
    offset = TITLE_D - XF
    for i, (text, d, _) in enumerate(SCENES):
        start, end = offset + 0.8, offset + d - XF * 0.6
        lines.append(f"Dialogue: 0,{ts(start)},{ts(end)},Cap,,0,0,0,,{{\\fad(600,500)}}{text}")
        offset += d - XF
    lines.append(f"Dialogue: 0,{ts(offset + 0.8)},{ts(offset + END_D - 0.2)},Title,,0,0,0,,{{\\fad(1000,800)\\pos(960,540)}}おわり")
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    return offset + END_D  # total duration


def pad_expr():
    # Am – F – C – G, 8 s per chord, each chord swelling in and out over a low A drone.
    chords = [(220.0, 261.63, 329.63), (174.61, 220.0, 261.63),
              (196.0, 261.63, 329.63), (196.0, 246.94, 293.66)]
    env = "pow(sin(PI*mod(t,8)/8),1.5)"
    parts = []
    for k, ch in enumerate(chords):
        tones = "+".join(f"sin(2*PI*{f}*t)+0.3*sin(2*PI*{2 * f}*t)" for f in ch)
        parts.append(f"eq(mod(floor(t/8),4),{k})*({tones})")
    return f"0.05*sin(2*PI*110*t)+0.035*{env}*({'+'.join(parts)})"


def main():
    with tempfile.TemporaryDirectory() as tmp:
        with ThreadPoolExecutor(max_workers=4) as ex:
            clips = list(ex.map(lambda i: render_scene(i, tmp), range(len(SCENES))))

        durations = [TITLE_D] + [d for _, d, _ in SCENES] + [END_D]
        ass = os.path.join(tmp, "captions.ass")
        total = build_ass(ass, durations)

        inputs = ["-f", "lavfi", "-t", str(TITLE_D), "-i", f"color=c=0x0b1026:s={W}x{H}:r={FPS}"]
        for c in clips:
            inputs += ["-i", c]
        inputs += ["-f", "lavfi", "-t", str(END_D), "-i", f"color=c=0x0b1026:s={W}x{H}:r={FPS}"]
        inputs += ["-f", "lavfi", "-t", f"{total:.2f}",
                   "-i", "aevalsrc='" + pad_expr().replace(",", "\\,") + "':s=48000:c=stereo"]

        fg = [f"[{k}:v]settb=AVTB,fps={FPS},setsar=1[s{k}]" for k in range(len(durations))]
        prev, offset = "[s0]", 0.0
        for k in range(1, len(durations)):
            offset += durations[k - 1] - XF
            label = f"[v{k}]"
            fg.append(f"{prev}[s{k}]xfade=transition=fade:duration={XF}:offset={offset:.3f}{label}")
            prev = label
        fg.append(f"{prev}subtitles='{ass}',format=yuv420p[vout]")
        a = len(durations)
        fg.append(f"[{a}:a]lowpass=f=1800,aecho=0.8:0.7:120|260:0.35|0.25,"
                  f"afade=t=in:d=3,afade=t=out:st={total - 4:.2f}:d=4,volume=3.5[aout]")

        run(["ffmpeg", "-y", *inputs, "-filter_complex", ";".join(fg),
             "-map", "[vout]", "-map", "[aout]", "-c:v", "libx264", "-crf", "24",
             "-preset", "slow", "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "160k",
             "-movflags", "+faststart", "-t", f"{total:.2f}", OUT])
    print(f"wrote {OUT} ({total:.1f}s)")


if __name__ == "__main__":
    main()

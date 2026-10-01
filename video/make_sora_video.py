#!/usr/bin/env python3
"""『空に還る灯台』: build the narrated-caption video from images/scene-XX.jpg.

Usage: python3 video/make_sora_video.py [out.mp4]
Each shot is one image with a slow camera move; the script's sentences are
shown one after another as captions, and each shot lasts as long as its
captions need. Shots cross-fade. The scene-aware music comes from
make_bgm.py (needs numpy).
"""
import os
import subprocess
import sys
import tempfile
from concurrent.futures import ThreadPoolExecutor

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, "images")
OUT = sys.argv[1] if len(sys.argv) > 1 else os.path.join(ROOT, "video", "sora_ni_kaeru_todai.mp4")
FPS = 30
W, H = 1920, 1080
XF = 1.5          # cross-fade between shots
LEAD = 1.2        # silence before first caption of a shot
GAP = 0.35        # pause between captions
TITLE = "空に還る灯台"
TITLE_D, END_D = 6, 6

# (image no., zoom from, zoom to, centre from, centre to, shake, [captions])
# centres are normalised (x, y) on the image; "\N" is a caption line break.
SHOTS = [
    (1, 1.6, 1.0, (0.75, 0.30), (0.5, 0.5), False, [
        "空に浮かぶ島々には、\\N夜になると必ず灯る、大きな灯台がありました。",
        "その光は雲の海に道を描き、\\N遠く離れた島と島を結んでいました。",
        "旅人は光を頼りに家へ帰り、\\N子どもたちは窓辺でその輝きを眺めながら眠りました。",
        "けれど、ある夜から、\\N灯台の光は少しずつ弱くなっていきました。",
        "雲の向こうへ渡る舟は減り、\\N村の風車も止まりがちになりました。",
        "人々は残った灯りを守るように、\\N早く戸を閉めるようになりました。",
    ]),
    (2, 1.0, 1.2, (0.5, 0.5), (0.45, 0.55), False, [
        "島の片隅に、古い時計を直して暮らす少女、\\Nリナがいました。",
        "リナの友だちは、小さな機械のツバメでした。\\N真鍮の体に、青いガラスの翼。",
        "名前はチル。祖父が残してくれた鳥で、\\Nリナが作業をする間、いつも机の端に止まっていました。",
        "ある晩、傷んだ翼を直すと、\\Nチルはうれしそうに羽ばたきました。",
    ]),
    (2, 1.3, 1.5, (0.58, 0.62), (0.75, 0.33), False, [
        "すると、翼から青い光がこぼれ、\\N机の上に島々の地図が浮かびました。",
        "光の点がひとつずつつながり、\\Nその先に、雲の果ての灯台が現れました。",
        "チルは地図の灯台を見つめ、\\Nそれからリナを振り返りました。",
    ]),
    (2, 1.35, 1.15, (0.36, 0.40), (0.45, 0.48), False, [
        "「そこへ行きたいの？」",
        "チルの瞳が、小さく瞬きました。",
        "リナは工具を鞄に入れ、\\N青緑のマントを羽織りました。",
        "「じゃあ、一緒に行こう」",
    ]),
    (3, 1.15, 1.15, (0.35, 0.50), (0.62, 0.45), False, [
        "眠る村を抜け、吊り橋を渡り、",
    ]),
    (4, 1.15, 1.0, (0.40, 0.60), (0.5, 0.5), False, [
        "青く光る実の森を歩きました。",
        "道が霧に隠れるたびに、\\Nチルが先へ飛び、リナを待っていました。",
    ]),
    (5, 1.0, 1.15, (0.5, 0.5), (0.42, 0.5), False, [
        "森の端には、古い舟が一艘、つながれていました。",
        "リナが船底の輪を直すと、\\N舟はふわりと浮かびました。",
    ]),
    (6, 1.2, 1.0, (0.35, 0.60), (0.5, 0.5), False, [
        "白い帆が風を受け、\\Nふたりは雲の海へ滑り出しました。",
        "見渡す限りの雲。その上に浮かぶ島々。",
        "岩の隙間から流れ落ちる滝は、\\N底の見えない空へ消えていました。",
        "リナは舵を握り、チルは船首で翼を広げました。",
    ]),
    (7, 1.12, 1.2, (0.5, 0.5), (0.45, 0.45), True, [
        "けれど、灯台へ近づくころ、\\N黒い雲が行く手を覆いました。",
        "雷が空を裂き、舟が大きく傾きました。",
        "帆が破れ、チルの小さな体が\\N風にさらわれそうになりました。",
        "リナは手を伸ばし、チルを胸に抱き寄せました。",
        "「大丈夫。離さないから」",
        "片手で縄を握り、\\Nもう片方の腕でチルを守りました。",
    ]),
    (8, 1.2, 1.2, (0.5, 0.75), (0.5, 0.30), False, [
        "長い嵐のあと、雲の切れ間に、\\N巨大な塔が現れました。",
        "灯台でした。",
    ]),
    (9, 1.0, 1.2, (0.5, 0.6), (0.5, 0.4), False, [
        "重い扉の向こうには、止まった歯車と、\\N果てしなく続く螺旋階段がありました。",
    ]),
    (10, 1.1, 1.35, (0.5, 0.5), (0.62, 0.45), False, [
        "壁には、古い絵が彫られていました。",
        "島々へ光を送る灯台。\\Nその中心に、翼を広げた一羽のツバメ。",
        "リナは腕に止まったチルを見ました。",
        "チルも、壁のツバメを見つめていました。",
    ]),
    (11, 1.15, 1.15, (0.30, 0.40), (0.5, 0.55), False, [
        "ふたりは黙って階段を登りました。",
    ]),
    (12, 1.0, 1.2, (0.5, 0.5), (0.55, 0.5), False, [
        "頂上には、大きなガラスのレンズがありました。",
        "その下の台座には、\\Nチルと同じ形のくぼみが空いていました。",
        "チルはリナの手から飛び立とうとしました。",
    ]),
    (13, 1.0, 1.15, (0.5, 0.5), (0.55, 0.42), False, [
        "リナは思わず、その体を抱きしめました。",
        "灯台にチルを置けば、村に光が戻る。",
        "けれど、明日から作業机の端には、\\N誰が止まるのでしょう。",
        "帰り道では、誰が先を飛んで\\N待っていてくれるのでしょう。",
    ]),
    (13, 1.2, 1.35, (0.52, 0.40), (0.50, 0.40), False, [
        "チルは嘴をそっと、リナの額に寄せました。",
        "いつも、直してもらったあとにする仕草でした。",
        "リナは目を閉じました。\\N涙が一粒、真鍮の翼に落ちました。",
        "「……一緒に来てくれて、ありがとう」",
    ]),
    (14, 1.0, 1.15, (0.5, 0.5), (0.6, 0.5), False, [
        "そして、ゆっくりとチルを台座へ置きました。",
        "青い翼がくぼみに収まると、\\N細い光が歯車を走りました。",
        "ひとつ、またひとつ。",
        "止まっていた歯車が動き、\\N大きなレンズに光が満ちていきました。",
    ]),
    (15, 1.25, 1.0, (0.5, 0.45), (0.5, 0.5), False, [
        "次の瞬間、灯台から\\N金色と青の光があふれ出しました。",
        "光は雲を越え、島々を巡り、\\N空いっぱいに大きな翼を広げました。",
    ]),
    (16, 1.15, 1.15, (0.62, 0.5), (0.35, 0.5), False, [
        "村の灯りが輝きを増し、風車が回り始めました。",
        "窓が開き、人々が空を見上げました。",
        "遠くの舟が、帰り道を見つけて帆を上げました。",
    ]),
    (17, 1.0, 1.15, (0.5, 0.5), (0.55, 0.55), False, [
        "リナは灯台の外へ出ました。",
        "朝日に染まる雲を眺めていると、\\N青いガラスの羽根が一枚、風に乗って届きました。",
        "手のひらに受け止めると、\\Nまだ少し温かい気がしました。",
        "リナは羽根を胸に当てました。",
    ]),
    (18, 1.2, 1.0, (0.40, 0.5), (0.55, 0.5), False, [
        "そのとき、一羽のツバメが欄干に降りてきました。",
        "小さな黒い翼。白いお腹。",
        "リナが指を差し出すと、ツバメはそこへ飛び移り、\\N不思議そうに首をかしげました。",
        "リナは涙を拭き、笑いました。",
        "背後では灯台が、\\N静かに光を送り続けていました。",
        "雲の海に、どこまでも続く帰り道を描きながら。",
    ]),
]


def read_time(text):
    chars = len(text.replace("\\N", ""))
    return max(3.2, chars / 6.5 + 1.6)


def shot_duration(caps):
    return LEAD + sum(read_time(c) + GAP for c in caps) + XF + 0.6


def run(cmd):
    r = subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, text=True)
    if r.returncode:
        sys.exit(r.stderr[-3000:])


def groups():
    """Consecutive shots of the same image become one continuous clip."""
    out = []
    for i, shot in enumerate(SHOTS):
        if out and SHOTS[out[-1][-1]][0] == shot[0]:
            out[-1].append(i)
        else:
            out.append([i])
    return out


def group_duration(g):
    return sum(shot_duration(SHOTS[i][6]) for i in g) - XF * (len(g) - 1)


def render_group(gi, g, tmp):
    """One image, camera moving through each shot's framing in turn."""
    n = int(group_duration(g) * FPS)
    segs, t = [], 0.0
    prev_end = None
    for j, i in enumerate(g):
        _, z0, z1, c0, c1, shake, caps = SHOTS[i]
        if prev_end:  # continue from where the previous framing stopped
            z0, c0 = prev_end
        start = 0 if j == 0 else int((t + XF / 2) * FPS)
        t += shot_duration(caps) - XF
        end = n if j == len(g) - 1 else int((t + XF / 2) * FPS)
        segs.append((start, end, z0, z1, c0, c1, shake))
        prev_end = (z1, c1)

    def piecewise(f):
        expr = None
        for a, b, *rest in reversed(segs):
            p = f"(0.5-0.5*cos(PI*(on-{a})/{b - a}))"
            e = f(p, *rest)
            expr = e if expr is None else f"if(lt(on,{b}),{e},{expr})"
        return expr

    z = piecewise(lambda p, z0, z1, c0, c1, sh: f"{z0}+({z1 - z0})*{p}")
    x = piecewise(lambda p, z0, z1, c0, c1, sh:
                  f"clip(({c0[0]}+({c1[0] - c0[0]})*{p})*iw-iw/zoom/2"
                  + ("+18*sin(on*1.7)*sin(on*0.31)" if sh else "") + ",0,iw-iw/zoom)")
    y = piecewise(lambda p, z0, z1, c0, c1, sh:
                  f"clip(({c0[1]}+({c1[1] - c0[1]})*{p})*ih-ih/zoom/2"
                  + ("+12*sin(on*2.3)*cos(on*0.27)" if sh else "") + ",0,ih-ih/zoom)")
    img = SHOTS[g[0]][0]
    out = os.path.join(tmp, f"shot{gi:02d}.mp4")
    vf = (f"scale=3840:2160:flags=lanczos,setsar=1,"
          f"zoompan=z='{z}':x='{x}':y='{y}':d={n}:s={W}x{H}:fps={FPS},format=yuv420p")
    run(["ffmpeg", "-y", "-loop", "1", "-i", os.path.join(SRC, f"scene-{img:02d}.jpg"),
         "-vf", vf, "-frames:v", str(n), "-c:v", "libx264", "-crf", "16", "-preset", "fast", out])
    return out


def ts(t):
    m, s = divmod(t, 60)
    return f"0:{int(m):02d}:{s:05.2f}"


def build_ass(path):
    """Write captions; return (total duration, storm (start, end))."""
    font = "IPAPGothic"
    lines = [
        "[Script Info]", "ScriptType: v4.00+", f"PlayResX: {W}", f"PlayResY: {H}", "",
        "[V4+ Styles]",
        "Format: Name,Fontname,Fontsize,PrimaryColour,SecondaryColour,OutlineColour,BackColour,"
        "Bold,Italic,Underline,StrikeOut,ScaleX,ScaleY,Spacing,Angle,BorderStyle,Outline,Shadow,"
        "Alignment,MarginL,MarginR,MarginV,Encoding",
        f"Style: Cap,{font},50,&H00F4EBDD,&H00000000,&H64000000,&H96000000,0,0,0,0,100,100,2,0,1,2.5,2,2,80,80,70,1",
        f"Style: Title,{font},104,&H00F4EBDD,&H00000000,&H50000000,&H00000000,1,0,0,0,100,100,10,0,1,0,4,5,80,80,0,1",
        "", "[Events]", "Format: Layer,Start,End,Style,Name,MarginL,MarginR,MarginV,Effect,Text",
        f"Dialogue: 0,{ts(0.8)},{ts(TITLE_D - 0.6)},Title,,0,0,0,,{{\\fad(1200,900)\\pos(960,540)}}{TITLE}",
    ]
    offset, storm = TITLE_D - XF, None
    for shot in SHOTS:
        caps, d = shot[6], shot_duration(shot[6])
        t = offset + LEAD
        for c in caps:
            r = read_time(c)
            lines.append(f"Dialogue: 0,{ts(t)},{ts(t + r)},Cap,,0,0,0,,{{\\fad(450,400)}}{c}")
            t += r + GAP
        if shot[5]:
            storm = (offset, offset + d)
        offset += d - XF
    lines.append(f"Dialogue: 0,{ts(offset + 1.0)},{ts(offset + END_D - 0.3)},Title,,0,0,0,,{{\\fad(1200,1000)\\pos(960,540)}}おわり")
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    return offset + END_D, storm


def main():
    for shot in SHOTS:
        for c in shot[6]:
            for part in c.split("\\N"):
                if len(part) > 28:
                    sys.exit(f"caption line too long ({len(part)}): {part}")

    with tempfile.TemporaryDirectory() as tmp:
        with ThreadPoolExecutor(max_workers=4) as ex:
            gs = groups()
            clips = list(ex.map(lambda a: render_group(a[0], a[1], tmp), enumerate(gs)))

        ass = os.path.join(tmp, "captions.ass")
        total, _ = build_ass(ass)
        bgm = os.path.join(tmp, "bgm.wav")
        run([sys.executable, os.path.join(os.path.dirname(os.path.abspath(__file__)), "make_bgm.py"), bgm])
        durations = [TITLE_D] + [group_duration(g) for g in gs] + [END_D]

        bg = f"color=c=0x0b1026:s={W}x{H}:r={FPS}"
        inputs = ["-f", "lavfi", "-t", str(TITLE_D), "-i", bg]
        for c in clips:
            inputs += ["-i", c]
        inputs += ["-f", "lavfi", "-t", str(END_D), "-i", bg]
        inputs += ["-i", bgm]

        n = len(durations)
        fg = [f"[{k}:v]settb=AVTB,fps={FPS},setsar=1[s{k}]" for k in range(n)]
        prev, offset = "[s0]", 0.0
        for k in range(1, n):
            offset += durations[k - 1] - XF
            fg.append(f"{prev}[s{k}]xfade=transition=fade:duration={XF}:offset={offset:.3f}[v{k}]")
            prev = f"[v{k}]"
        fg.append(f"{prev}subtitles='{ass}',format=yuv420p[vout]")
        fg.append(f"[{n}:a]anull[aout]")

        run(["ffmpeg", "-y", *inputs, "-filter_complex", ";".join(fg),
             "-map", "[vout]", "-map", "[aout]", "-c:v", "libx264", "-crf", "26",
             "-maxrate", "1500k", "-bufsize", "3000k", "-preset", "slow", "-tune", "stillimage", "-pix_fmt", "yuv420p",
             "-c:a", "aac", "-b:a", "128k", "-movflags", "+faststart", "-t", f"{total:.2f}", OUT])
    print(f"wrote {OUT} ({total:.1f}s)")


if __name__ == "__main__":
    main()

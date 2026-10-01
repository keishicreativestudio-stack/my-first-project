#!/usr/bin/env python3
"""台本(JSON)から TikTok 用の縦型テロップ動画 (1080x1920 / 30fps) を作るツール。

使い方:
  python3 make_video.py scripts/sample_build.json            # 動画を作る
  python3 make_video.py scripts/*.json                        # まとめて作る
  python3 make_video.py scripts/sample_prompts.json --photos  # フォトモード用の画像を書き出す

出力は out/ フォルダに「台本名.mp4」「台本名.srt」(字幕) として保存されます。
台本の書き方は README.md を見てください。
"""
import argparse
import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

try:
    from PIL import Image, ImageDraw, ImageFilter, ImageFont
except ImportError:
    sys.exit("Pillow が入っていません。 pip install -r requirements.txt を実行してください。")

W, H = 1080, 1920
FPS = 30
ANIM_FRAMES = 7          # テロップが出てくるアニメーションのフレーム数
SIDE = 110               # 左右の余白（右側は TikTok のボタンと重ならないよう広め）
SAFE_TOP = 250           # 上の余白（TikTok の「フォロー中/おすすめ」タブ）
SAFE_BOTTOM = 1480       # これより下は TikTok のキャプションと被るので使わない

THEMES = {
    "dark":  {"bg": ("#0e1330", "#26306b"), "text": "#ffffff", "accent": "#ffd84d",
              "outline": "#070a1c", "on_accent": "#0e1330", "panel": "#0a0d22", "panel_text": "#d9e2ff", "bar": "#ffd84d"},
    "light": {"bg": ("#fbfaf6", "#e4ebfb"), "text": "#14161f", "accent": "#e8364f",
              "outline": "#ffffff", "on_accent": "#ffffff", "panel": "#ffffff", "panel_text": "#1d2233", "bar": "#e8364f"},
    "pop":   {"bg": ("#ff5470", "#ffb347"), "text": "#ffffff", "accent": "#fff36b",
              "outline": "#3a0f1f", "on_accent": "#3a0f1f", "panel": "#1b1740", "panel_text": "#fff3d6", "bar": "#fff36b"},
    "green": {"bg": ("#06201a", "#0f4a3b"), "text": "#ffffff", "accent": "#7dffb2",
              "outline": "#03110d", "on_accent": "#03110d", "panel": "#021410", "panel_text": "#c9ffe2", "bar": "#7dffb2"},
}

# 行頭に来てはいけない文字（禁則処理）
NO_LINE_START = set("、。，．・：；？！ー―…‥」』）】〉》〕’”ぁぃぅぇぉっゃゅょゎァィゥェォッャュョヮヵヶ!?),.")

FONT_CANDIDATES = [
    # macOS
    "/System/Library/Fonts/ヒラギノ角ゴシック W8.ttc",
    "/System/Library/Fonts/ヒラギノ角ゴシック W6.ttc",
    "/System/Library/Fonts/Hiragino Sans GB.ttc",
    # Windows
    "C:/Windows/Fonts/YuGothB.ttc",
    "C:/Windows/Fonts/meiryob.ttc",
    "C:/Windows/Fonts/msgothic.ttc",
    # Linux
    "/usr/share/fonts/opentype/noto/NotoSansCJK-Black.ttc",
    "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc",
    "/usr/share/fonts/noto-cjk/NotoSansCJK-Bold.ttc",
    "/usr/share/fonts/opentype/ipafont-gothic/ipag.ttf",
    "/usr/share/fonts/truetype/fonts-japanese-gothic.ttf",
]


# ---------------------------------------------------------------- 準備

def find_font(user_font=None):
    here = Path(__file__).parent
    candidates = [user_font] if user_font else []
    candidates += sorted(str(p) for p in (here / "fonts").glob("*.[ot]t[fc]"))
    candidates += FONT_CANDIDATES
    for c in candidates:
        if c and Path(c).exists():
            return c
    sys.exit("日本語フォントが見つかりません。tiktok-studio/fonts/ にフォント(.ttf/.otf)を置くか --font で指定してください。")


def find_ffmpeg():
    exe = shutil.which("ffmpeg")
    if exe:
        return exe
    try:
        import imageio_ffmpeg
        return imageio_ffmpeg.get_ffmpeg_exe()
    except ImportError:
        sys.exit("ffmpeg が見つかりません。 pip install -r requirements.txt を実行してください。")


class Fonts:
    def __init__(self, path):
        self.path = path
        self.cache = {}

    def get(self, size):
        if size not in self.cache:
            self.cache[size] = ImageFont.truetype(self.path, size)
        return self.cache[size]


# ---------------------------------------------------------------- テキスト配置

def parse_marks(text):
    """「**強調**」を (文字, 強調か) のリストにする。"""
    out, hi = [], False
    for part in re.split(r"(\*\*)", text):
        if part == "**":
            hi = not hi
        else:
            out += [(ch, hi) for ch in part]
    return out


def plain(text):
    return text.replace("**", "")


def wrap(chars, font, max_w):
    """1文字ずつ詰めて折り返す。改行(\\n)と禁則処理に対応。"""
    lines, line, width = [], [], 0
    for ch, hi in chars:
        if ch == "\n":
            lines.append(line)
            line, width = [], 0
            continue
        cw = font.getlength(ch)
        if line and width + cw > max_w:
            carry = []
            if ch in NO_LINE_START and len(line) > 1:
                carry = [line.pop()]
            lines.append(line)
            line = carry
            width = sum(font.getlength(c) for c, _ in line)
        line.append((ch, hi))
        width += cw
    lines.append(line)
    return lines


def fit_text(chars, fonts, max_w, max_h, size_max, size_min, spacing=1.28, keep_breaks=True):
    """枠に収まる一番大きい文字サイズを探す。
    自分で入れた改行の位置を優先し、1行が勝手に折り返されない大きさを選ぶ。"""
    manual_lines = sum(1 for c, _ in chars if c == "\n") + 1
    fallback = None
    for size in range(size_max, size_min - 1, -4):
        font = fonts.get(size)
        lines = wrap(chars, font, max_w)
        line_h = int(size * spacing)
        if len(lines) * line_h > max_h:
            continue
        if not keep_breaks or len(lines) == manual_lines:
            return font, lines, line_h
        fallback = fallback or (font, lines, line_h)
    if fallback:
        return fallback
    font = fonts.get(size_min)
    return font, wrap(chars, font, max_w), int(size_min * spacing)


def draw_lines(draw, lines, font, line_h, cx, top, theme, align="center", left=0,
               color=None, outline=True):
    size = font.size
    stroke = max(4, size // 11) if outline else 0
    for i, line in enumerate(lines):
        y = top + i * line_h
        lw = sum(font.getlength(c) for c, _ in line)
        x = cx - lw / 2 if align == "center" else left
        for ch, hi in line:
            fill = theme["accent"] if hi else (color or theme["text"])
            if stroke:
                draw.text((x, y), ch, font=font, fill=theme["outline"],
                          stroke_width=stroke, stroke_fill=theme["outline"])
            # stroke を同色で重ねて太字に見せる（細いフォント対策）
            draw.text((x, y), ch, font=font, fill=fill, stroke_width=max(1, size // 40), stroke_fill=fill)
            x += font.getlength(ch)


# ---------------------------------------------------------------- 画面を描く

def gradient(theme):
    top, bottom = (Image.new("RGB", (1, 1), c).getpixel((0, 0)) for c in theme["bg"])
    col = Image.new("RGB", (1, H))
    for y in range(H):
        t = y / (H - 1)
        col.putpixel((0, y), tuple(int(a + (b - a) * t) for a, b in zip(top, bottom)))
    return col.resize((W, H))


def rounded_panel(size, color, radius=36):
    panel = Image.new("RGBA", size, (0, 0, 0, 0))
    ImageDraw.Draw(panel).rounded_rectangle((0, 0, size[0] - 1, size[1] - 1), radius, fill=color)
    return panel


def paste_shadowed(base, img, xy, radius=36):
    shadow = Image.new("RGBA", (img.width + 80, img.height + 80), (0, 0, 0, 0))
    ImageDraw.Draw(shadow).rounded_rectangle((40, 50, img.width + 40, img.height + 50), radius, fill=(0, 0, 0, 110))
    shadow = shadow.filter(ImageFilter.GaussianBlur(22))
    base.alpha_composite(shadow, (xy[0] - 40, xy[1] - 40))
    mask = Image.new("L", img.size, 0)
    ImageDraw.Draw(mask).rounded_rectangle((0, 0, img.width - 1, img.height - 1), radius, fill=255)
    base.paste(img.convert("RGBA"), xy, mask)


MEDIA_BOX = (SIDE - 40, 220, W - SIDE + 40, 1240)   # 画面録画・画像を置く枠


class Scene:
    """1シーン分の画面。背景(＋画像/録画) と テロップ層 を分けて持つ。"""

    def __init__(self, spec, cfg, fonts, theme, index, total):
        self.theme = theme
        self.style = spec.get("style", "normal")
        self.has_media = bool(spec.get("clip") or spec.get("image"))
        self.base_dir = cfg["_dir"]
        # 画面録画・画像がまだ無いときは「ここに入ります」の仮の枠で仕上がりを確認できるようにする
        media = spec.get("clip") or spec.get("image")
        missing = media and not self.path(media).exists()
        if missing:
            print(f"  ※ {media} が見つからないので仮の枠で作ります")
            spec = {k: v for k, v in spec.items() if k not in ("clip", "image")}
            spec.setdefault("duration", 3.0)
        self.spec = spec
        self.text_layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        self.static = Image.new("RGBA", (W, H), (0, 0, 0, 0))   # アニメーションしない装飾
        self._draw_text(fonts, cfg, index, total)
        self.image = None
        if missing:
            self.image = self._placeholder(fonts, media)
        elif spec.get("image"):
            self.image = self._load_image(spec["image"])

    def _placeholder(self, fonts, name):
        bw, bh = self.media_size()
        img = Image.new("RGB", (bw, bh - 200), self.theme["panel"])
        d = ImageDraw.Draw(img)
        is_photo = Path(name).suffix.lower() in (".jpg", ".jpeg", ".png", ".webp", ".heic")
        d.text((bw // 2, img.height // 2 - 40), "ここに写真" if is_photo else "ここに画面録画", font=fonts.get(64),
               fill=self.theme["panel_text"], anchor="mm")
        d.text((bw // 2, img.height // 2 + 50), Path(name).name, font=fonts.get(40),
               fill=self.theme["panel_text"], anchor="mm")
        return img

    def path(self, p):
        p = Path(p)
        return p if p.is_absolute() else self.base_dir / p

    def media_size(self):
        x0, y0, x1, y1 = MEDIA_BOX
        return x1 - x0, y1 - y0

    def _load_image(self, p):
        img = Image.open(self.path(p)).convert("RGB")
        bw, bh = self.media_size()
        img.thumbnail((bw, bh), Image.LANCZOS)
        return img

    def _draw_text(self, fonts, cfg, index, total):
        t, spec = self.theme, self.spec
        d = ImageDraw.Draw(self.text_layer)
        max_w = W - SIDE * 2
        text = spec.get("text", "")
        code = spec.get("code")

        if self.has_media:
            area_top, area_bottom = MEDIA_BOX[3] + 50, SAFE_BOTTOM
            size_max, size_min = 84, 52
        elif self.style == "hook":
            area_top, area_bottom = SAFE_TOP + 120, SAFE_BOTTOM - 120
            size_max, size_min = 132, 64
        else:
            area_top, area_bottom = SAFE_TOP + 60, SAFE_BOTTOM
            size_max, size_min = 100, 56

        code_block = None
        if code:
            cf, clines, clh = fit_text([(c, False) for c in code], fonts, max_w - 90, 640, 52, 34, 1.45,
                                         keep_breaks=False)  # プロンプトは折り返してよいので、どのページも同じ大きさにする
            ch = len(clines) * clh + 90
            code_block = (cf, clines, clh, ch)

        label = spec.get("label")
        label_h = 90 if label else 0
        avail = area_bottom - area_top - label_h - (code_block[3] + 50 if code_block else 0)
        font, lines, line_h = fit_text(parse_marks(text), fonts, max_w, max(avail, 200), size_max, size_min)
        text_h = len(lines) * line_h if text else 0
        block_h = label_h + text_h + (code_block[3] + 50 if code_block else 0)
        top = area_top if self.has_media else area_top + max(0, (area_bottom - area_top - block_h) // 2)

        if label:
            lf = fonts.get(44)
            lw = int(lf.getlength(label)) + 64
            sd = ImageDraw.Draw(self.static)
            x0 = (W - lw) // 2
            sd.rounded_rectangle((x0, top, x0 + lw, top + 70), 35, fill=t["accent"])
            sd.text((W // 2, top + 35), label, font=lf, fill=t["on_accent"], anchor="mm")
            top += label_h
        if text:
            draw_lines(d, lines, font, line_h, W // 2, top, t)
            top += text_h + 50
        if code_block:
            cf, clines, clh, ch = code_block
            x0 = SIDE
            panel = rounded_panel((max_w, ch), t["panel"], 32)
            self.text_layer.alpha_composite(panel, (x0, top))
            draw_lines(d, clines, cf, clh, 0, top + 45, dict(t, text=t["panel_text"]),
                       align="left", left=x0 + 45, outline=False)

        if self.style == "cta" and cfg.get("handle"):
            hf = fonts.get(64)
            handle = cfg["handle"]
            hw = int(hf.getlength(handle)) + 120
            x0, y0 = (W - hw) // 2, SAFE_BOTTOM - 150
            d.rounded_rectangle((x0, y0, x0 + hw, y0 + 120), 60, fill=t["accent"])
            d.text((W // 2, y0 + 60), handle, font=hf, fill=t["on_accent"], anchor="mm")

        sd = ImageDraw.Draw(self.static)
        if cfg.get("series"):
            sf = fonts.get(40)
            sd.text((SIDE - 40, 150), cfg["series"], font=sf, fill=t["text"],
                    stroke_width=3, stroke_fill=t["outline"])
        if cfg.get("handle") and self.style != "cta":
            hf = fonts.get(34)
            sd.text((W - SIDE + 40, 150), cfg["handle"], font=hf, fill=t["text"], anchor="ra",
                    stroke_width=3, stroke_fill=t["outline"])
        if cfg.get("page_numbers"):
            pf = fonts.get(36)
            sd.text((W // 2, SAFE_BOTTOM + 40), f"{index + 1} / {total}", font=pf, fill=t["text"],
                    anchor="mm", stroke_width=3, stroke_fill=t["outline"])

    def frame(self, bg, media_frame, progress, anim, show_bar):
        """1フレームを合成して返す。anim は 0→1 でテロップが出てくる。"""
        img = bg.copy()
        media = media_frame or self.image
        if media is not None:
            x0, y0, x1, y1 = MEDIA_BOX
            pos = (x0 + (x1 - x0 - media.width) // 2, y0 + (y1 - y0 - media.height) // 2)
            paste_shadowed(img, media, pos)
        img.alpha_composite(self.static)
        if anim >= 1:
            img.alpha_composite(self.text_layer)
        else:
            ease = 1 - (1 - anim) ** 3
            layer = self.text_layer
            if ease < 1:
                alpha = layer.getchannel("A").point(lambda a: int(a * ease))
                layer = layer.copy()
                layer.putalpha(alpha)
            img.alpha_composite(layer, (0, int((1 - ease) * 40)))
        if show_bar:
            d = ImageDraw.Draw(img)
            d.rectangle((0, 0, W, 14), fill=(0, 0, 0, 90))
            d.rectangle((0, 0, int(W * progress), 14), fill=self.theme["bar"])
        return img.convert("RGB")


# ---------------------------------------------------------------- 画面録画の読み込み

def clip_seconds(ffmpeg, path):
    proc = subprocess.run([ffmpeg, "-i", str(path)], capture_output=True, text=True)
    m = re.search(r"Duration: (\d+):(\d+):([\d.]+)", proc.stderr)
    if not m:
        sys.exit(f"動画の長さを読めません: {path}")
    h, mi, s = m.groups()
    return int(h) * 3600 + int(mi) * 60 + float(s)


def clip_frames(ffmpeg, scene, n_frames):
    """画面録画を枠のサイズに縮めて1フレームずつ返す。足りない分は最後のフレームを使う。"""
    spec = scene.spec
    bw, bh = scene.media_size()
    speed = float(spec.get("clip_speed", 1))
    crop = spec.get("clip_crop")   # [x, y, 幅, 高さ]（元の動画のピクセル）で一部だけ切り出す
    vf = (f"crop={crop[2]}:{crop[3]}:{crop[0]}:{crop[1]}," if crop else "")
    vf += (f"setpts=PTS/{speed},fps={FPS},"
          f"scale={bw}:{bh}:force_original_aspect_ratio=decrease,"
          f"scale=trunc(iw/2)*2:trunc(ih/2)*2")
    cmd = [ffmpeg, "-v", "error", "-ss", str(spec.get("clip_start", 0)), "-i", str(scene.path(spec["clip"])),
           "-an", "-vf", vf, "-frames:v", str(n_frames), "-f", "rawvideo", "-pix_fmt", "rgb24", "-"]
    # 出力サイズを知るため、先に1フレームだけ取る
    probe = subprocess.run(cmd[:-1] + ["-frames:v", "1", "-f", "image2pipe", "-vcodec", "png", "-"],
                           capture_output=True)
    if probe.returncode != 0 or not probe.stdout:
        sys.exit(f"画面録画を読めません: {spec['clip']}\n{probe.stderr.decode(errors='ignore')}")
    import io
    fw, fh = Image.open(io.BytesIO(probe.stdout)).size
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE)
    size = fw * fh * 3
    last = None
    for _ in range(n_frames):
        buf = proc.stdout.read(size)
        if len(buf) == size:
            last = Image.frombytes("RGB", (fw, fh), buf)
        yield last
    proc.stdout.close()
    proc.wait()


# ---------------------------------------------------------------- 全体の流れ

def auto_duration(spec, ffmpeg, scene):
    if "duration" in spec:
        return float(spec["duration"])
    if spec.get("clip"):
        speed = float(spec.get("clip_speed", 1))
        length = (clip_seconds(ffmpeg, scene.path(spec["clip"])) - float(spec.get("clip_start", 0))) / speed
        return max(1.5, min(length, float(spec.get("clip_max", 12))))
    n = len(plain(spec.get("text", ""))) + len(spec.get("code", "")) * 0.35
    d = 0.9 + n * 0.11
    if spec.get("style") == "hook":
        d = max(d, 1.8)
    return max(1.5, min(d, 6.0))


def srt_time(sec):
    ms = int(round(sec * 1000))
    return f"{ms // 3600000:02}:{ms // 60000 % 60:02}:{ms // 1000 % 60:02},{ms % 1000:03}"


def build(script_path, out_dir, fonts, ffmpeg, photos=False):
    script_path = Path(script_path)
    cfg = json.loads(script_path.read_text(encoding="utf-8"))
    cfg["_dir"] = script_path.parent
    theme = THEMES.get(cfg.get("theme", "dark"), THEMES["dark"])
    specs = cfg["scenes"]
    scenes = [Scene(s, cfg, fonts, theme, i, len(specs)) for i, s in enumerate(specs)]
    bg = gradient(theme).convert("RGBA")
    name = script_path.stem
    out_dir.mkdir(parents=True, exist_ok=True)

    if photos:
        folder = out_dir / f"{name}_photos"
        folder.mkdir(exist_ok=True)
        for i, sc in enumerate(scenes):
            first = next(clip_frames(ffmpeg, sc, 1)) if sc.spec.get("clip") else None
            sc.frame(bg, first, 0, 1, False).save(folder / f"{i + 1:02}.png")
        print(f"  → {folder}/ に {len(scenes)} 枚")
        return

    durations = [auto_duration(s.spec, ffmpeg, s) for s in scenes]
    total = sum(durations)
    show_bar = cfg.get("progress_bar", True)
    silent = out_dir / f".{name}_video.mp4"
    enc = subprocess.Popen(
        [ffmpeg, "-y", "-v", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
         "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-preset", "medium", "-crf", "19",
         "-pix_fmt", "yuv420p", "-movflags", "+faststart", str(silent)],
        stdin=subprocess.PIPE)

    srt, t0, frame_no = [], 0.0, 0
    total_frames = round(total * FPS)
    for i, (sc, dur) in enumerate(zip(scenes, durations)):
        n = round((t0 + dur) * FPS) - round(t0 * FPS)
        media = clip_frames(ffmpeg, sc, n) if sc.spec.get("clip") else None
        cached = None
        for f in range(n):
            anim = min(1.0, (f + 1) / ANIM_FRAMES) if sc.spec.get("animate", True) else 1.0
            mf = next(media) if media else None
            progress = frame_no / max(1, total_frames - 1)
            if mf is None and anim >= 1 and not show_bar:
                cached = cached or sc.frame(bg, None, 0, 1, False).tobytes()
                enc.stdin.write(cached)
            else:
                enc.stdin.write(sc.frame(bg, mf, progress, anim, show_bar).tobytes())
            frame_no += 1
        if sc.spec.get("text") or sc.spec.get("code"):
            srt.append((t0, t0 + dur, plain(sc.spec.get("text", "")) or sc.spec.get("code", "")))
        t0 += dur
    enc.stdin.close()
    if enc.wait() != 0:
        sys.exit("動画の書き出しに失敗しました")

    out = out_dir / f"{name}.mp4"
    audio = [(cfg[k], k) for k in ("voice", "bgm") if cfg.get(k)]
    if audio:
        cmd = [ffmpeg, "-y", "-v", "error", "-i", str(silent)]
        filters, labels = [], []
        for idx, (p, kind) in enumerate(audio, start=1):
            if kind == "bgm":
                cmd += ["-stream_loop", "-1"]
            cmd += ["-i", str(cfg["_dir"] / p)]
            vol = cfg.get("bgm_volume", 0.15) if kind == "bgm" else cfg.get("voice_volume", 1.0)
            filters.append(f"[{idx}:a]volume={vol}[a{idx}]")
            labels.append(f"[a{idx}]")
        filters.append(f"{''.join(labels)}amix=inputs={len(labels)}:duration=longest:normalize=0,"
                       f"atrim=0:{total:.3f},afade=t=out:st={max(0, total - 0.6):.3f}:d=0.6[aout]")
        cmd += ["-filter_complex", ";".join(filters), "-map", "0:v", "-map", "[aout]",
                "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-t", f"{total:.3f}", str(out)]
        if subprocess.run(cmd).returncode != 0:
            sys.exit("音声の合成に失敗しました")
        silent.unlink()
    else:
        os.replace(silent, out)

    with open(out_dir / f"{name}.srt", "w", encoding="utf-8") as f:
        for n, (a, b, txt) in enumerate(srt, 1):
            f.write(f"{n}\n{srt_time(a)} --> {srt_time(b)}\n{txt}\n\n")
    print(f"  → {out}（{total:.1f}秒 / {len(scenes)}シーン）")


def main():
    ap = argparse.ArgumentParser(description="台本(JSON)から TikTok 用の縦型テロップ動画を作る")
    ap.add_argument("scripts", nargs="+", help="台本のJSONファイル（複数可）")
    ap.add_argument("-o", "--out", default=str(Path(__file__).parent / "out"), help="出力フォルダ")
    ap.add_argument("--photos", action="store_true", help="動画ではなくフォトモード用のPNGを書き出す")
    ap.add_argument("--font", help="使うフォントファイルのパス")
    args = ap.parse_args()

    fonts = Fonts(find_font(args.font))
    ffmpeg = find_ffmpeg()
    print(f"フォント: {fonts.path}")
    for s in args.scripts:
        print(f"作成中: {s}")
        build(s, Path(args.out), fonts, ffmpeg, photos=args.photos)


if __name__ == "__main__":
    main()

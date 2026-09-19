/* ==========================================================
   効果音 & ナレーション（外部音声ファイル不使用）
   - 効果音: Web Audio API でその場合成
   - ナレーション: Web Speech API（ブラウザ標準の音声合成）
   どちらもブラウザの自動再生ポリシーにより、ページを開いただけの
   状態では鳴らず、最初のクリック/タップで有効化される。
   ========================================================== */
window.VideoAudio = (function () {
  "use strict";

  var ctx = null;
  var enabled = true;
  var voices = [];
  var jaVoice = null;

  function ensureCtx() {
    if (!ctx) {
      var AC = window.AudioContext || window.webkitAudioContext;
      if (!AC) return null;
      ctx = new AC();
    }
    return ctx;
  }

  function unlock() {
    var c = ensureCtx();
    if (c && c.state === "suspended") {
      c.resume().catch(function () {});
    }
  }

  function isRunning() {
    return !!ctx && ctx.state === "running";
  }

  // 短いトーン（ピポ音・チャイム等の基本パーツ）
  function tone(freq, dur, opts) {
    if (!enabled || !isRunning()) return;
    opts = opts || {};
    var t0 = ctx.currentTime + (opts.delay || 0);
    var osc = ctx.createOscillator();
    var gain = ctx.createGain();
    osc.type = opts.type || "sine";
    osc.frequency.setValueAtTime(freq, t0);
    if (opts.slideTo) {
      osc.frequency.exponentialRampToValueAtTime(Math.max(opts.slideTo, 1), t0 + dur);
    }
    var peak = opts.gain != null ? opts.gain : 0.18;
    gain.gain.setValueAtTime(0.0001, t0);
    gain.gain.exponentialRampToValueAtTime(peak, t0 + Math.min(0.02, dur / 3));
    gain.gain.exponentialRampToValueAtTime(0.0001, t0 + dur);
    osc.connect(gain).connect(ctx.destination);
    osc.start(t0);
    osc.stop(t0 + dur + 0.03);
  }

  // ノイズバースト（whoosh等）
  function noiseBurst(dur, opts) {
    if (!enabled || !isRunning()) return;
    opts = opts || {};
    var t0 = ctx.currentTime + (opts.delay || 0);
    var size = Math.max(1, Math.floor(ctx.sampleRate * dur));
    var buffer = ctx.createBuffer(1, size, ctx.sampleRate);
    var data = buffer.getChannelData(0);
    for (var i = 0; i < size; i++) {
      data[i] = (Math.random() * 2 - 1) * (1 - i / size);
    }
    var src = ctx.createBufferSource();
    src.buffer = buffer;
    var filter = ctx.createBiquadFilter();
    filter.type = "lowpass";
    filter.frequency.setValueAtTime(opts.freqStart || 5000, t0);
    filter.frequency.exponentialRampToValueAtTime(opts.freqEnd || 350, t0 + dur);
    var gain = ctx.createGain();
    gain.gain.setValueAtTime(opts.gain || 0.1, t0);
    gain.gain.exponentialRampToValueAtTime(0.0001, t0 + dur);
    src.connect(filter).connect(gain).connect(ctx.destination);
    src.start(t0);
  }

  var sfx = {
    punch: function () {
      tone(190, 0.16, { type: "triangle", gain: 0.22, slideTo: 90 });
      noiseBurst(0.14, { gain: 0.09 });
    },
    whoosh: function () {
      noiseBurst(0.32, { freqStart: 6000, freqEnd: 300, gain: 0.07 });
    },
    tick: function () {
      tone(1500, 0.025, { type: "square", gain: 0.045 });
    },
    pop: function (delay) {
      tone(520, 0.09, { type: "sine", gain: 0.16, delay: delay || 0, slideTo: 720 });
    },
    highlight: function () {
      tone(880, 0.12, { type: "sine", gain: 0.15 });
      tone(1320, 0.14, { type: "sine", gain: 0.11, delay: 0.07 });
    },
    sadDip: function () {
      tone(300, 0.24, { type: "sine", gain: 0.14, slideTo: 170 });
    },
    question: function (idx) {
      var freqs = [660, 740, 880];
      tone(freqs[idx] || 700, 0.14, { type: "sine", gain: 0.16 });
    },
    success: function () {
      [523, 659, 784, 988].forEach(function (f, i) {
        tone(f, 0.16, { type: "sine", gain: 0.13, delay: i * 0.09 });
      });
    },
    cta: function () {
      tone(660, 0.12, { type: "sine", gain: 0.17 });
      tone(990, 0.22, { type: "sine", gain: 0.13, delay: 0.1 });
    }
  };

  // ---------------- ナレーション（Web Speech API） ----------------
  function loadVoices() {
    if (!("speechSynthesis" in window)) return;
    voices = window.speechSynthesis.getVoices();
    jaVoice =
      voices.find(function (v) { return /^ja/i.test(v.lang); }) || null;
  }
  if ("speechSynthesis" in window) {
    loadVoices();
    window.speechSynthesis.onvoiceschanged = loadVoices;
  }

  function narrate(text, opts) {
    if (!enabled || !("speechSynthesis" in window)) return;
    opts = opts || {};
    try {
      window.speechSynthesis.cancel();
      var u = new SpeechSynthesisUtterance(text);
      u.lang = "ja-JP";
      if (jaVoice) u.voice = jaVoice;
      u.rate = opts.rate || 1.12;
      u.pitch = opts.pitch || 1.0;
      u.volume = opts.volume != null ? opts.volume : 1.0;
      window.speechSynthesis.speak(u);
    } catch (e) {
      /* 音声合成が使えない環境では無視（字幕表示は継続） */
    }
  }

  function stopNarration() {
    if ("speechSynthesis" in window) {
      try { window.speechSynthesis.cancel(); } catch (e) {}
    }
  }

  function setEnabled(v) {
    enabled = v;
    if (!v) stopNarration();
  }

  return {
    unlock: unlock,
    isUnlocked: isRunning,
    sfx: sfx,
    narrate: narrate,
    stopNarration: stopNarration,
    setEnabled: setEnabled
  };
})();

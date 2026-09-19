(function () {
  "use strict";

  var stage = document.getElementById("stage");
  var progressBar = document.getElementById("progress-bar");

  // シーン開始時刻（ミリ秒）
  var TIMELINE = {
    hook: 0,
    add: 2000,
    before: 5000,
    after: 10000,
    questions: 15000,
    transform: 21000,
    cta: 25000
  };
  var END = 29500;      // CTA表示の最終ホールド
  var LOOP_GAP = 180;   // 次ループへの短いつなぎ（シームレスループ用）
  var LOOP_DURATION = END + LOOP_GAP;

  var timers = [];
  var rafId = null;
  var startTs = null;

  // ---------- スケーリング（1080x1920を画面に収める） ----------
  function scaleStage() {
    var vw = window.innerWidth;
    var vh = window.innerHeight;
    var s = Math.min(vw / 1080, vh / 1920);
    stage.style.transform = "translate(-50%,-50%) scale(" + s + ")";
  }
  stage.style.position = "absolute";
  stage.style.top = "50%";
  stage.style.left = "50%";
  window.addEventListener("resize", scaleStage);
  scaleStage();

  // ---------- タイマーユーティリティ ----------
  function at(ms, fn) {
    timers.push(setTimeout(fn, ms));
  }
  function clearTimers() {
    timers.forEach(function (t) { clearTimeout(t); });
    timers = [];
  }

  function activate(name) {
    var scenes = document.querySelectorAll(".scene");
    for (var i = 0; i < scenes.length; i++) scenes[i].classList.remove("active");
    var el = document.getElementById("scene-" + name);
    if (el) el.classList.add("active");
  }

  function resetAll() {
    document.querySelectorAll(".scene").forEach(function (s) {
      s.classList.remove("active");
    });
    document.querySelectorAll(".typed").forEach(function (t) {
      t.textContent = "";
    });
    document.querySelectorAll(".qa-row").forEach(function (r) {
      r.classList.remove("show-typing", "show-msg");
    });
    document.querySelectorAll(".bubble-user").forEach(function (b) {
      b.classList.remove("typed-done");
    });
  }

  function typeText(el, text, speed, onDone) {
    var i = 0;
    function step() {
      if (!el) return;
      if (i <= text.length) {
        el.textContent = text.slice(0, i);
        if (i > 0 && i % 3 === 0) VideoAudio.sfx.tick();
        i++;
        timers.push(setTimeout(step, speed));
      } else if (onDone) {
        onDone();
      }
    }
    step();
  }

  // 3つの質問をテンポよく表示
  var QUESTION_TEXTS = ["使える時間は？", "初期費用は？", "得意なことは？"];
  function runQuestions() {
    var rows = document.querySelectorAll("#question-body .qa-row");
    var stepGap = 2000;
    rows.forEach(function (row, idx) {
      var t0 = idx * stepGap;
      at(t0, function () { row.classList.add("show-typing"); });
      at(t0 + 550, function () {
        row.classList.remove("show-typing");
        row.classList.add("show-msg");
        VideoAudio.sfx.question(idx);
        VideoAudio.narrate(QUESTION_TEXTS[idx], { rate: 1.15 });
      });
    });
  }

  // ---------- シーンスケジュール ----------
  function scheduleAll() {
    clearTimers();
    resetAll();

    at(TIMELINE.hook, function () {
      activate("hook");
      VideoAudio.sfx.punch();
      VideoAudio.narrate("ChatGPT、普通に質問するのやめて。", { rate: 1.18 });
    });

    at(TIMELINE.add, function () {
      activate("add");
      VideoAudio.sfx.whoosh();
      VideoAudio.narrate("最後に、この一文を足してみて。", { rate: 1.15 });
      at(750, function () { VideoAudio.sfx.highlight(); });
    });

    at(TIMELINE.before, function () {
      activate("before");
      VideoAudio.sfx.whoosh();
      VideoAudio.narrate("副業のアイデアを考えて。これだと、なんか普通な回答に。", { rate: 1.18 });
      var typedEl = document.querySelector("#scene-before .typed");
      var typedBubble = document.querySelector("#scene-before .bubble-user");
      at(550, function () {
        typeText(typedEl, "副業のアイデアを考えて", 62, function () {
          if (typedBubble) typedBubble.classList.add("typed-done");
        });
      });
      at(1500, function () { VideoAudio.sfx.pop(); });
      at(2150, function () { VideoAudio.sfx.sadDip(); });
    });

    at(TIMELINE.after, function () {
      activate("after");
      VideoAudio.sfx.whoosh();
      at(350, function () { VideoAudio.sfx.pop(); });
      at(1050, function () {
        VideoAudio.sfx.highlight();
        VideoAudio.narrate("回答する前に、不足している情報があれば質問してください。", { rate: 1.12 });
      });
    });

    at(TIMELINE.questions, function () {
      activate("questions");
      VideoAudio.sfx.whoosh();
      runQuestions();
    });

    at(TIMELINE.transform, function () {
      activate("transform");
      VideoAudio.sfx.whoosh();
      VideoAudio.narrate("自分に合った回答に変わります。", { rate: 1.12 });
      at(450, function () { VideoAudio.sfx.success(); });
    });

    at(TIMELINE.cta, function () {
      activate("cta");
      VideoAudio.sfx.whoosh();
      VideoAudio.narrate("この一文、保存して使ってみてください。", { rate: 1.1 });
      at(50, function () { VideoAudio.sfx.cta(); });
    });

    at(END, function () {
      var cta = document.getElementById("scene-cta");
      if (cta) cta.classList.remove("active");
      VideoAudio.stopNarration();
    });
  }

  // ---------- 進捗バー & ループ ----------
  var debugEl = null;
  if (location.search.indexOf("debug") !== -1) {
    debugEl = document.createElement("div");
    debugEl.id = "debug";
    document.body.appendChild(debugEl);
  }

  function currentSceneName(ms) {
    var names = Object.keys(TIMELINE);
    var current = names[0];
    for (var i = 0; i < names.length; i++) {
      if (ms >= TIMELINE[names[i]]) current = names[i];
    }
    if (ms >= END) current = "(hold)";
    return current;
  }

  function tick(ts) {
    if (startTs === null) startTs = ts;
    var elapsed = ts - startTs;
    var pct = Math.min(100, (elapsed / END) * 100);
    progressBar.style.width = pct + "%";

    if (debugEl) {
      debugEl.textContent =
        "t=" + Math.round(elapsed) + "ms  scene=" + currentSceneName(elapsed);
    }

    if (elapsed < LOOP_DURATION) {
      rafId = requestAnimationFrame(tick);
    } else {
      startLoop();
    }
  }

  function startLoop() {
    clearTimers();
    resetAll();
    VideoAudio.stopNarration();
    startTs = null;
    scheduleAll();
    if (rafId) cancelAnimationFrame(rafId);
    rafId = requestAnimationFrame(tick);
  }

  // ---------- 音声の有効化（ブラウザの自動再生ポリシー対応） ----------
  // 効果音・ナレーションはユーザー操作なしには鳴らせないため、
  // 最初のクリック/タップで有効化し、頭から再生し直して音声と同期させる。
  // 2回目以降のクリックはQA用の即リスタートとして機能する。
  var audioHint = document.getElementById("audio-hint");
  function handleUserGesture() {
    VideoAudio.unlock();
    if (audioHint) audioHint.classList.add("hidden");
    startLoop();
  }
  document.addEventListener("click", handleUserGesture);
  document.addEventListener("touchstart", handleUserGesture, { passive: true });
  window.addEventListener("keydown", function (e) {
    if (e.key === "r" || e.key === "R") handleUserGesture();
  });

  startLoop();
})();

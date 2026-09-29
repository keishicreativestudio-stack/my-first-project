const POSITIONS = {
  1: ["今日のメッセージ"],
  3: ["過去", "現在", "未来"],
};

const $ = (sel) => document.querySelector(sel);
const drawBtn = $("#draw");
const againBtn = $("#again");
const table = $("#table");
const result = $("#result");
const hint = $("#hint");

let drawn = [];
let revealed = 0;

function shuffle(arr) {
  const a = [...arr];
  for (let i = a.length - 1; i > 0; i--) {
    const j = Math.floor(Math.random() * (i + 1));
    [a[i], a[j]] = [a[j], a[i]];
  }
  return a;
}

function draw() {
  const count = Number(document.querySelector('input[name="spread"]:checked').value);
  const labels = POSITIONS[count];
  drawn = shuffle(CARDS).slice(0, count).map((card, i) => ({
    card,
    reversed: Math.random() < 0.5,
    label: labels[i],
  }));
  revealed = 0;

  table.innerHTML = "";
  result.innerHTML = "";
  result.hidden = true;
  againBtn.hidden = true;
  drawBtn.disabled = true;
  hint.hidden = false;

  drawn.forEach((d, i) => table.appendChild(createSlot(d, i)));
}

function createSlot(d, i) {
  const slot = document.createElement("div");
  slot.className = "slot";

  const label = document.createElement("div");
  label.className = "slot-label";
  label.textContent = d.label;

  const btn = document.createElement("button");
  btn.className = "card";
  btn.style.animationDelay = `${i * 0.15}s`;
  btn.setAttribute("aria-label", `${d.label}のカードをめくる`);
  btn.innerHTML = `
    <div class="card-inner">
      <div class="face back">✦</div>
      <div class="face front${d.reversed ? " reversed" : ""}">
        <div class="num">${ROMAN[d.card.num]}</div>
        <div class="art">
          <div class="symbol">${d.card.symbol}</div>
        </div>
        <div>
          <div class="name">${d.card.name}</div>
          <div class="en">${d.card.en}</div>
        </div>
      </div>
    </div>`;
  btn.addEventListener("click", () => reveal(btn, i), { once: true });

  slot.append(label, btn);
  return slot;
}

function reveal(btn, i) {
  btn.classList.add("flipped");
  btn.disabled = true;
  revealed++;
  if (revealed === drawn.length) {
    hint.hidden = true;
    setTimeout(showResult, 700);
  }
}

function showResult() {
  result.innerHTML = drawn.map(({ card, reversed, label }) => `
    <article class="reading">
      <div class="pos">${label}</div>
      <h2>${card.name}
        <span class="tag ${reversed ? "rev" : "up"}">${reversed ? "逆位置" : "正位置"}</span>
      </h2>
      <div class="kw">${card.keywords}</div>
      <p>${reversed ? card.rev : card.up}</p>
    </article>`).join("");
  result.hidden = false;
  againBtn.hidden = false;
  drawBtn.disabled = false;
  result.scrollIntoView({ behavior: "smooth", block: "start" });
}

function reset() {
  table.innerHTML = "";
  result.hidden = true;
  againBtn.hidden = true;
  hint.hidden = true;
  drawBtn.disabled = false;
  window.scrollTo({ top: 0, behavior: "smooth" });
}

drawBtn.addEventListener("click", draw);
againBtn.addEventListener("click", reset);

// ---- 星空の背景 ----
(function stars() {
  const canvas = $("#stars");
  const ctx = canvas.getContext("2d");
  let stars = [];

  function resize() {
    canvas.width = innerWidth * devicePixelRatio;
    canvas.height = innerHeight * devicePixelRatio;
    const n = Math.floor((innerWidth * innerHeight) / 5000);
    stars = Array.from({ length: n }, () => ({
      x: Math.random() * canvas.width,
      y: Math.random() * canvas.height,
      r: (Math.random() * 1.2 + 0.3) * devicePixelRatio,
      phase: Math.random() * Math.PI * 2,
      speed: Math.random() * 0.02 + 0.005,
    }));
  }

  function frame() {
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    for (const s of stars) {
      s.phase += s.speed;
      ctx.globalAlpha = 0.35 + 0.65 * Math.abs(Math.sin(s.phase));
      ctx.fillStyle = "#fff7e0";
      ctx.beginPath();
      ctx.arc(s.x, s.y, s.r, 0, Math.PI * 2);
      ctx.fill();
    }
    requestAnimationFrame(frame);
  }

  addEventListener("resize", resize);
  resize();
  frame();
})();

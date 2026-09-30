/* tapered strand: used for hair tufts and fur */
function leaf(g, x, y, ang, len, w, curl) {
  const nx = -Math.sin(ang), ny = Math.cos(ang);
  const ta = ang + curl, tx = x + Math.cos(ta) * len, ty = y + Math.sin(ta) * len;
  const mx = x + Math.cos(ang + curl * .4) * len * .55, my = y + Math.sin(ang + curl * .4) * len * .55;
  g.moveTo(x + nx * w / 2, y + ny * w / 2);
  g.quadraticCurveTo(mx + nx * w * .35, my + ny * w * .35, tx, ty);
  g.quadraticCurveTo(mx - nx * w * .15, my - ny * w * .15, x - nx * w / 2, y - ny * w / 2);
  g.closePath();
}
/* fill every sub-shape on its own so overlaps never punch holes */
function solid(g, draw) { g.beginPath(); draw(); g.fill(); }
function defaultSilhouette(g) {
  const hx = 118, hy = 130, rx = 92, ry = 84;
  const L = (...a) => solid(g, () => leaf(g, ...a));
  solid(g, () => g.ellipse(hx, hy, rx, ry, 0, 0, Math.PI * 2));
  /* hair: overlapping rounded clumps give a soft mop outline */
  const C = (x, y, r) => solid(g, () => g.arc(x, y, r, 0, Math.PI * 2));
  for (let i = 0; i <= 18; i++) {
    const a = Math.PI * (.93 + i / 18 * 1.14);
    const r = 24 + hash(i + 11) * 8;
    const x = hx + Math.cos(a) * (rx - r * .55), y = hy + Math.sin(a) * (ry - r * .5);
    C(x, y, r);
    /* each clump ends in a tip that swirls away from the centre line */
    const dir = Math.cos(a) >= 0 ? 1 : -1;
    L(x + Math.cos(a) * r * .75, y + Math.sin(a) * r * .75, a + dir * .25, 22 + hash(i + 90) * 14, 16, dir * (.7 + hash(i + 95) * .4));
  }
  /* pointed strands where the mop meets the face line, curling outward */
  const wisp = [[-1, 150, 2.5, 34, 20, -.7], [-1, 176, 2.1, 30, 18, -.6], [-1, 118, 3.0, 26, 18, -.5],
                [1, 150, .64, 34, 20, .7], [1, 176, 1.04, 30, 18, .6], [1, 118, .14, 26, 18, .5]];
  for (const [sd, y, ang, len, w, curl] of wisp) L(hx + sd * (rx - 14), y, ang, len, w, curl);
  /* flicks on the crown */
  L(126, 60, -1.75, 34, 9, 1.0); L(100, 62, -1.55, 22, 8, -.9); L(150, 70, -1.2, 22, 8, .8);

  /* hoodie body, hands tucked in the front pocket */
  solid(g, () => {
    g.moveTo(74, 202); g.bezierCurveTo(92, 192, 146, 192, 164, 202);
    g.bezierCurveTo(184, 214, 190, 252, 192, 300); g.quadraticCurveTo(193, 318, 184, 322);
    g.lineTo(178, 336); g.lineTo(58, 336); g.lineTo(52, 322); g.quadraticCurveTo(43, 318, 44, 300);
    g.bezierCurveTo(46, 252, 54, 214, 74, 202); g.closePath();
  });
  solid(g, () => { g.moveTo(64, 330); g.lineTo(113, 330); g.lineTo(111, 414); g.lineTo(70, 414); g.closePath(); });
  solid(g, () => { g.moveTo(123, 330); g.lineTo(172, 330); g.lineTo(166, 414); g.lineTo(125, 414); g.closePath(); });
  solid(g, () => { g.moveTo(66, 410); g.bezierCurveTo(60, 424, 58, 436, 70, 437); g.lineTo(114, 437); g.bezierCurveTo(118, 426, 116, 414, 112, 410); g.closePath(); });
  solid(g, () => { g.moveTo(124, 410); g.bezierCurveTo(120, 424, 120, 436, 128, 437); g.lineTo(172, 437); g.bezierCurveTo(180, 432, 172, 414, 166, 410); g.closePath(); });

  /* fluffy cat, sitting, facing the viewer */
  const cx = 256, cy = 378, crx = 44, cry = 60;
  solid(g, () => g.ellipse(cx, cy, crx, cry, 0, 0, Math.PI * 2));
  solid(g, () => g.ellipse(cx, 302, 34, 30, 0, 0, Math.PI * 2));
  solid(g, () => { g.moveTo(226, 292); g.lineTo(226, 262); g.lineTo(250, 280); g.closePath(); });
  solid(g, () => { g.moveTo(286, 292); g.lineTo(288, 262); g.lineTo(262, 280); g.closePath(); });
  /* fur: soft bumps round the body, a few tufts poking out */
  for (let i = 0; i < 22; i++) {
    const a = (i / 22) * Math.PI * 2, x = cx + Math.cos(a) * crx * .82, y = cy + Math.sin(a) * cry * .82;
    if (y > 426) continue;
    C(x, y, 10 + hash(i + 300) * 5);
    if (i % 3 === 0 && y < 410) L(cx + Math.cos(a) * crx, cy + Math.sin(a) * cry, a, 8 + hash(i + 700) * 6, 8, (hash(i + 200) - .5) * .9);
  }
  for (let i = 0; i < 7; i++) {                    /* cheek ruff */
    const a = Math.PI * (.05 + i / 6 * .9);
    C(cx + Math.cos(a) * 28, 308 + Math.sin(a) * 20, 9);
  }
  solid(g, () => g.rect(cx - 34, 420, 68, 17));
  solid(g, () => { g.moveTo(290, 424); g.bezierCurveTo(318, 414, 320, 384, 306, 366); g.bezierCurveTo(300, 360, 293, 366, 298, 373); g.bezierCurveTo(308, 392, 302, 410, 276, 420); g.closePath(); });
}

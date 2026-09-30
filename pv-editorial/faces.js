function stickerFace(g, cx, cy, r, col, expr) {
  g.save();
  g.fillStyle = '#fff'; g.beginPath(); g.ellipse(cx, cy, r * 1.14, r * 1.06, 0, 0, 7); g.fill();
  g.fillStyle = col; g.beginPath(); g.ellipse(cx, cy, r, r * .92, 0, 0, 7); g.fill();
  g.beginPath(); g.moveTo(cx - r * .8, cy - r * .5); g.lineTo(cx - r * .62, cy - r * 1.12); g.lineTo(cx - r * .2, cy - r * .82); g.fill();
  g.beginPath(); g.moveTo(cx + r * .8, cy - r * .5); g.lineTo(cx + r * .62, cy - r * 1.12); g.lineTo(cx + r * .2, cy - r * .82); g.fill();
  g.fillStyle = '#1b1b24'; g.strokeStyle = '#1b1b24'; g.lineWidth = r * .09; g.lineCap = 'round';
  const ey = cy - r * .08, ex = r * .36;
  if (expr === 4) { for (const sx of [-1, 1]) { g.beginPath(); g.moveTo(cx + sx * ex - r * .13, ey); g.lineTo(cx + sx * ex + r * .13, ey); g.stroke(); } }
  else if (expr === 1) { for (const sx of [-1, 1]) { g.beginPath(); g.arc(cx + sx * ex, ey + r * .05, r * .13, Math.PI * 1.1, Math.PI * 1.9); g.stroke(); } }
  else for (const sx of [-1, 1]) { g.beginPath(); g.arc(cx + sx * ex, ey, r * .1, 0, 7); g.fill(); }
  g.fillStyle = 'rgba(255,90,120,.45)'; for (const sx of [-1, 1]) { g.beginPath(); g.ellipse(cx + sx * r * .58, cy + r * .2, r * .15, r * .09, 0, 0, 7); g.fill(); }
  g.beginPath();
  if (expr === 3) { g.arc(cx, cy + r * .2, r * .2, 0, Math.PI); g.fillStyle = '#1b1b24'; g.fill(); }
  else if (expr === 2) { g.moveTo(cx - r * .12, cy + r * .26); g.lineTo(cx + r * .12, cy + r * .26); g.stroke(); }
  else { g.arc(cx, cy + r * .16, r * .14, .15 * Math.PI, .85 * Math.PI); g.stroke(); }
  g.restore();
}
function stickerText(g, s, x, y, px) {
  g.save(); g.font = font(900, px); g.textAlign = 'center'; g.lineJoin = 'round';
  g.strokeStyle = '#fff'; g.lineWidth = px * .32; g.strokeText(s, x, y);
  g.fillStyle = '#1b1b24'; g.fillText(s, x, y); g.restore();
}

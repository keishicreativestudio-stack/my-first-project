// usage: node snap.js out_prefix t1 t2 ...   |  node snap.js --frames dir
const fs=require('fs');
const { chromium } = require(require('child_process').execSync('npm root -g').toString().trim() + '/playwright');
(async () => {
  const args=process.argv.slice(2);
  const frames = args[0]==='--frames';
  const W = frames ? 1920 : 1280;
  const b = await chromium.launch();
  const p = await b.newPage({ viewport: { width: W, height: Math.round(W*9/16)+200 } });
  const errs=[]; p.on('pageerror', e=>errs.push(e.message)); p.on('console', m=>{ if(m.type()==='error') errs.push(m.text()); });
  await p.goto('file://' + process.cwd() + '/lab/index.html');
  await p.addStyleTag({ content: fs.readFileSync('fonts.css','utf8') });
  await p.addStyleTag({ content: 'body{padding:0!important}.wrap{max-width:none;gap:0}header.top{display:none}.screen{border-radius:0}' });
  await p.evaluate(async () => { await document.fonts.load('700 92px Quicksand','a'); await document.fonts.load('300 92px Quicksand','a'); await document.fonts.load('700 27px "M PLUS Rounded 1c"','あ'); });
  await p.waitForTimeout(1300);
  await p.evaluate(() => { const bt=document.getElementById('play'); if (bt.textContent.includes('一時停止')) bt.click(); });
  const el = await p.$('#cv');
  if (frames) {
    const dir=args[1]; fs.mkdirSync(dir,{recursive:true});
    const n = await p.evaluate(()=>Math.round(DUR*FPS));
    for (let i=0;i<n;i++){ await p.evaluate(t=>renderAt(t), i/30); await el.screenshot({ path: `${dir}/${String(i).padStart(4,'0')}.png` }); }
  } else {
    const pre=args[0];
    for (const t of args.slice(1)) { await p.evaluate(t=>renderAt(t), +t); await el.screenshot({ path: `${pre}_${t}.png` }); }
  }
  if (errs.length) console.log('ERRORS', errs);
  await b.close();
})();

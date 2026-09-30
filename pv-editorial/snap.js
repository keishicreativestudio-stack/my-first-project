// node snap.js prefix t1 t2 ... | node snap.js --frames dir
const fs=require('fs');
const { chromium } = require(require('child_process').execSync('npm root -g').toString().trim() + '/playwright');
(async () => {
  const args=process.argv.slice(2), frames=args[0]==='--frames', W=frames?1080:540;
  const b=await chromium.launch(); const p=await b.newPage({viewport:{width:W+40,height:Math.round(W*16/9)+40}});
  const errs=[]; p.on('pageerror',e=>errs.push(e.message));
  await p.goto('file://'+process.cwd()+'/index.html');
  await p.addStyleTag({content:fs.readFileSync('fonts.css','utf8')});
  await p.addStyleTag({content:`body{padding:0!important}.wrap{display:block!important;max-width:none}.side{display:none!important}.screen{width:${W}px!important;max-height:none;border-radius:0}`});
  await p.waitForFunction(()=>window.__ready===true);
  await p.evaluate(async()=>{ await document.fonts.ready; build(); resize(); });
  await p.waitForTimeout(1400);
  await p.evaluate(()=>{ if (playing) setPlaying(false); });
  fs.writeFileSync('cues.json', JSON.stringify(await p.evaluate(()=>CUES)));
  const save=async (t,path)=>{ const d=await p.evaluate(t=>{renderAt(t);return document.getElementById('cv').toDataURL('image/png');},t); fs.writeFileSync(path,Buffer.from(d.split(',')[1],'base64')); };
  if(frames){ fs.mkdirSync(args[1],{recursive:true}); const n=await p.evaluate(()=>Math.round(DUR*FPS)); const a0=+(args[2]||0), a1=+(args[3]||n); for(let i=a0;i<a1;i++) await save(i/30,`${args[1]}/${String(i).padStart(4,'0')}.png`); }
  else for(const t of args.slice(1)) await save(+t,`${args[0]}_${t}.png`);
  const sz=await p.evaluate(()=>[cv.width,cv.height]); console.log('canvas',sz.join('x'));
  if(errs.length) console.log('ERRORS',errs);
  await b.close();
})();

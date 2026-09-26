// AIチャレンジ365 の見出し画像を書き出す
// 使い方: node make.js 10        （episodes.json の "10" を使う）
//        node make.js 10 11 12  （複数の回をまとめて）
// no を指定すると号数を上書き（案の比較用に "9a" などのキーを使うとき）
// title の書き方: 改行は \n、下線で強調したい部分は [[ ]] で囲む
const fs=require('fs'),path=require('path');
const {chromium}=require('/opt/node22/lib/node_modules/playwright');
const esc=s=>s.replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');
const eps=JSON.parse(fs.readFileSync(path.join(__dirname,'episodes.json'),'utf8'));
const tpl=fs.readFileSync(path.join(__dirname,'template.html'),'utf8');
const days=process.argv.slice(2);
if(!days.length){console.error('回の番号を指定してください（例: node make.js 10）');process.exit(1);}
(async()=>{
  const b=await chromium.launch();
  for(const d of days){
    const e=eps[d]; if(!e){console.error(`episodes.json に "${d}" がありません`);continue;}
    const html=tpl.replace('{{no}}',esc(String(e.no??d))).replace('{{kicker}}',esc(e.kicker))
      .replace('{{title}}',esc(e.title).replace(/\[\[(.+?)\]\]/g,'<u>$1</u>').replace(/\n/g,'<br>'))
      .replace('{{foot}}',e.foot.map(f=>`<span>${esc(f)}</span>`).join('<span>・</span>'));
    const tmp=path.join(__dirname,`.render_${d}.html`);fs.writeFileSync(tmp,html);
    for(const [s,size] of [[1,'1280x670'],[1.5,'1920x1005']]){
      const p=await b.newPage({viewport:{width:1280,height:670},deviceScaleFactor:s});
      await p.goto('file://'+tmp,{waitUntil:'networkidle'});await p.evaluate(()=>document.fonts.ready);
      const out=path.join(__dirname,'out',`ai365_day${d}_${size}.png`);fs.mkdirSync(path.dirname(out),{recursive:true});
      await p.screenshot({path:out});await p.close();console.log(out);
    }
    fs.unlinkSync(tmp);
  }
  await b.close();
})();

// 使い方: node render.js  → 各テンプレートを 1280×670 と 1920×1005 で書き出す
const {chromium}=require('/opt/node22/lib/node_modules/playwright');
const jobs=[['template.html','day10_a'],['template_b.html','day10_b'],['template_c.html','day10_c']];
(async()=>{const b=await chromium.launch();
for(const [tpl,out] of jobs)for(const [s,size] of [[1,'1280x670'],[1.5,'1920x1005']]){
const p=await b.newPage({viewport:{width:1280,height:670},deviceScaleFactor:s});
await p.goto('file://'+__dirname+'/'+tpl,{waitUntil:'networkidle'});await p.evaluate(()=>document.fonts.ready);
await p.screenshot({path:`${__dirname}/${out}_${size}.png`});await p.close();}
await b.close();})();

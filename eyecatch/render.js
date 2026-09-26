const {chromium}=require('/opt/node22/lib/node_modules/playwright');
(async()=>{const b=await chromium.launch();
for(const [s,n] of [[1,'day10_1280x670.png'],[1.5,'day10_1920x1005.png']]){
const p=await b.newPage({viewport:{width:1280,height:670},deviceScaleFactor:s});
await p.goto('file://'+__dirname+'/template.html',{waitUntil:'networkidle'});await p.evaluate(()=>document.fonts.ready);await p.waitForTimeout(800);
await p.screenshot({path:__dirname+'/'+n});await p.close();}
await b.close();})();

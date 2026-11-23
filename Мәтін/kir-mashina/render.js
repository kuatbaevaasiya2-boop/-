// node render.js data.json frames "t1,t2" outdir | node render.js data.json video > stdout
const {chromium}=require('playwright');const fs=require('fs');const path=require('path');
(async()=>{
 const [,,dataF,mode,arg,out]=process.argv; const data=JSON.parse(fs.readFileSync(dataF,'utf8'));
 const b=await chromium.launch(); const p=await b.newPage({viewport:{width:360,height:640},deviceScaleFactor:3});
 await p.goto('file://'+path.join(__dirname,'page.html'));
 await p.evaluate(async()=>{for(const f of ['800 20px MS','italic 900 20px MS']) await document.fonts.load(f,'Aaәғқңөұүһі'); await document.fonts.load('20px "Noto Color Emoji"','😅'); await document.fonts.ready;});
 await p.evaluate(d=>window.setup(d),data); await p.waitForTimeout(200);
 if(mode==='frames'){ let i=0; for(const t of arg.split(',').map(Number)){ await p.evaluate(t=>window.draw(t),t);
   await p.screenshot({path:path.join(out,`f${String(i++).padStart(2,'0')}.jpg`),type:'jpeg',quality:92}); } }
 else if(mode==='cover'){ await p.evaluate(t=>window.draw(t),Number(arg)); await p.evaluate(()=>{
   document.querySelector('#bub').style.opacity=0; document.querySelector('#who').style.opacity=0;
   const s=document.querySelector('#title span'); s.innerHTML='Мінезіңді<br><b style="color:#E5322D;font-style:italic;font-weight:900">магазинде</b> көрсетесің! 😤';
   s.style.font='800 28px/1.15 MS, "Noto Color Emoji"'; s.style.padding='14px 18px'; document.querySelector('#wm').style.top='222px';
   document.querySelector('#title').style.top='60px';});
   await p.screenshot({path:out,type:'jpeg',quality:95}); }
 else { const n=Math.ceil(data.dur*data.fps);
   for(let i=0;i<n;i++){ await p.evaluate(t=>window.draw(t),i/data.fps); const buf=await p.screenshot({type:'jpeg',quality:93});
     if(!process.stdout.write(buf)) await new Promise(r=>process.stdout.once('drain',r));
     if(i%90===0) process.stderr.write(`кадр ${i}/${n}\n`); } }
 await b.close();
})();

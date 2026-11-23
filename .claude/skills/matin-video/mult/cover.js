// node cover.js data.json out.jpg "мәтін *қызыл* мәтін" pose
const {chromium}=require('playwright');const fs=require('fs');const path=require('path');
(async()=>{
 const [,,dataF,out,title,pose,lab]=process.argv; const data=JSON.parse(fs.readFileSync(dataF,'utf8'));
 const b=await chromium.launch(); const p=await b.newPage({viewport:{width:360,height:640},deviceScaleFactor:3});
 await p.goto('file://'+path.join(__dirname,data.page||'page.html'));
 await p.evaluate(async()=>{for(const f of ['800 21px MS','italic 900 21px MS']) await document.fonts.load(f,'Aaәғқңөұүһі');});
 data.scenes[0].pose=pose||'thumb';
 data.env=data.env.map(()=>0.45); await p.evaluate(d=>window.setup(d),data); await p.evaluate(()=>window.draw(4.9)); await p.evaluate(()=>{for(const q of ['#dots','#prog']){const e=document.querySelector(q); if(e) e.style.display='none';}});
 await p.evaluate(({title,lab})=>{
  const s=document.querySelector('#scenes .scene'); s.querySelector('.hl').remove(); s.querySelector('.lab').textContent=lab||'// телефоннан монтаж · 45 сек';
  const html=title.replace(/\*([^*]+)\*/g,'<b style="color:#E5322D;font-style:italic;font-weight:900">$1</b>');
  const h=document.createElement('div'); h.innerHTML=html;
  h.style.cssText='position:absolute;left:18px;right:18px;top:78px;font:800 37px/1.12 MS;letter-spacing:-.6px;color:#1d1d2b';
  s.appendChild(h);
  const c=s.querySelector('.cards'); c.style.transform='translateY('+(document.querySelector('#a_p')?54:76)+'px) scale(.92)'; const ap=s.querySelector('#a_p'); if(ap) ap.style.display='none'; c.style.transformOrigin='50% 0';
  const q=s.querySelector('#h_q'); if(q) q.style.display='none';
 },{title,lab});
 await p.screenshot({path:out,type:'jpeg',quality:95}); await b.close();
})();

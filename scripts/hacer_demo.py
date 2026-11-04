"""Graba el video de demo desde final.html. Comprueba en pantalla las cifras que dicen los subtitulos y falla si no coinciden.
Uso: python scripts/hacer_demo.py <carpeta>; espera <carpeta>/w2/final.html, y escribe <carpeta>/v2/demo.mp4. Necesita Playwright, Pillow y ffmpeg.
"""
import io,json,subprocess,sys,re
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
from playwright.sync_api import sync_playwright
S=Path(sys.argv[1]);URL='file://'+str(S/'w2/final.html');COVER=str(Path(__file__).resolve().parents[1]/'renders'/'luna_portada_v5_sitio456.png')
OUT=S/'v2/demo.mp4';FPS=24;W,H=1280,720;BAND=107
FONT=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',29)
def sub(img,text):
    c=Image.new('RGB',(W,H),(4,8,14));c.paste(img,(0,0));d=ImageDraw.Draw(c)
    words=text.split();lines=[];cur=''
    for w in words:
        if d.textlength((cur+' '+w).strip(),font=FONT)>1160:lines.append(cur);cur=w
        else:cur=(cur+' '+w).strip()
    lines.append(cur);y=H-BAND+(BAND-len(lines)*38)//2
    for l in lines:
        d.text(((W-d.textlength(l,font=FONT))/2,y),l,font=FONT,fill=(255,255,255));y+=38
    return c
frames=[];log={}
def hold(img,text,sec):
    f=sub(img,text);frames.extend([f]*round(sec*FPS))
def shot(pg):return Image.open(io.BytesIO(pg.screenshot())).convert('RGB').resize((W,H-BAND))
def topof(pg,sel,off=8):
    pg.evaluate(f"(()=>{{const e=document.querySelector('{sel}');window.scrollTo(0,e.getBoundingClientRect().top+scrollY-{off});}})()");pg.wait_for_timeout(120)
SUB={'a':"The launch slips. Does the mission still work?",
'b':"21 June 2030, site 456: both visible, but the Sun sets in 4 hours.",
'c':"Sun and Earth against the real terrain horizon, hour by hour.",
'd':"14-day mission arriving 21 June: 4 percent of the time with both.",
'e':"Arrive 7 August instead: 73 percent.",
'f':"Move 100 m: site 456 stays at 20 to 22 percent Sun.",
'g':"Bright site 14 swings from 33 to 58, unconfirmed at pixel scale.",
'h':"Checked against LROC, PGDA and 5 dated 2009 images. Limits are published.",
'i':"For comparing, not certifying."}
with sync_playwright() as p:
    b=p.chromium.launch();c=b.new_context(viewport={'width':960,'height':460},device_scale_factor=4/3,locale='en-US',color_scheme='dark');pg=c.new_page();errs=[];pg.on('pageerror',lambda e:errs.append(str(e)))
    pg.goto(URL);pg.wait_for_selector('#app:not([hidden])');pg.wait_for_timeout(1500)
    if pg.inner_text('#lang')!='ES':pg.click('#lang')
    assert pg.inner_text('#lang')=='ES'
    # portada
    im=Image.open(COVER).convert('RGB');r=min(W/im.width,(H-BAND)/im.height);im2=im.resize((round(im.width*r),round(im.height*r)));cv=Image.new('RGB',(W,H-BAND),(4,8,14));cv.paste(im2,((W-im2.width)//2,0));hold(cv,SUB['a'],3)
    # respuesta
    txt=pg.inner_text('#ans-text');sd=pg.inner_text('#ans-sd');assert 'Ends in 4 h' in sd and pg.inner_text('#ans-at').startswith('2030-06-21 11:00') and txt.startswith('There is Sun for power and line of sight');log['ans']=(txt,sd,pg.inner_text('#ans-td'))
    topof(pg,'#answer');hold(shot(pg),SUB['b'],4.5)
    # panorama en movimiento
    pg.click('.chip[data-id="14"]');pg.click('.chip[data-id="1358"]');pg.wait_for_timeout(200);assert pg.evaluate('S.sel')==['456']
    topof(pg,'.card');st=pg.evaluate('S.idx');step=6
    n=42;st0=pg.evaluate('S.idx')
    for k in range(n):
        pg.evaluate(f'setIdx({st0}+{k}*{step},true)');f=sub(shot(pg),SUB['c']);frames.extend([f,f])
    pg.evaluate(f'setIdx({st0},true)')
    # calendario
    topof(pg,'#cal-meta',6);assert pg.evaluate('[S.calSite,S.cal.year,S.cal.day,S.cal.len]')==['456',2030,171,14]
    r1=pg.inner_text('#cal-read');m=pg.inner_text('#cal-max');assert 'Arrival 2030-06-21, 14 days' in r1 and 'both 4 %' in r1 and 'arrival 2030-08-07, 73 %' in m;log['cal']=(r1,m)
    def ring():pg.evaluate("""(()=>{let e=document.getElementById('vring');if(!e){e=document.createElement('div');e.id='vring';e.style.cssText='position:absolute;border:3px solid #fff;border-radius:50%;width:34px;height:34px;pointer-events:none;box-shadow:0 0 0 2px #000';document.body.appendChild(e);}const c=document.querySelector('#cal-cv'),g=c._g,r=c.getBoundingClientRect(),x=r.left+scrollX+g.pl+(S.cal.day+.5)/g.days*g.w,y=r.top+scrollY+g.pt+(28-S.cal.len+.5)/28*g.h;e.style.left=(x-17)+'px';e.style.top=(y-17)+'px';})()""");pg.wait_for_timeout(60)
    ring();hold(shot(pg),SUB['d'],3.5)
    d=pg.evaluate('Math.round((Date.UTC(2030,7,7)-Date.UTC(2030,0,1))/864e5)');pg.evaluate(f'(()=>{{S.cal.day={d};renderCal();}})()');ring();r2=pg.inner_text('#cal-read');assert 'Arrival 2030-08-07, 14 days' in r2 and 'both 73 %' in r2;log['cal2']=r2;hold(shot(pg),SUB['e'],2.5)
    pg.evaluate("document.getElementById('vring').remove()")
    # mapa de calor
    topof(pg,'#h-stat',6);v=pg.eval_on_selector_all('#h-stat .v','e=>e.map(x=>x.textContent)');assert v==['20','21','22'],v;hold(shot(pg),SUB['f'],3)
    pg.select_option('#h-site','14');pg.wait_for_timeout(100);v=pg.eval_on_selector_all('#h-stat .v','e=>e.map(x=>x.textContent)');assert v==['33','49','58'],v;hold(shot(pg),SUB['g'],3.5)
    # validacion: una sola columna para que el texto se lea; el contenido no cambia
    pg.add_style_tag(content='#about .two{grid-template-columns:1fr!important}#about .two>.box:first-child{display:none}')
    pg.wait_for_timeout(100)
    pg.evaluate("(()=>{const e=[...document.querySelectorAll('#valid li')].find(x=>x.textContent.startsWith('Time and direction'));window.scrollTo(0,e.getBoundingClientRect().top+scrollY-10);})()");pg.wait_for_timeout(100);t=pg.inner_text('#valid');assert '0.737' in t;hold(shot(pg),SUB['h'],3.5)
    topof(pg,'#limits',42);t=pg.inner_text('#limits');assert '5 dates in 2009' in t and 'only Site04' in t and 'does not validate the 2026–2045' in t and 'more lit points' in t and 'below 0.5' in t;hold(shot(pg),SUB['i'],3)
    assert not errs,errs;b.close()
total=len(frames);print('frames',total,total/FPS)
need=30*FPS
assert total==need,total
if total<need:frames.extend([frames[-1]]*(need-total))
frames=frames[:need]
pr=subprocess.Popen(['ffmpeg','-y','-v','error','-f','rawvideo','-pix_fmt','rgb24','-s',f'{W}x{H}','-r',str(FPS),'-i','-','-c:v','libx264','-crf','20','-preset','medium','-pix_fmt','yuv420p','-movflags','+faststart',str(OUT)],stdin=subprocess.PIPE)
last=None;raw=None
for f in frames:
    if f is not last:raw=f.tobytes();last=f
    pr.stdin.write(raw)
pr.stdin.close();pr.wait()
print(json.dumps(log,ensure_ascii=False)[:600]);print('palabras',sum(len(v.split()) for v in SUB.values()))
json.dump(SUB,open(S/'v2/subs.json','w'))

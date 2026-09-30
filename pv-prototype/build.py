import base64
import sys
import glob,json,os
s=open('src.html').read().replace('/*SIL*/',open('sil.js').read())
groups={'posters':'cyber_poster_*','chars':'cyber_character_*','stickers':'cyber_sticker_*','films':'cyber_film_*','logos':'cyber_logo_*'}
imgs={k:['data:image/webp;base64,'+base64.b64encode(open(f,'rb').read()).decode() for f in sorted(glob.glob('assets/'+p+'.webp'))] for k,p in groups.items()}
s=s.replace('/*IMGS*/{}',json.dumps(imgs))
audio=base64.b64encode(open(sys.argv[1],'rb').read()).decode() if len(sys.argv)>1 else ''
tag='<audio id="track" preload="auto"%s></audio>'%(f' src="data:audio/mpeg;base64,{audio}"' if audio else '')
s=s.replace('<!--AUDIO-->',tag); open('index.html','w').write(s)

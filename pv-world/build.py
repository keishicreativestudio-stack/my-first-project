import sys,base64,glob,json,os
s=open('src.html').read()
imgs={os.path.basename(f)[:-5]:'data:image/webp;base64,'+base64.b64encode(open(f,'rb').read()).decode() for f in sorted(glob.glob('assets/*.webp'))}
s=s.replace('/*IMGS*/{}',json.dumps(imgs))
tag='<audio id="track" preload="auto"></audio>'
if len(sys.argv)>1: tag=f'<audio id="track" preload="auto" src="data:audio/mpeg;base64,{base64.b64encode(open(sys.argv[1],"rb").read()).decode()}"></audio>'
open('index.html','w').write(s.replace('<!--AUDIO-->',tag))

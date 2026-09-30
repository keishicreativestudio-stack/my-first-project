import sys,base64
s=open('src.html').read().replace('/*SIL*/',open('sil.js').read()).replace('/*FACES*/',open('faces.js').read())
tag='<audio id="track" preload="auto"></audio>'
if len(sys.argv)>1: tag=f'<audio id="track" preload="auto" src="data:audio/mpeg;base64,{base64.b64encode(open(sys.argv[1],"rb").read()).decode()}"></audio>'
open('index.html','w').write(s.replace('<!--AUDIO-->',tag))

import sys
s=open('src.html').read().replace('/*SIL*/',open('sil.js').read())
audio=sys.argv[1] if len(sys.argv)>1 else ''
tag='<audio id="track" preload="auto"%s></audio>'%(f' src="data:audio/mpeg;base64,{audio}"' if audio else '')
s=s.replace('<!--AUDIO-->',tag); open('index.html','w').write(s)

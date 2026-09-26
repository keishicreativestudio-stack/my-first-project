# Google Fonts を fonts/ にダウンロードし、ローカル参照のCSSを作る
import re,urllib.request,os,sys
from concurrent.futures import ThreadPoolExecutor
UA={"User-Agent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120 Safari/537.36"}
def fetch(family,weights,out):
  u=f"https://fonts.googleapis.com/css2?family={family.replace(' ','+')}:wght@{weights}&display=swap"
  css=urllib.request.urlopen(urllib.request.Request(u,headers=UA),timeout=30).read().decode()
  urls=sorted(set(re.findall(r'https://fonts.gstatic.com[^)]+',css)))
  def g(x):
    n="fonts/"+x.rsplit("/",1)[1]
    if not os.path.exists(n): open(n,"wb").write(urllib.request.urlopen(x,timeout=30).read())
  with ThreadPoolExecutor(12) as ex: list(ex.map(g,urls))
  for x in urls: css=css.replace(x,x.rsplit("/",1)[1])
  open(f"fonts/{out}.css","w").write(css);print(out,len(urls))
for fam,w,out in [("Zen Maru Gothic","500;700;900","zen-maru-gothic"),("Zen Kaku Gothic New","500;900","zen-kaku-gothic-new"),("Zen Old Mincho","500;700","zen-old-mincho"),("Klee One","600","klee-one")]:
  fetch(fam,w,out)

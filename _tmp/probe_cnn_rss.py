import urllib.request
for url in ['http://rss.cnn.com/rss/edition_world.rss','http://rss.cnn.com/rss/money_latest.rss']:
    try:
        req=urllib.request.Request(url,headers={'User-Agent':'Mozilla/5.0'})
        with urllib.request.urlopen(req,timeout=20) as r:
            data=r.read().decode('utf-8','ignore')
        print('URL',url,'LEN',len(data))
        print(data[:1200])
        print('\n---\n')
    except Exception as e:
        print('ERR',url,e)

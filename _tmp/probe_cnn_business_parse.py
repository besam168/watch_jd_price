import urllib.request, xml.etree.ElementTree as ET
for url in ['http://rss.cnn.com/rss/money_latest.rss']:
    req=urllib.request.Request(url,headers={'User-Agent':'Mozilla/5.0'})
    raw=urllib.request.urlopen(req,timeout=20).read()
    print('BYTES',len(raw))
    root=ET.fromstring(raw)
    channel=root.find('channel')
    items=channel.findall('item') if channel is not None else []
    print('ITEMS',len(items))
    for it in items[:5]:
        title=(it.findtext('title','') or '').strip()
        print(title)

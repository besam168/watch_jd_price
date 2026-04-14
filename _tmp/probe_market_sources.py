import urllib.request, json, re

headers_common = {'User-Agent':'Mozilla/5.0'}

def fetch(url, headers=None, encoding='utf-8'):
    req = urllib.request.Request(url, headers=headers or headers_common)
    with urllib.request.urlopen(req, timeout=20) as r:
        return r.read().decode(encoding, 'ignore')

results = {}

# Eastmoney
try:
    url='https://push2.eastmoney.com/api/qt/ulist.np/get?fltt=2&invt=2&fields=f12,f14,f2,f3&secids=1.000001,0.399001,0.399006,100.HSI,100.NDX,100.NKY,100.GC00Y,100.CL00Y,133.USDCNH,119.USDINDEX'
    txt = fetch(url, {'User-Agent':'Mozilla/5.0','Referer':'https://quote.eastmoney.com'}, 'utf-8')
    results['eastmoney'] = txt[:3000]
except Exception as e:
    results['eastmoney_error'] = str(e)

# Sina
try:
    url='http://hq.sinajs.cn/list=s_sh000001,s_sz399001,s_sz399006,rt_hkHSI,int_dji,int_nasdaq,int_sp500,int_nikkei,hf_GC,hf_CL,USDCNY,fx_susdcnh,DINIW'
    txt = fetch(url, {'User-Agent':'Mozilla/5.0','Referer':'https://finance.sina.com.cn'}, 'gbk')
    results['sina'] = txt[:3000]
except Exception as e:
    results['sina_error'] = str(e)

# Tencent
try:
    url='http://qt.gtimg.cn/q=s_sh000001,s_sz399001,s_sz399006,r_hkHSI,usDJI,usIXIC,usINX,hf_GC,hf_CL,fx_susdcnh,USDCNY'
    txt = fetch(url, {'User-Agent':'Mozilla/5.0','Referer':'https://gu.qq.com'}, 'gbk')
    results['tencent'] = txt[:3000]
except Exception as e:
    results['tencent_error'] = str(e)

print(json.dumps(results, ensure_ascii=False, indent=2))

import os, json, urllib.request, urllib.parse
def load_env(p=".env"):
    e={}
    for line in open(p,encoding="utf-8"):
        line=line.strip()
        if "=" in line and not line.startswith("#"):
            k,v=line.split("=",1); e[k.strip()]=v.strip()
    return e
env=load_env(); KEY_GO=env.get("DATA_GO_KR_KEY","")
def probe(url,timeout=20):
    try:
        req=urllib.request.Request(url,headers={"User-Agent":"MAPZ/1.0"})
        with urllib.request.urlopen(req,timeout=timeout) as r:
            b=r.read(800); return {"ok":True,"status":r.status,"head":b[:300].decode("utf-8","replace")}
    except Exception as ex:
        return {"ok":False,"err":str(ex)[:250]}
res={}
# 전국박물관미술관정보 표준데이터 API (data.go.kr standard data)
res["museum_std"]=probe("https://api.odcloud.kr/api/15012511/v1/uddi:???")  # placeholder likely fails
res["museum_std2"]=probe(f"http://api.data.go.kr/openapi/tn_pubr_public_museum_info_api?serviceKey={urllib.parse.quote(KEY_GO)}&pageNo=1&numOfRows=2&type=json")
# Overpass properly encoded
q="[out:json][timeout:25];node[tourism=museum](37.5,126.9,37.6,127.0);out 2;"
res["overpass"]=probe("https://overpass-api.de/api/interpreter?data="+urllib.parse.quote(q))
# TourAPI festival (data.go.kr) - needs key
res["tourapi"]=probe(f"http://apis.data.go.kr/B551011/KorService1/searchFestival1?serviceKey={urllib.parse.quote(KEY_GO)}&numOfRows=2&pageNo=1&MobileOS=ETC&MobileApp=MAPZ&_type=json&eventStartDate=20260101")
print(json.dumps(res,ensure_ascii=False,indent=2))

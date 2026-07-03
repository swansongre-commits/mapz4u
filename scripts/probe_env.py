import os, json, socket, sys, urllib.request, urllib.parse
def load_env(p=".env"):
    e={}
    if os.path.exists(p):
        for line in open(p, encoding="utf-8"):
            line=line.strip()
            if "=" in line and not line.startswith("#"):
                k,v=line.split("=",1); e[k.strip()]=v.strip()
    return e
env=load_env()
KEY_GO=env.get("DATA_GO_KR_KEY",""); KEY_LIB=env.get("DATA4LIBRARY_KEY","")
res={"keys":{"DATA_GO_KR_KEY":bool(KEY_GO and len(KEY_GO)>10),"DATA4LIBRARY_KEY":bool(KEY_LIB and len(KEY_LIB)>10)}}
# network
try:
    socket.create_connection(("8.8.8.8",53),timeout=4); res["network"]=True
except Exception as ex:
    res["network"]=False; res["net_err"]=str(ex)
def probe(url,timeout=12):
    try:
        req=urllib.request.Request(url, headers={"User-Agent":"MAPZ/1.0"})
        with urllib.request.urlopen(req,timeout=timeout) as r:
            body=r.read(600)
            return {"ok":True,"status":r.status,"len_head":len(body),"head":body[:200].decode("utf-8","replace")}
    except Exception as ex:
        return {"ok":False,"err":str(ex)[:200]}
if res["network"]:
    # 1) data4library popular loan
    res["lib_api"]=probe(f"http://data4library.kr/api/loanItemSrch?authKey={urllib.parse.quote(KEY_LIB)}&startDt=2024-01-01&endDt=2024-12-31&age=8&format=json&pageSize=2")
    # 2) 문화정보원 한눈에보는문화정보 (data.go.kr)
    res["culture_api"]=probe(f"http://api.kcisa.kr/openapi/service/rest/meta13/getEvent?serviceKey={urllib.parse.quote(KEY_GO)}&numOfRows=2&pageNo=1")
    # 3) OSM Overpass reachability
    res["overpass"]=probe("https://overpass-api.de/api/interpreter?data=[out:json];node[tourism=museum](37.5,126.9,37.6,127.0);out 1;")
print(json.dumps(res,ensure_ascii=False,indent=2))

import json, urllib.request, urllib.parse
q="[out:json][timeout:25];node[tourism=museum](37.4,126.8,37.7,127.2);out 3;"
mirrors=["https://overpass.kumi.systems/api/interpreter","https://overpass-api.de/api/interpreter","https://maps.mail.ru/osm/tools/overpass/api/interpreter"]
for m in mirrors:
    try:
        req=urllib.request.Request(m+"?data="+urllib.parse.quote(q),headers={"User-Agent":"MAPZ/1.0"})
        with urllib.request.urlopen(req,timeout=30) as r:
            d=json.loads(r.read().decode("utf-8"))
            n=len(d.get("elements",[]))
            print("OK",m,"elements=",n)
            if n>0:
                import sys; print("SAMPLE:", d["elements"][0].get("tags",{}).get("name")); sys.exit(0)
    except Exception as ex:
        print("FAIL",m,str(ex)[:100])

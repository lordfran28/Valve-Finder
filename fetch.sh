set -x
cd fetched
rm -rf old sv
mkdir -p sv
UA="KnockelsSiteBuild/1.0 (https://github.com/lordfran28; site build)"
curl -fsSL -A "$UA" --get "https://nominatim.openstreetmap.org/search" --data-urlencode "q=112 West Center Street, Monona, Iowa 52159" --data-urlencode "format=jsonv2" --data-urlencode "addressdetails=1" -o sv/geo1.json
curl -fsSL -A "$UA" --get "https://nominatim.openstreetmap.org/search" --data-urlencode "q=Knockel's Floor Covering, Monona, Iowa" --data-urlencode "format=jsonv2" -o sv/geo2.json
curl -fsSL -A "$UA" --get "https://nominatim.openstreetmap.org/search" --data-urlencode "street=112 W Center St" --data-urlencode "city=Monona" --data-urlencode "state=Iowa" --data-urlencode "format=jsonv2" -o sv/geo3.json
cat sv/geo*.json
pip install -q playwright >/dev/null 2>&1 && python -m playwright install --with-deps chromium >/dev/null 2>&1
cat > shot.py <<'PY'
import json, sys
from playwright.sync_api import sync_playwright
geo = None
for f in ['sv/geo1.json','sv/geo3.json','sv/geo2.json']:
    try:
        d = json.load(open(f))
        if d: geo = (float(d[0]['lat']), float(d[0]['lon'])); break
    except Exception: pass
print('geo', geo)
if not geo: sys.exit(0)
lat, lng = geo
urls = {}
for h in (0, 90, 180, 270):
    urls['legacy_h%d' % h] = "https://maps.google.com/maps?q=&layer=c&cbll=%f,%f&cbp=11,%d,0,0,0&source=embed&output=svembed" % (lat, lng, h)
urls['place_embed'] = "https://maps.google.com/maps?q=Knockel%27s%20Floor%20Covering%2C%20112%20W%20Center%20St%2C%20Monona%2C%20IA%2052159&t=k&z=19&output=embed"
with sync_playwright() as p:
    b = p.chromium.launch()
    pg = b.new_page(viewport={'width': 900, 'height': 560})
    for name, u in urls.items():
        try:
            pg.set_content('<html><body style="margin:0"><iframe src="%s" width="900" height="560" style="border:0" allowfullscreen></iframe></body></html>' % u)
            pg.wait_for_timeout(9000)
            pg.screenshot(path='sv/%s.png' % name)
            print('ok', name)
        except Exception as e:
            print('fail', name, e)
    b.close()
json.dump(urls, open('sv/urls.json', 'w'), indent=1)
PY
python shot.py
ls -la sv

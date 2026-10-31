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

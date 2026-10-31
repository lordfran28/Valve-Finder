from playwright.sync_api import sync_playwright
lat0 = 43.0530206
shots = []
for dlng in (-0.00025, 0.0, 0.00025):
    lng = -91.390142 + dlng
    for h in (315, 340, 0, 20, 45):
        shots.append(('lng%+.5f_h%d' % (dlng, h), "https://maps.google.com/maps?q=&layer=c&cbll=%f,%f&cbp=12,%d,0,0,-4&source=embed&output=svembed" % (lat0 - 0.00008, lng, h)))
with sync_playwright() as p:
    b = p.chromium.launch(); pg = b.new_page(viewport={'width': 900, 'height': 520})
    for name, u in shots:
        pg.set_content('<html><body style="margin:0"><iframe src="%s" width="900" height="520" style="border:0"></iframe></body></html>' % u)
        pg.wait_for_timeout(7000); pg.screenshot(path='sv2/%s.png' % name); print('ok', name)
    b.close()
open('sv2/urls.txt', 'w').write('\n'.join('%s %s' % s for s in shots))

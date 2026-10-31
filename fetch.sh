set -x
cd fetched
rm -rf ph acg commons *.json
UA="KnockelsSiteBuild/1.0 (https://github.com/lordfran28; site build)"
mkdir -p photos fonts
big() { # $1 = Commons file title (without File:), $2 = output name, $3 = width
  url=$(curl -fsSL -A "$UA" --get "https://commons.wikimedia.org/w/api.php" --data-urlencode "action=query" --data-urlencode "format=json" --data-urlencode "titles=File:$1" --data-urlencode "prop=imageinfo" --data-urlencode "iiprop=url|extmetadata" --data-urlencode "iiurlwidth=$3" | tee "photos/$2.json" | jq -r '.query.pages[].imageinfo[0].thumburl')
  curl -fsSL -A "$UA" -o "photos/$2.jpg" "$url"
}
big "Mississippiatpikespeak.JPG" river 2400
big "204-202-200 South Main Street, Monona, IA - c. 1925.jpg" monona-1925 1499
big "Monona, Iowa.jpg" monona-aerial 2400
big "9 Irving A 2014 hardwood floors living room and part of bedroom.JPG" room-bay 786
big "Empty apartment room with corner windows.jpg" room-corner 2000
big "CLASSEN Verlegung Laminat.jpg" laying 2000
big "Gfp-iowa-pikes-peak-state-park-mississippi-river.jpg" river2 2400
# fonts (SIL Open Font License), latin woff2 from Google Fonts
CSSUA="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"
curl -fsSL -A "$CSSUA" "https://fonts.googleapis.com/css2?family=Zilla+Slab:wght@500;600;700&family=Public+Sans:ital,wght@0,400;0,500;0,600;1,400&display=swap" -o fonts/fonts.css
grep -o 'https://fonts.gstatic.com[^)]*' fonts/fonts.css | sort -u | while read u; do curl -fsSL -o "fonts/$(basename "$u")" "$u"; done
curl -fsSL -o fonts/ZillaSlab-OFL.txt "https://raw.githubusercontent.com/google/fonts/main/ofl/zillaslab/OFL.txt" || true
curl -fsSL -o fonts/PublicSans-OFL.txt "https://raw.githubusercontent.com/google/fonts/main/ofl/publicsans/OFL.txt" || true
ls -la photos fonts

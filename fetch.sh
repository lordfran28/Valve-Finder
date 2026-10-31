set -x
cd fetched
mkdir -p backfull
UA="KnockelsSiteBuild/1.0 (https://github.com/lordfran28; site build)"
big() { curl -fsSL --max-time 30 -A "$UA" --get "https://commons.wikimedia.org/w/api.php" --data-urlencode "action=query" --data-urlencode "format=json" --data-urlencode "titles=File:$1" --data-urlencode "prop=imageinfo" --data-urlencode "iiprop=url|extmetadata" > "backfull/$2.json"; url=$(jq -r '.query.pages[].imageinfo[0].url' "backfull/$2.json"); curl -fsSL --max-time 120 -A "$UA" -o "backfull/$2.jpg" "$url"; }
big "Carpet (AM 1995.36.1-5).jpg" am5
big "Carpet (AM 1995.36.1-6).jpg" am6
big "Carpet (AM 1995.36.1-7).jpg" am7
big "Carpet installers (3833872385).jpg" inst1
big "Carpet installers (3834666540).jpg" inst2
big "Rug (AM 1999.80.3-3).jpg" rug3
ls -la backfull

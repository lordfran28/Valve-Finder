set -x
cd fetched
rm -rf pat; mkdir -p patfull
UA="KnockelsSiteBuild/1.0 (https://github.com/lordfran28; site build)"
big() { curl -fsSL --max-time 30 -A "$UA" --get "https://commons.wikimedia.org/w/api.php" --data-urlencode "action=query" --data-urlencode "format=json" --data-urlencode "titles=File:$1" --data-urlencode "prop=imageinfo" --data-urlencode "iiprop=url|extmetadata" > "patfull/$2.json"; url=$(jq -r '.query.pages[].imageinfo[0].url' "patfull/$2.json"); curl -fsSL --max-time 120 -A "$UA" -o "patfull/$2.jpg" "$url"; }
big "20070919340DR Dresden-Striesen Voglerstraße 10 Entree.jpg" vogler
big "20070916355DR Dresden-Löbtau Klingestraße 7 Fliesen.jpg" klinge
big "20070923150DR Dresden-Leipziger Vorstadt Gehestraße 21 Haustür.jpg" gehe
ls -la patfull

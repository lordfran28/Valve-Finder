set -x
cd fetched
rm -rf sv sv2 soft
mkdir -p soft/commons
UA="KnockelsSiteBuild/1.0 (https://github.com/lordfran28; site build)"
for id in curly_teddy_natural curly_teddy_checkered faux_fur_geometric polar_fleece knitted_fleece wool_boucle velour_velvet terry_cloth caban jogging_melange; do
  url=$(curl -fsSL -A "$UA" "https://api.polyhaven.com/files/$id" | jq -r '.Diffuse["2k"].jpg.url // empty')
  [ -n "$url" ] && curl -fsSL -A "$UA" -o "soft/$id.jpg" "$url" || echo "none $id"
done
q() { curl -fsSL -A "$UA" --get "https://commons.wikimedia.org/w/api.php" --data-urlencode "action=query" --data-urlencode "format=json" --data-urlencode "generator=search" --data-urlencode "gsrnamespace=6" --data-urlencode "gsrsearch=$1 filetype:bitmap" --data-urlencode "gsrlimit=20" --data-urlencode "prop=imageinfo" --data-urlencode "iiprop=url|extmetadata|size" --data-urlencode "iiurlwidth=640" -o "soft/commons/$2.json"; }
q "shag carpet" shag
q "carpet pile close-up" pile
q "sheepskin rug" sheepskin
for f in soft/commons/*.json; do
  jq -r '.query.pages[]? | [.title, .imageinfo[0].thumburl] | @tsv' "$f" | while IFS=$'\t' read -r title thumb; do
    n=$(echo "$title" | sed 's/^File://; s/[^A-Za-z0-9._-]/_/g' | cut -c1-70); d="soft/commons/$(basename "$f" .json)"; mkdir -p "$d"
    curl -fsSL -A "$UA" -o "$d/$n" "$thumb" || true; sleep 0.2
  done
done
ls -la soft

set -x
cd fetched
rm -rf carpet carpet2
mkdir -p carpet2
UA="KnockelsSiteBuild/1.0 (https://github.com/lordfran28; site build)"
q() { curl -fsSL -A "$UA" --get "https://commons.wikimedia.org/w/api.php" --data-urlencode "action=query" --data-urlencode "format=json" --data-urlencode "generator=search" --data-urlencode "gsrnamespace=6" --data-urlencode "gsrsearch=$1 filetype:bitmap" --data-urlencode "gsrlimit=30" --data-urlencode "prop=imageinfo" --data-urlencode "iiprop=url|extmetadata|size" --data-urlencode "iiurlwidth=500" -o "carpet2/$2.json"; }
q "flokati" flokati
q "Hochflorteppich" hochflor
q "deep pile carpet" deeppile
q "carpet macro" macro
q "Teppich Detail" teppich
q "wool rug texture" woolrug
q "plush carpet" plush
q "carpet fibres" fibres
for f in carpet2/*.json; do
  jq -r '.query.pages[]? | select(.imageinfo[0].width >= 1600) | [.title, .imageinfo[0].thumburl] | @tsv' "$f" | while IFS=$'\t' read -r title thumb; do
    n=$(echo "$title" | sed 's/^File://; s/[^A-Za-z0-9._-]/_/g' | cut -c1-70); d="carpet2/$(basename "$f" .json)"; mkdir -p "$d"
    curl -fsSL -A "$UA" -o "$d/$n" "$thumb" || true; sleep 0.15
  done
done
du -sh carpet2

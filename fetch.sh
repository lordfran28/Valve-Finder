set -x
cd fetched
rm -rf ovtest; mkdir -p cand4/cm
UA="KnockelsSiteBuild/1.0 (https://github.com/lordfran28; site build)"
api() { curl -fsSL --max-time 30 -A "$UA" --get "https://commons.wikimedia.org/w/api.php" "$@"; }
n=0
for q in "shaggy" "Hochflor" "Hochflorteppich" "Teppich Nahaufnahme" "rya rug" "ryijy" "rag rug" "hooked rug" "carpet fibers" "carpet fibres" "rug detail" "carpet detail" "pile carpet" "alfombra" "moqueta" "tapis" "pink fluffy" "fluffy" "fuzzy carpet" "fuzzy rug" "pastel" "faux fur" "sheepskin" "bath mat" "bathmat" "doormat close" "chenille" "terry towel close" "plush" "yarn close up" "wool close up" "tufting" "tufted"; do
  slug=$(echo "$q" | tr ' ' '_')
  api --data-urlencode "action=query" --data-urlencode "format=json" --data-urlencode "generator=search" --data-urlencode "gsrnamespace=6" --data-urlencode "gsrsearch=$q filetype:bitmap" --data-urlencode "gsrlimit=40" --data-urlencode "prop=imageinfo" --data-urlencode "iiprop=url|size|extmetadata" --data-urlencode "iiurlwidth=320" > "cand4/s-$slug.json" || echo "fail $q"
done
for c in "Shag carpets" "Shag rugs" "Carpets by color" "Pink carpets" "Purple carpets" "Blue carpets" "Green carpets" "Yellow carpets" "Orange carpets" "Close-ups of carpets" "Carpet textures" "Rya rugs" "Ryijy" "Rag rugs" "Hooked rugs" "Flokati" "Carpets (textile)" "Rugs" "Textures of textiles" "Close-ups of textiles"; do
  slug=$(echo "$c" | tr ' ()' '___')
  api --data-urlencode "action=query" --data-urlencode "format=json" --data-urlencode "generator=categorymembers" --data-urlencode "gcmtitle=Category:$c" --data-urlencode "gcmtype=file" --data-urlencode "gcmlimit=100" --data-urlencode "prop=imageinfo" --data-urlencode "iiprop=url|size|extmetadata" --data-urlencode "iiurlwidth=320" > "cand4/c-$slug.json" || echo "fail cat $c"
done
jq -s -r '[.[] | .query.pages? // {} | to_entries[] | .value] | unique_by(.title)[] | select(.imageinfo[0].width >= 1600 and .imageinfo[0].height >= 1100) | [.title, .imageinfo[0].thumburl, .imageinfo[0].width, .imageinfo[0].height, (.imageinfo[0].extmetadata.LicenseShortName.value // "?")] | @tsv' cand4/*.json > cand4/list.tsv
wc -l cand4/list.tsv
while IFS=$'\t' read title thumb w h lic; do n=$((n+1)); k=$(printf %03d $n); curl -fsSL --max-time 20 -A "$UA" -o "cand4/cm/$k.jpg" "$thumb" && echo -e "$k\t$title\t$w\t$h\t$lic" >> cand4/index.tsv; done < cand4/list.tsv
ls cand4/cm | wc -l; du -sh cand4

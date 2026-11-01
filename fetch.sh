set -x
cd fetched
rm -rf back backfull; mkdir -p pat/cm
UA="KnockelsSiteBuild/1.0 (https://github.com/lordfran28; site build)"
api() { curl -fsSL --max-time 30 -A "$UA" --get "https://commons.wikimedia.org/w/api.php" "$@"; }
for q in "encaustic tiles" "encaustic tile floor" "cement tiles" "cement tile floor" "baldosa hidráulica" "baldosas hidráulicas" "suelo hidráulico" "carreaux de ciment" "Zementfliesen" "Victorian floor tiles" "Victorian tiled floor" "Minton tiles" "geometric floor tiles" "patterned floor tiles" "tile floor pattern" "linoleum" "linoleum floor" "vintage linoleum" "inlaid linoleum" "linoleum pattern" "vinyl floor" "floor tiles" "tiled floor" "Mettlach tiles" "Villeroy Boch floor tiles" "mosaic floor tiles pattern" "Portuguese tiles floor" "majolica floor" "Sicilian floor tiles" "piastrelle" "cementine" "mosaico idraulico" "tegels vloer" "Art Nouveau floor tiles"; do
  slug=$(echo "$q" | tr ' ' '_')
  api --data-urlencode "action=query" --data-urlencode "format=json" --data-urlencode "generator=search" --data-urlencode "gsrnamespace=6" --data-urlencode "gsrsearch=$q filetype:bitmap" --data-urlencode "gsrlimit=50" --data-urlencode "prop=imageinfo" --data-urlencode "iiprop=url|size|extmetadata" --data-urlencode "iiurlwidth=300" > "pat/s-$slug.json" || echo "fail $q"
done
for c in "Encaustic tiles" "Cement tiles" "Hydraulic tiles" "Baldosas hidráulicas" "Carreaux de ciment" "Victorian tiles" "Minton tiles" "Linoleum" "Tiled floors" "Floor tiles" "Geometric tiles" "Mettlach tiles"; do
  slug=$(echo "$c" | tr ' ()' '___')
  api --data-urlencode "action=query" --data-urlencode "format=json" --data-urlencode "generator=categorymembers" --data-urlencode "gcmtitle=Category:$c" --data-urlencode "gcmtype=file" --data-urlencode "gcmlimit=200" --data-urlencode "prop=imageinfo" --data-urlencode "iiprop=url|size|extmetadata" --data-urlencode "iiurlwidth=300" > "pat/c-$slug.json" || echo "fail cat $c"
done
jq -s -r '[.[] | .query.pages? // {} | to_entries[] | .value] | unique_by(.title)[] | select(.imageinfo[0].width >= 1400 and .imageinfo[0].height >= 1000) | [.title, .imageinfo[0].thumburl, .imageinfo[0].width, .imageinfo[0].height, (.imageinfo[0].extmetadata.LicenseShortName.value // "?")] | @tsv' pat/*.json > pat/list.tsv
wc -l pat/list.tsv
n=0; while IFS=$'\t' read title thumb w h lic; do n=$((n+1)); k=$(printf %03d $n); curl -fsSL --max-time 20 -A "$UA" -o "pat/cm/$k.jpg" "$thumb" && echo -e "$k\t$title\t$w\t$h\t$lic" >> pat/index.tsv; done < pat/list.tsv
ls pat/cm | wc -l; du -sh pat

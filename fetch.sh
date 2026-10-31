set -x
cd fetched
rm -rf cand4 pad; mkdir -p back/cm
UA="KnockelsSiteBuild/1.0 (https://github.com/lordfran28; site build)"
api() { curl -fsSL --max-time 30 -A "$UA" --get "https://commons.wikimedia.org/w/api.php" "$@"; }
for q in "carpet backing" "back of carpet" "carpet back" "carpet underside" "underside of carpet" "rug backing" "back of rug" "rug back" "rug reverse" "reverse of rug" "reverse side carpet" "Teppichrückseite" "Teppich Rückseite" "envers tapis" "tufted carpet" "tufting carpet" "carpet tufting" "carpet roll" "rolled carpet" "carpet rolls" "roll of carpet" "jute backing" "latex backing" "primary backing" "carpet manufacturing" "carpet factory" "carpet installation" "carpet installer" "carpet fitter" "laying carpet" "carpet remnant" "carpet offcut" "carpet sample" "hooked rug back" "rag rug back"; do
  slug=$(echo "$q" | tr ' ' '_')
  api --data-urlencode "action=query" --data-urlencode "format=json" --data-urlencode "generator=search" --data-urlencode "gsrnamespace=6" --data-urlencode "gsrsearch=$q filetype:bitmap" --data-urlencode "gsrlimit=40" --data-urlencode "prop=imageinfo" --data-urlencode "iiprop=url|size|extmetadata" --data-urlencode "iiurlwidth=320" > "back/s-$slug.json" || echo "fail $q"
done
for c in "Carpet backing" "Carpet rolls" "Carpet installation" "Carpet fitters" "Tufting" "Tufted carpets" "Carpet manufacturing" "Backs of rugs" "Reverse sides of carpets"; do
  slug=$(echo "$c" | tr ' ()' '___')
  api --data-urlencode "action=query" --data-urlencode "format=json" --data-urlencode "generator=categorymembers" --data-urlencode "gcmtitle=Category:$c" --data-urlencode "gcmtype=file" --data-urlencode "gcmlimit=100" --data-urlencode "prop=imageinfo" --data-urlencode "iiprop=url|size|extmetadata" --data-urlencode "iiurlwidth=320" > "back/c-$slug.json" || echo "fail cat $c"
done
jq -s -r '[.[] | .query.pages? // {} | to_entries[] | .value] | unique_by(.title)[] | select(.imageinfo[0].width >= 1000) | [.title, .imageinfo[0].thumburl, .imageinfo[0].width, .imageinfo[0].height, (.imageinfo[0].extmetadata.LicenseShortName.value // "?")] | @tsv' back/*.json > back/list.tsv
wc -l back/list.tsv
n=0; while IFS=$'\t' read title thumb w h lic; do n=$((n+1)); k=$(printf %03d $n); curl -fsSL --max-time 20 -A "$UA" -o "back/cm/$k.jpg" "$thumb" && echo -e "$k\t$title\t$w\t$h\t$lic" >> back/index.tsv; done < back/list.tsv
ls back/cm | wc -l; du -sh back

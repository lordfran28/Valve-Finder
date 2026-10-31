set -x
cd fetched
rm -rf carpet3 cand; mkdir -p cand/acg cand/ph cand/cm
UA="KnockelsSiteBuild/1.0 (https://github.com/lordfran28; site build)"
# ambientCG carpets and fabrics with pile
for q in carpet rug fabric; do
  curl -fsSL -A "$UA" "https://ambientcg.com/api/v2/full_json?type=Material&q=$q&limit=200&include=imageData,dimensionsData" > cand/acg-$q.json
  jq -r '.foundAssets[] | [.assetId, (.previewImage["256-PNG"] // .previewImage["128-PNG"] // "")] | @tsv' cand/acg-$q.json | while IFS=$'\t' read id url; do
    [ -n "$url" ] && [ ! -f "cand/acg/$id.png" ] && curl -fsSL -A "$UA" -o "cand/acg/$id.png" "$url"
  done
done
# Poly Haven textures tagged carpet, rug, fabric
curl -fsSL -A "$UA" "https://api.polyhaven.com/assets?t=textures" > cand/ph.json
jq -r 'to_entries[] | select(([.value.tags[]?, .value.categories[]?] | join(" ")) | test("carpet|rug|fabric|wool|felt|towel|fur"; "i")) | .key' cand/ph.json | while read id; do
  curl -fsSL -A "$UA" -o "cand/ph/$id.png" "https://cdn.polyhaven.com/asset_img/thumbs/$id.png?width=256&height=256"
done
# Wikimedia Commons photos
for q in "shag rug" "shag carpet" "pink carpet" "pink rug" "pastel rug" "fluffy rug" "flokati" "wool rug close" "carpet texture" "rug texture" "tufted rug" "yellow carpet" "green carpet close" "lavender rug" "mint rug" "blue shag" "plush carpet" "carpet macro" "carpet pile" "colorful carpet close-up"; do
  slug=$(echo "$q" | tr ' ' '_')
  curl -fsSL -A "$UA" --get "https://commons.wikimedia.org/w/api.php" --data-urlencode "action=query" --data-urlencode "format=json" --data-urlencode "generator=search" --data-urlencode "gsrnamespace=6" --data-urlencode "gsrsearch=$q filetype:bitmap" --data-urlencode "gsrlimit=30" --data-urlencode "prop=imageinfo" --data-urlencode "iiprop=url|size|extmetadata" --data-urlencode "iiurlwidth=320" > "cand/cm-$slug.json"
done
jq -s -r '[.[] | .query.pages? // {} | to_entries[] | .value] | unique_by(.title)[] | select(.imageinfo[0].width >= 1800 and .imageinfo[0].height >= 1200) | [.title, .imageinfo[0].thumburl, .imageinfo[0].width, .imageinfo[0].height, (.imageinfo[0].extmetadata.LicenseShortName.value // "?")] | @tsv' cand/cm-*.json > cand/cm-list.tsv
n=0; while IFS=$'\t' read title thumb w h lic; do n=$((n+1)); curl -fsSL -A "$UA" -o "cand/cm/$(printf %03d $n).jpg" "$thumb"; echo -e "$(printf %03d $n)\t$title\t$w\t$h\t$lic" >> cand/cm-index.tsv; done < cand/cm-list.tsv
ls cand/acg | wc -l; ls cand/ph | wc -l; ls cand/cm | wc -l
du -sh cand

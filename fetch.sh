set -x
cd fetched
rm -rf cand2 full; mkdir -p cand3/ov
UA="KnockelsSiteBuild/1.0 (https://github.com/lordfran28; site build)"
for q in "shag rug" "shag carpet" "pink rug" "pink carpet" "pastel rug" "fluffy rug" "fluffy carpet" "plush carpet" "mint carpet" "green shag" "yellow shag" "lavender rug" "blue shag" "flokati" "rug texture" "carpet texture" "carpet closeup" "tufted rug" "wool rug" "sheepskin rug" "pastel carpet" "carpet macro" "rug macro" "orange shag"; do
  slug=$(echo "$q" | tr ' ' '_')
  for pg in 1 2; do
    curl -fsS -A "$UA" --get "https://api.openverse.org/v1/images/" --data-urlencode "q=$q" --data-urlencode "license_type=commercial" --data-urlencode "page_size=20" --data-urlencode "page=$pg" > "cand3/ov-$slug-$pg.json" || echo "ov fail $q $pg"
    sleep 1
  done
done
jq -s -r '[.[] | .results[]?] | unique_by(.id)[] | select((.width // 0) >= 1600) | [.id, .thumbnail, .url, (.width|tostring), (.height|tostring), .license, .license_version, .creator, .title, .foreign_landing_url] | @tsv' cand3/ov-*.json > cand3/ov-list.tsv
n=0; while IFS=$'\t' read id thumb url w h lic ver creator title land; do n=$((n+1)); k=$(printf %03d $n); curl -fsSL -A "$UA" -o "cand3/ov/$k.jpg" "$thumb" && echo -e "$k\t$id\t$w\t$h\t$lic $ver\t$creator\t$title\t$url\t$land" >> cand3/ov-index.tsv; done < cand3/ov-list.tsv
ls cand3/ov | wc -l; du -sh cand3

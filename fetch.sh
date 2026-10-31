set -x
cd fetched
rm -rf cand; mkdir -p cand2/ov cand2/us full
UA="KnockelsSiteBuild/1.0 (https://github.com/lordfran28; site build)"
# the lavender shag on Commons, full size
url=$(curl -fsSL -A "$UA" --get "https://commons.wikimedia.org/w/api.php" --data-urlencode "action=query" --data-urlencode "format=json" --data-urlencode "titles=File:Carpet (original).png" --data-urlencode "prop=imageinfo" --data-urlencode "iiprop=url|extmetadata" | tee full/lavender.json | jq -r '.query.pages[].imageinfo[0].url')
curl -fsSL -A "$UA" -o full/lavender.png "$url"
# Openverse (Flickr and others), licences that allow use on a business site
for q in "shag rug" "shag carpet" "pink rug" "pink carpet" "pastel rug" "fluffy rug" "fluffy carpet" "plush carpet" "mint carpet" "green shag" "yellow shag" "lavender rug" "blue shag" "flokati" "rug texture" "carpet texture" "carpet closeup" "tufted rug" "wool rug closeup" "sheepskin rug"; do
  slug=$(echo "$q" | tr ' ' '_')
  curl -fsSL -A "$UA" --get "https://api.openverse.org/v1/images/" --data-urlencode "q=$q" --data-urlencode "license_type=commercial" --data-urlencode "page_size=40" --data-urlencode "size=large" > "cand2/ov-$slug.json" || echo "ov fail $q"
  sleep 1
done
jq -s -r '[.[] | .results[]?] | unique_by(.id)[] | [.id, .thumbnail, .url, (.width|tostring), (.height|tostring), .license, .license_version, .creator, .title, .foreign_landing_url] | @tsv' cand2/ov-*.json > cand2/ov-list.tsv
n=0; while IFS=$'\t' read id thumb url w h lic ver creator title land; do n=$((n+1)); k=$(printf %03d $n); curl -fsSL -A "$UA" -o "cand2/ov/$k.jpg" "$thumb" && echo -e "$k\t$id\t$w\t$h\t$lic $ver\t$creator\t$title\t$url\t$land" >> cand2/ov-index.tsv; done < cand2/ov-list.tsv
# Unsplash's own search (free licence; skip paid Unsplash+)
for q in "pastel rug" "pink shag rug" "fluffy rug" "shag carpet" "carpet texture" "rug close up" "plush carpet" "colorful carpet"; do
  slug=$(echo "$q" | tr ' ' '_')
  curl -fsSL -A "Mozilla/5.0" --get "https://unsplash.com/napi/search/photos" --data-urlencode "query=$q" --data-urlencode "per_page=30" > "cand2/us-$slug.json" || echo "us fail $q"
  sleep 1
done
jq -s -r '[.[] | .results[]?] | unique_by(.id)[] | select(.premium != true and .plus != true) | [.id, .urls.small, .urls.raw, (.width|tostring), (.height|tostring), .user.name, (.alt_description // ""), .links.html] | @tsv' cand2/us-*.json > cand2/us-list.tsv
n=0; while IFS=$'\t' read id small raw w h user alt link; do n=$((n+1)); k=$(printf %03d $n); curl -fsSL -A "Mozilla/5.0" -o "cand2/us/$k.jpg" "$small" && echo -e "$k\t$id\t$w\t$h\t$user\t$alt\t$raw\t$link" >> cand2/us-index.tsv; done < cand2/us-list.tsv
ls cand2/ov | wc -l; ls cand2/us | wc -l; ls -la full; du -sh cand2

set -x
cd fetched
rm -f *.json
UA="KnockelsSiteBuild/1.0 (https://github.com/lordfran28; site build)"
mkdir -p ph acg commons
for id in wood_floor wood_floor_worn laminate_floor laminate_floor_02 laminate_floor_03 plank_flooring plank_flooring_02 plank_flooring_04 herringbone_parquet rectangular_parquet diagonal_parquet dark_wood wooden_floor_01 old_wooden_floor_03 floor_tiles_06 marble_01 terracotta_floor_tiles slate_floor_03 grey_cartago_01 grey_cartago_03 terrazzo_tiles interior_tiles brown_floor_tiles granite_tile_03 slab_tiles worn_tile_floor square_brick_floor dirty_carpet; do
  url=$(curl -fsSL -A "$UA" "https://api.polyhaven.com/files/$id" | jq -r '.Diffuse["2k"].jpg.url // .diffuse["2k"].jpg.url // empty')
  [ -n "$url" ] && curl -fsSL -A "$UA" -o "ph/$id.jpg" "$url" || echo "no diffuse for $id"
done
for id in Carpet016 Carpet015 Carpet001 Carpet014 Fabric033 WoodFloor068 WoodFloor069 WoodFloor070 WoodFloor071 WoodFloor042 WoodFloor043 WoodFloor044 Planks009 Tiles002 Tiles027 Tiles028 Tiles073 Tiles138 Marble026; do
  curl -fsSL -A "$UA" -o "/tmp/$id.zip" "https://ambientcg.com/get?file=${id}_2K-JPG.zip" && unzip -o -j -q "/tmp/$id.zip" "*_Color.jpg" -d acg/ || echo "failed $id"
done
q() { curl -fsSL -A "$UA" --get "https://commons.wikimedia.org/w/api.php" --data-urlencode "action=query" --data-urlencode "format=json" --data-urlencode "generator=search" --data-urlencode "gsrnamespace=6" --data-urlencode "gsrsearch=$1 filetype:bitmap" --data-urlencode "gsrlimit=24" --data-urlencode "prop=imageinfo" --data-urlencode "iiprop=url|extmetadata|size" --data-urlencode "iiurlwidth=480" -o "commons/$2.json"; }
q "Monona Iowa" monona
q "Pikes Peak State Park Iowa" pikespeak
q "McGregor Iowa" mcgregor
q "Clayton County Iowa" clayton
q "Driftless Area Iowa" driftless
q "Mississippi River Iowa bluffs" bluffs
q "empty room wooden floor" emptyroom
q "living room interior hardwood floor" livingroom
q "laying laminate flooring" laying
q "carpet installation" carpetinstall
q "tile setter floor tiles" tilesetter
q "hardwood floor installation" hardwoodinstall
for f in commons/*.json; do
  jq -r '.query.pages[]? | [.title, .imageinfo[0].thumburl] | @tsv' "$f" | while IFS=$'\t' read -r title thumb; do
    n=$(echo "$title" | sed 's/^File://; s/[^A-Za-z0-9._-]/_/g' | cut -c1-80)
    d="commons/$(basename "$f" .json)"; mkdir -p "$d"
    curl -fsSL -A "$UA" -o "$d/$n" "$thumb" || true
    sleep 0.2
  done
done
du -sh ph acg commons; ls ph acg

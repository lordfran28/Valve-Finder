set -x
cd fetched
UA="Mozilla/5.0 (Knockels site build)"
curl -fsSL -A "$UA" "https://api.polyhaven.com/assets?t=textures" -o polyhaven-textures.json
curl -fsSL -A "$UA" "https://api.polyhaven.com/categories/textures" -o polyhaven-categories.json
for q in WoodFloor Carpet Tiles Marble Planks Fabric Travertine Terrazzo Wood; do
  curl -fsSL -A "$UA" "https://ambientcg.com/api/v2/full_json?type=Material&q=$q&limit=100&include=downloadData,previewData" -o "acg-$q.json"
done
ls -la

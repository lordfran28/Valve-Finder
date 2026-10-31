set -x
cd fetched
rm -rf cand3; mkdir -p pad ovtest
UA="KnockelsSiteBuild/1.0 (https://github.com/lordfran28; site build)"
for t in hessian_230 hessian_380; do curl -fsSL --max-time 60 -A "$UA" -o pad/$t.jpg "https://dl.polyhaven.org/file/ph-assets/Textures/jpg/2k/$t/${t}_diff_2k.jpg" || echo "ph fail $t"; done
# one Openverse request, to see what it says
curl -sS --max-time 30 -A "$UA" -o ovtest/one.json -w "%{http_code} %{time_total}\n" --get "https://api.openverse.org/v1/images/" --data-urlencode "q=pink shag rug" --data-urlencode "page_size=20"
head -c 600 ovtest/one.json; echo
ls -la pad

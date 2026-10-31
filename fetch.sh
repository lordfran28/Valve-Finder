set -x
cd fetched
rm -rf carpet2
mkdir -p carpet3
UA="KnockelsSiteBuild/1.0 (https://github.com/lordfran28; site build)"
big() { url=$(curl -fsSL -A "$UA" --get "https://commons.wikimedia.org/w/api.php" --data-urlencode "action=query" --data-urlencode "format=json" --data-urlencode "titles=File:$1" --data-urlencode "prop=imageinfo" --data-urlencode "iiprop=url" | jq -r '.query.pages[].imageinfo[0].url'); curl -fsSL -A "$UA" -o "carpet3/$2" "$url"; }
big "The Fuzzy Carpet (51167298287).jpg" fuzzy.jpg
big "Flokati rug edge.jpg" flokati.jpg
ls -la carpet3

set -x
cd fetched
rm -rf photos fonts old
mkdir -p old/img
UA="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"
curl -fsSL -A "$UA" "https://knockelsfloorcovering.com/" -o old/index.html
# every image, background image and frame the page uses
grep -oE '(src|data-src|href)="[^"]+\.(jpg|jpeg|png|webp|gif)[^"]*"' old/index.html | sed -E 's/^[a-z-]+="//; s/"$//' > old/urls.txt
grep -oE "url\(['\"]?[^)'\"]+\.(jpg|jpeg|png|webp)[^)'\"]*['\"]?\)" old/index.html | sed -E "s/^url\(['\"]?//; s/['\"]?\)$//" >> old/urls.txt
grep -oE '<iframe[^>]*>' old/index.html > old/iframes.txt || true
grep -oE 'https://www\.google\.com/maps/embed\?pb=[^"'"'"' ]+' old/index.html >> old/iframes.txt || true
sort -u old/urls.txt -o old/urls.txt
i=0
while read -r u; do
  case "$u" in http*) full="$u";; //*) full="https:$u";; /*) full="https://knockelsfloorcovering.com$u";; *) full="https://knockelsfloorcovering.com/$u";; esac
  i=$((i+1)); n=$(basename "${u%%\?*}"); curl -fsSL -A "$UA" -o "old/img/$(printf %02d $i)-$n" "$full" || echo "failed $full"
done < old/urls.txt
# linked css may hold more images
grep -oE 'href="[^"]+\.css[^"]*"' old/index.html | sed -E 's/^href="//; s/"$//' > old/css.txt
ls -la old/img; cat old/iframes.txt | head -20

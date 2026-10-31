set -x
cd fetched
rm -rf soft carpet
mkdir -p carpet
UA="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"
for id in er1KJ1bvFGE C_ldv5csD-U hCzHhu1v0fA 2iAky1ttuHw YR68IEvkggo SqE-6SW9fO8 KAwP1Nwo5yQ W2M4dORIL7A ezWRDRxT6Tw dSy9191pcx4 PcMI_etcjYw; do
  curl -fsSL -A "$UA" -o "carpet/$id.jpg" "https://unsplash.com/photos/$id/download?force=true&w=2400" && echo "ok $id $(stat -c %s carpet/$id.jpg)" || echo "fail $id"
  curl -fsSL -A "$UA" "https://unsplash.com/photos/$id" -o "carpet/$id.html" || true
  grep -oE '"(premium|plus)":(true|false)|Unsplash\+|Free to use under the Unsplash License|"username":"[^"]+"|"name":"[^"]{1,60}"' "carpet/$id.html" | head -6 > "carpet/$id.meta"
  rm -f "carpet/$id.html"
done
ls -la carpet

# Valve Finder

B♭ trumpet valve fingerings under every note of a song, with a song library.

**Live site:** https://lordfran28.github.io/Valve-Finder/

## What it reads
- **MusicXML** (`.musicxml`, `.xml`, `.mxl`) from Klangio, Scan2Notes, MuseScore and most notation apps
- **MIDI** (`.mid`) from Basic Pitch or any notation app
- **Tony note lists** (`.csv`: onset seconds, frequency in Hz, duration seconds)

Files are read in the browser. Nothing is sent anywhere except your own GitHub song repository, if you turn on backup.

## Song library and backup
Every song you add is saved in the browser. With GitHub backup on, each song is also saved to the private repository `lordfran28/valve-finder-songs`:

- `index.json`: the song list
- `songs/<id>.json`: one file per song, holding the original file (base64), its title and its settings

Backup uses a fine-grained personal access token with **Contents: Read and write** on the song repository only. The token stays in the browser where you paste it.

## Images and fonts
Everything the page shows is stored in this repository, so the site keeps working on its own.

- **Clio**, detail of Johannes Vermeer, *The Art of Painting* (c. 1666–68), Kunsthistorisches Museum, Vienna. Public domain. `assets/clio-vermeer.jpg`
- **Silk**, *Piece*, Italian (possibly Genoa), 17th–18th century, silk and metal thread, The Metropolitan Museum of Art, [30.95.68](https://www.metmuseum.org/art/collection/search/222358). Public domain (Met Open Access). Recoloured into `assets/textile-light.jpg` (ochre on parchment) and `assets/textile-dark.jpg` (gold on navy).
- Other public-domain textiles considered for the design are kept in `assets/source/`; `assets/sources.txt` lists where each came from.
- **Fonts:** [EB Garamond](https://github.com/octaviopardo/EBGaramond12) and [IM Fell French Canon](https://iginomarini.com/fell/) (the Fell Types, cut in the 1670s), both under the SIL Open Font License; licences in `assets/fonts/`.

`.github/workflows/fetch-images.yml` downloads anything listed in `assets/sources.txt` and commits it.

## How it's built
One self-contained page, `index.html`, served by GitHub Pages. No build step.

# Valve Finder

B♭ trumpet valve fingerings under every note of a song, with a song library.

**Live site:** https://lordfran28.github.io/Valve-Finder/

## What it reads
- **MusicXML** (`.musicxml`, `.xml`, `.mxl`) from Klangio, Scan2Notes, MuseScore and most notation apps
- **MIDI** (`.mid`) from Basic Pitch or any notation app
- **Tony note lists** (`.csv`: onset seconds, frequency in Hz, duration seconds)

## Your songs
Every song is a file in the [`songs`](songs/) folder of this repository, so the site shows the same library on every phone and computer.

- **From your computer:** put MIDI, MusicXML or Tony files in `songs/` (subfolders are fine), then commit and push in GitHub Desktop.
- **From the site:** on a device connected as owner, *Add a song* puts the file in `songs/` for you. Titles, settings and the notes typed under each note are saved beside it in `<file>.vf.json`.

`.github/workflows/song-index.yml` rewrites `songs/index.json`, the list the site reads, after every change to the folder.

### Owner devices
Anyone can open and play the songs. Only a connected device can add, rename or delete them, or save notes under the notes. To connect one, open `…/Valve-Finder/#owner`, make a key on GitHub (a fine-grained personal access token for the **Valve-Finder** repository with **Contents: Read and write**), and paste it. *Connect your phone* shows a QR code that connects a phone with the same key. The key stays in that browser. Songs added on a device that isn't connected stay on that device.

## Images and fonts
Everything the page shows is stored in this repository, so the site keeps working on its own.

- **Clio**, detail of Johannes Vermeer, *The Art of Painting* (c. 1666–68), Kunsthistorisches Museum, Vienna. Public domain. `assets/clio-vermeer.jpg`
- **Silk**, *Piece*, Italian (possibly Genoa), 17th–18th century, silk and metal thread, The Metropolitan Museum of Art, [30.95.68](https://www.metmuseum.org/art/collection/search/222358). Public domain (Met Open Access). Recoloured into `assets/textile-light.jpg` (ochre on parchment) and `assets/textile-dark.jpg` (gold on navy).
- Other public-domain textiles considered for the design are kept in `assets/source/`; `assets/sources.txt` lists where each came from.
- **Fonts:** [EB Garamond](https://github.com/octaviopardo/EBGaramond12) and [IM Fell French Canon](https://iginomarini.com/fell/) (the Fell Types, cut in the 1670s), both under the SIL Open Font License; licences in `assets/fonts/`.

`.github/workflows/fetch-images.yml` downloads anything listed in `assets/sources.txt` and commits it.

## How it's built
One self-contained page, `index.html`, served by GitHub Pages. No build step.

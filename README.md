# Valve Finder

B♭ trumpet valve fingerings under every note of a song, with a song library.

**Live site:** https://lordfran28.github.io/Valve-Finder/

## What it reads
- **MusicXML** (`.musicxml`, `.xml`, `.mxl`) from Klangio, Scan2Notes, MuseScore and most notation apps
- **MIDI** (`.mid`) from Basic Pitch or any notation app
- **Tony note lists** (`.csv`: onset seconds, frequency in Hz, duration seconds)

## Your songs
Every song is a file in the [`songs`](songs/) folder of this repository, so the site shows the same library on every phone and computer.

- **From your computer, automatically:** `tools/pc-upload/` is a small Windows script that watches a folder (on the PC: *Music Studio\MIDI Valve Finder Songs*) and adds every new song file to `songs/` within a minute or two. It only adds or updates, never deletes, and skips files whose contents are already on the site under any name. Run *Set up automatic upload* once; it starts with Windows after that.
- **From your computer, by hand:** put MIDI, MusicXML or Tony files in `songs/` (subfolders are fine), then commit and push in GitHub Desktop, or upload them at https://github.com/lordfran28/Valve-Finder/upload/main/songs.
- **From the site:** on a device connected as owner, *Add a song* puts the file in `songs/` for you. Titles, settings and the notes typed under each note are saved beside it in `<file>.vf.json`.

`.github/workflows/song-index.yml` rewrites `songs/index.json`, the list the site reads, after every change to the folder.

### Owner devices
Anyone can open and play the songs. Only a connected device can add, rename or delete them, or save notes under the notes. To connect one, open `…/Valve-Finder/#owner`, make a key on GitHub (a fine-grained personal access token for the **Valve-Finder** repository with **Contents: Read and write**), and paste it. *Connect your phone* shows a QR code that connects a phone with the same key. The key stays in that browser. Songs added on a device that isn't connected stay on that device.

## Images and fonts
Everything the page shows is stored in this repository, so the site keeps working on its own.

- **Clio**, detail of Johannes Vermeer, *The Art of Painting* (c. 1666–68), Kunsthistorisches Museum, Vienna. Public domain. `assets/clio-vermeer.jpg`
- **Silk**, *Piece*, Italian (possibly Genoa), 17th–18th century, silk and metal thread, The Metropolitan Museum of Art, [30.95.68](https://www.metmuseum.org/art/collection/search/222358). Public domain (Met Open Access). Recoloured into `assets/textile-light.jpg` (ochre on parchment) and `assets/textile-dark.jpg` (gold on navy).
- Other public-domain textiles considered for the design are kept in `assets/source/`; `assets/sources.txt` lists where each came from.
- **Trumpet sound:** University of Iowa Electronic Music Studios, [Musical Instrument Samples](https://theremin.music.uiowa.edu/MISBbtrumpet.html), B♭ trumpet (Bach Stradivarius) played by Aren Van Houzen, 2003, "used for any projects, without restrictions". Cut into one mp3 per note in `assets/trumpet/` (sets: `mf`, `vib` = mf with vibrato, `ff`, `pp`; file name = concert MIDI note; `manifest.json` holds each note's tuning correction and sustain loop).
- **Background paintings** (`assets/art/`): an angel playing a natural trumpet, from a Baroque fresco, and Gerrit Dou's Trumpet Player in front of a Banquet (c. 1660–65, Louvre; public domain), both sent by Francisco. They drift up slowly as you scroll and come round again. Each is tinted into the palette (ochre ink for light mode, gold for dark) and feathered so it sits in the silk.
- **Fonts:** [EB Garamond](https://github.com/octaviopardo/EBGaramond12) and [IM Fell French Canon](https://iginomarini.com/fell/) (the Fell Types, cut in the 1670s), both under the SIL Open Font License; licences in `assets/fonts/`.

`.github/workflows/fetch-images.yml` downloads anything listed in `assets/sources.txt` and commits it.

## How it's built
One self-contained page, `index.html`, served by GitHub Pages. No build step.

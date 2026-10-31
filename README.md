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

## How it's built
One self-contained file, `index.html`, served by GitHub Pages. No build step and no dependencies apart from Google Fonts.

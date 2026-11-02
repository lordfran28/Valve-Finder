# Songs

Every song on Valve Finder is a file in this folder. The site lists whatever is here.

**To add songs from your computer:** put MIDI (.mid), MusicXML (.musicxml, .xml, .mxl) or Tony note-list (.csv) files in this folder, then commit and push in GitHub Desktop. They appear on the site, on every device, a minute or two later. Subfolders are fine.

**To add songs from the site:** open the site's owner page on a connected device and use *Add a song* as usual. The site puts the file here for you.

The file name becomes the song's title. A file ending in `.vf.json` next to a song holds what you set on the site: its title, settings and the notes under each note, plus its category (classical, contemporary or anthems) and, for some songs, the details entry shown under it. Leave those in place; delete one together with its song.

`index.json` is rewritten automatically after every change. Don't edit it by hand.

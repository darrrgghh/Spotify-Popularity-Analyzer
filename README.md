# Spotify Popularity Analyzer

**Version: 0.5**

This is a desktop Python application for analyzing the popularity of artists' releases on Spotify. It uses the Spotify API and allows you to:

- Search for artists  
- Browse their discographies
- View the popularity of all and each release, as well as tracks (with graphs)  
- Filter releases by keywords (e.g., `live`, `remastered`, `demo`)  
- Export popular albums and tracks to a text file  
- Manually exclude unwanted releases  
- Log in using your own Spotify API keys  
- Log out to remove saved credentials

---

## How to Use

1. Get your **Client ID** and **Client Secret** from [Spotify for Developers](https://developer.spotify.com/dashboard/applications)  
2. On first launch, the app will ask for your credentials and save them to `.spotify_credentials`  
3. Enter an artist name and click **Search**  
4. Select the desired artist and explore their data  
5. Use the **File → Export Popularity...** menu to export data  
6. Open **Settings** to adjust filters and the number of albums/tracks to export

---

## Interface

- Left panel: artist matches and discography  
- Right panel: popularity graphs (albums and tracks)  
- Top bar: search field  
- Menu bar: export, settings, raw data, exit, about

---

## Building Executables

### Windows:

```bash
pyinstaller --onefile --noconsole popularity.py --hidden-import=spotipy
```


### macOS:

1. Make sure `pyinstaller` is installed:

```bash
pip install pyinstaller
```

2. Build using the provided popularity.spec file (recommended):

```bash
pyinstaller --onefile --windowed popularity.py --hidden-import=spotipy
```
Alternatively, you can build manually like this:

```bash
pyinstaller --onefile --windowed popularity.py --hidden-import=spotipy
```

3. Run the resulting file from `dist/`:

> If blocked by macOS Gatekeeper, allow the app in **System Settings → Privacy & Security**.

---

## Files

- `popularity.py` — main GUI  
- `auth_handler.py` — handles login and credentials storage  
- `.spotify_credentials` — your saved API keys (hidden file, or not so hidden actually)  
- `.spotify_credentials` — your saved API keys (sort of hidden file)
- `popularity.spec` — PyInstaller build specification
- `splash.png` — splash screen image
- `ico.ico` — app icon (required for builds). Currently, for Windows only.
- `README.md` — you're reading me


---

## Author

Alexey Voronin  
Georgia Tech, 2025  
avoronin3@gatech.edu  

---

## Designed with metalheads in mind 🤘

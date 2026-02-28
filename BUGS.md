# BalkGrab - Bug Tracking & Fix Plan

**Verzija:** 0.2.0-alpha
**Datum:** 2025-02-14 (ažurirano: 2026-02-15)

---

## Bug #1 - Preview video stane na ~50%
**Prioritet:** Srednji
**Opis:** Na nekim videima preview se zaustavi otprilike na polovici. Ne desi se na svakom videu.
**Fix:** Dodan `mediaStatusChanged` handler koji detektira `StalledMedia` status i automatski pokušava resume (seek + play). Također, dodan `noplaylist` flag na preview stream fetch.

**Status:** [x] FIXANO (v3 - dual stall detection)

**Implementirano rješenje (v3 - Dual stall detection):**
Dva mehanizma za detekciju stall-a:
1. **Qt StalledMedia signal** - Qt sam detektuje kad stream stane
2. **Timeout detekcija (v3 novo)** - ako se pozicija ne mijenja 5 sekundi zaredom, manualno triggeruje refresh

Recovery flow (oba mehanizma):
1. Zapamti poziciju → `_preview_auto_refreshing = True`
2. Fetch svježi stream URL od yt-dlp u background threadu
3. `setSource(novi_url)` + `play()`
4. `LoadedMedia` → `setPosition(stara_pozicija)` → nastavlja gdje je stao

**NAPOMENA:** Ovo je YouTube-side limitacija - stream URL-ovi expiraju nakon par minuta. Ne moze se 100% rijesiti, ali auto-refresh minimizira prekide.

**Odbačene alternative:**
- v1 (simple seek+play na isti URL) - ne rješava expired URL
- v2 (samo StalledMedia signal) - Qt ne okida signal uvijek kad se stream zamrzne

---

## Bug #2 - Search lista loada samo ~10 videa
**Prioritet:** Nizak (feature request)
**Opis:** Pretraga vraća samo prvih ~10 rezultata.
**Fix:** Dodan "Load More" button ispod rezultata. SearchWorker prima `count` parametar. Svaki klik učitava +10 rezultata (20, 30, 40...). Button se sakriva kad nema više rezultata. Dodane translacije za EN/DE/HR.

**Status:** [x] FIXANO

---

## Bug #3 - Build skripte za .deb, .rpm + AppImage
**Prioritet:** Nizak
**Opis:** Trebamo build skripte za Linux pakete.
**Fix:** Kreiran `build-scripts/` folder sa:
- `build-deb.sh` - gradi .deb paket (za Ubuntu/Debian/Mint)
- `build-rpm.sh` - gradi .rpm paket (za Fedora/RHEL/openSUSE)
- `build-appimage.sh` - gradi AppImage (univerzalni Linux)
Svaka skripta: kopira fajlove, kreira venv, instalira deps, pakuje sa ikonicama i .desktop fajlom.
Windows .exe ostaje TODO (treba Windows mašina).

**Status:** [x] FIXANO (Linux paketi, .exe TODO)

---

## Bug #4 - Age-restricted videi ne rade (cookies)
**Prioritet:** Srednji
**Opis:** Videi s age restriction javljaju grešku: "Sign in to confirm your age".
**Fix:** Dodana opcija "Browser cookies" u Settings (None/Firefox/Chrome/Chromium/Brave/Edge). Kad je browser odabran, `cookiesfrombrowser` se proslijeđuje svim yt-dlp pozivima (download, fetch_video_info, preview stream).

**Status:** [x] FIXANO

---

## Bug #5 - "Cannot find" poruka za fajlove s navodnicima u imenu
**Prioritet:** Visok
**Opis:** Nakon skidanja fajla čiji naziv sadrži navodnike, pojavi se "Cannot find" greška.
**Fix:** Umjesto ručnog konstruiranja filepath iz raw title-a, koristi se `ydl.prepare_filename(info)` koji vraća sanitizirani path identičan onome koji yt-dlp zapravo koristi na disku.

**Status:** [x] FIXANO

---

## Bug #6 - Preview layout se raspadne na malim ekranima (800px visina)
**Prioritet:** Visok
**Opis:** Na 1600x900 rezoluciji seeker/slider i Stop tipka idu preko video playera.
**Fix:** Kompletno redizajniran preview controls layout:
- Play/Stop tipka je sad mala okrugla ikonica (32x32) lijevo od seekera
- Sve kontrole u jednom redu: `[▶] [0:00] [===seeker===] [3:45] [vol_slider] [70%]`
- Thumbnail koristi min/max size umjesto fiksnog (280-320 x 158-180)
- Uklonjen nepotreban drugi red sa velikim Play dugmetom i spacerima

**Status:** [x] FIXANO

---

## Bug #7 - Pretraga putem YouTube linka ne radi / skida cijeli YouTube
**Prioritet:** KRITIČAN
**Opis:** Kad se unese YouTube URL s playlist parametrima, "Skini odmah" skida cijelu playlistu.
**Fix:**
1. Dodana `clean_youtube_url()` metoda koja parsira URL i uklanja `&list=`, `&index=` parametre
2. Dodan `'noplaylist': True` u SVE yt-dlp pozive (download audio, download video, fetch_video_info, preview stream)
3. Dodan import `urllib.parse` za URL parsiranje

**Status:** [x] FIXANO

---

## Bug #8 - "Skini odmah" tipka treba postati "Stop Download" (dinamična)
**Prioritet:** Srednji
**Opis:** "Skini odmah" tipka treba se pretvoriti u "Stop Download" kad je download aktivan.
**Fix:**
1. Download button sad mijenja tekst u "Stop Download" (lokalizirano) i boju u crvenu kad download počne
2. Klik na "Stop Download" poziva `cancel()` na DownloadWorkeru (koji baca exception u progress_hook)
3. Kad download završi/failuje, tipka se automatski resetira na "Download Now"
4. Dodan `_active_download_id` tracking i `_reset_download_btn()` helper
5. Dodane 'stop_download' translacije za EN/DE/HR

**Status:** [x] FIXANO

---

## Bug #9 - Skidanje cijele liste bez mogućnosti prekida
**Prioritet:** KRITIČAN (povezano s #7)
**Opis:** Korisnik je uspio pokrenuti skidanje cijele YouTube liste bez mogućnosti prekida.
**Fix:** Riješeno zajedno s Bug #7 (noplaylist + URL cleanup) i Bug #8 (Stop Download tipka).

**Status:** [x] FIXANO (zajedno s #7 i #8)

---

## Bug #10 - Dvoklik na system tray ikonicu ne vraća prozor
**Prioritet:** Srednji
**Opis:** Dvoklik na system tray ikonu ne diže program natrag u fokus.
**Fix:** Promijenjen `tray_activated()`:
- `self.show()` → `self.showNormal()` (radi kad je prozor bio hidden/minimized)
- Dodano `self.setWindowState(self.windowState() & ~Qt.WindowMinimized)` za clear minimized flag
- Dodan `Trigger` (single click) pored `DoubleClick` - KDE/Plasma ne šalje DoubleClick uopšte, samo Trigger

**Status:** [x] FIXANO

---

## Bug #11 - Stop tipka ostaje aktivna nakon zatvaranja playera
**Prioritet:** Nizak (poznat, dokumentiran u README)
**Opis:** Nakon što se vanjski player (VLC, MPV) zatvori, Stop tipka ostaje u aktivnom stanju.
**Fix:** Dodan QTimer (`_ext_player_timer`) koji svaku sekundu provjerava `poll()` na external player procesu. Kad se player zatvori (returncode != None), automatski resetira Play/Stop button i now_playing label.

**Status:** [x] FIXANO (može se ukloniti iz Known Bugs u README)

---

## Bug #12 - Simultano sviranje zvuka iz preview-a i downloads playera
**Prioritet:** Srednji
**Opis:** Ako pustite preview jednog videa, pa odete u Downloads i pustite drugi, oba sviraju istovremeno. Nema načina da zaustavite oba odjednom.
**Fix:** Dodana `stop_all_audio()` metoda koja gasi preview player i downloads player. Poziva se prije svakog novog playback-a (preview, downloads play, external player).

**Status:** [x] FIXANO

---

## Bug #13 - Radio/Mix playlist URL i dalje skida cijelu listu
**Prioritet:** Visok
**Opis:** URL sa `&list=RD...&start_radio=1` parametrima i dalje pokreće download cijele radio playlist.
**Fix:**
1. `set_direct_url()` detektuje `list` ili `start_radio` parametre i prikazuje QMessageBox pitanje korisniku
2. Ako korisnik odabere "Yes", URL se čisti na samo `?v=` parametar
3. Ako korisnik odabere "No", operacija se prekida
4. Dodan safety check u `fetch_video_info()` - ako yt-dlp vrati `entries` (playlist), koristi samo prvi entry

**Status:** [x] FIXANO

---

## Bug #14 - Direktan YouTube link ne prikazuje video u search listi
**Prioritet:** Srednji
**Datum:** 2026-02-14
**Opis:** Kad se zalijepi YouTube URL, video se učita u preview ali se NE pojavi u search listi. Korisnik nema opciju za Play jer `set_direct_url()` zaobilazi kompletno listu rezultata.
**Fix:**
1. `set_direct_url()` više ne postavlja `selected_video` direktno
2. `fetch_video_info()` sad emituje video kao search result: `signals.search_results.emit([video])`
3. Video se pojavi u listi kao jedan rezultat - klikneš na njega i dobiješ preview/play opciju, identično kao kad tražiš
4. Uklonjena nepotrebna `_update_preview_info()` metoda

**Status:** [x] FIXANO

---

## Bug #15 - "Buffering, please wait..." label ne nestaje nakon seek-a
**Prioritet:** Nizak (UX poboljšanje)
**Datum:** 2026-02-14
**Opis:** Kad se koristi seeker u preview-u, treba par sekundi da se stream buffer-a na novoj poziciji. Nije bilo nikakvog feedback-a korisniku. Dodan "Buffering, please wait..." label, ali se nije pouzdano gasio jer `BufferedMedia` status ne okida uvijek.
**Fix:**
1. `preview_seek_position()` postavlja status label na "Buffering, please wait..." kad je preview aktivan
2. `on_preview_state_changed()` detektuje `PlayingState` i vraća label na "Playing preview..."
3. `on_preview_media_status()` također prati `BufferedMedia` kao backup

**Status:** [x] FIXANO

---

## Dodatno urađeno (nije bilo u originalnoj listi)

- [x] Kreirane play/stop ikonice (PNG svi formati + ICO za Windows) u `Icons/`
- [x] Preview play/stop button koristi ikonice umjesto tekst karaktera
- [x] Svi komentari u kodu prebačeni sa bosanskog na engleski
- [x] Kreiran `requirements.txt` (PySide6, yt-dlp, requests)
- [x] Kreiran `.venv/` sa svim zavisnostima
- [x] Kreiran `build-scripts/` folder (build-deb.sh, build-rpm.sh, build-appimage.sh)

---

## Session log - 2026-02-14

### Danas urađeno:
- Bug #12: Simultano sviranje - `stop_all_audio()` gasi sve playere prije novog playback-a
- Bug #13: Radio/Mix playlist URL - QMessageBox prompt + URL cleanup + safety check u `fetch_video_info()`
- Bug #14: Direktan link sad prikazuje video u search listi (emituje kao search result)
- Bug #15: "Buffering, please wait..." feedback pri seek-u + auto-hide kad muzika krene

### Poznati zajeb od prekjučer (2026-02-12):
- Program se zvao "BalkTube" što je zvučalo kao porno sajt 💋🤣
- Preimenovan u "BalkGrab" - čisto, profesionalno, i ne izgleda NSFW
- Zajedno s preimenovanjem pushnut sjebani kod na GitHub koji je trebao bug fixing session

---

## Bug #16 - Pametno playlist handling sa autodetekcijom
**Prioritet:** Srednji (feature request iz txt fajla)
**Datum:** 2026-02-14
**Opis:** Kad se zalijepi playlist URL, program je samo pitao "load single video? Yes/No" bez info o playlisti. Korisnik nije mogao vidjeti koliko videa ima niti učitati cijelu listu.
**Fix:**
1. Kad se detektuje playlist URL (`list` ili `start_radio` param), prvo se dohvata playlist info u pozadini sa `extract_flat: True`
2. Prikaže se dialog: "Ova playlista sadrži N videa" sa 3 opcije:
   - "Prikaži prvi video" - čisti URL i učitava samo jedan video (dosadašnje ponašanje)
   - "Prikaži svih N videa" - svi videi iz playliste se pojave u search rezultatima
   - "Odustani" - ništa se ne desi
3. Novi signal `playlist_info` za komunikaciju background thread → GUI
4. Nova metoda `fetch_playlist_info()` (background) i `on_playlist_info()` (GUI slot)
5. Sve lokalizirano na EN/DE/HR

**Status:** [x] FIXANO

---

## Bug #17 - Status bar za globalni feedback
**Prioritet:** Srednji (UX poboljšanje)
**Datum:** 2026-02-14
**Opis:** Program nije imao centralno mjesto za prikazivanje statusa operacija (search, download, playlist, greške).
**Fix:**
1. Dodan `QStatusBar` na dnu glavnog prozora
2. Helper `set_statusbar(message, error=False)` - zeleni font za normalne poruke, crveni za greške
3. Hookano na sve evente: search, playlist detection, download start/progress/complete/fail, settings saved, thumbnail loading
4. "Settings saved" poruka se sad prikazuje i u status baru

**Status:** [x] FIXANO

---

## Bug #18 - Checkbox selekcija za playlist videe
**Prioritet:** Srednji (feature request)
**Datum:** 2026-02-14
**Opis:** Kad se učita playlista, korisnik nije mogao odabrati koje videe želi skinuti - mogao je samo jedan po jedan.
**Fix:**
1. Dodan `QCheckBox` na svaki `VideoItemWidget` (skriven po defaultu, vidljiv samo u playlist modu)
2. Select All / Deselect All / Download Selected tipke u select baru iznad liste
3. `_playlist_mode` flag kontrolira vidljivost checkboxova i Load More buttona
4. Status bar prikazuje "N of M videos selected and ready to download"
5. `download_selected_videos()` batch download svih označenih videa

**Status:** [x] FIXANO

---

## Bug #19 - Thumbnail loading bez feedbacka
**Prioritet:** Nizak (UX poboljšanje)
**Datum:** 2026-02-14
**Opis:** Kad se učita playlista sa puno videa, thumbnailovi se skidaju u pozadini bez ikakvog vizualnog feedbacka.
**Fix:**
1. Dodani `_thumbnail_total` / `_thumbnail_loaded` brojači
2. Status bar prikazuje progress: "Loading thumbnails... 15/50"
3. Kad završi: "All thumbnails loaded"

**Status:** [x] FIXANO

---

## Bug #20 - Clipboard interceptor + Paste tipka
**Prioritet:** Srednji (feature request iz txt fajla)
**Datum:** 2026-02-14
**Opis:** Korisnik mora ručno desni klik → paste za lijepljenje YouTube linka. Nema autodetekcije clipboard-a.
**Fix:**
1. `on_clipboard_changed()` - prati `QApplication.clipboard().dataChanged`, automatski detektuje YouTube URL u clipboard-u i popuni search polje
2. `paste_from_clipboard()` - lijepi sadržaj clipboard-a i automatski pokreće search ako je YouTube URL
3. 📋 Paste tipka ugrađena unutar search polja (desna strana) kao `QToolButton`

**Status:** [x] FIXANO

---

## Bug #21 - Layout optimizacija za male ekrane (750px)
**Prioritet:** Visok
**Datum:** 2026-02-14
**Opis:** Na ekranima visine 900px (1600x900) i uz Windows taskbar (~50px), UI elementi se preklapaju.
**Fix:**
1. Minimalna visina prozora: 650px, početna: 1100x750
2. Kompaktirani margini i spacing kroz cijeli Search tab
3. Format sekcija u GroupBox-u sa jednorednim sadržajem
4. Status sekcija u GroupBox-u: label iznad progress bara, kompaktno
5. Download tipka gurnuta na dno sa `addStretch()`
6. Settings tab umotan u `QScrollArea` za male ekrane
7. Preview thumbnail smanjen na min 260x146

**Status:** [x] FIXANO

---

## Bug #22 - Verzija podignuta na 0.2.0-alpha
**Prioritet:** Info
**Datum:** 2026-02-14
**Opis:** Version bump sa svim novim featurima.
**Fix:**
1. `APP_VERSION = "0.2.0-alpha"`
2. README badge ažuriran
3. About sekcija ažurirana u sva 3 jezika (EN/DE/HR) sa novim featurima

**Status:** [x] FIXANO

---

## Dodatno urađeno - Session 2 (2026-02-14)

- [x] Playlist dropdown za velike liste (učitaj prvih 20/50/100/sve) umjesto fiksnog "show all"
- [x] `stop_all_audio()` gasi sve playere prije novog playback-a (Bug #12)
- [x] Load More button se sakriva u playlist modu (da ne briše učitane rezultate)
- [x] Downloads tab - potvrđeno da QTableWidget ima ugrađeni scroll za 10+ videa

## Dodatno urađeno - Session 3 (2026-02-14, kasno uveče)

- [x] Bug #10: System tray klik FIXANO - dodan `Trigger` (single click) pored `DoubleClick` za KDE/Plasma kompatibilnost
- [x] "Settings saved" poruka se sad prikazuje u status baru (zeleno)
- [x] Paste tipka premještena unutar search polja kao `QToolButton` (28x28, emoji 📋)
- [x] README: dodana Acknowledgements sekcija (yt-dlp, PySide6, FFmpeg, Requests)

---

## Bug #23 - yt-dlp remote_components pogrešan option name
**Prioritet:** KRITIČAN
**Datum:** 2026-02-15
**Opis:** Kod je koristio `allow_remote_components` umjesto `remote_components` - yt-dlp je tiho ignorisao opciju, YouTube JS challenge solver se nikad nije aktivirao. Preview, download i fetch_video_info su svi bili pokvareni.
**Fix:**
1. Preimenovano `allow_remote_components` → `remote_components` na 3 mjesta (audio download, video download, preview stream)
2. Dodano `remote_components: ['ejs:github']` u `fetch_video_info()` i `fetch_playlist_info()` gdje je nedostajalo
3. Instaliran deno runtime (~/.deno/bin/) za YouTube JS challenge solving

**Status:** [x] FIXANO

---

## Bug #24 - Cookie browser se ne auto-detektuje
**Prioritet:** Srednji
**Datum:** 2026-02-15
**Opis:** Default za cookie browser je bio "" (disabled). Korisnik je morao ručno otići u Settings i odabrati browser.
**Fix:**
1. Dodana `detect_default_browser()` metoda - provjerava cookie database putanje za Firefox, Chrome, Chromium, Brave, Edge
2. Podržava i Linux i Windows putanje
3. Na prvom pokretanju automatski detektuje i spremi browser

**Status:** [x] FIXANO

---

## Bug #25 - Clipboard interceptor hvata debug output kao YouTube URL
**Prioritet:** Nizak
**Datum:** 2026-02-15
**Opis:** Debug output koji sadrži "youtube.com/watch" u tekstu je bio detektovan kao YouTube link.
**Fix:** Nova `is_youtube_url()` metoda - tekst mora počinjati sa `http://`, `https://` ili `www.` da bi bio prihvaćen.

**Status:** [x] FIXANO

---

## Bug #26 - Nedostupni videi nemaju error feedback
**Prioritet:** Srednji
**Datum:** 2026-02-15
**Opis:** Kad video nije dostupan (live stream, private, geo-restricted), korisnik je vidio samo "No results found" bez objašnjenja.
**Fix:**
1. `fetch_video_info()` čuva error poruku u `_last_fetch_error`
2. `on_search_results()` prikazuje specifičnu grešku u statusbaru crveno
3. Search error iz SearchWorkera koji se gubio u download error handleru - dodan handling za `download_id == "search"`

**Status:** [x] FIXANO

---

## Bug #27 - Download/konverzija status poruke neadekvatne
**Prioritet:** Nizak (UX)
**Datum:** 2026-02-15
**Opis:** Status u tabeli je govorio samo "Audio"/"Video" po završetku. Statusbar je imao generički "Download complete" za sve.
**Fix:**
1. Audio: "Downloading..." → "Converting..." → "Converted" + statusbar "Download and conversion complete"
2. Video: "Downloading..." → "Merging..." → "Complete" + statusbar "Download complete"
3. Notification poruke razlikuju audio/video

**Status:** [x] FIXANO

---

## Bug #28 - Minimize to tray killuje muziku
**Prioritet:** Srednji
**Datum:** 2026-02-15
**Opis:** Kad se prozor zatvori sa minimize to tray uključen, `closeEvent` je uvijek zaustavljao sve playere.
**Fix:** Dodan "Continue playing when minimized to tray" checkbox u Settings (default: OFF). Kad je upaljen, `closeEvent` ne dira playere pri sakrivanju u tray.

**Status:** [x] FIXANO

---

## Bug #29 - Media keys ne rade
**Prioritet:** Nizak
**Datum:** 2026-02-15
**Opis:** Tipkovnice sa media keys (Play/Pause/Stop) nisu kontrolisale playback.
**Fix:** Testirano sa `keyPressEvent` handlerom - ne radi na Linuxu jer media keys idu kroz D-Bus/MPRIS, ne Qt key events. Kod uklonjen - MPRIS implementacija nije vrijedna za app koji nije media player.

**Status:** [x] ZATVORENO (won't fix - Linux limitacija)

---

## Bug #30 - Ikone nesređene, nepotrebne veličine
**Prioritet:** Nizak (cleanup)
**Datum:** 2026-02-15
**Opis:** 20 ikona u jednom folderu, 16 nekorištenih, duplikati u Icons/new/.
**Fix:**
1. Reorganizirano u `Icons/linux/` (8 PNG) i `Icons/windows/` (3 ICO)
2. Obrisane nekorištene veličine play/stop (16, 24, 48, 64px)
3. Obrisan `Icons/new/` folder (duplikati, icon_48x48.png sačuvan)
4. Ažurirane sve reference u BalkGrab.py, setup.sh, i build skriptama

**Status:** [x] FIXANO

---

## Dodatno urađeno - Session 4 (2026-02-15)

- [x] Build skripte updateovane sa 0.1.2 na 0.2.0-alpha
- [x] Search results redizajnirani (card efekat, ravnomjerni borderi, bolji hover/selected stilovi)
- [x] deno instaliran za yt-dlp JS challenge solving
- [x] Obrisan `bugovi tokom koristenja.txt` (svi bugovi riješeni)

---

## Bug #31 - Downloads tab nema context menu
**Prioritet:** Srednji (feature request)
**Datum:** 2026-02-15
**Opis:** Desni klik na skinuti fajl u Downloads tabu nije radio ništa. Korisnik nije mogao konvertirati fajl, ponovo skinuti, ili ukloniti sa liste bez "Clear Completed".
**Fix:**
1. Dodan desni klik context menu na `QTableWidget` sa opcijama:
   - **▶ Play** - pokreće playback (isti kao Play button)
   - **📂 Open containing folder** - otvara folder u file manageru
   - **⬇ Download again** - prebacuje na Search tab sa URL-om i pokreće search
   - **🔄 Convert to →** submenu: MP3, MP4, FLAC, WAV, OGG, AAC (FFmpeg u pozadini)
   - **🗑 Remove from list** - uklanja sa liste (ne briše fajl sa diska)
2. Konverzija koristi `subprocess.Popen` + `QTimer` polling - ne blokira GUI
3. Status bar feedback: "Converting to MP3..." → "Converted to MP3"
4. Zaštita: ne dozvoljava konverziju u isti format, izbjegava overwrite (dodaje `_1`, `_2`)
5. Sve lokalizirano na EN/DE/HR

**Status:** [x] FIXANO

---

## Dodatno urađeno - Session 5 (2026-02-15)

- [x] Novi screenshotovi (search, downloads, settings, about) kopirani u `.github/screenshots/`
- [x] README ažuriran sa "File Conversion" featurom
- [x] BUGS.md ažuriran sa Bug #31 i session 5 logom
- [x] Bug #29 zatvoren kao "won't fix" (media keys ne rade na Linuxu bez MPRIS)

---

---

## Bug #32 - Windows system tray ikonica se ne pojavljuje
**Prioritet:** Visok
**Datum:** 2026-02-25
**Opis:** Na Windowsu system tray ikonica nije bila vidljiva. Kad je "Minimize to tray" upalijen i prozor se zatvori, app radi u pozadini ali ikonica je nevidljiva/blank → korisnik zarobljen, ne može otvoriti app.
**Uzrok:** Svi icon pathovi bili hardcoded na `Icons/linux/` koji ne postoji na Windows instalaciji. Qt je postavljao tray ikonu bez fajla → blank/transparent ikona. `tray_icon.isVisible()` je i dalje vraćao `True` → `closeEvent` skrivao prozor u tray umjesto zatvaranja.
**Fix:**
1. Dodana `ICON_DIR = "windows" if sys.platform == "win32" else "linux"` konstanta (linija 64)
2. Sve icon reference zamijenjene sa `ICON_DIR` umjesto hardcoded `"linux"`
3. U `setup_system_tray()`: Windows koristi `Icons/windows/icon.ico` (fallback: `icon_64x64.png`)
4. Zahvaćene lokacije: window icon, app icon, play/stop ikone, system tray setup

**Status:** [x] FIXANO

---

## Bug #33 - Windows build skripta ima pogrešan working directory
**Prioritet:** KRITIČAN
**Datum:** 2026-02-25
**Opis:** `build-windows.bat` radio `cd /d "%SCRIPT_DIR%"` → promijenio working dir u `build-scripts/` folder. Svi pathovi (`Icons\windows\icon.ico`, `Icons;Icons`, `BalkGrab.py`) bili relativni i nisu bili pronađeni → build pao, ikonica nije bila uključena.
**Fix:**
1. Promijenjeno `cd /d "%SCRIPT_DIR%"` → `cd /d "%SCRIPT_DIR%.."` (ide u repo root)
2. Output directories eksplicitno postavljeni na `build-scripts\dist\` i `build-scripts\build\`
3. Uklonjen `pywin32` (nije korišten u kodu)
4. Uklonjen stdlib hidden-imports (`logging`, `json`, `threading`, `urllib`, `http`) - PyInstaller ih uključuje automatski
5. Ffmpeg copy popravljeno: `for /f` loop sa `where ffmpeg` umjesto broken wildcard `copy Python*\ffmpeg.exe`
6. Dodat automatski PowerShell download ffmpega iz GitHub (yt-dlp/FFmpeg-Builds) ako nije pronađen lokalno

**Status:** [x] FIXANO

---

## Dodatno urađeno - Session 6 (2026-02-25)

- [x] Bug #32: Windows tray ikonica nevidljiva - FIXANO (`ICON_DIR` konstanta, platform-aware paths)
- [x] Bug #33: Windows build skripta path bug - FIXANO (`cd` na repo root, ffmpeg auto-download)
- [x] Obrisani nepotrebni fajlovi: `Novi screenshoti/`, `Screenshot_20260215_113349.png`, `download complete copying al gdje.png`
- [x] README ažuriran: Windows release sada uključuje ffmpeg, dodat `setup.sh` za Linux source install, poboljšan Uninstall section

---

## Preostalo za uraditi

1. Windows .exe build za 0.2.0-alpha (build skripta je sad ispravna, treba Windows mašina)
2. Automatski testovi
3. Push sve fixeve na GitHub

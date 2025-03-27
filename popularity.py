#!/usr/bin/env python3
import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext, filedialog
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
import matplotlib
matplotlib.use("TkAgg")
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
import json
import sys
import os
import datetime
from auth_handler import load_credentials, prompt_for_credentials
from auth_handler import save_credentials, delete_credentials
from PIL import ImageTk, Image
import time

creds = load_credentials()
if not creds:
    prompt_for_credentials()
    creds = load_credentials()
    if not creds:
        sys.exit()

client_id = creds["client_id"]
client_secret = creds["client_secret"]


class SpotifyAnalyzer(tk.Tk):
    # ------------------------------
    # UI Functions & stuff
    # ------------------------------
    def __init__(self, client_id, client_secret):
        super().__init__()
        self.title("Spotify Popularity Analyzer")
        self.geometry("1200x800")
        self.minsize(800, 600)
        self.resizable(True, True)
        # Set up Spotipy authentication with error handling (e.g., when there's no internet connection or no spotify API credentials)
        try:
            auth_manager = SpotifyClientCredentials(client_id=client_id, client_secret=client_secret)
            self.sp = spotipy.Spotify(auth_manager=auth_manager)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to authenticate with Spotify: {e}")
            self.destroy()
            return
        self.artist_id = None
        self.artist_name = None
        self.albums = []
        self.current_album_tracks = []
        self.settings = {
            "types": ["album", "single", "compilation"],
            "filters": [],  # По умолчанию — без фильтрации
            "albums_to_export": "3",
            "tracks_to_export": "5",
            "sort_order": "Descending"
        }

        self._create_menubar()
        self._create_main_layout()

    def _create_menubar(self):
        menubar = tk.Menu(self)
        self.config(menu=menubar)

        file_menu = tk.Menu(menubar, tearoff=False)
        menubar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="Export Popularity...", command=self.export_popularity)
        file_menu.add_command(label="Raw Data", command=self.show_raw_data)
        file_menu.add_command(label="Settings", command=self.open_settings_window)
        file_menu.add_separator()
        file_menu.add_command(label="Log Out", command=self.logout_spotify)
        file_menu.add_command(label="Exit", command=self.destroy)

        help_menu = tk.Menu(menubar, tearoff=False)
        help_menu.add_command(label="About...", command=self.show_about)
        menubar.add_cascade(label="Help", menu=help_menu)

    def logout_spotify(self):
        if messagebox.askyesno("Log Out", "Are you sure you want to log out from Spotify API?"):
            delete_credentials()
            messagebox.showinfo("Logged Out", "Credentials removed. Please restart the app.")
            self.destroy()
            sys.exit()

    def open_settings_window(self):
        settings_win = tk.Toplevel(self)
        if hasattr(sys, "_MEIPASS"):
            base_path = sys._MEIPASS
        else:
            base_path = os.path.abspath(".")
        icon_path = os.path.join(base_path, "ico.ico")
        settings_win.iconbitmap(icon_path)
        settings_win.title("Settings")
        settings_win.geometry("400x400")
        settings_win.resizable(False, False)
        settings_win.focus_force()
        settings_win.grab_set()
        settings_win.transient(self)

        label_font = ("Arial", 11, "bold")
        checkbox_font = ("Arial", 10)

        # Секция: Типы релизов
        tk.Label(settings_win, text="To Look For:", font=label_font, fg='black').grid(row=0, column=1, sticky="w", padx=10,
                                                                                   pady=(10, 0))
        self.release_types = {
            key: tk.BooleanVar(value=(key in self.settings["types"]))
            for key in ["album", "single", "compilation"]
        }
        for i, (rtype, var) in enumerate(self.release_types.items()):
            tk.Checkbutton(settings_win, text=rtype.capitalize(), variable=var, font=checkbox_font).grid(row=1,
                                                                                                         column=i,
                                                                                                         padx=10,
                                                                                                         sticky="w")

        # Секция: Фильтрация по ключевым словам
        tk.Label(settings_win, text="To Filter Out:", font=label_font, fg='black').grid(row=2, column=1, sticky="w",
                                                                                        padx=10, pady=(15, 0))

        keywords_list = ["demo", "live", "remastered", "edition", "deluxe", "reissue", "remix", "edit", "feat",
                         "instrumental"]
        self.filter_keywords = {
            key: tk.BooleanVar(value=(key in self.settings["filters"]))
            for key in keywords_list
        }

        # Select All checkbox
        self.select_all_var = tk.BooleanVar()

        def toggle_all_filters():
            select_all = self.select_all_var.get()
            for var in self.filter_keywords.values():
                var.set(select_all)

        tk.Checkbutton(
            settings_win, text="Select All", variable=self.select_all_var,
            font=("Arial", 9, "italic"), command=toggle_all_filters
        ).grid(row=3, column=0, padx=10, sticky="w")

        # Отображение всех фильтров
        for i, (keyword, var) in enumerate(self.filter_keywords.items()):
            row = 4 + i // 3
            col = i % 3
            tk.Checkbutton(settings_win, text=keyword.capitalize(), variable=var, font=checkbox_font).grid(
                row=row, column=col, padx=10, sticky="w"
            )

        # Кол-во альбомов и треков
        tk.Label(settings_win, text="Export Settings", font=label_font, fg='black').grid(row=9, column=1, sticky="w",
                                                                                         padx=10, pady=(20, 0))
        tk.Label(settings_win, text="Albums to export:", font=checkbox_font).grid(row=12, column=1, padx=10, sticky="w")
        self.album_export_var = tk.StringVar(value=self.settings.get("albums_to_export", "3"))
        album_options = ["1", "2", "3", "4", "5", "All"]
        ttk.OptionMenu(settings_win, self.album_export_var, self.album_export_var.get(), *album_options).grid(row=12,
                                                                                                              column=2,
                                                                                                              sticky="w")

        tk.Label(settings_win, text="Tracks per album:", font=checkbox_font).grid(row=14, column=1, padx=10,
                                                                                  pady=(10, 0), sticky="w")
        self.track_export_var = tk.StringVar(value=self.settings.get("tracks_to_export", "3"))
        track_options = ["1", "2", "3", "4", "5", "All"]
        ttk.OptionMenu(settings_win, self.track_export_var, self.track_export_var.get(), *track_options).grid(row=14,
                                                                                                              column=2,
                                                                                                              sticky="w")
        tk.Label(settings_win, text="Popularity order:", font=checkbox_font).grid(row=16, column=1, padx=10, sticky="w")
        self.sort_order_var = tk.StringVar(value=self.settings.get("sort_order", "Descending"))
        sort_options = ["Descending", "Ascending"]
        ttk.OptionMenu(settings_win, self.sort_order_var, self.sort_order_var.get(), *sort_options).grid(row=16,
                                                                                                         column=2,
                                                                                                         sticky="w")

        # Кнопка сохранить
        def save_and_close():
            self.settings = {
                "types": [k for k, v in self.release_types.items() if v.get()],
                "filters": [k for k, v in self.filter_keywords.items() if v.get()],
                "albums_to_export": self.album_export_var.get(),
                "tracks_to_export": self.track_export_var.get(),
                "sort_order": self.sort_order_var.get()
            }
            settings_win.destroy()
            if self.artist_id:
                self.fetch_albums()

        # Кнопки OK и Cancel в один ряд
        button_frame = ttk.Frame(settings_win)
        button_frame.grid(row=17, column=0, columnspan=3, pady=15)

        ttk.Button(button_frame, text="OK", command=save_and_close, width=10).pack(side=tk.LEFT, padx=10)
        ttk.Button(button_frame, text="Cancel", command=settings_win.destroy, width=10).pack(side=tk.LEFT, padx=10)

        # Центрирование окна Settings
        settings_win.update_idletasks()
        w, h = settings_win.winfo_reqwidth(), settings_win.winfo_reqheight()
        x = (settings_win.winfo_screenwidth() // 2) - (w // 2)
        y = (settings_win.winfo_screenheight() // 2) - (h // 2)
        settings_win.geometry(f"{w}x{h}+{x}+{y}")

    def _create_main_layout(self):
        # Top frame for the search bar
        top_frame = ttk.Frame(self)
        top_frame.pack(side=tk.TOP, fill=tk.X, padx=5, pady=5)
        top_frame.columnconfigure(0, weight=0)
        top_frame.columnconfigure(1, weight=1)
        ttk.Label(top_frame, text="Search Artist:").grid(row=0, column=0, sticky="w")
        self.search_entry = ttk.Entry(top_frame, width=30)
        self.search_entry.grid(row=0, column=1, sticky="ew", padx=5)
        self.search_entry.bind("<Return>", lambda e: self.search_artist())
        search_btn = ttk.Button(top_frame, text="Search", command=self.search_artist)
        search_btn.grid(row=0, column=2, padx=5)

        # Main horizontal Paned Window (left = artist/discography, right = charts)
        main_paned = tk.PanedWindow(self, orient=tk.HORIZONTAL, sashrelief=tk.RAISED)
        main_paned.pack(side=tk.TOP, fill=tk.BOTH, expand=True)

        # Left frame: Artist Matches + Discography
        left_frame = ttk.Frame(main_paned)
        left_frame.pack(fill=tk.BOTH, expand=True)
        ttk.Label(left_frame, text="Artist Matches:").pack(anchor=tk.NW)
        self.matches_listbox = tk.Listbox(left_frame, height=5)
        self.matches_listbox.pack(fill=tk.X)
        self.matches_listbox.bind("<<ListboxSelect>>", self.on_select_artist)
        ttk.Label(left_frame, text="Discography (Albums):").pack(anchor=tk.NW, pady=(10, 0))
        self.albums_listbox = tk.Listbox(left_frame, height=15)
        self.albums_listbox.pack(fill=tk.BOTH, expand=True)
        self.albums_listbox.bind("<<ListboxSelect>>", self.on_select_album)
        self.albums_listbox.bind("<Delete>", self.delete_selected_album)
        main_paned.add(left_frame, minsize=200)

        # Right Paned Window for charts (split vertically, but you can adjust any of these)
        right_paned = tk.PanedWindow(main_paned, orient=tk.VERTICAL, sashrelief=tk.RAISED)
        right_paned.pack(fill=tk.BOTH, expand=True)
        main_paned.add(right_paned, minsize=400)

        # Top sub-frame for the album chart
        album_frame = ttk.Frame(right_paned)
        album_frame.pack(fill=tk.BOTH, expand=True)
        album_pack_frame = ttk.Frame(album_frame)
        album_pack_frame.pack(fill=tk.BOTH, expand=True)

        # Create the album chart figure and axes
        self.album_fig = plt.Figure(figsize=(5, 3), dpi=100)
        self.album_ax = self.album_fig.add_subplot(111)
        self.album_ax.set_title("Album Popularity", fontsize=8)
        self.album_ax.tick_params(axis='x', labelsize=6)
        self.album_ax.tick_params(axis='y', labelsize=6)
        self.album_canvas = FigureCanvasTkAgg(self.album_fig, master=album_pack_frame)
        album_canvas_widget = self.album_canvas.get_tk_widget()
        album_canvas_widget.pack(side=tk.TOP, fill=tk.BOTH, expand=True)
        # Create and pack the toolbar for the album chart
        self.album_toolbar = NavigationToolbar2Tk(self.album_canvas, album_pack_frame)
        self.album_toolbar.update()
        self.album_toolbar.pack(side=tk.BOTTOM, fill=tk.X)
        right_paned.add(album_frame, minsize=200)

        # Bottom sub-frame for the track chart
        track_frame = ttk.Frame(right_paned)
        track_frame.pack(fill=tk.BOTH, expand=True)
        track_pack_frame = ttk.Frame(track_frame)
        track_pack_frame.pack(fill=tk.BOTH, expand=True)
        # Create the track chart figure and axes
        self.track_fig = plt.Figure(figsize=(5, 3), dpi=100)
        self.track_ax = self.track_fig.add_subplot(111)
        self.track_ax.set_title("Track Popularity", fontsize=8)
        self.track_ax.tick_params(axis='x', labelsize=6)
        self.track_ax.tick_params(axis='y', labelsize=6)
        self.track_canvas = FigureCanvasTkAgg(self.track_fig, master=track_pack_frame)
        track_canvas_widget = self.track_canvas.get_tk_widget()
        track_canvas_widget.pack(side=tk.TOP, fill=tk.BOTH, expand=True)
        # Create and pack the toolbar for the track chart
        self.track_toolbar = NavigationToolbar2Tk(self.track_canvas, track_pack_frame)
        self.track_toolbar.update()
        self.track_toolbar.pack(side=tk.BOTTOM, fill=tk.X)
        right_paned.add(track_frame, minsize=200)

    def _get_expanded_keywords(self):
        filters = self.settings.get("filters", [])
        alias_map = {
            "reissue": ["reissue", "re-issue"],
            "remix": ["remix", "remixed"],
            "remastered": ["remastered", "remaster"]
        }
        result = []
        for keyword in filters:
            if keyword in alias_map:
                result.extend(alias_map[keyword])
            else:
                result.append(keyword)
        return result

    def show_about(self):
        about_text = (
            "Spotify Popularity Analyzer 0.5\n"
            "\n"
            "Explore and analyze the popularity\n"
            "of albums and tracks using Spotify data.\n\n"
            "Features:\n"
            "  • Search and display artist discographies\n"
            "  • Filter releases by type and keywords\n"
            "  • Visualize popularity with graphs\n"
            "  • Export structured data on artist's popularty metrics\n"
            "  • Export raw data from Spotify API as .txt or .json\n"
            "  • More features to be introduced soon!\n"
            "  • Designed with metalheads in mind 🤘\n\n"
            "Voroshka software, 2025\n"
            "Alexey Voronin\n"
            "avoronin3@gatech.edu\n"
            "|     .-.\n"
            "|    /   \\         .-.\n"
            "|   /     \\       /   \\       .-.     .-.     _   _\n"
            "+--/-------\\-----/-----\\-----/---\\---/---\\---/-\\-/-\\/\\/---\n"
            "| /         \\   /       \\   /     '-'     '-'\n"
            "|/           '-'         '-'\n"
        )

        dialog = tk.Toplevel(self)
        if hasattr(sys, "_MEIPASS"):
            base_path = sys._MEIPASS
        else:
            base_path = os.path.abspath(".")
        icon_path = os.path.join(base_path, "ico.ico")
        dialog.iconbitmap(icon_path)
        dialog.title("About")
        dialog.resizable(False, False)
        dialog.focus_force()
        dialog.transient(self)
        dialog.grab_set()

        label = tk.Label(dialog, text=about_text, font=("Courier", 10), justify="left")
        label.pack(padx=15, pady=10)

        ok_btn = ttk.Button(dialog, text="OK", command=dialog.destroy)
        ok_btn.pack(pady=(0, 10))

        # Центрирование окна
        dialog.update_idletasks()
        w, h = dialog.winfo_reqwidth(), dialog.winfo_reqheight()
        x = (dialog.winfo_screenwidth() // 2) - (w // 2)
        y = (dialog.winfo_screenheight() // 2) - (h // 2)
        dialog.geometry(f"{w}x{h}+{x}+{y}")

    # ------------------------------
    # Spotify API Functions
    # ------------------------------
    def search_artist(self):
        # this function is called when the 'Search' button is clicked or the Enter key is pressed.
        # the app then asks Spotify for up to 5 matching artists and displays them in the matches listbox.
        # if you increase the number of matches, you'll need to scroll down the results, I didn't make any sliders for that.
        # Also, you're free to make typos or any mistakes in your inquiry. Normally, if artist name is correct, the first matching result is what you're looking for.

        query = self.search_entry.get().strip()
        if not query:
            messagebox.showinfo("Info", "Please enter an artist name.")
            return
        self.matches_listbox.delete(0, tk.END)
        try:
            results = self.sp.search(q=query, type='artist', limit=5) # feel free to increase/decrease this number if needed
        except Exception as e:
            messagebox.showerror("Error", f"Search failed: {e}")
            return
        artists = results['artists']['items']
        if not artists:
            self.matches_listbox.insert(tk.END, "No matches found.")
            return
        for artist in artists:
            entry = f"{artist['name']} ({artist['id']})"
            self.matches_listbox.insert(tk.END, entry)

    def on_select_artist(self, event):
        # this function is triggered when an artist is selected from the 'Artist Matches' listbox.
        selection = self.matches_listbox.curselection()
        if not selection:
            return
        idx = selection[0]
        text = self.matches_listbox.get(idx)
        if "No matches found." in text:
            return
        try:
            artist_id = text.split("(")[1].split(")")[0]
        except:
            messagebox.showerror("Error", "Unable to parse artist ID.")
            return
        try:
            artist_info = self.sp.artist(artist_id)
        except Exception as e:
            messagebox.showerror("Error", f"Artist retrieval failed: {e}")
            return
        self.artist_id = artist_id
        self.artist_name = artist_info["name"]
        # Reset filters to defaults on new artist selection
        self.settings = {
            "types": ["album", "single", "compilation"],  # appears_on отключён
            "filters": [],  # никаких ключевых фильтров
            "albums_to_export": "3",
            "tracks_to_export": "3"
        }
        self.current_album_tracks = []
        self.track_ax.clear()
        self.track_ax.set_title("Track Popularity")
        self.track_canvas.draw()
        self.fetch_albums()

    def fetch_albums(self):
        self.albums_listbox.delete(0, tk.END)
        self.albums.clear()
        offset = 0

        album_types = ",".join(self.settings.get("types", ["album"]))
        all_keywords = self._get_expanded_keywords()

        while True:
            try:
                results = self.sp.artist_albums(self.artist_id, album_type=album_types, limit=50, offset=offset)
            except Exception as e:
                messagebox.showerror("Error", f"Album retrieval failed: {e}")
                return

            items = results["items"]
            if not items:
                break

            for album in items:
                album_name = album.get("name", "")
                if any(kw in album_name.lower() for kw in all_keywords):
                    continue

                album_id = album["id"]
                try:
                    details = self.sp.album(album_id)
                    pop = details.get("popularity", 0)
                    release_date = details.get("release_date", "unknown")
                    release_year = release_date.split("-")[0]
                except Exception:
                    pop = 0
                    release_year = "????"
                self.albums.append((album_id, album_name, pop, release_year))

            offset += 50
            if len(items) < 50:
                break

        for (alb_id, alb_name, alb_pop, alb_year) in self.albums:
            display_str = f"{alb_name} ({alb_year}) [pop: {alb_pop}]"
            self.albums_listbox.insert(tk.END, display_str)

        self.update_album_graph()

    def update_album_graph(self):
        self.album_ax.clear()
        if not self.albums:
            self.album_ax.set_title("No Albums Found")
            self.album_canvas.draw()
            return
        sorted_albums = sorted(self.albums, key=lambda x: x[2], reverse=True)
        names = [f"{a[1]} ({a[3]})" for a in sorted_albums]
        pops = [a[2] for a in sorted_albums]
        self.album_ax.barh(names, pops, color="skyblue")
        self.album_ax.invert_yaxis()  # Highest popularity at the top
        self.album_ax.set_title(f"{self.artist_name} - Albums")
        self.album_ax.set_xlabel("Popularity")
        self.album_canvas.draw()

    def on_select_album(self, event):
        # This function is triggered when an album is selected from the discography listbox.
        selection = self.albums_listbox.curselection()
        if not selection:
            return
        idx = selection[0]
        if idx >= len(self.albums):
            return
        album_id, album_name, alb_pop, alb_year = self.albums[idx]
        try:
            album_tracks = self.sp.album_tracks(album_id, limit=50)['items']
        except Exception as e:
            messagebox.showerror("Error", f"Track retrieval failed: {e}")
            return
        self.current_album_tracks = []
        # List of keywords for filtering tracks
        filter_keywords = ["live", "remastered", "re-issue", "reissue", "demo"]
        for track in album_tracks:
            track_name = track.get("name", "")
            # Skip tracks whose name contains any of the filtered keywords
            # You can modify the keyword list or comment this section if you want to look through all albums
            if any(keyword in track_name.lower() for keyword in filter_keywords):
                continue
            track_id = track["id"]
            try:
                full_track = self.sp.track(track_id)
                track_pop = full_track.get("popularity", 0)
            except Exception:
                track_pop = 0
            self.current_album_tracks.append({
                "id": track_id,
                "name": track_name,
                "popularity": track_pop
            })
        self._update_track_graph(album_name, self.current_album_tracks)

    def delete_selected_album(self, event):
        # this functions allows you to delete selected item in discography. it also updates graphs.
        selection = self.albums_listbox.curselection()
        if not selection:
            return
        idx = selection[0]
        # Remove the album from the internal list
        del self.albums[idx]
        # Update the listbox
        self.albums_listbox.delete(0, tk.END)
        for (alb_id, alb_name, alb_pop, alb_year) in self.albums:
            display_str = f"{alb_name} ({alb_year}) [pop: {alb_pop}]"
            self.albums_listbox.insert(tk.END, display_str)
        # Update the album graph
        self.update_album_graph()
        # Clear the track graph since
        self.current_album_tracks = []
        self.track_ax.clear()
        self.track_ax.set_title("Track Popularity")
        self.track_canvas.draw()

    def _update_track_graph(self, album_name, track_list):
        # Updates the track popularity bar chart using the track data for the selected album
        self.track_ax.clear()
        if not track_list:
            self.track_ax.set_title("No Tracks Found")
            self.track_canvas.draw()
            return
        sorted_tracks = sorted(track_list, key=lambda x: x["popularity"], reverse=True)
        track_names = [t["name"] for t in sorted_tracks]
        track_pops = [t["popularity"] for t in sorted_tracks]
        self.track_ax.barh(track_names, track_pops, color="orange")
        self.track_ax.invert_yaxis()  # Highest popularity at the top
        self.track_ax.set_xlabel("Popularity")
        self.track_ax.set_title(f"Tracks in '{album_name}'")
        self.track_canvas.draw()

    def show_raw_data(self):
        raw_win = tk.Toplevel(self)
        if hasattr(sys, "_MEIPASS"):
            base_path = sys._MEIPASS
        else:
            base_path = os.path.abspath(".")
        icon_path = os.path.join(base_path, "ico.ico")
        raw_win.iconbitmap(icon_path)
        raw_win.title("Raw Data")
        raw_win.geometry("800x600")

        # Центрирование только позиции — без изменения размера!
        raw_win.update_idletasks()
        x = (raw_win.winfo_screenwidth() // 2) - (800 // 2)
        y = (raw_win.winfo_screenheight() // 2) - (600 // 2)
        raw_win.geometry(f"+{x}+{y}")

        # Text area
        text_area = scrolledtext.ScrolledText(raw_win, wrap=tk.WORD)
        text_area.pack(fill=tk.BOTH, expand=True)

        # Styles (only red for errors)
        text_area.tag_config("error", foreground="red")

        # Context menu (right-click)
        def copy_selection():
            try:
                selection = text_area.get(tk.SEL_FIRST, tk.SEL_LAST)
                raw_win.clipboard_clear()
                raw_win.clipboard_append(selection)
            except tk.TclError:
                pass

        context_menu = tk.Menu(raw_win, tearoff=0)
        context_menu.add_command(label="Copy", command=copy_selection)
        text_area.bind("<Button-3>", lambda event: context_menu.tk_popup(event.x_root, event.y_root))

        # Bottom buttons
        button_frame = ttk.Frame(raw_win)
        button_frame.pack(pady=5)

        def ms_to_minsec(ms):
            minutes = ms // 60000
            seconds = (ms % 60000) // 1000
            return f"{minutes}:{seconds:02d}"

        def insert(line, tag=None):
            text_area.insert(tk.END, line + "\n", tag)

        def copy_all():
            text = text_area.get("1.0", tk.END).strip()
            raw_win.clipboard_clear()
            raw_win.clipboard_append(text)
            messagebox.showinfo("Copied", "Raw data copied to clipboard.")

        def export_to_txt():
            content = text_area.get("1.0", tk.END).strip()
            file_path = filedialog.asksaveasfilename(
                defaultextension=".txt",
                filetypes=[("Text files", "*.txt"), ("All files", "*.*")],
                title="Save Raw Data"
            )
            if file_path:
                try:
                    with open(file_path, "w", encoding="utf-8") as f:
                        f.write(content)
                    messagebox.showinfo("Saved", f"Raw data exported to:\n{file_path}")
                except Exception as e:
                    messagebox.showerror("Error", f"Failed to save file:\n{e}")

        def export_to_json():
            json_data = {
                "artist_info": {},
                "albums": [],
                "tracks": []
            }

            if self.artist_id:
                try:
                    artist = self.sp.artist(self.artist_id)
                    json_data["artist_info"] = {
                        "name": self.artist_name,
                        "genres": artist.get("genres", []),
                        "followers": artist.get("followers", {}).get("total", 0),
                        "spotify_url": artist.get("external_urls", {}).get("spotify", "")
                    }
                except:
                    pass

            for alb_id, alb_name, alb_pop, alb_year in self.albums:
                try:
                    album = self.sp.album(alb_id)
                    json_data["albums"].append({
                        "id": alb_id,
                        "name": alb_name,
                        "popularity": alb_pop,
                        "release_date": album.get("release_date", "N/A"),
                        "spotify_url": album.get("external_urls", {}).get("spotify", "")
                    })
                except:
                    continue

            if self.current_album_tracks:
                track_ids = [t["id"] for t in self.current_album_tracks]
                try:
                    features = self.sp.audio_features(track_ids)
                except:
                    features = [None] * len(track_ids)

                for t, f in zip(self.current_album_tracks, features):
                    track_json = {
                        "id": t["id"],
                        "name": t["name"],
                        "popularity": t["popularity"],
                        "duration_ms": t.get("duration_ms", None),
                        "duration": ms_to_minsec(t["duration_ms"]) if t.get("duration_ms") else "N/A",
                        "spotify_url": t.get("external_urls", {}).get("spotify", "N/A")
                    }
                    if f:
                        track_json["tempo"] = f.get("tempo", "N/A")
                        track_json["valence"] = f.get("valence", "N/A")
                    json_data["tracks"].append(track_json)

            file_path = filedialog.asksaveasfilename(
                defaultextension=".json",
                filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
                title="Export as JSON"
            )
            if file_path:
                try:
                    with open(file_path, "w", encoding="utf-8") as f:
                        json.dump(json_data, f, indent=2)
                    messagebox.showinfo("Saved", f"JSON exported to:\n{file_path}")
                except Exception as e:
                    messagebox.showerror("Error", f"Failed to export JSON:\n{e}")

        ttk.Button(button_frame, text="Copy All", command=copy_all).pack(side=tk.LEFT, padx=10)
        ttk.Button(button_frame, text="Export to .txt", command=export_to_txt).pack(side=tk.LEFT, padx=10)
        ttk.Button(button_frame, text="Export as JSON", command=export_to_json).pack(side=tk.LEFT, padx=10)

        # Populate text area
        if not self.artist_id:
            insert("Albums: No album data available.", "error")
            insert("Tracks: No track data available.", "error")
            return

        try:
            artist_info = self.sp.artist(self.artist_id)
            insert("Artist Info:")
            insert(f"  Name: {self.artist_name}")
            insert(f"  Genres: {', '.join(artist_info.get('genres', []))}")
            insert(f"  Followers: {artist_info['followers']['total']}")
            insert(f"  Spotify URL: {artist_info['external_urls']['spotify']}")
            insert("")
        except Exception as e:
            insert(f"Error loading artist info: {e}", "error")
            insert("")

        if not self.albums:
            insert("Albums: No album data available.", "error")
            insert("Tracks: No track data available.", "error")
            return

        insert("Albums:")
        for alb_id, alb_name, alb_pop, alb_year in self.albums:
            try:
                album_data = self.sp.album(alb_id)
                insert(f"  • {alb_name} ({alb_year})")
                insert(f"     ID: {alb_id}")
                insert(f"     Popularity: {alb_pop}")
                insert(f"     Release date: {album_data.get('release_date', 'N/A')}")
                insert(f"     Spotify URL: {album_data['external_urls']['spotify']}")
                insert("")
            except Exception as e:
                insert(f"  • {alb_name} — Error fetching album details: {e}", "error")
                insert("")

        if not self.current_album_tracks:
            insert("Tracks: No track data available.", "error")
            return

        insert("Tracks:")
        track_ids = [t["id"] for t in self.current_album_tracks]
        try:
            features_list = self.sp.audio_features(track_ids)
        except Exception as e:
            features_list = [None] * len(track_ids)
            insert(f"(Audio features not loaded: {e})", "error")
            insert("")

        for t, f in zip(self.current_album_tracks, features_list):
            insert(f"  • {t['name']}")
            insert(f"     ID: {t['id']}")
            insert(f"     Popularity: {t['popularity']}")
            dur = t.get("duration_ms", None)
            insert(f"     Duration: {ms_to_minsec(dur)} ({dur} ms)" if dur else "     Duration: N/A")
            insert(f"     Spotify URL: {t.get('external_urls', {}).get('spotify', 'N/A')}")
            if f:
                insert(f"     Tempo: {f.get('tempo', 'N/A')}")
                insert(f"     Valence: {f.get('valence', 'N/A')}")
            else:
                insert("     No audio features available.", "error")
            insert("")

    def export_popularity(self):
        if not self.artist_id or not self.albums:
            messagebox.showinfo("Info", "Please search and select an artist first.")
            return

        count_option = self.settings.get("albums_to_export", "3")
        export_num = len(self.albums) if count_option == "All" else min(int(count_option), len(self.albums))

        reverse_order = self.settings.get("sort_order", "Descending") == "Descending"
        sorted_albums = sorted(self.albums, key=lambda x: x[2], reverse=reverse_order)
        top_albums = sorted_albums[:export_num]

        dt = datetime.datetime.now().astimezone()
        all_keywords = self._get_expanded_keywords()

        try:
            artist_info = self.sp.artist(self.artist_id)
            genres = artist_info.get("genres", [])
            genre_str = ", ".join(sorted(set(genres))) if genres else "N/A"
        except:
            genre_str = "N/A"

        lines = []
        lines.append(f"Popularity Export for Artist: {self.artist_name}")
        lines.append(f"Date/Time (Local): {dt.strftime('%Y-%m-%d %H:%M:%S %Z')}")
        lines.append(f"Genre: {genre_str}")
        lines.append(f"The most popular song: ")
        lines.append(f"Stream Count: ")
        lines.append("Source: Spotify API — https://www.spotify.com\n")

        for (alb_id, alb_name, alb_pop, alb_year) in top_albums:
            lines.append(f"Album: {alb_name} ({alb_year}), Popularity: {alb_pop}")
            try:
                album_tracks = self.sp.album_tracks(alb_id, limit=50)['items']
            except Exception as e:
                lines.append(f"  Error fetching tracks: {e}\n")
                continue

            track_data = []
            for tr in album_tracks:
                tr_name = tr.get("name", "")
                if any(kw in tr_name.lower() for kw in all_keywords):
                    continue
                tr_id = tr["id"]
                try:
                    full_tr = self.sp.track(tr_id)
                    tr_pop = full_tr.get("popularity", 0)
                except Exception:
                    tr_pop = 0
                track_data.append((tr_name, tr_pop))

            track_data.sort(key=lambda x: x[1], reverse=reverse_order)

            track_limit = self.settings.get("tracks_to_export", "3")
            top_tracks = track_data if track_limit == "All" else track_data[:int(track_limit)]

            for (t_name, t_pop) in top_tracks:
                lines.append(f"   Track: {t_name}, Popularity: {t_pop}, Stream Count: ")
            lines.append("")

        output_text = "\n".join(lines)
        save_path = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")],
            title="Save Popularity Export"
        )
        if not save_path:
            return
        try:
            with open(save_path, "w", encoding="utf-8") as f:
                f.write(output_text)
            messagebox.showinfo("Export Complete", f"Data exported to:\n{save_path}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to write file: {e}")


def main():
    # Поддержка путей внутри PyInstaller-сборки
    if hasattr(sys, "_MEIPASS"):
        base_path = sys._MEIPASS
    else:
        base_path = os.path.abspath(".")

    icon_path = os.path.join(base_path, "ico.ico")
    splash_path = os.path.join(base_path, "splash.png")
    # Показ сплэш-экрана
    splash = tk.Tk()
    splash.overrideredirect(True)
    splash.geometry("600x400+{}+{}".format(
        (splash.winfo_screenwidth() - 600) // 2,
        (splash.winfo_screenheight() - 400) // 2
    ))

    try:
        splash_img = Image.open(splash_path)
        w, h = splash_img.size

        max_w, max_h = 800, 600  # максимальные размеры окна
        scale = min(max_w / w, max_h / h)
        new_size = (int(w * scale), int(h * scale))

        splash_img = splash_img.resize(new_size, Image.LANCZOS)
        splash_photo = ImageTk.PhotoImage(splash_img)

        label = tk.Label(splash, image=splash_photo, bg="black")
        label.image = splash_photo
        label.pack(expand=True)
        splash.geometry(
            f"{new_size[0]}x{new_size[1]}+{(splash.winfo_screenwidth() - new_size[0]) // 2}+{(splash.winfo_screenheight() - new_size[1]) // 2}")
    except Exception as e:
        print("Could not load splash image:", e)

    splash.after(2500, splash.destroy)
    splash.mainloop()

    creds = load_credentials()
    if not creds:
        prompt_for_credentials()
        creds = load_credentials()
        if not creds:
            sys.exit()

    client_id = creds["client_id"]
    client_secret = creds["client_secret"]

    app = SpotifyAnalyzer(client_id, client_secret)
    app.iconbitmap(icon_path)
    app.mainloop()

if __name__ == "__main__":
    main()
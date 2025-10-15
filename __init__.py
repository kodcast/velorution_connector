from pynicotine.pluginsystem import BasePlugin
from gi.repository import Gtk, GLib
from pynicotine.core import core
from pynicotine.events import events
from pynicotine.slskmessages import FileListMessage
import re
import gettext
import os
import urllib.request
import json
import urllib.parse

# Configuration de la localisation.
LOCALE_DIR = os.path.join(os.path.dirname(__file__), "locales")
# Le domaine est celui du plugin.
gettext.bindtextdomain("velorution_connector", LOCALE_DIR)
gettext.textdomain("velorution_connector")
_ = gettext.gettext

def normalize_quality(q):
    """Normalise la chaîne de qualité en supprimant les espaces et en passant en minuscules."""
    return re.sub(r'\s+', '', q.lower())

class Plugin(BasePlugin):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.log(_("🔄 Loading velorution plugin..."))
        self.download_launched = False
        self.search_terms = []  # Liste des recherches à effectuer (propositions validées)
        self.current_search_index = 0
        self.current_pending_term = ""
        self.current_timeout = None
        self.response_timeout = 5  # secondes à attendre pour une réponse de recherche
        self.download_delay = 3    # délai avant de lancer le téléchargement
        self.missing_search_terms = set()
        self.search_stopped = False
        self.paused = False

    def loaded_notification(self):
        """Appelée lors du chargement du plugin."""
        self.log(_("🔔 Plugin velorution loaded."))
        events.connect("file-search-response", self.file_search_response)
        self.show_window()

    def show_window(self):
        """Crée la fenêtre principale avec les options de recherche."""
        self.log(_("🔧 Creating main window..."))
        self.window = Gtk.Window(title=_("velorution"))
        self.window.set_default_size(400, 300)
        self.window.connect("destroy", self.on_window_destroy)

        self.widget = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        self.widget.set_margin_top(10)
        self.widget.set_margin_bottom(10)
        self.widget.set_margin_start(10)
        self.widget.set_margin_end(10)
        self.window.set_child(self.widget)

        # Label pour la saisie de l'URL
        url_label = Gtk.Label(label=_("enter the adress (ex: https://velorutionsaintnazaire.fr) :"))
        url_label.set_xalign(0.5)
        url_label.set_halign(Gtk.Align.CENTER)
        self.widget.append(url_label)

        # Champ de saisie unique pour l'URL de base
        self.url_entry = Gtk.Entry()
        self.url_entry.set_placeholder_text(_("URL de base"))
        self.widget.append(self.url_entry)

        # Sélection du format audio
        format_label = Gtk.Label(label=_("Audio Format:"))
        format_label.set_xalign(0)
        self.widget.append(format_label)
        self.format_combo = Gtk.ComboBoxText()
        for fmt in ["MP3", "FLAC", "OGG", "OPUS", "WAV"]:
            self.format_combo.append_text(fmt)
        self.format_combo.set_active(0)
        self.widget.append(self.format_combo)

        # Sélection de la qualité audio
        quality_label = Gtk.Label(label=_("Audio Quality:"))
        quality_label.set_xalign(0)
        self.widget.append(quality_label)
        self.quality_combo = Gtk.ComboBoxText()
        for quality in ["320kbps", "192kbps", "128kbps", "44.1 KHz/16 bit", ""]:
            self.quality_combo.append_text(quality)
        self.quality_combo.set_active(0)
        self.widget.append(self.quality_combo)

        # Zone des boutons: "Search and Download", "Stop" et "Pause/Resume"
        button_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        apply_button = Gtk.Button(label="🔍 " + _("Search and Download"))
        apply_button.connect("clicked", self.on_apply_button_clicked)
        button_box.append(apply_button)

        stop_button = Gtk.Button(label="⏹️ " + _("Stop"))
        stop_button.connect("clicked", self.on_stop_button_clicked)
        button_box.append(stop_button)

        self.pause_button = Gtk.Button(label="⏸️ " + _("Pause"))
        self.pause_button.connect("clicked", self.on_pause_button_clicked)
        button_box.append(self.pause_button)

        self.widget.append(button_box)

        # Zone scrollable pour afficher les messages finaux (ex. propositions non trouvées)
        final_scrolled = Gtk.ScrolledWindow()
        final_scrolled.set_size_request(-1, 100)
        self.final_message_view = Gtk.TextView()
        self.final_message_view.set_wrap_mode(Gtk.WrapMode.WORD)
        self.final_message_view.set_editable(False)
        self.final_message_view.set_cursor_visible(False)
        self.final_message_buffer = self.final_message_view.get_buffer()
        final_scrolled.set_child(self.final_message_view)
        self.widget.append(final_scrolled)

        self.window.present()

    def on_window_destroy(self, window):
        """Ferme correctement la fenêtre."""
        self.log(_("❌ Window closed."))
        window.destroy()

    def set_final_message(self, message):
        """Affiche un message dans la zone finale."""
        self.final_message_buffer.set_text(message)

    def on_apply_button_clicked(self, button):
        """Initialise la recherche à partir de l'URL saisie."""
        self.log(_("🖱️ 'Search and Download' button clicked!"))
        self.download_launched = False
        self.current_search_index = 0
        self.missing_search_terms = set()
        self.search_stopped = False
        self.paused = False
        self.pause_button.set_label("⏸️ " + _("Pause"))
        if self.current_timeout is not None:
            GLib.source_remove(self.current_timeout)
            self.current_timeout = None
        self.set_final_message("")
        
        base_url = self.url_entry.get_text().strip()
        if not base_url:
            self.log(_("⚠️ No URL provided."))
            self.set_final_message(_("⚠️ Please enter a valid URL."))
            return
        
        # S'assurer que l'URL se termine par un '/'
        if not base_url.endswith('/'):
            base_url += '/'
        json_url = base_url + "propositions.json"
        self.log(_("📡 Fetching propositions from {url}").format(url=json_url))
        try:
            with urllib.request.urlopen(json_url) as response:
                data = response.read().decode('utf-8')
                propositions = json.loads(data)
        except Exception as e:
            self.log(_("❌ Error fetching or parsing JSON: {error}").format(error=e))
            self.set_final_message(_("❌ Error fetching or parsing JSON: {error}").format(error=e))
            return

        # Filtrer les propositions avec un status "validated"
        self.search_terms = []
        for item in propositions:
            if item.get("status", "").strip().lower() == "validated":
                artiste = item.get("artiste", "").strip()
                titre = item.get("titre", "").strip()
                if artiste or titre:
                    term = f"{artiste} {titre}".strip()
                    self.search_terms.append(term)
        if not self.search_terms:
            self.log(_("⚠️ No validated propositions found."))
            self.set_final_message(_("⚠️ No validated propositions found."))
            return
        self.log(_("🔍 Starting searches for {count} proposition(s)").format(count=len(self.search_terms)))
        self.schedule_next_search()

    def on_stop_button_clicked(self, button):
        """Arrête le processus de recherche."""
        self.log(_("⏹️ Stop button clicked. Stopping search..."))
        self.search_stopped = True
        if self.current_timeout is not None:
            GLib.source_remove(self.current_timeout)
            self.current_timeout = None
        self.set_final_message(_("Search stopped by user."))

    def on_pause_button_clicked(self, button):
        """Met en pause ou reprend la recherche."""
        if not self.paused:
            self.paused = True
            if self.current_timeout is not None:
                GLib.source_remove(self.current_timeout)
                self.current_timeout = None
            self.set_final_message(_("Search paused by user."))
            self.pause_button.set_label("▶️ " + _("Resume"))
            self.log(_("⏸️ Search paused by user."))
        else:
            self.paused = False
            self.set_final_message(_("Search resumed."))
            self.pause_button.set_label("⏸️ " + _("Pause"))
            self.log(_("▶️ Search resumed."))
            self.schedule_next_search()

    def schedule_next_search(self):
        """
        Lance la recherche pour le terme courant puis planifie le suivant.
        """
        if self.search_stopped:
            self.log(_("⏹️ Search process has been stopped by the user."))
            self.set_final_message(_("Search stopped by user."))
            return

        if self.paused:
            self.log(_("⏸️ Search process is paused."))
            return

        if self.current_search_index >= len(self.search_terms):
            if self.missing_search_terms:
                message = _("❌ No file found for:\n ") + "\n ".join(sorted(self.missing_search_terms))
            else:
                message = _("✅ All files have been found.")
            self.set_final_message(message)
            self.log(message)
            return

        term = self.search_terms[self.current_search_index]
        self.current_pending_term = term
        self.download_launched = False

        self.log(_("📡 Searching for: {term}").format(term=term))
        try:
            core.search.do_search(term, mode="global")
        except Exception as e:
            self.log(_("❌ Error during search for '{term}': {error}").format(term=term, error=e))
            self.missing_search_terms.add(term)
            self.current_search_index += 1
            GLib.idle_add(self.schedule_next_search)
            return

        self.current_timeout = GLib.timeout_add_seconds(self.response_timeout, self.process_current_search, term)
        self.current_search_index += 1

    def process_current_search(self, term):
        """
        Si aucune réponse n'est reçue pour le terme courant dans le délai imparti,
        le terme est marqué comme non trouvé et la recherche passe au terme suivant.
        """
        if self.search_stopped or self.paused:
            self.log(_("Search process is paused or stopped."))
            return False

        if term == self.current_pending_term and not self.download_launched:
            self.log(_("❌ No matching file found for {term}").format(term=term))
            self.missing_search_terms.add(term)
        
        # Mettre à jour le statut de la proposition dans propositions.json
        self.update_proposal_status(term, "searched")
        
        self.current_timeout = None
        self.schedule_next_search()
        return False

    def file_search_response(self, response):
        """
        Traite la réponse de recherche. Si un résultat correspondant est trouvé pour le terme courant,
        lance le téléchargement.
        """
        if self.search_stopped or self.paused or self.download_launched:
            return

        self.log(_("📩 Received search results..."))
        result_list = getattr(response, "list", None)
        if result_list is None:
            return

        selected_format = self.format_combo.get_active_text().lower()
        selected_quality = self.quality_combo.get_active_text()
        user = getattr(response, "username", "Unknown")
        found_match = False

        for result in result_list:
            try:
                _code, file_path, size, _ext, file_attributes, *rest = result
            except Exception as e:
                self.log(_("❌ Error extracting tuple: {error}").format(error=e))
                continue

            filename = file_path.split("\\")[-1]
            h_format = filename.split(".")[-1].lower()
            h_quality, bitrate, h_length, length = FileListMessage.parse_audio_quality_length(size, file_attributes)
            if not h_quality and file_attributes and isinstance(file_attributes, tuple):
                try:
                    bitrate_val = int(file_attributes[0])
                    h_quality = f"{int(bitrate_val/1000)}kbps"
                except Exception as e:
                    self.log(_("❌ Error converting bitrate: {error}").format(error=e))
                    h_quality = ""
            else:
                h_quality = h_quality or ""

            quality_match = normalize_quality(selected_quality) == normalize_quality(h_quality) if h_quality else False
            format_match = (h_format == selected_format)
            is_private = "[prive]" in filename.lower()

            self.log(_("🎯 Checking file: {filename} (Format: {h_format}, Quality: {h_quality}, Format match: {format_match}, Quality match: {quality_match}, private: {is_private})").format(
                filename=filename, h_format=h_format, h_quality=h_quality,
                format_match=format_match, quality_match=quality_match, is_private=is_private))
            if format_match and quality_match and not is_private:
                found_match = True
                self.log(_("✅ Matching result found for {term}: {filename}").format(term=self.current_pending_term, filename=filename))
                if self.current_timeout is not None:
                    GLib.source_remove(self.current_timeout)
                    self.current_timeout = None
                GLib.timeout_add_seconds(self.download_delay, self.delayed_download, user, file_path)
                self.download_launched = True
                
                # Mettre à jour le statut de la proposition dans propositions.json
                self.update_proposal_status(self.current_pending_term, "searched")
                break

        if not found_match:
            self.log(_("❌ No matching file found for {term}").format(term=self.current_pending_term))

    def delayed_download(self, user, file_path):
        """
        Lance le téléchargement après le délai et planifie la recherche du terme suivant.
        """
        if self.search_stopped or self.paused:
            self.log(_("⏸️/⏹️ Download postponed due to pause/stop command."))
            return False

        try:
            core.downloads.enqueue_download(user, file_path)
            self.log(_("🚀 Download launched for: {file}").format(file=file_path))
        except Exception as e:
            self.log(_("❌ Error downloading {file}: {error}").format(file=file_path, error=e))
        self.schedule_next_search()
        return False

    def update_proposal_status(self, term, status="searched"):
        """
        Envoie une requête POST à playlist.php pour mettre à jour le statut d'une proposition.
        """
        base_url = self.url_entry.get_text().strip()
        if not base_url.endswith('/'):
            base_url += '/'
        
        url = base_url + "index.php"
        data = urllib.parse.urlencode({'term': term, 'status': status}).encode('utf-8')
        
        try:
            with urllib.request.urlopen(url, data=data) as response:
                response_data = response.read().decode('utf-8')
                self.log(_("📡 Updated status for {term} to {status}").format(term=term, status=status))
        except Exception as e:
            self.log(_("❌ Error updating status for {term}: {error}").format(term=term, error=e))

    def log(self, message):
        """Affiche un message dans les logs de Nicotine+."""
        print(f"[djheros_connector] {message}")

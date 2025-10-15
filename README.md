# Vélorution_connector - Plugin Nicotine+

## Français

### 📌 Description

**velorution_connector** est un plugin pour Nicotine+ qui permet de rechercher et télécharger automatiquement des fichiers audio en fonction d'une liste de critères définis. Il utilise le service [velorutioweb]([https://framagit.org/velorutionsaintnazaire/velorutioweb](https://framagit.org/velorutionsaintnazaire/velorutioweb))  pour faciliter la récupération de morceaux.

### 🚀 Fonctionnalités

- ✅ Recherche automatique des fichiers audio correspondants
- ✅ Filtres avancés sur le format (MP3, FLAC, OGG, OPUS, WAV) et la qualité audio
- ✅ Téléchargement automatique des fichiers trouvés
- ✅ Exclusion des fichiers privés contenant `[prive]` dans leur nom
- ✅ Intégration directe avec DjHeros

### 🔧 Installation

#### 🐧 Sous Linux :

1. Cloner le dépôt
    ```bash
    git clone https://github.com/kodcast/velorution_connectorr.git
    ```

2. Copier le plugin dans le dossier des plugins de Nicotine+ :
    ```bash
    mkdir -p ~/.local/share/nicotine/plugins/
    cp -r velorution_connector ~/.local/share/nicotine/plugins/
    ```

3. Redémarrer Nicotine+ et activer le plugin dans les paramètres.

#### 🖥️ Sous Windows :

1. Télécharger le dépôt depuis GitHub

2. Copier le plugin dans le dossier des plugins de Nicotine+ : `%APPDATA%/nicotine/plugins/`

3. Vérifier la configuration du plugin (URL JSON, filtres audio)

4. Lancer Nicotine+ et activer le plugin

### 🎯 Utilisation

1. Lancer Nicotine+ et activer le plugin
2. Entrer l’URL ex : https://velorution_ta_ville.com
3. Sélectionner le format audio et la qualité souhaitée
4. Cliquer sur **Rechercher et Télécharger**

### 🤝 Contribution

Les contributions sont les bienvenues ! Vous pouvez signaler un bug, proposer une amélioration ou envoyer une pull request sur **velorution_connector**.

### 📜 Licence

Distribué sous licence **GNU General Public License v3.0**.

---

## English

### 📌 Description

**PasseMonTruc Connector** is a plugin for Nicotine+ that allows you to automatically search and download audio files based on predefined criteria. It use [Passe Mon Truc](https://passemontruc.kodcast.com) service to simplify track retrieval.

### 🚀 Features

- ✅ Automatic search for matching audio files
- ✅ Advanced filters on format (MP3, FLAC, OGG, OPUS, WAV) and audio quality
- ✅ Automatic download of found files
- ✅ Exclusion of private files containing `[prive]` in their name
- ✅ Direct integration with DjHeros

### 🔧 Installation

#### 🐧 On Linux :

1. Clone the repository
    ```bash
    git clone https://github.com/kodcast/djheros_connector.git
    ```

2. Copy the plugin to Nicotine+'s plugin directory:
    ```bash
    mkdir -p ~/.local/share/nicotine/plugins/
    cp -r djheros_connector ~/.local/share/nicotine/plugins/
    ```

3. Restart Nicotine+ and enable the plugin in the settings.

#### 🖥️ On Windows :

1. Download the repository from GitHub

2. Copy the plugin to Nicotine+'s plugin directory: `%APPDATA%/nicotine/plugins/`

3. Check the plugin configuration (JSON URL, audio filters)

4. Launch Nicotine+ and enable the plugin

### 🎯 Usage

1. Launch Nicotine+ and enable the plugin
2. Enter the URL ex : https://passemontruc.kodcast.com/playlists/your_playlist
3. Select the desired audio format and quality
4. Click on **Search and Download**

### 🤝 Contribution

Contributions are welcome! Feel free to report an issue, suggest an improvement, or submit a pull request on **DjHeros Connector**.

### 📜 License

Licensed under the **GNU General Public License v3.0**.

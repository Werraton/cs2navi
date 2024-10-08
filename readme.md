
# CS2Navi

**CS2Navi** is a *Counter-Strike 2* add-on providing **audio feedback** for various in-game events, such as bomb possession, defuse kit collection, and player health. The aim is to give players **real-time** audio cues, enhancing their gameplay awareness.

![screenshot](screenshot.png)

---

## 🛠️ Features

- **Alerts** when you pick up the bomb or defuse kit.
- **Warnings** for low health or low ammo.
- Provides **feedback** on bomb status and defuse kit possession when the bomb is planted.
- **Bilingual Support**: Defaults to English, switchable to Finnish.
- **Audio Customization**: *New in this version!* Easily enable **custom sounds** for events with files in your selected folder.
- **Fully Customizable**: Adjust settings to match your play style.
- **Debug Mode**: Enable or disable debug mode from the main menu.

---

## ⚙️ Installation

### Python Version

1. Clone this repository:

   ```bash
   git clone https://github.com/Werraton/cs2navi.git
   ```

2. Install the dependencies:

   ```bash
   pip install -r requirements.txt
   ```

3. Run the program:

   ```bash
   python cs2navi.py
   ```

### Executable Version

If you prefer not to run the code directly from Python, download the `.exe` file from the [releases](https://github.com/Werraton/cs2navi/releases) page. Place it in your desired folder, ensure the necessary configuration files are set up, and run it directly.

> **Note:** Initial startup might take up to a minute.

---

## 🎮 Usage

1. **Select Option 4** from the main menu to copy the configuration to your game's `cfg` folder.
2. Follow the **in-menu instructions** to customize your settings.
3. **Custom Sounds**: If enabled, place custom sounds in a folder and configure it from the menu.

> Ctrl+C returns to the main menu.

---

## 🔧 Configuration Files

Place `gamestate_integration_cs2navi.cfg` in your game's `cfg` folder (default location: `C:\Program Files (x86)\Steam\steamapps\common\Counter-Strike Global Offensive\csgo\cfg`). You can customize settings like **volume, language, event triggers**, and **custom sound options** in `settings.json`.

---

## 🖋️ Author

Created and maintained by **Werraton**. Official repository:

[https://github.com/Werraton/cs2navi](https://github.com/Werraton/cs2navi)

---

### Päivitys

Versio sisältää:

- **Custom Sound** Support: Käytä omia äänitiedostoja pelin tapahtumien ilmoituksissa.
- **Koodikorjauksia**: Optimoitu äänitiedostojen käyttö sekä ilmoitusten tarkkuutta parannettu.

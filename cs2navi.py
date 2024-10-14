import os
import json
import time
import datetime
import simpleaudio as sa
from flask import Flask, request
import logging
import shutil
import numpy as np
import sys

# ASCII Art
ascii_art = """
 ░▒▓██████▓▒░   ░▒▓███████▓▒░ ░▒▓███████▓▒░  ░▒▓███████▓▒░   ░▒▓██████▓▒░  ░▒▓█▓▒░░▒▓█▓▒░ ░▒▓█▓▒░ 
░▒▓█▓▒░░▒▓█▓▒░ ░▒▓█▓▒░               ░▒▓█▓▒░ ░▒▓█▓▒░░▒▓█▓▒░ ░▒▓█▓▒░░▒▓█▓▒░ ░▒▓█▓▒░░▒▓█▓▒░ ░▒▓█▓▒░ 
░▒▓█▓▒░        ░▒▓█▓▒░               ░▒▓█▓▒░ ░▒▓█▓▒░░▒▓█▓▒░ ░▒▓█▓▒░░▒▓█▓▒░  ░▒▓█▓▒▒▓█▓▒░  ░▒▓█▓▒░ 
░▒▓█▓▒░         ░▒▓██████▓▒░   ░▒▓██████▓▒░  ░▒▓█▓▒░░▒▓█▓▒░ ░▒▓████████▓▒░  ░▒▓█▓▒▒▓█▓▒░  ░▒▓█▓▒░ 
░▒▓█▓▒░               ░▒▓█▓▒░ ░▒▓█▓▒░        ░▒▓█▓▒░░▒▓█▓▒░ ░▒▓█▓▒░░▒▓█▓▒░   ░▒▓█▓▓█▓▒░   ░▒▓█▓▒░ 
░▒▓█▓▒░░▒▓█▓▒░        ░▒▓█▓▒░ ░▒▓█▓▒░        ░▒▓█▓▒░░▒▓█▓▒░ ░▒▓█▓▒░░▒▓█▓▒░   ░▒▓█▓▓█▓▒░   ░▒▓█▓▒░ 
 ░▒▓██████▓▒░  ░▒▓███████▓▒░  ░▒▓████████▓▒░ ░▒▓█▓▒░░▒▓█▓▒░ ░▒▓█▓▒░░▒▓█▓▒░    ░▒▓██▓▒░    ░▒▓█▓▒░ 

                    By Werraton                            
"""

# Function to get the absolute path to resources
def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

# Default settings
default_settings = {
    "low_health_threshold": 30,
    "low_health_notification_delay": 2,
    "ammo_threshold_percentage": 25,  # Default 25%
    "volume": 100,
    "max_plays": {
        "lowhp": 1,
        "lowbullets": 5,
        "picked_up_kit": 1,
        "kits": 1,
        "no_kits": 1,
        "bomb": 2  # Added 2 to allow bomb reminders
    },
    "enabled_events": {
        "low_health": True,
        "low_ammo": True,
        "picked_up_kit": True,
        "kits_when_bomb_planted": True,
        "bomb_possession_at_start": True,
        "picked_up_bomb": True
    },
    "bomb_reminder_delay": 15,  # New setting for bomb reminder delay
    "language": "en",
    "custom_sounds_enabled": False,
    "custom_sound_folder": "",
    "weapon_accuracy_feedback": {
        "deagle": True,
        "xm1014": True
    },
    "steady_shot_sound": "steady_shot.wav"
}

# Function to merge default and loaded settings
def merge_settings(defaults, loaded):
    for key, value in defaults.items():
        if isinstance(value, dict):
            loaded_value = loaded.get(key, {})
            if not isinstance(loaded_value, dict):
                loaded_value = {}
            loaded[key] = merge_settings(value, loaded_value)
        else:
            loaded.setdefault(key, value)
    return loaded

# Load settings from file or use defaults
config_path = resource_path(os.path.join("conf-settings", "settings.json"))
if os.path.exists(config_path):
    with open(config_path, 'r') as f:
        try:
            loaded_settings = json.load(f)
            print("[DEBUG] Loaded custom settings from file.")
            # Merge loaded settings with defaults
            custom_settings = merge_settings(default_settings, loaded_settings)
            # Save merged settings back to file if new keys were added
            with open(config_path, 'w') as fw:
                json.dump(custom_settings, fw, indent=4)
                print("[DEBUG] Updated settings.json with any new default settings.")
        except json.JSONDecodeError as e:
            print(f"[ERROR] Failed to parse settings.json: {e}")
            custom_settings = default_settings.copy()
            os.makedirs(resource_path("conf-settings"), exist_ok=True)
            with open(config_path, 'w') as fw:
                json.dump(custom_settings, fw, indent=4)
            print("[DEBUG] Reset to default settings.")
else:
    custom_settings = default_settings.copy()
    os.makedirs(resource_path("conf-settings"), exist_ok=True)
    with open(config_path, 'w') as f:
        json.dump(custom_settings, f, indent=4)
    print("[DEBUG] Created default settings.json.")

language = custom_settings.get('language', 'en')

wav_files = {
    "en": {
        "lowhp": "lowhp.wav",
        "lowbullets": "lowbullets.wav",
        "picked_up_kit": "kits.wav",
        "kits": "kits.wav",
        "no_kits": "no_kits.wav",
        "bomb": "bomb.wav",
        "steady_shot": custom_settings.get('steady_shot_sound', 'steady_shot.wav')
    },
    "fi": {
        "lowhp": "matala_hp.wav",
        "lowbullets": "panokset_vahissa.wav",
        "picked_up_kit": "kitit.wav",
        "kits": "kitit.wav",
        "no_kits": "ei_kitteja.wav",
        "bomb": "pommi.wav",
        "steady_shot": custom_settings.get('steady_shot_sound', 'steady_shot.wav')
    }
}

# Custom sound files always in English
custom_wav_files = {
    "lowhp": "lowhp.wav",
    "lowbullets": "lowbullets.wav",
    "picked_up_kit": "kits.wav",
    "kits": "kits.wav",
    "no_kits": "no_kits.wav",
    "bomb": "bomb.wav",
    "steady_shot": custom_settings.get('steady_shot_sound', 'steady_shot.wav')
}

def check_files(language):
    custom_folder = custom_settings.get("custom_sound_folder", "")
    
    if custom_settings.get("custom_sounds_enabled", False) and os.path.isdir(custom_folder):
        print("Checking for custom sound files..." if language == 'en' else "Tarkistetaan custom-äänitiedostot...")
        custom_files_used = []
        default_files_used = []
        for key, filename in custom_wav_files.items():  # Use English filenames for custom sounds
            custom_path = os.path.join(custom_folder, filename)
            if os.path.exists(custom_path):
                wav_files[language][key] = custom_path  # Replace with found custom sounds
                custom_files_used.append(custom_path)
            else:
                # If custom file is missing, use the default sound based on the selected language
                default_path = resource_path(os.path.join(f"{language}-wav", filename))
                wav_files[language][key] = default_path  # Use default directory for missing
                default_files_used.append(default_path)
        
        # Notify which custom sounds are in use
        if custom_files_used:
            print("Custom sound files in use:" if language == 'en' else "Käytössä olevat custom-äänitiedostot:")
            for file in custom_files_used:
                print(f" - {file}")
        # Notify which default sounds are in use due to missing custom sounds
        if default_files_used:
            print("Default sound files in use due to missing custom sounds:" if language == 'en' else "Oletusäänet käytössä, koska vastaavia custom-äänitiedostoja ei löytynyt:")
            for file in default_files_used:
                print(f" - {file}")
        
        input("Press Enter to continue..." if language == 'en' else "Paina Enter jatkaaksesi...")
    else:
        # If custom sounds are not enabled, inform the user that default sounds are being used
        print("Using default sound files." if language == 'en' else "Käytetään oletusäänitiedostoja.")
    
    print("[DEBUG] All required files are present.")

app = Flask(__name__)
log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)

def play_sound(sound_key):
    try:
        print(f"[DEBUG] Attempting to play sound for key: {sound_key}")
        filename = wav_files[language][sound_key]

        # Use custom sound if enabled
        if custom_settings.get("custom_sounds_enabled", False):
            sound_file = filename  # Custom sounds are already set in wav_files[language][key]
        else:
            sound_file = resource_path(os.path.join(f"{language}-wav", filename))

        if not os.path.exists(sound_file):
            print(f"[ERROR] Sound file does not exist: {sound_file}")
            return

        # Load WAV file
        wave_obj = sa.WaveObject.from_wave_file(sound_file)
        # Adjust volume
        volume = custom_settings.get('volume', 100) / 100  # Volume scale
        audio_data = wave_obj.audio_data
        sample_rate = wave_obj.sample_rate
        num_channels = wave_obj.num_channels
        bytes_per_sample = wave_obj.bytes_per_sample

        # Convert bytes to numpy array
        dtype_map = {1: np.int8, 2: np.int16, 4: np.int32}
        dtype = dtype_map.get(bytes_per_sample, np.int16)
        audio_array = np.frombuffer(audio_data, dtype=dtype)

        # Adjust volume
        audio_array = (audio_array * volume).astype(dtype)

        # Convert back to bytes
        adjusted_audio = audio_array.tobytes()

        # Create new WaveObject with adjusted audio
        adjusted_wave_obj = sa.WaveObject(
            adjusted_audio, num_channels, bytes_per_sample, sample_rate)

        # Play sound
        play_obj = adjusted_wave_obj.play()
        play_obj.wait_done()
        print(f"[DEBUG] Sound played: {sound_file}")
    except Exception as e:
        print(f"[ERROR] Error playing sound {sound_key}: {e}")

# Initialize sound play counts
sound_play_count = {key: 0 for key in custom_settings["max_plays"].keys()}
low_health_start_time = None
last_low_ammo_time = datetime.datetime.min

# Variables to track state
had_bomb = False
bomb_planted = False
had_defuse_kit = False
player_alive = True  # Player's alive status
bomb_acquired_time = None  # Time when bomb was acquired

# Variables to track weapon firing
weapon_last_shot_time = {
    'weapon_deagle': None,
    'weapon_xm1014': None
}
previous_ammo_clip = {}

# Weapon maximum ammo counts
weapon_max_ammo = {
    'weapon_glock': 20,
    'weapon_hkp2000': 13,
    'weapon_p250': 13,
    'weapon_usp_silencer': 12,
    'weapon_elite': 30,
    'weapon_fiveseven': 20,
    'weapon_tec9': 18,
    'weapon_cz75a': 12,
    'weapon_deagle': 7,
    'weapon_revolver': 8,
    'weapon_nova': 8,
    'weapon_xm1014': 7,
    'weapon_sawedoff': 7,
    'weapon_mag7': 5,
    'weapon_m249': 100,
    'weapon_negev': 150,
    'weapon_mp9': 30,
    'weapon_mac10': 30,
    'weapon_mp7': 30,
    'weapon_mp5sd': 30,
    'weapon_ump45': 25,
    'weapon_p90': 50,
    'weapon_bizon': 64,
    'weapon_famas': 25,
    'weapon_galilar': 35,
    'weapon_m4a1': 30,
    'weapon_m4a1_silencer': 25,
    'weapon_ak47': 30,
    'weapon_sg556': 30,
    'weapon_aug': 30,
    'weapon_ssg08': 10,
    'weapon_awp': 10,
    'weapon_g3sg1': 20,
    'weapon_scar20': 20
}

# Weapons that do not use ammo
non_ammo_weapons = [
    'weapon_knife',
    'weapon_knife_t',
    'weapon_bayonet',
    'weapon_flashbang',
    'weapon_smokegrenade',
    'weapon_hegrenade',
    'weapon_molotov',
    'weapon_decoy',
    'weapon_incgrenade',
    'weapon_taser',
    'weapon_breachcharge',
    'weapon_c4',
    'weapon_tagrenade',
    'weapon_fists',
    'weapon_tablet',
    'weapon_healthshot',
    'weapon_shield'
]

@app.route('/', methods=['POST'])
def gamestate():
    global last_low_ammo_time, low_health_start_time, sound_play_count
    global had_bomb, bomb_planted, had_defuse_kit, player_alive, bomb_acquired_time
    global weapon_last_shot_time, previous_ammo_clip
    try:
        data = request.json
        print("[DEBUG] Received gamestate data.")
        provider_steamid = data.get('provider', {}).get('steamid', '')
        game_state = data.get('player', {})
        player_state = game_state.get('state', {})
        weapons = game_state.get('weapons', {})
        health = player_state.get('health', 100)
        round_data = data.get('round', {})
        now = datetime.datetime.now()

        player_steamid = game_state.get('steamid', '')

        if player_steamid != provider_steamid:
            print("[DEBUG] Player is spectating another player. Skipping notifications.")
            player_alive = False
            return 'OK', 200
        else:
            # Update player's alive status
            if health > 0:
                if not player_alive:
                    print("[DEBUG] Player has respawned.")
                player_alive = True
            else:
                if player_alive:
                    print("[DEBUG] Player has died.")
                player_alive = False

        print(f"[DEBUG] Player health: {health}")

        if round_data.get('phase') == 'over':
            print("[DEBUG] Round over. Resetting play counts.")
            reset_play_counts()

        if player_alive:

            # Handle low health
            if custom_settings['enabled_events'].get('low_health', True):
                if health < custom_settings['low_health_threshold']:
                    if not low_health_start_time:
                        low_health_start_time = time.time()
                        print("[DEBUG] Low health detected. Starting timer.")
                    elif time.time() - low_health_start_time > \
                            custom_settings['low_health_notification_delay']:
                        if sound_play_count['lowhp'] < \
                                custom_settings['max_plays']['lowhp']:
                            print("[DEBUG] Playing low health sound.")
                            play_sound('lowhp')
                            sound_play_count['lowhp'] += 1
                        else:
                            print("[DEBUG] Low health sound play count reached.")
                else:
                    if low_health_start_time is not None:
                        print("[DEBUG] Health restored. Resetting timer.")
                    low_health_start_time = None

            # Handle low ammo
            if custom_settings['enabled_events'].get('low_ammo', True):
                if (now - last_low_ammo_time).total_seconds() > 5:
                    for weapon_id, weapon in weapons.items():
                        weapon_name = weapon.get('name', '')
                        if weapon_name in non_ammo_weapons:
                            print(f"[DEBUG] Skipping non-ammo weapon: {weapon_name}")
                            continue  # Skip weapons that do not use ammo

                        ammo_clip = weapon.get('ammo_clip', 0)
                        max_ammo = weapon_max_ammo.get(weapon_name, 0)
                        if max_ammo == 0:
                            print(f"[DEBUG] Max ammo not defined for weapon: {weapon_name}")
                            continue  # Skip if max ammo is not defined

                        # Calculate threshold based on percentage
                        ammo_threshold_percentage = custom_settings.get(
                            'ammo_threshold_percentage', 25)
                        threshold = int((max_ammo * ammo_threshold_percentage) / 100)
                        print(f"[DEBUG] Checking weapon: {weapon_name}, "
                              f"Ammo: {ammo_clip}, Threshold: {threshold}")

                        if ammo_clip <= threshold:
                            if sound_play_count['lowbullets'] < \
                                    custom_settings['max_plays']['lowbullets']:
                                print("[DEBUG] Playing low bullets sound.")
                                play_sound('lowbullets')
                                sound_play_count['lowbullets'] += 1
                                last_low_ammo_time = now
                            else:
                                print("[DEBUG] Low bullets sound play count reached.")
                            break  # Play sound for the first weapon that meets the condition

            # Handle weapon accuracy feedback
            for weapon_id, weapon in weapons.items():
                weapon_name = weapon.get('name', '')
                if weapon_name not in ['weapon_deagle', 'weapon_xm1014']:
                    continue  # Only interested in Desert Eagle and XM1014

                setting_key = 'deagle' if weapon_name == 'weapon_deagle' else 'xm1014'
                if not custom_settings['weapon_accuracy_feedback'].get(setting_key, False):
                    continue  # Skip if feedback is disabled for this weapon

                ammo_clip = weapon.get('ammo_clip', 0)
                previous_clip = previous_ammo_clip.get(weapon_id, ammo_clip)
                previous_ammo_clip[weapon_id] = ammo_clip  # Update ammo clip for next check

                if ammo_clip < previous_clip:
                    # Player fired a shot
                    current_time = time.time()
                    last_shot_time = weapon_last_shot_time.get(weapon_name, None)
                    required_delay = 0.55 if weapon_name == 'weapon_deagle' else 0.35

                    if last_shot_time:
                        time_since_last_shot = current_time - last_shot_time
                        print(f"[DEBUG] Time since last shot for {weapon_name}: {time_since_last_shot}s")
                        if time_since_last_shot < required_delay:
                            print(f"[DEBUG] Firing too quickly with {weapon_name}. Playing steady_shot sound.")
                            play_sound('steady_shot')
                    weapon_last_shot_time[weapon_name] = current_time

            # Handle bomb possession
            has_bomb = any(weapon.get('name') == 'weapon_c4' for weapon in weapons.values())

            if has_bomb:
                if not had_bomb:
                    bomb_acquired_time = time.time()
                    if round_data.get('phase') == 'freezetime':
                        # Bomb possessed at the start
                        if custom_settings['enabled_events'].get('bomb_possession_at_start', True):
                            if sound_play_count['bomb'] < custom_settings['max_plays']['bomb']:
                                print("[DEBUG] Player has the bomb at round start. Playing bomb sound.")
                                play_sound('bomb')
                                sound_play_count['bomb'] += 1
                            else:
                                print("[DEBUG] Bomb sound play count reached.")
                    else:
                        # Bomb picked up from the ground
                        if custom_settings['enabled_events'].get('picked_up_bomb', True):
                            if sound_play_count['bomb'] < custom_settings['max_plays']['bomb']:
                                print("[DEBUG] Player picked up the bomb. Playing bomb sound.")
                                play_sound('bomb')
                                sound_play_count['bomb'] += 1
                            else:
                                print("[DEBUG] Bomb sound play count reached.")
                else:
                    # Check if bomb reminder should be played
                    bomb_reminder_delay = custom_settings.get('bomb_reminder_delay', 15)
                    if bomb_acquired_time and (time.time() - bomb_acquired_time >= bomb_reminder_delay) and has_bomb:
                        if sound_play_count['bomb'] < custom_settings['max_plays']['bomb']:
                            print(f"[DEBUG] Bomb reminder after {bomb_reminder_delay} seconds. Playing bomb sound.")
                            play_sound('bomb')
                            sound_play_count['bomb'] += 1
                            if sound_play_count['bomb'] >= custom_settings['max_plays']['bomb']:
                                bomb_acquired_time = None  # Reset to prevent further reminders
                        else:
                            print("[DEBUG] Bomb sound play count reached.")
                had_bomb = True
            else:
                had_bomb = False  # Reset if the player loses the bomb
                bomb_acquired_time = None  # Reset bomb possession time

            # Handle defuse kit acquisition
            has_defuse_kit = player_state.get('defusekit', False)
            if has_defuse_kit and not had_defuse_kit:
                if custom_settings['enabled_events'].get('picked_up_kit', True):
                    if sound_play_count['picked_up_kit'] < custom_settings['max_plays']['picked_up_kit']:
                        print("[DEBUG] Player acquired a defuse kit. Playing picked_up_kit sound.")
                        play_sound('picked_up_kit')
                        sound_play_count['picked_up_kit'] += 1
                    else:
                        print("[DEBUG] picked_up_kit sound play count reached.")
                had_defuse_kit = True
            elif not has_defuse_kit:
                had_defuse_kit = False  # Reset if the player loses the kit

            # Handle enemy plant of the bomb
            bomb_state = round_data.get('bomb')
            player_team = game_state.get('team')
            if bomb_state == 'planted' and not bomb_planted:
                # Ensure the player is alive and on the CT team
                if health > 0 and player_team == 'CT':
                    # Check if the player has a defuse kit
                    has_defuse_kit = player_state.get('defusekit', False)
                    sound_key = 'kits' if has_defuse_kit else 'no_kits'
                    if custom_settings['enabled_events'].get('kits_when_bomb_planted', True):
                        if round_data.get('phase') != 'over':
                            if sound_play_count[sound_key] < custom_settings['max_plays'][sound_key]:
                                print(f"[DEBUG] Bomb planted and player {'has' if has_defuse_kit else 'does not have'} defuse kit. Playing {sound_key} sound.")
                                play_sound(sound_key)
                                sound_play_count[sound_key] += 1
                            else:
                                print(f"[DEBUG] {sound_key} sound play count reached.")
                    else:
                        print("[DEBUG] kits_when_bomb_planted event is disabled.")
                else:
                    print("[DEBUG] Bomb planted but player is not on CT team or is dead. No sound played.")
                bomb_planted = True
            elif bomb_state != 'planted':
                bomb_planted = False  # Reset if the bomb is not planted

        else:
            print("[DEBUG] Player is dead. Skipping notifications.")

        return 'OK', 200

    except Exception as e:
        logging.error(f"Error in gamestate endpoint: {e}")
        print(f"[ERROR] Error in gamestate endpoint: {e}")
        return f"Error: {str(e)}", 500

def reset_play_counts():
    global low_health_start_time, last_low_ammo_time, sound_play_count
    global had_bomb, bomb_planted, had_defuse_kit, bomb_acquired_time
    global weapon_last_shot_time, previous_ammo_clip
    for key in sound_play_count.keys():
        sound_play_count[key] = 0
    low_health_start_time = None
    last_low_ammo_time = datetime.datetime.min
    had_bomb = False
    bomb_planted = False
    had_defuse_kit = False  # Reset defuse kit tracking
    bomb_acquired_time = None  # Reset bomb possession time
    weapon_last_shot_time = {
        'weapon_deagle': None,
        'weapon_xm1014': None
    }
    previous_ammo_clip = {}
    print("[DEBUG] Reset sound play counts and timers.")

def change_language(lang):
    global language
    if lang in wav_files:
        language = lang
        print(f"Language changed to: {language}" if language == 'en'
              else f"Kieli vaihdettu: {language}")
    else:
        print(f"Language {lang} not recognized" if language == 'en'
              else f"Kieltä {lang} ei tunnistettu")

def validate_settings(settings):
    try:
        assert isinstance(settings['ammo_threshold_percentage'], int) and \
            settings['ammo_threshold_percentage'] in [15, 25, 35], \
            "ammo_threshold_percentage must be 15, 25, or 35"
        assert isinstance(settings['low_health_threshold'], int) and \
            0 <= settings['low_health_threshold'] <= 99, \
            "low_health_threshold must be between 0 and 99"
        assert isinstance(settings['volume'], int) and \
            0 <= settings['volume'] <= 100, \
            "volume must be between 0 and 100"
        assert isinstance(settings['bomb_reminder_delay'], int) and \
            0 <= settings['bomb_reminder_delay'] <= 60, \
            "bomb_reminder_delay must be between 0 and 60 seconds"
        for key, value in settings['max_plays'].items():
            assert isinstance(value, int) and 0 <= value <= 10, \
                f"max_plays['{key}'] must be between 0 and 10"
        assert isinstance(settings['enabled_events'], dict), \
            "enabled_events must be a dictionary"
        for key, value in settings['enabled_events'].items():
            assert isinstance(value, bool), \
                f"enabled_events['{key}'] must be a boolean"
        # Check weapon_accuracy_feedback settings
        assert isinstance(settings['weapon_accuracy_feedback'], dict), \
            "weapon_accuracy_feedback must be a dictionary"
        for key, value in settings['weapon_accuracy_feedback'].items():
            assert key in ['deagle', 'xm1014'], \
                f"Invalid weapon key in weapon_accuracy_feedback: {key}"
            assert isinstance(value, bool), \
                f"weapon_accuracy_feedback['{key}'] must be a boolean"
        # Check custom sound settings
        assert isinstance(settings.get('custom_sounds_enabled', False), bool), \
            "custom_sounds_enabled must be a boolean"
        if settings.get('custom_sounds_enabled', False):
            folder = settings.get('custom_sound_folder', '')
            assert os.path.isdir(folder), "custom_sound_folder must be a valid directory"
        print("[DEBUG] Settings validation passed.")
    except AssertionError as e:
        print(f"[ERROR] Settings validation failed: {e}")
        raise ValueError("Invalid configuration settings")

def main_menu():
    global language, custom_settings
    while True:
        os.system('cls' if os.name == 'nt' else 'clear')
        print(ascii_art)
        if language == 'en':
            print("Press number and enter. Remember to copy the config file.")
            print("  1. Language selection")
            print("  2. Customization")
            print("  3. Choose events to be played")
            print("  4. Copy config file")
            print("  5. Start program")
            print("  6. About")
            print("  7. Toggle Custom Sounds")
            print("  8. Exit")
            choice = input("Choose an option (1-8): ")
        else:
            print("Kirjoita numero ja paina enter. Muista kopioida conffi.")
            print("  1. Kielen valinta")
            print("  2. Kustomointi")
            print("  3. Valitse toistettavat tapahtumat")
            print("  4. Copy config file")
            print("  5. Aloita ohjelma")
            print("  6. Tietoa ohjelmasta")
            print("  7. Toggle Custom Sounds")
            print("  8. Poistu")
            choice = input("Valitse vaihtoehto (1-8): ")

        if choice == '1':
            language_selection()
        elif choice == '2':
            customize_settings()
        elif choice == '3':
            choose_events()
        elif choice == '4':
            copy_config_menu()
        elif choice == '5':
            start_program()
        elif choice == '6':
            about()
        elif choice == '7':
            toggle_custom_sounds()
        elif choice == '8':
            print("Exiting program." if language == 'en'
                  else "Poistutaan ohjelmasta.")
            break
        else:
            print("Invalid choice, try again." if language == 'en'
                  else "Virheellinen valinta, yritä uudelleen.")
            input("Press Enter to continue..." if language == 'en'
                  else "Paina Enter jatkaaksesi...")

def start_program():
    print("Starting the program..." if language == 'en'
          else "Ohjelma käynnistyy...")
    check_files(language)
    print("[DEBUG] Starting Flask app.")
    app.run(host='0.0.0.0', port=3000)

def language_selection():
    global language, custom_settings
    print("1. English\n2. Suomi")
    choice = input("Choose your language (1-2): " if language == 'en'
                   else "Valitse kielesi (1-2): ")
    previous_language = language
    language = 'en' if choice == '1' else 'fi'

    if previous_language != language:
        print(f"Language changed to: {language}" if language == 'en'
              else f"Kieli vaihdettu: {language}")
        custom_settings['language'] = language  # Save language setting
        with open(config_path, 'w') as f:
            json.dump(custom_settings, f, indent=4)
        print("Language preference saved." if language == 'en' else "Kieliasetus tallennettu.")
    else:
        print("Language unchanged." if language == 'en' else "Kieli ei muuttunut.")

    input("Press Enter to continue..." if language == 'en'
          else "Paina Enter jatkaaksesi...")

def get_input(prompt, default, current, expected_type='int', choices=None):
    if expected_type == 'int':
        value = input(f"{prompt} default: {default}, current: {current}: "
                      if language == 'en'
                      else f"{prompt} vakio: {default}, nykyinen: {current}: ")
        if value.strip() == "":
            return current
        try:
            value = int(value)
            if choices and value not in choices:
                print("Invalid choice. Keeping current value." if language == 'en'
                      else "Virheellinen valinta. Säilytetään nykyinen arvo.")
                return current
            return value
        except ValueError:
            print("Invalid input. Keeping current value." if language == 'en'
                  else "Virheellinen syöte. Säilytetään nykyinen arvo.")
            return current
    elif expected_type == 'bool':
        value = input(f"{prompt} (y/n) default: {'y' if default else 'n'}, current: {'y' if current else 'n'}: "
                      if language == 'en'
                      else f"{prompt} (k/e) vakio: {'k' if default else 'e'}, nykyinen: {'k' if current else 'e'}: ")
        if value.strip() == "":
            return current
        if value.lower() in ['y', 'k']:
            return True
        elif value.lower() in ['n', 'e']:
            return False
        else:
            print("Invalid input. Keeping current value." if language == 'en'
                  else "Virheellinen syöte. Säilytetään nykyinen arvo.")
            return current
    else:
        return current

def customize_settings():
    global custom_settings
    settings = custom_settings.copy()
    print("Customize program settings:" if language == 'en'
          else "Kustomoidaan ohjelman asetuksia:")

    settings['ammo_threshold_percentage'] = get_input(
        "Enter ammo threshold percentage (15, 25, 35)"
        if language == 'en' else
        'Anna panosraja prosentteina (15, 25, 35)',
        default_settings['ammo_threshold_percentage'],
        custom_settings['ammo_threshold_percentage'],
        expected_type='int',
        choices=[15, 25, 35]
    )
    settings['low_health_threshold'] = get_input(
        "Enter new health threshold (0-99)" if language == 'en' else
        'Anna uusi raja terveydelle (0-99)',
        default_settings['low_health_threshold'],
        custom_settings['low_health_threshold'],
        expected_type='int'
    )
    settings['volume'] = get_input(
        "Enter volume (0-100)" if language == 'en' else
        'Anna äänenvoimakkuus (0-100)',
        default_settings['volume'],
        custom_settings['volume'],
        expected_type='int'
    )
    settings['bomb_reminder_delay'] = get_input(
        "Enter bomb reminder delay in seconds (0-60)" if language == 'en' else
        'Anna pommin muistutuksen viive sekunneissa (0-60)',
        default_settings['bomb_reminder_delay'],
        custom_settings['bomb_reminder_delay'],
        expected_type='int'
    )

    for key in settings['max_plays']:
        settings['max_plays'][key] = get_input(
            f"Enter max plays for sound \"{key}\" per round (0-10)"
            if language == 'en' else
            f'Anna toistokerrat äänelle "{key}" per kierros (0-10)',
            default_settings['max_plays'][key],
            custom_settings['max_plays'][key],
            expected_type='int'
        )

    # Customize weapon accuracy feedback
    print("\nWeapon Accuracy Feedback Settings:" if language == 'en'
          else "\nAseen Tarkkuuspalautteen Asetukset:")
    for key in settings['weapon_accuracy_feedback']:
        current = settings['weapon_accuracy_feedback'][key]
        prompt = f"Enable accuracy feedback for {key}? (y/n)" if language == 'en' else f"Ota käyttöön tarkkuuspalautetta aseelle {key}? (k/e)"
        settings['weapon_accuracy_feedback'][key] = get_input(
            prompt,
            default_settings['weapon_accuracy_feedback'][key],
            current,
            expected_type='bool'
        )

    try:
        validate_settings(settings)
        custom_settings = settings
        with open(config_path, 'w') as f:
            json.dump(custom_settings, f, indent=4)
        print("Settings saved." if language == 'en'
              else "Asetukset tallennettu.")
    except ValueError as e:
        print(f"Error: {str(e)}" if language == 'en'
              else f"Virhe: {str(e)}")
        print("[DEBUG] Resetting to default settings due to validation failure.")
        custom_settings = default_settings.copy()
        with open(config_path, 'w') as f:
            json.dump(custom_settings, f, indent=4)
        print("Settings have been reset to default due to invalid configuration."
              if language == 'en'
              else "Asetukset on palautettu oletuksiin virheellisen konfiguraation vuoksi.")

    input("Press Enter to continue..." if language == 'en'
          else "Paina Enter jatkaaksesi...")

def get_event_display_name(event_key):
    event_names_en = {
        "low_health": "Low Health",
        "low_ammo": "Low Ammo",
        "picked_up_kit": "Picked up Defuse Kit",
        "kits_when_bomb_planted": "Defuse Kit when Bomb Planted",
        "bomb_possession_at_start": "Bomb Possession at Start",
        "picked_up_bomb": "Picked up Bomb"
    }
    event_names_fi = {
        "low_health": "Matala Energia",
        "low_ammo": "Panokset Vähissä",
        "picked_up_kit": "Kitit Maasta",
        "kits_when_bomb_planted": "Kitit kun Pommi Laitetaan",
        "bomb_possession_at_start": "Pommi Aloituksessa Hallussa",
        "picked_up_bomb": "Pommi Maasta"
    }
    if language == 'en':
        return event_names_en.get(event_key, event_key)
    else:
        return event_names_fi.get(event_key, event_key)

def choose_events():
    global custom_settings
    events = custom_settings.get('enabled_events', {})
    while True:
        os.system('cls' if os.name == 'nt' else 'clear')
        print("Choose events to be played:" if language == 'en'
              else "Valitse toistettavat tapahtumat:")
        print("(Enter the number to toggle on/off, or '0' to go back)" if language == 'en'
              else "(Kirjoita numero vaihtaaksesi päälle/pois, tai '0' palataksesi takaisin)")
        for idx, (event_key, enabled) in enumerate(events.items(), start=1):
            event_name = get_event_display_name(event_key)
            status = 'ON' if enabled else 'OFF'
            print(f"  {idx}. {event_name}: {status}")
        choice = input("Your choice: " if language == 'en'
                       else "Valintasi: ")
        if choice == '0':
            # Save settings and return to main menu
            with open(config_path, 'w') as f:
                json.dump(custom_settings, f, indent=4)
            break
        else:
            try:
                idx = int(choice)
                if 1 <= idx <= len(events):
                    event_key = list(events.keys())[idx -1]
                    events[event_key] = not events[event_key]
                else:
                    print("Invalid choice." if language == 'en' else "Virheellinen valinta.")
            except ValueError:
                print("Invalid input." if language == 'en' else "Virheellinen syöte.")
        input("Press Enter to continue..." if language == 'en' else "Paina Enter jatkaaksesi...")

def copy_config_menu():
    print("1. Default folder\n2. Custom folder" if language == 'en'
          else "1. Vakio kansio\n2. Kustomoitu kansio")
    choice = input("Choose an option (1-2): " if language == 'en'
                   else "Valitse vaihtoehto (1-2): ")
    if choice == '1':
        destination_folder = ("C:\\Program Files (x86)\\Steam\\steamapps\\common\\"
                              "Counter-Strike Global Offensive\\csgo\\cfg")
        print(f"[DEBUG] Default destination folder selected: {destination_folder}")
    elif choice == '2':
        destination_folder = input("Enter folder path: " if language == 'en'
                                   else "Anna kansion osoite: ")
        print(f"[DEBUG] Custom destination folder entered: {destination_folder}")
    else:
        print("Invalid choice." if language == 'en' else "Virheellinen valinta.")
        input("Press Enter to continue..." if language == 'en'
              else "Paina Enter jatkaaksesi...")
        return

    if os.path.isdir(destination_folder):
        copy_config_file(destination_folder)
    else:
        print("Invalid folder path. Try again." if language == 'en'
              else "Virheellinen kansiopolku. Yritä uudelleen.")
        input("Press Enter to continue..." if language == 'en'
              else "Paina Enter jatkaaksesi...")

def copy_config_file(destination_folder):
    source_file = resource_path(os.path.join("conf-settings", "gamestate_integration_cs2navi.cfg"))
    dest_file = os.path.join(destination_folder, 'gamestate_integration_cs2navi.cfg')
    if not os.path.exists(source_file):
        print(f"Source config file does not exist: {source_file}" if language == 'en'
              else f"Lähdekonfiguraatiotiedostoa ei ole olemassa: {source_file}")
        input("Press Enter to continue..." if language == 'en'
              else "Paina Enter jatkaaksesi...")
        return
    try:
        shutil.copy(source_file, dest_file)
        print(f"File copied to {destination_folder}" if language == 'en'
              else f"Tiedosto kopioitu kansioon {destination_folder}")
    except Exception as e:
        print(f"Failed to copy file: {e}" if language == 'en'
              else f"Tiedoston kopiointi epäonnistui: {e}")
    input("Press Enter to continue..." if language == 'en'
          else "Paina Enter jatkaaksesi...")

def toggle_custom_sounds():
    global custom_settings
    status = "enabled" if custom_settings.get("custom_sounds_enabled", False) else "disabled"
    print(f"Custom sounds are currently {status}." if language == 'en' else f"Custom-äänet ovat nyt {status}.")

    # Add message informing user of required files for custom sounds
    if language == 'en':
        print("To replace default sounds, place these files in the custom folder:\n"
              " - lowhp.wav\n"
              " - lowbullets.wav\n"
              " - kits.wav\n"
              " - no_kits.wav\n"
              " - bomb.wav\n"
              " - steady_shot.wav\n"
              "Files should be in .wav format.")
    else:
        print("Korvataksesi oletusäänet, laita seuraavat tiedostot custom-kansioon:\n"
              " - lowhp.wav\n"
              " - lowbullets.wav\n"
              " - kits.wav\n"
              " - no_kits.wav\n"
              " - bomb.wav\n"
              " - steady_shot.wav\n"
              "Tiedostojen on oltava .wav-muodossa.")

    choice = input("Enable custom sounds? (y/n): " if language == 'en' else "Ota käyttöön custom-äänet? (k/e): ")
    if choice.lower() in ['y', 'k']:
        custom_folder = input("Enter custom sound folder path: " if language == 'en' else "Anna custom-äänikansion polku: ")
        if os.path.isdir(custom_folder):
            custom_settings["custom_sounds_enabled"] = True
            custom_settings["custom_sound_folder"] = custom_folder
            print("[DEBUG] Custom sounds enabled and path set.")
        else:
            print("Invalid folder path." if language == 'en' else "Virheellinen kansiopolku.")
    else:
        custom_settings["custom_sounds_enabled"] = False
        print("[DEBUG] Custom sounds disabled.")
    
    # Save settings
    with open(config_path, 'w') as f:
        json.dump(custom_settings, f, indent=4)
    print("Settings saved." if language == 'en' else "Asetukset tallennettu.")
    input("Press Enter to continue..." if language == 'en' else "Paina Enter jatkaaksesi...")

def about():
    about_text_en = """
The program works with the game's own gamestate integration.
You can find more in the documentation, and the program has been
used for 700 hours without any issues.
Official address: https://github.com/Werraton/cs2navi
Libraries used: Flask, simpleaudio, numpy
Python code.
"""
    about_text_fi = """
Ohjelma toimii pelin omalla gamestate integratiolla.
Dokumentaatiosta löydät lisää ja ohjelmaa on käytetty 700 tuntia
eikä ongelmia ole ollut.
Virallinen osoite: https://github.com/Werraton/cs2navi
Käytetyt kirjastot: Flask, simpleaudio, numpy
Koodattu Pythonille.
"""
    print(about_text_en if language == 'en' else about_text_fi)
    input("Press Enter to return to the main menu" if language == 'en'
          else "Paina Enter palataksesi päävalikkoon.")

if __name__ == '__main__':
    # Validate settings
    try:
        validate_settings(custom_settings)
    except ValueError as e:
        print(f"[ERROR] Initial settings validation failed: {e}")
        print("[DEBUG] Resetting to default settings.")
        custom_settings = default_settings.copy()
        language = 'en'
        with open(config_path, 'w') as f:
            json.dump(custom_settings, f, indent=4)
    # Start main menu
    main_menu()

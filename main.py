from mod_processor import parse_mod_files
from models import game_mod
import sys


def main():
    try:
        # mod_list = parse_mod_files.get_mods_list("C:\\Games\\Factorio_2.0.8\\mods")
        # print(mod_list)
        # mod_list = [("AutoDeconstruct", "1.0.2"), ("Smart_Inserters", "2.0.6"), ("cargo-ships", "1.0.8"), ("alien-biomes-graphics", "0.7.0"), ("Krastorio2Assets", "1.2.3")]
        # mod_downloader.download_mods(mod_list, download_dir="temp")
        # mod = game_mod.GameMod.from_json(fetch_and_parse_json("https://mods.factorio.com/api/mods/alien-biomes/full"))
        # print("dfdf")
        mod_list = parse_mod_files.get_mods_list("C:\\Games\\Factorio_2.0.8\\mods")
        mod_list = game_mod.GameMod.sync_mod_list_with_remote(mod_list)


        print("done")

    except ValueError as e:
        print(f"Error: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        sys.exit(1)

# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    main()
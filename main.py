from mod_processor import parse_mod_files
from models import game_mod


def main():
    mod_list = parse_mod_files.get_mods_list("C:\\Games\\Factorio_2.0.8\\mods")
    mod_list = game_mod.GameMod.sync_mod_list_with_remote(mod_list)


    print("done")
    print(mod_list)


# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    main()
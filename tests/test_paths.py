import os

from core.paths import ROOT, resource


def test_resources_are_found_from_any_working_directory(tmp_path):
    previous = os.getcwd()
    os.chdir(tmp_path)  # as if the game were launched from a shortcut elsewhere
    try:
        assert resource("levels", "level1.txt").is_file()
        assert resource("locales", "en.json").is_file()
    finally:
        os.chdir(previous)


def test_resource_paths_are_absolute():
    assert ROOT.is_absolute()
    assert resource("assets").is_absolute()

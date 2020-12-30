from pathlib import Path
from os import getenv
from platform import system

data_dir_map = {
    'Linux': getenv(
        'XDG_DATA_DIR',
        Path(Path.home(), '.local/share')
    ),

    'Windows': getenv(
        'XDG_DATA_DIR',
        Path(Path.home(), 'AppData/Roaming')
    ),

    'macOS': getenv(
        'XDG_DATA_DIR', Path(Path.home(), 'Library')
    )
}

print(Path(data_dir_map[system()]).joinpath('interestingimages'))

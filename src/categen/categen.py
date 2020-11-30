from PrintingPress import Placements, operate
from configparser import ConfigParser
from hentai import Hentai, Format
from requests import get as rget
from datetime import datetime
from os import getenv, mkdir
from platform import system
from pathlib import Path
from PIL import Image
from json import load
from git import Repo


_file_dir = Path(__file__).parent
_local_format_dir = Path(_file_dir).joinpath('format')

# Directory Checks
data_dir_map = {
    'Linux': getenv(
        'XDG_DATA_DIR', Path(Path.home(),'.local/share/interestingimages')
    ),

    'Windows': getenv(
        'XDG_DATA_DIR', Path(Path.home(),'AppData\Roaming\interestingimages')
    ),

    'macOS': getenv(
        'XDG_DATA_DIR', Path(Path.home(), 'Library/interestingimages')
    )
}

_data_dir = Path(data_dir_map[system()])
_format_dir = _data_dir.joinpath('format')
_config_file = _data_dir.joinpath('config.ini')

if _data_dir.is_dir() is False:
    mkdir(_data_dir)

# Configuration
global config

if _config_file.is_file() is False:
    config = ConfigParser()
    config['Repository'] = {
        'format_repository': 'git://github.com/interestingimages/Format.git',
        'latest_placements': 'https://raw.githubusercontent.com/' + 
            'interestingimages/Design/master/placements.json',
        'download_path': str(_format_dir)
    }

    with open(_config_file, 'w') as _wop_config_file:
        config.write(_wop_config_file)

else:
    config = ConfigParser()
    config.read(_config_file)

# Format Repo Checks
if _format_dir.is_dir() is False:
    try:
        Repo.clone_from(config['Repository']['format_repository'],
                        config['Repository']['download_path'])
    
    except Exception as e:
        print(f'Could not clone Format repository. ({e})')

        try:
            local_format_repo = Repo(_local_format_dir)

        except Exception as e:
            raise Exception(f'Could not find local Format repository. ({e})')

        else:
            local_format_repo.clone(
                Path(config['Repository']['download_path']).absolute()
            )


class CatalogueGenerator:
    def __init__(
        self,
        cat_id: int,
        doujin_id: int,
        preview: Image.Image,
        format_dir: Path = Path(config['Repository']['download_path']),
        score: int = 5,
        desc: str = ''
    ):
        assert isinstance(
            doujin_id, int
        ), f'doujin_id must be int (got {type(doujin_id)})'

        assert isinstance(
            preview, Image.Image
        ), f'preview arg passed must be a PIL Image (got {type(preview)})'

        self.format_dir = format_dir
        assert self.format_dir.is_dir(), f'{format_dir} is a non-existant dir.'

        self.format_repo = Repo(format_dir)

        self.placements = format_dir.joinpath('placements.json')
        assert self.placements.is_file(), f'{self.placements} is a non-existant file.'

        self.template = format_dir.joinpath('thumbnail/template.png')
        assert self.template.is_file(), f'{self.template} is a non-existant file.'

        self.entry_path = format_dir.joinpath('entry.txt')
        assert self.template.is_file(), f'{self.template} is a non-existant file.'

        self.meta = {
            'id': cat_id,
            'score': score,
            'desc': desc
        }

        try:
            self.doujin = Hentai(doujin_id)
        except Exception as e:
            raise (f'Doujin could not be retrieved. ({e})')
    
    def update_check(self) -> None:
        lplacements = load(rget(config['Repository']['latest_placements']).text)

        with open(self.placements, 'r') as placements_file:
            cplacements = load(placements_file)
        
        report = {
            'status': lplacements['.meta']['version'] == cplacements['.meta']['version'],
            'latest': lplacements['.meta']['version'],
            'currect': cplacements['.meta']['version']
        }

        return report
    
    def update(self) -> Repo:
        return Repo.clone_from(url=config['Repository']['format_repository'],
                               path_to=self.format_dir)
    
    def entry(self) -> str:  # TODO
        with open(self.entry_path, 'r') as entry_file:
            entry_text = entry_file.read()
        
        entry_text = entry_text.replace('f:number', str(self.meta['id']))

        entry_text = entry_text.replace('f:title.pretty',
                                        self.doujin.title(Format.Pretty))

        entry_text = entry_text.replace('f:title.jp',
                                        self.doujin.title(Format.Japanese))
        
        entry_text = entry_text.replace('f:title.english', self.doujin.title())

        entry_text = entry_text.replace('f:pages', str(self.doujin.num_pages))

        # fuck you, i use british english
        entry_text = entry_text.replace('f:favourites', str(self.doujin.num_favorites))

        entry_text = entry_text.replace('f:rating', str(self.meta['score']))

        entry_text = entry_text.replace('f:desc', self.meta['desc'])

        entry_text = entry_text.replace('f:link', self.doujin.url)

        # f:time String Creation
        time = datetime.fromtimestamp(self.doujin.epos)
        entry_text = entry_text.replace('f:time', time.strftime('%B %d %Y, %H:%M:%S'))

        # f:creator String Creation
        artist_names = [tag.name for tag in self.doujin.artist]
        artist_names_str = ', '.join(artist_names)

        group_names = [tag.name for tag in self.doujin.group]
        group_names_str = ', '.join(artist_names)

        if len(artist_names) > 0 and len(group_names) > 0:  # artist + group
            creator = f'({artist_names_str} / {group_names_str})'
            entry_text = entry_text.replace('f:creator', creator)

        elif len(artist_names) > 0 and len(group_names) == 0:  # artist
            creator = f'({artist_names_str})'
            entry_text = entry_text.replace('f:creator', creator)
        
        elif len(artist_names) == 0 and len(group_names) > 0:  # group:
            creator = f'({group_names_str})'
            entry_text = entry_text.replace('f:creator', creator)

        else:  # nothing
            entry_text = entry_text.replace(' f:creator', '')

        # Parody
        if len(self.doujin.parody) > 0 and self.doujin.parody[0].name != 'original':
            total = len(self.doujin.parody)
            tag_names = [tag.name for tag in self.doujin.parody]

            entry_text = entry_text.replace('f:parody',
                                            'Parodying: ' + ', '.join(tag_names))

        else: 
            entry_text = entry_text.replace('\nf:parody', '')

        # Characters
        if len(self.doujin.character) > 0:
            tag_names = [tag.name for tag in self.doujin.character]
            total = len(tag_names)
            prefix = 'Character: ' if total == 1 else 'Characters: '

            entry_text = entry_text.replace('f:characters',
                                            prefix + ', '.join(tag_names))

        else: 
            entry_text = entry_text.replace('\nf:characters', '')

        # Tags
        tag_names = [tag.name for tag in self.doujin.tag]
        total = len(tag_names)
        entry_text = entry_text.replace('f:tags', 'Tagged: ' + ', '.join(tag_names))

        return entry_text

    def thumbnail(self) -> Image.Image:
        with open(self.placements, 'r') as placements_file:
            placements = load(placements_file)

        template_image = Image.open(self.template).convert('RGBA')

        thumbnail = operate(image=template_image, placements=placements)


def retrieve_latest_format(
    format_dir: Path = config['Repository']['download_path']
) -> Repo:
    return Repo.clone_from(url=config['Repository']['format_repository'],
                           path_to=format_dir)
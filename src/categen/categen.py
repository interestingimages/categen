from configparser import ConfigParser
from os import getenv, mkdir, walk
from tarfile import open as topen
from requests import get as rget
from datetime import datetime
from json import loads, load
from platform import system
from shutil import rmtree
from pathlib import Path

from PrintingPress import Placements, operate
from hentai import Hentai, Format
from PIL import Image
from git import Repo


_file_dir = Path(__file__).parent
_local_format_dir = Path(_file_dir).joinpath('format')

# Directory Checks
data_dir_map = {
    'Linux': getenv(
        'XDG_DATA_DIR',
        Path(Path.home(),'.local/share')
    ),

    'Windows': getenv(
        'XDG_DATA_DIR',
        Path(Path.home(),'AppData\Roaming')
    ),

    'macOS': getenv(
        'XDG_DATA_DIR', Path(Path.home(), 'Library')
    )
}

_data_dir = Path(data_dir_map[system()]).joinpath('interestingimages')
_format_dir = _data_dir.joinpath('format')
_config_file = _data_dir.joinpath('categen.ini')

if _data_dir.is_dir() is False:
    mkdir(_data_dir)

# Configuration
global config

if _config_file.is_file() is False:
    config = ConfigParser()
    config['Repository'] = {
        'format_repository': 'git://github.com/interestingimages/Format.git',
        'latest_placements': 'https://raw.githubusercontent.com/' + 
            'interestingimages/Format/master/placements.json',
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


def sanitize(name) -> str:
    # Really old [] removal from InterestingSystems/Author,
    # since nhentai doesnt give pretty Japanese titles.
    stop = [')', ']']
    watching = False
    detagged = name
    keyword = ''
    signal = ''

    for letter in name:
        if watching:
            keyword = keyword + letter

        if letter == '[' and signal == '':
            signal = ']'
            watching = True
            keyword = letter

        if letter == '(' and signal == '':
            signal = ')'
            watching = True
            keyword = letter

        if letter in stop and letter == signal:
            watching = False

            signal = ''

            detagged = detagged.replace(keyword, '')
            keyword = ''

    detagged = detagged.split(' ')
    pure = [elem for elem in detagged if elem != '']

    return ' '.join(pure)

def retrieve_latest_format(
    format_dir: Path = config['Repository']['download_path']
) -> Repo:
    return Repo.clone_from(url=config['Repository']['format_repository'],
                           to_path=format_dir)


class CatalogueGenerator:
    def __init__(
        self,
        cat_id: int,
        doujin_id: int,
        preview: Image.Image,
        score: str,
        desc: str,
        format_dir: Path = Path(config['Repository']['download_path']),
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

        self.preview = preview

        self.entry_path = format_dir.joinpath('entry.txt')
        assert self.entry_path.is_file(), f'{self.entry_path} is a non-existant file.'

        self.meta = {
            'id': f'{"0" * (3 - len(str(cat_id)))}{cat_id}',
            'score': score,
            'desc': desc
        }

        try:
            self.doujin = Hentai(doujin_id)
        except Exception as e:
            raise (f'Doujin could not be retrieved. ({e})')
    
    def update_check(self) -> dict:
        lplacements = loads(rget(config['Repository']['latest_placements']).text)

        with open(self.placements, 'r') as placements_file:
            cplacements = load(placements_file)
        
        report = {
            'status': lplacements['.meta']['version'] == cplacements['.meta']['version'],
            'latest': lplacements['.meta']['version'],
            'current': cplacements['.meta']['version']
        }

        return report
    
    def update(self) -> Repo:
        # Back up current repo
        with topen(_data_dir.joinpath('format-backup.tar.bz2'), mode='w:bz2') as backup:
            backup.add(self.format_dir, recursive=True)
            backup.close()

        rmtree(self.format_dir)

        return Repo.clone_from(url=config['Repository']['format_repository'],
                               to_path=self.format_dir)

    def format(self, text: str) -> str:  # TODO
        # Title Generation
        title_p_en = self.doujin.title(Format.Pretty)
        title_p_jp = sanitize(self.doujin.title(Format.Japanese))

        if title_p_en != '' and title_p_jp != '':  #      en + jp
            title = f'{title_p_en - title_p_jp}'
        elif title_p_en != '' and title_p_jp == '':  #    en
            title = f'{title_p_en}'
        elif title_p_en == '' and title_p_jp != '':  #    jp
            title = f'{title_p_jp}'
        else:  #                                          nothing
            title = ''

        # Creator Text Generation
        artist_names = [tag.name for tag in self.doujin.artist]
        artist_names_str = ', '.join(artist_names)

        group_names = [tag.name for tag in self.doujin.group]
        group_names_str = ', '.join(group_names)

        if len(artist_names) > 0 and len(group_names) > 0:  #      artist + group
            creator = f'({artist_names_str} / {group_names_str})'
        elif len(artist_names) > 0 and len(group_names) == 0:  #   artist
            creator = f'({artist_names_str})'
        elif len(artist_names) == 0 and len(group_names) > 0:  #   group:
            creator = f'({group_names_str})'
        else:  #                                                   nothing
            creator = ''

        format_map = {
            '<[bold]>': self.formatting['bold'],
            '<[italic]>': self.formatting['italic'],
            '<[scode]>': self.formatting['scode'],
            '<[mcode]>': self.formatting['mcode'],

            '<[entry_id]>': self.meta['id'],
            '<[rating]>': self.meta['score'],
            '<[description]>': self.meta['desc'],

            '<[title.english]>': self.doujin.title(),
            '<[title.english.pretty]>': title_p_en,
            '<[title.japanese]>:': self.doujin.title(Format.Japanese),
            '<[title.japanese.pretty]>': title_p_jp,
            '<[title]>': title,

            '<[creator.scanlator]>': self.doujin.scanlator,
            '<[creator.artist]>': ', '.join(self.doujin.artist),
            '<[creator.group]>': ', '.join(self.doujin.group),
            '<[creator]>': creator,

            '<[doujin_id]>': self.doujin.magic,
            '<[pages]>': self.doujin.num_pages,
            '<[favourites]>': self.doujin.num_favorites,
            '<[link]>': self.doujin.url,
            '<[time]>': datetime.fromtimestamp(
                self.doujin.epos
            ).strftime('%B %d %Y, %H:%M:%S')
        }

        for keyword, replacement in format_map.items():
            text = text.format(keyword, replacement)

    def entry(self) -> str:
        with open(self.entry_path, 'r') as entry_file:
            entry_text = entry_file.read()
        
        entry_text = entry_text.replace('f:number', self.meta['id'])

        entry_text = entry_text.replace('f:title.en-pretty',
                                        self.doujin.title(Format.Pretty))

        entry_text = entry_text.replace('f:title.en', self.doujin.title())

        entry_text = entry_text.replace('f:title.jp-pretty',
                                        sanitize(self.doujin.title(Format.Japanese)))

        entry_text = entry_text.replace('f:title.jp',
                                        self.doujin.title(Format.Japanese))

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

    def thumbnail(self, suppress: bool = False) -> Image.Image:
        with open(self.placements, 'r') as placements_file:
            placements = load(placements_file)

        placements['viewfinder']['path'] = self.preview

        for area_name, area_data in placements.items():
            if area_name != '.meta':
                if isinstance(area_data['path'], str):
                    area_data['path'] = str(self.format_dir.joinpath(area_data['path']))

        artist_names = [tag.name for tag in self.doujin.artist]
        artist_names_str = ', '.join(artist_names)

        placements['artist']['text'] = artist_names_str

        tag_names = [tag.name for tag in self.doujin.tag]
        placements['tags']['text'] = ', '.join(tag_names)

        placements['title']['text'] = self.doujin.title(Format.Pretty)

        placements['id']['text'] = self.meta['id']

        placements['link']['text'] = f'nh.{self.doujin.id}'

        template_image = Image.open(self.template).convert('RGBA')

        return operate(image=template_image,
                       placements=Placements.parse(placements),
                       suppress=suppress)

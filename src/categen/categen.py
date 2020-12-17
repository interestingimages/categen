from configparser import ConfigParser
from tarfile import open as topen
from requests import get as rget
from datetime import datetime
from json import loads, load
from os import getenv, mkdir
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
    config['Settings'] = {
        'markdown_type': 'Telegram',
        'divide': 'both',
        'interestingtags': True,
    }
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
    markdown_map = {
        'WhatsApp': {
            # *Hello World*
            'bold': ['*', '*'],

            # _Hello World_
            'italic': ['_', '_'],

            #```Hello World```
            'scode': ['```', '```'],
            'mcode': ['```', '```']
        },

        'Telegram': {
            # **Hello World**
            'bold': ['**', '**'],

            # __Hello World__
            'italic': ['__', '__'],

            # `Hello World`
            'scode': ['`', '`'],

            # ```
            # Hello World
            # ```
            'mcode': ['```\n', '\n```']
        }
    }

    def __init__(
        self,
        cat_id: int,
        doujin_id: int,
        preview: Image.Image,
        score: str,
        desc: str,
        format_dir: Path = Path(config['Repository']['download_path']),
        markdown: str = config['Settings']['markdown_type'],
        divide: str = config['Settings']['divide'],
        interestingtags: bool = True if config['Settings']['interestingtags'] == 'True' else False
    ):
        assert markdown in self.markdown_map, f'Invalid markdown type! ({markdown})'
        self.markdown = markdown

        assert divide in ['left', 'right', 'both']
        self.divide_type = divide

        assert isinstance(
            doujin_id, int
        ), f'doujin_id must be int (got {type(doujin_id)})'

        assert isinstance(
            preview, Image.Image
        ), f'preview arg passed must be a PIL Image (got {type(preview)})'

        self.format_dir = format_dir
        assert self.format_dir.is_dir(), f'{format_dir} is a non-existant dir.'

        self.formatting_map = format_dir.joinpath('formatting.json')
        if self.formatting_map.is_file():
            self.formatting_map = load(open(self.formatting_map, 'r', encoding='utf-8'))
        else:
            self.formatting_map = {}

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
            raise Exception(f'Doujin could not be retrieved. ({e})')

        self.tagsofinterest_path = format_dir.joinpath('tagsofinterest.json')
        if not self.tagsofinterest_path.exists():
            self.tagsofinterest = [tag.name for tag in self.doujin.tag]
            self.interestingtags = False

        else:
            with open(self.tagsofinterest_path, 'r', encoding='utf-8') as toi:
                self.tagsofinterest = load(toi)
                self.interestingtags = interestingtags
    
    def divide(self, text: str) -> str:
        if self.divide_type == 'both':
            return text
        elif self.divide_type == 'left':
            if '|' in text:
                return text.split('|')[0].lstrip().rstrip()
            else:
                return text
        else:
            if '|' in text:
                return text.split('|')[1].lstrip().rstrip()
            else:
                return text
    
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

    def format(self, text: str, markdown_type: str) -> str:
        def fword(keyword: str) -> str:
            try:
                override = self.formatting_map[keyword]
            except KeyError:
                return keyword
            else:
                return f'{keyword}:{override}'

        # Title Generation
        title_p_en = self.doujin.title(Format.Pretty)
        title_p_jp = sanitize(self.doujin.title(Format.Japanese))

        markdown = self.markdown_map[markdown_type]

        bold = markdown['bold'][0]
        _bold = markdown['bold'][1]

        if title_p_en != '' and title_p_jp != '':  # <--- en + jp
            title = f'{bold}{title_p_en}{_bold} - {title_p_jp}'
        elif title_p_en != '' and title_p_jp == '':  # <- en
            title = f'{bold}{title_p_en}{_bold}'
        elif title_p_en == '' and title_p_jp != '':  # <- jp
            title = f'{bold}{title_p_jp}{_bold}'
        else:  # <--------------------------------------- nothing
            title = ''

        # Creator Text Generation
        artist_names = [tag.name for tag in self.doujin.artist]
        artist_names_str = ', '.join(artist_names)

        group_names = [tag.name for tag in self.doujin.group]
        group_names_str = ', '.join(group_names)

        if len(artist_names) > 0 and len(group_names) > 0:  # <---- artist + group
            creator = f'({artist_names_str} / {group_names_str})'
        elif len(artist_names) > 0 and len(group_names) == 0:  # <- artist
            creator = f'({artist_names_str})'
        elif len(artist_names) == 0 and len(group_names) > 0:  # <- group:
            creator = f'({group_names_str})'
        else:  # <------------------------------------------------- nothing
            creator = ''

        # Tags
        tags = [self.divide(tag.name) for tag in self.doujin.tag]
        tags_interest = [tag for tag in tags if tag in self.tagsofinterest]
        tags_remainder = [tag for tag in tags if tag not in tags_interest]

        format_map = {
            'bold': markdown['bold'][0],
            '-bold': markdown['bold'][1],

            'italic': markdown['italic'][0],
            '-italic': markdown['italic'][1],

            'scode': markdown['scode'][0],
            '-scode': markdown['scode'][1],

            'mcode': markdown['mcode'][0],
            '-mcode': markdown['mcode'][1],

            fword('entry_id'): self.meta['id'],
            fword('rating'): self.meta['score'],
            fword('description'): self.meta['desc'],

            fword('title.english'): self.doujin.title(),
            fword('title.english.pretty'): title_p_en,
            fword('title.japanese:'): self.doujin.title(Format.Japanese),
            fword('title.japanese.pretty'): title_p_jp,
            fword('title'): title,

            fword('tags.interest'): ', '.join(tags_interest),
            fword('tags.remainder'): ', '.join(tags_remainder),
            fword('tags'): ', '.join(tags),

            fword('creator.scanlator'): self.doujin.scanlator,
            fword('creator.artist'): ', '.join([t.name for t in self.doujin.artist]),
            fword('creator.group'): ', '.join([t.name for t in self.doujin.group]),  # <- applicable
            fword('creator'): creator,

            fword('doujin_id'): self.doujin.id,
            fword('pages'): self.doujin.num_pages,
            fword('favourites'): self.doujin.num_favorites,  # <------------------------- applicable
            fword('link'): self.doujin.url,
            fword('time'): datetime.fromtimestamp(self.doujin.epos).strftime('%B %d %Y, %H:%M:%S'),

            fword('parody'): ', '.join([t.name for t in self.doujin.parody]),  # <------- applicable
            fword('characters'): ', '.join([t.name for t in self.doujin.character]),  # <- applicable

            fword('slink'): f'nh.{self.doujin.id}'
        }

        for keyword, replacement in format_map.items():
            conditions = [
                'parody' in keyword and replacement == 'original',
                'parody' in keyword and replacement == '',
                'favourites' in keyword and replacement == '0',
                'character' in keyword and replacement == '',
                'creator.group' in keyword and replacement == ''
            ]
            if not any(conditions):
                if ':' in keyword:
                    # keyword:\nkeyword\n
                    _keyword = keyword
                    keyword = keyword.split(':')[0]
                    replacement = _keyword.lstrip(keyword.split(':')[0] + ':').replace('{}', replacement)

                text = self.divide(text.replace(f'<[{keyword}]>', str(replacement)))
            
            else:
                text = text.replace(f'<[{keyword}]>', '')

        return text

    def entry(self, markdown: str = '') -> str:
        markdown = self.markdown if markdown == '' else markdown
        assert markdown in self.markdown_map, f'Invalid markdown type! ({markdown})'

        with open(self.entry_path, 'r') as entry_file:
            entry_text = self.format(entry_file.read(), markdown_type=markdown)

        return entry_text

    def thumbnail(self, suppress: bool = False) -> Image.Image:
        with open(self.placements, 'r') as placements_file:
            placements = load(placements_file)

        placements['viewfinder']['path'] = self.preview

        for area_name, area_data in placements.items():
            if area_name != '.meta':
                if isinstance(area_data['path'], str):
                    area_data['path'] = str(self.format_dir.joinpath(area_data['path']))
                
                if 'text' in area_data:
                    area_data['text'] = self.format(area_data['text'],
                                                    markdown_type=self.markdown)
                
                placements[area_name] = area_data

        template_image = Image.open(self.template).convert('RGBA')

        return operate(image=template_image,
                       placements=Placements.parse(placements),
                       suppress=suppress)

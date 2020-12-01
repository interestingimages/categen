from argparse import ArgumentParser
from time import sleep, time
from pathlib import Path
from os import mkdir

from git import exc


class status:
    def __init__(self, message: str, indent: int = 0):
        if indent > 0:
            indent = '  ' * (indent - 1) + '└─ '
        else:
            indent = ''

        print(f'{indent}⌛ {message}', end='\r')

        self.message = message
        self.indent = indent

    def complete(self, suppress: bool = False):
        print(f'{self.indent}✅ {self.message}')


def ask(
    message,
    max_len: int = 0,
    is_file: bool = False,
    is_dir: bool = False,
    is_int: bool = False
):
    non_int = 'Response must be able to be converted to an integer!'
    non_file = 'Response is not a valid file!'
    non_dir = 'Response is not a valid directory!'
    max_len_err = f'Response is longer than expected, {max_len} chars!'

    print(message)

    while True:
        tripped = False
        retrieved = input('-> ')

        if max_len != 0 and len(retrieved) > max_len:
            tripped = True
            print(max_len_err, end='\r')
            sleep(1.5)
            print(' ' * max_len_err, end='\r')

        if is_int and not tripped:
            try:
                int(retrieved)
            
            except ValueError:
                print(non_int, end='\r')
                sleep(1.5)
                print(' ' * len(non_int), end='\r')

            else:
                return int(retrieved)
        
        elif is_file and not tripped:
            retrieved = Path(retrieved)
            if not retrieved.is_file():
                print(non_file, end='\r')
                sleep(1.5)
                print(' ' * len(non_file), end='\r')

            else:
                return retrieved
        
        elif is_dir and not tripped:
            retrieved = Path(retrieved)
            try:
                if not retrieved.is_dir():
                    mkdir(retrieved)
            
            except Exception as e:
                print('Error:', e, end='\r')
                sleep(1.5)
                print('Error:', ' ' * len(str(e)), end='\r')
            
            else:
                return retrieved

        elif not tripped:
            return retrieved


header = 'interesting images: Catalogue Entry Generator'
print(f'{header}\n{"─" * len(header)}')

# Argument Collection
parser = ArgumentParser()

parser.add_argument('-f', '--format',
                    type=str,
                    help='the Format directory',
                    default=None)

args = parser.parse_args()

# Imports
wait_msg = 'Initializing. Please wait a moment...'
print(wait_msg, end='\r')

from categen import config, CatalogueGenerator
from PIL import Image

print(' ' * len(wait_msg), end='\r')

# Checks
if args.format is None:
    format_arg = config['Repository']['download_path']
else:
    format_arg = args.design

format_path = Path(format_arg)
assert format_path.is_dir(), 'Format path is non-existant!'

# Information Gathering
preview_path = ask('Preview Image Path', is_file=True)
print()

output_path = ask('Output Directory Path', is_dir=True)
print()

cat_id = ask('Catalogue ID', is_int=True, max_len=3)
print()

doujin_id = ask('Doujin ID', is_int=True, max_len=6)
print()

desc_text = ask('Description')
print()

rating = ask('Score (out of 10)')
print()

# Operation
print('Starting Operation...')
start = time()

preview_image = Image.open(preview_path).convert('RGBA')

gen_status = status('Creating a Catalogue Generator...', indent=1)
generator = CatalogueGenerator(doujin_id=doujin_id,
                               cat_id=cat_id,
                               preview=preview_image,
                               format_dir=format_path,
                               score=rating,
                               desc=desc_text)
gen_status.complete()

entry_status = status('Generating Entry Text...', indent=1)
entry_text = generator.entry()
entry_status.complete

thumbnail_status = status('Generating Entry Thumbnail', indent=1)
thumbnail_image = generator.thumbnail(suppress=True)
thumbnail_status.complete()

write_status = status('Writing Files...', indent=1)
with open(output_path.joinpath('entry.txt'), 'w', encoding='utf-8') as entry_file:
    entry_file.write(entry_text)

thumbnail_image.save(str(output_path.joinpath('thumbnail.png')))
write_status.complete()

end = time()
print(f'\n✅ Operation completed in {round(end - start)}s!')

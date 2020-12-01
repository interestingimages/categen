from argparse import ArgumentParser
from time import sleep, time
from pathlib import Path
from os import mkdir

from categen import Config, CatalogueGenerator
from PIL import Image


file_dir = Path(__file__).parent.absolute()


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


def ask(message, is_int: bool = False):
    non_int = 'Response must be able to be converted to an integer!'
    non_int_len = len(non_int)

    print(message)

    while True:
        retrieved = input('-> ')

        if is_int:
            try:
                int(retrieved)
            
            except ValueError:
                print(non_int, end='\r')
                sleep(0.75)
                print(' ' * non_int_len, end='\r')

            else:
                break
        
        else:
            break
    
    return retrieved


# Argument Collection
parser = ArgumentParser()

parser.add_argument('-d', '--design',
                    type=str,
                    help='the Design directory',
                    default=Config['Repository']['download_path'])
parser.add_argument('preview', type=str, help='the 2:3 preview image')
parser.add_argument('output', type=str, help='output')

args = parser.parse_args()

# Checks
design_path = Path(args.design)
assert design_path.is_dir(), 'Design path is non-existant!'

preview_path = Path(args.preview)
assert preview_path.is_file(), 'Preview image is non-existant!'

output_path = Path(args.output)
if not output_path.is_dir():
    mkdir(output_path)

# Information Gathering
cat_id = ask('Catalogue ID', is_int=True)
print()

doujin_id = ask('Doujin ID', is_int=True)
print()

desc_text = ask('Description')
print()

rating = ask('Score (out of 10)', is_int=True)
print()

# Operation
start = time()

preview_image = Image.open(preview_path).convert('RGBA')

gen_status = status('Creating a Catalogue Generator...', indent=1)
generator = CatalogueGenerator(doujin_id=doujin_id,
                               cat_id=cat_id,
                               preview=preview_image,
                               design_dir=design_path,
                               score=rating,
                               desc=desc_text)
gen_status.complete()

entry_status = status('Generating Entry Text...', indent=1)
entry_text = generator.entry()
entry_status.complete

thumbnail_status = status('Generating Entry Thumbnail', indent=1)
thumbnail_image = generator.thumbnail()
thumbnail_status.complete()

write_status = status('Writing Files...', indent=1)
with open(output_path.joinpath('entry.txt'), 'w', encoding='utf-8') as entry_file:
    entry_file.writable(entry_text)

thumbnail_image.save(str(output_path.joinpath('thumbnail.png')))
write_status.complete()

end = time()
print(f'\n✅ Operation completed in {round(end - start)}s!')

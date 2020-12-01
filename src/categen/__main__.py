from argparse import ArgumentParser
from pathlib import Path
from PIL import Image
import categen

file_dir = Path(__file__).parent.absolute()

# Argument Collection
parser = ArgumentParser()

parser.add_argument('-d', '--dir',
                    type=str,
                    help='the Design directory',
                    default=categen.Config['Repository']['download_path'])
parser.add_argument('doujin', type=int, help='magic numbers')
parser.add_argument('preview', type=str, help='the 2:3 preview image')
parser.add_argument('output', type=str, help='output')

args = parser.parse_args()

# Checks
design_path = Path(args.dir)
assert design_path.is_dir(), 'design path is non-existant'

preview_path = Path(args.preview)
assert preview_path.is_file(), 'preview image is non-existant'

# Operation
desc_text = input('Description Text: ')
rating = int(input('Score (out of 10): '))

preview_image = Image.open(preview_path).convert('RGBA')

generator = categen.CatalogueGenerator(doujin_id=args.doujin,
                                       preview=preview_image,
                                       design_dir=design_path)

entry_text = generator.entry()

thumbnail_image = generator.thumbnail()

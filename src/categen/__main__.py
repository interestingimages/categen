from categen import CatalogueGenerator
from argparse import ArgumentParser
from pathlib import Path
from PIL import Image

file_dir = Path(__file__).parent.absolute()

# Argument Collection
parser = ArgumentParser()

parser.add_argument("-d", "--dir",
                    type=str,
                    help="the Design directory",
                    default=file_dir.joinpath("Design"))
parser.add_argument("doujin", type=int, help="magic numbers")
parser.add_argument("preview", type=str, help="the 2:3 preview image")

args = parser.parse_args()

# Checks
design_path = Path(args.dir)
assert design_path.is_dir(), "design path is non-existant"

preview_path = Path(args.preview)
assert preview_path.is_file(), "preview image is non-existant"

# Operation
preview_image = Image.open(preview_path).convert("RGBA")

generator = CatalogueGenerator(doujin_id=args.doujin,
                               preview=preview_image,
                               design_dir=design_path)

thumbnail_image = generator.thumbnail()

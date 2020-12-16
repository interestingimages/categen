# interesting images: Catalogue Entry Generator

A Catalogue Entry Generator for interesting images.

## Storage

categen comes with the
[interestingimages/Format]('https://github.com/interestingimages/Format')
repository, but downloads the repo to a dir if internet is available using GitPython.

The storage for interesting images scripts is standardized, and is dictated by the
`XDG_DATA_DIR` environment variable.

By default, the universal interesting images data directory is located in the following:

- Windows: `C:\Users\<username>\AppData\Roaming\interestingimages`
- Linux: `~/.local/share/interestingimages`
- macOS: `~/Library/interestingimages`

categen stores the following files within said folder:

- `format/` - The downloaded/copied Format repository.
- `categen.ini` - The categen configuration file.

## Usage

You can infer from code, `__main__.py` or `tests/generation.py` for more detailed usage.

```python
from src.categen import CatalogueGenerator
from PIL import Image

preview = Image.open('tests/verycool23ar.png').convert('RGBA')

# make a generator
generator = CatalogueGenerator(
    cat_id=1,           # catalogue id                 int
    doujin_id=177013,   # magic numbers                int
    preview=preview,    # preview image for thumbnail  PIL.Image.Image,
    score="6.9"         # doujin score (out of 10)     str (to allow 3.5 or meh)
    desc="its fucked",  # doujin description           str
)

# check for updates
report = generator.update_check()  # 3 keys: status, current, latest
if report['status'] is False:  # newer version found, update
    generator.update()

# make entry text
text = generator.entry()  # return str

# make thumnail
thumbnail = generator.thumbnail()  # returns PIL.Image.Image

# you can then handle the files or write them out
```

You can run a test on the main functions of categen by using the following command
in the root of the repository directory:

`python -c "import tests.generation"`

## Contact

This script isn't intended for much usage out of the interesting images Community,
but if you need help with understanding the script, you may reach out to me at
`hello at rxyth dot co`

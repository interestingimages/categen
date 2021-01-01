# interesting images: Catalogue Entry Generator

A Catalogue Entry Generator for interesting images.

## Installation

```
pip3 install iicategen
```

Minimum Python version is `3.7`.

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

categen is meant as an internal tool, and if you are interested in utilizing the code personally, you may do any of the following:

- Infer from Code
  - `src/categen/data.py`
  - `src/categen/catentry.py`
  - `tests/gen/all.py`

- Contact Me (rxyth at criptext dot com)

```python
from categen import CatalogueGenerator
from PIL import Image

preview = Image.open('tests/verycool23ar.png').convert('RGBA')

# Make a "Generator"
generator = CatalogueGenerator(
    eid=1,
    hid=177013,
    score="7.5",
    desc="the sheer cursery"
)

# Advanced - Check for Updates
if generator.format.latest_ver != generator.format.current_ver:
    try:
        # Attempt to pull from configured repo
        generator.format.pull()

    except Exception:
        from shutil import rmtree

        # Backup format repo
        generator.format.backup()
        # Remove current format repo
        rmtree(generator.config["Repository"]["path"])
        # Clone new format repo
        generator.format.clone()

# Generate Entry Text (str)
text = generator.entry()

# Generate Thumbnail (PIL.Image.Image)
thumbnail = generator.thumbnail()

# ... Write them out to files or whatever
```

## Tests

You can run a test on the main functions of categen by using the following command
in the root of the repository directory:

`python -c "import tests.gen.all"` (Generates image+text)

Other test scripts include:

- `tests.gen.txt`: Generates text only
- `tests.gen.img`: Generates image only
- `tests.git`: Tests Git Handling Functionality

from pathlib import Path
from PIL import Image
from time import time
from os import mkdir

class Test:
    def __init__(self, message: str, indent: int = 0):
        if indent > 0:
            indent = '  ' * (indent - 1) + '└─ '
        else:
            indent = ''

        print(f'{indent}⌛ {message}', end='\r')

        self.message = message
        self.indent = indent
        self.start_time = time()
    
    def change(self, icon, message):
        self.message = message
        print(f'{self.indent}{icon} {message}', end='\r')

    def stop(self, new_message: str = '', suppress: bool = False):
        if new_message != '':
            new_message = f'- {new_message} '

        taken = round(time() - self.start_time, 5)
        print(f'{self.indent}✅ {self.message} {new_message}- Time Taken: {taken}')


# Miscellaneous
file_dir = Path(__file__).parent
preview_img = Image.open(str(file_dir.joinpath('verycool23ar.png')))
output_dir = file_dir.joinpath('output')
entry_wa_text = output_dir.joinpath('entry-wa.txt')
entry_tg_text = output_dir.joinpath('entry-tg.txt')

if output_dir.is_dir() is False:
    mkdir(output_dir)

start = time()

# Tests
test = Test('Module Import')
from src.categen import CatalogueGenerator
test.stop()

test = Test('Generator Initialization')
generator = CatalogueGenerator(cat_id=0,
                               doujin_id=338763,
                               preview=preview_img,
                               score=10,
                               desc='The test of the century.',
                               )
test.stop()

test = Test('Checking for Updates')
report = generator.update_check()
if report['status'] is False:
    test.change('✅', f'Checking for Updates - Found newer version {report["latest"]}')
    print()  # Advance /n
    test = Test('Updating Format Repository', indent=1)
    generator.update()
    test.stop(new_message=f'{report["current"]} -> {report["latest"]}')
else:
    test.stop()

test = Test('Thumbnail Generation')
thumbnail = generator.thumbnail(suppress=True)
test.stop()
thumbnail.save(str(output_dir.joinpath('thumbnail.png')))

end = time()

print(f'\n✅ Test completed in {round(end - start, 5)}s.')
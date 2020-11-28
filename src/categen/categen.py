from PrintingPress import Placements, operate
from hentai import Hentai
from pathlib import Path
from PIL import Image
from json import load


file_dir = Path(__file__).parent.absolute()


class CatalogueGenerator:
    def __init__(self,
                 doujin_id: int,
                 preview: Image.Image,
                 design_dir: Path = file_dir.joinpath("Design")):
        assert isinstance(
            doujin_id, int
        ), f"doujin_id must be int (got {type(doujin_id)})"

        assert isinstance(
            preview, Image.Image
        ), f"preview arg passed must be a PIL Image (got {type(preview)})"

        self.design_dir = design_dir
        assert self.design_dir.is_dir(), f"{design_dir} is a non-existant dir."

        self.placements = design_dir.joinpath("placements.json")
        assert self.placements.is_file(), f"{self.placements} is a non-existant file."

        self.template = design_dir.joinpath("templates/template.png")
        assert self.template.is_file(), f"{self.template} is a non-existant file."

        self.doujin = Hentai(doujin_id)
        assert Hentai.exists(self.doujin.id), 'Given doujin_id is not valid.'
    
    def entry(self) -> str:  # TODO
        pass

    def thumbnail(self) -> Image.Image:
        with open(self.placements, "r") as placements_file:
            placements = load(placements_file)

        template_image = Image.open(self.template).convert("RGBA")

        thumbnail = operate(image=template_image, placements=placements)

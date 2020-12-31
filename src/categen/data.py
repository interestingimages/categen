from os import getenv, mkdir
from platform import system
from pathlib import Path


_file_dir = Path(__file__).parent
_local_format_dir = Path(_file_dir.joinpath("format"))
_data_dir_map = {
    "Linux": getenv("XDG_DATA_DIR", Path(Path.home(), ".local/share")),
    "Windows": getenv("XDG_DATA_DIR", Path(Path.home(), "AppData/Roaming")),
    "macOS": getenv("XDG_DATA_DIR", Path(Path.home(), "Library")),
}

data_dir = Path(_data_dir_map[system()]).joinpath("interestingimages")
format_dir = data_dir.joinpath("format")
config_file = data_dir.joinpath("categen.toml")
backup_file = data_dir.joinpath("format-ver.tar.bz2")

if not data_dir.is_dir():
    mkdir(data_dir)


class Config:
    default = {
        "Settings": {
            "markdown_type": "Telegram",
            "divide": "both",
            "interestingtags": True,
        },
        "Repository": {
            "path": str(format_dir),
            "format_repository": "git://github.com/interestingimages/Format.git",
            "latest_placements": "https://raw.githubusercontent.com/"
            "interestingimages/Format/master/placements.json",
            "backup_file": str(backup_file),
        },
    }

    def __init__(self, encoding: str = "utf-8") -> None:
        import tomlkit

        self.tomlkit = tomlkit

        if not config_file.is_file():
            self.file = open(config_file, "w", encoding=encoding)

            # Make new config file
            self.data = self.tomlkit.document()

            for key, value in Config.default.items():
                self.data[key] = value

            # Cleanup
            self.file.write(self.tomlkit.dumps(self.data))
            self.file.flush()

        else:
            self.file = open(config_file, "r+", encoding=encoding)
            self.data = tomlkit.loads(self.file.read())

            # Add unadded tables
            for table in [
                t for t in Config.default.keys() if t not in self.data.keys()
            ]:
                print(
                    f'categen: Appending non-present table "{table}" not present '
                    "in categen.toml."
                )
                self.data.update({table: Config.default[table]})

            # Add unadded keys to existing tables
            for table, contents in self.data.items():
                if table in Config.default:
                    if contents.keys() != Config.default[table].keys():
                        for key in [
                            k
                            for k in Config.default[table].keys()
                            if k not in contents.keys()
                        ]:
                            print(
                                f'categen: Appending non-present key value pair "{key}" '
                                f"not present in categen.toml:{table}"
                            )
                            self.data[table][key] = Config.default[table][key]

            # Cleanup
            self.file.seek(0)
            self.file.write(self.tomlkit.dumps(self.data))
            self.file.flush()

    def __getitem__(self, item):
        return self.data[item]

    def get(self, item, default=None):
        return self.data.get(item, default=default)

    def write(self) -> None:
        self.file.seek(0)
        self.write(self.tomlkit.dumps(self.data))
        self.file.flush()

    def close(self) -> None:
        self.file.close()


class Format:
    def __init__(self, repo_config: dict) -> None:
        import git

        self.git = git
        self.config = repo_config
        self.repo = self.git.Repo(self.config["path"])

    def pull(self):
        origin = self.repo.remotes["origin"]
        origin.pull()

    def backup(self, file_path=None, format_path=None) -> None:
        from tarfile import open

        if file_path is None:
            file_path = self.config["backup_file"]

        if format_path is None:
            format_path = self.config["path"]

        with open(
            str(file_path).replace("ver", Format.current_ver()), mode="w:bz2"
        ) as backup:
            backup.add(format_path)

    def clone(self, path=None, url=None) -> None:
        if url is None:
            url = self.config["format_repository"]

        if path is None:
            path = self.config["path"]

        assert any(Path(path).iterdir()), f"{str(path)} is not empty."

        repo = self.git.Repo.clone_from(url=url, to_path=path)

        self.repo = repo

    @staticmethod
    def current_ver() -> str:
        from json import load

        placements = open(format_dir.joinpath("placements.json"), "r", encoding="utf-8")
        current = load(placements)[".meta"]["version"]
        placements.close()

        return current

    @staticmethod
    def latest_ver(url: str) -> str:
        from requests import get
        from json import loads

        return loads(get(url).text)[".meta"]["version"]

    @staticmethod
    def retrieve_local(format_dir=format_dir) -> None:
        from shutil import move

        move(_local_format_dir, format_dir)

    @staticmethod
    def retrieve_online(url, path) -> None:
        from git import Repo

        Repo.clone_from(url=url, to_path=path)

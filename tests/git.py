from src import categen
from tests import utils

import colorama

colorama.init(autoreset=True)


def main():
    print(
        f"{colorama.Style.BRIGHT}interesting images"
        f"{colorama.Style.RESET_ALL} Tests / Format Git Repository\n"
    )

    tbcollect = utils.TracebackCollector()

    stsmgr = categen.cli.StatusManager("Repository Operations")
    cfgini = stsmgr.register("Config Initialization")
    rpoini = stsmgr.register("Initialization")
    rpomta = stsmgr.register("Meta Check")
    rpobak = stsmgr.register("Backup")
    rpopll = stsmgr.register("Pull")
    rpocln = stsmgr.register("Clone")

    # Initialization
    def cfginit() -> categen.data.Config:
        return categen.data.Config()

    def rpoinit(status, config: categen.data.Config) -> categen.data.Format:
        try:
            return categen.data.Format(config["Repository"])

        except Exception as e:
            tbcollect.add(status, e)
            try:
                status.text("Retrieving from online repo")
                categen.data.Format.retrieve_online(
                    url=config["Repository"]["link"], path=config["Repository"]["path"]
                )
            except Exception as e:
                status.text("Retrieving from offline repo")
                tbcollect.add(status, e)
                categen.data.Format.retrieve_local(config["Repository"]["path"])

            return categen.data.Format(config["Repository"])

    config = utils.attempt(cfgini, tbcollect, cfginit)
    if config is None:  # Failed, cannot continue.
        tbcollect.display()
        exit()

    repo = utils.attempt(rpoini, tbcollect, rpoinit, rpoini, config)
    if repo is None:  # Failed, cannot continue.
        tbcollect.display()
        exit()

    # Meta Check
    def meta():
        return {
            "text": f"Current: {categen.data.Format.current_ver()}, "
            f"Latest: {categen.data.Format.latest_ver(config['Repository']['latest_placements'])}",
        }

    utils.attempt(rpomta, tbcollect, meta)

    # Backup
    backup_status = utils.attempt(rpobak, tbcollect, repo.backup, ret=False)

    # Pull
    utils.attempt(rpopll, tbcollect, repo.pull)

    # Clone
    def clone(repo: categen.data.Format, backup_status):
        if backup_status is False:
            raise Exception(
                "Cannot be executed due to Repository Backup test not passing."
            )
        else:
            from shutil import rmtree
            from os import mkdir

            repo.backup()
            rmtree(repo.config["path"])
            mkdir(repo.config["path"])
            repo.clone()

    utils.attempt(rpocln, tbcollect, clone, repo, backup_status)

    tbcollect.display()


if __name__ == "__main__":
    main()

from traceback import print_tb
from src import categen
from time import time
import colorama

colorama.init(autoreset=True)


def main():
    print(
        f"{colorama.Style.BRIGHT}interesting images"
        f"{colorama.Style.RESET_ALL} Tests / Format Git Repository\n"
    )

    tracebacks = []

    def add_traceback(status: categen.cli.StatusManager.Status, exc: Exception):
        tracebacks.append(
            (
                f"{colorama.Style.BRIGHT}{colorama.Fore.RED}"
                f"[{status.manager.operations[status.id]['message']}] "
                f"{exc.__class__.__name__}: {exc}\n{colorama.Style.RESET_ALL}",
                exc.__traceback__,
            )
        )

    def print_tracebacks():
        for payload in tracebacks:
            msg, obj = payload

            print(f"\n{msg}", end="\r")
            print_tb(obj)

    def attempt(status, operation, *args, ret=None):
        status.colour(colorama.Fore.YELLOW)
        stime = time()

        try:
            stime = time()
            result = operation(*args)

        except Exception as e:
            status.colour(colorama.Fore.RED)
            status.text(f"{e.__class__.__name__}: {e}")
            add_traceback(status, e)
            return ret

        else:
            if isinstance(result, dict) and "text" in result:
                add_text = f'{result["text"]} - '
            else:
                add_text = ""

            status.colour(colorama.Fore.GREEN)
            status.text(
                f"{colorama.Style.DIM}{add_text}Time Taken: {round(time() - stime, 3)}"
            )

            if isinstance(result, dict) and "result" in result:
                return result["result"]
            else:
                return result

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
            add_traceback(status, e)
            try:
                status.text('Retrieving from online repo')
                categen.data.Format.retrieve_online(
                    url=config["Repository"]["link"], path=config["Repository"]["path"]
                )
            except Exception as e:
                status.text('Retrieving from offline repo')
                add_traceback(status, e)
                categen.data.Format.retrieve_local(config["Repository"]["path"])

            return categen.data.Format(config["Repository"])

    config = attempt(cfgini, cfginit)
    if config is None:  # Failed, cannot continue.
        print_tracebacks()
        exit()

    repo = attempt(rpoini, rpoinit, rpoini, config)
    if repo is None:  # Failed, cannot continue.
        print_tracebacks()
        exit()

    # Meta Check
    def meta():
        return {
            "text": f"Current: {categen.data.Format.current_ver()}, "
            f"Latest: {categen.data.Format.latest_ver(config['Repository']['latest_placements'])}",
        }

    attempt(rpomta, meta)

    # Backup
    backup_status = attempt(rpobak, repo.backup, ret=False)

    # Pull
    attempt(rpopll, repo.pull)

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

    attempt(rpocln, clone, repo, backup_status)

    if len(tracebacks) >= 1:
        print_tracebacks()


if __name__ == "__main__":
    main()

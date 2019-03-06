import configparser
import getpass
import os
import shutil
import sys
from typing import Dict, List

import click
import texttable

from .www import WWW, WWWError


@click.group()
@click.option("--config-file", "-c", default="~/.pklookup.ini")
@click.pass_context
def cli(ctx: click.Context, config_file: str) -> None:
    config = configparser.ConfigParser()
    config.read(os.path.expanduser(config_file))

    url = config.get("pklookup", "url", fallback="").rstrip("/")
    if not url:
        sys.stderr.write("ERROR: no 'url' in {}\n".format(config_file))
        sys.exit(1)
    url = "{}/api/v1".format(url)

    admin_token = config.get("pklookup", "admin_token", fallback="")
    if not admin_token:
        admin_token = getpass.getpass("Admin token: ")

    cafile = config.get("pklookup", "cafile", fallback="") or None

    known_hosts = os.path.expanduser(config.get("pklookup", "known_hosts",
                                                fallback="~/known_hosts"))

    ctx.obj = {
        "known_hosts": known_hosts,
        "www": WWW(url, token=admin_token, cafile=cafile)
    }


@cli.group()
def token() -> None:
    pass


@token.command("add")
@click.option("--description", "-d")
@click.option("--role", "-r", required=True, type=click.Choice([
    "admin",
    "server"
]))
@click.pass_obj
def token_add(options: Dict, role: str, description: str) -> None:
    try:
        res = options["www"].post("token", role=role, description=description)
        print("{} token: {token}".format(role, **res))
    except WWWError as e:
        sys.stderr.write("ERROR: {}\n".format(e))
        sys.exit(1)
    except (KeyError, TypeError):
        sys.stderr.write("ERROR: invalid response\n")
        sys.exit(1)


@token.command("delete")
@click.option("--id", "token_id", type=int, required=True)
@click.pass_obj
def token_delete(options: Dict, token_id: int) -> None:
    try:
        res = options["www"].delete("token", id=token_id)
        print("token: {message}".format(**res))
    except WWWError as e:
        sys.stderr.write("ERROR: {}\n".format(e))
        sys.exit(1)
    except (KeyError, TypeError):
        sys.stderr.write("ERROR: invalid response\n")
        sys.exit(1)


@token.command("list")
@click.pass_obj
def token_list(options: Dict) -> None:
    try:
        res = options["www"].get("token")
        tabulate(["id", "role", "description", "created"], res["tokens"])
    except WWWError as e:
        sys.stderr.write("ERROR: {}\n".format(e))
        sys.exit(1)
    except (KeyError, TypeError):
        sys.stderr.write("ERROR: invalid token list\n")
        sys.exit(1)


@cli.group()
def server() -> None:
    pass


@server.command("add")
@click.option("--public-key", required=True)
@click.pass_obj
def server_add(options: Dict, public_key: str) -> None:
    if public_key.startswith("@"):
        try:
            with open(public_key[1:], "r") as f:
                public_key = f.readline().strip()
        except IOError as e:
            sys.stderr.write("ERROR: {}\n".format(e))
            sys.exit(1)

    try:
        res = options["www"].post("server", public_key=public_key)
        print("server: {message}".format(**res))
    except WWWError as e:
        sys.stderr.write("ERROR: {}\n".format(e))
        sys.exit(1)
    except (KeyError, TypeError):
        sys.stderr.write("ERROR: invalid response\n")
        sys.exit(1)


@server.command("list")
@click.pass_obj
def server_list(options: Dict) -> None:
    try:
        res = options["www"].get("server")
        headers = [
            "id",
            "token_id",
            "ip",
            "port",
            "key_type",
            "key_data",
            "key_comment",
            "created"]
        tabulate(headers, res["servers"])
    except WWWError as e:
        sys.stderr.write("ERROR: {}\n".format(e))
        sys.exit(1)
    except (KeyError, TypeError):
        sys.stderr.write("ERROR: invalid server list\n")
        sys.exit(1)


@server.command("save-key")
@click.option("--id", "server_id", type=int, required=True)
@click.pass_obj
def server_save_key(options: Dict, server_id: int) -> None:
    try:
        res = options["www"].get("server", id=server_id)
        entry = "{ip} {key_type} {key_data}".format(**res["servers"][0])
    except WWWError as e:
        sys.stderr.write("ERROR: {}\n".format(e))
        sys.exit(1)
    except IndexError:
        sys.stderr.write("ERROR: invalid server id\n")
        sys.exit(1)
    except (KeyError, TypeError):
        sys.stderr.write("ERROR: invalid server list\n")
        sys.exit(1)

    print("{known_hosts}: saving '{}'".format(entry, **options))
    with open(options["known_hosts"], "a") as f:
        f.write("{}\n".format(entry))


def tabulate(header: List[str], rows: List[Dict[str, str]]) -> None:
    """
    Print rows as a table with the given headers.
    """
    size = shutil.get_terminal_size()  # type: ignore
    table = texttable.Texttable(max_width=size.columns)
    table.header(header)
    for row in rows:
        table.add_row([row[key] for key in header])
    print(table.draw())

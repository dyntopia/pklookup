import configparser
import getpass
import os
import sys
from typing import Dict, List

import click
import texttable

from . import www


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

    admin_token = config.get("pklookup", "admin_token", fallback="")
    if not admin_token:
        admin_token = getpass.getpass("Admin token: ")

    ctx.obj = {"admin_token": admin_token, "url": "{}/api/v1".format(url)}


@cli.command("add-token")
@click.option("--description", "-d")
@click.option("--role", "-r", required=True, type=click.Choice([
    "admin",
    "server"
]))
@click.pass_obj
def add_token(options: Dict[str, str], role: str, description: str) -> None:
    url = "{url}/token".format(**options)
    admin_token = options["admin_token"]

    try:
        res = www.post(url, admin_token, role=role, description=description)
        print("{} token: {token}".format(role, **res))
    except www.WWWError as e:
        sys.stderr.write("ERROR: {}\n".format(e))
        sys.exit(1)
    except (KeyError, TypeError):
        sys.stderr.write("ERROR: invalid response\n")
        sys.exit(1)


@cli.command("list-tokens")
@click.pass_obj
def list_tokens(options: Dict[str, str]) -> None:
    url = "{url}/token".format(**options)
    admin_token = options["admin_token"]

    try:
        res = www.get(url, admin_token)
        tabulate(["id", "role", "description", "created"], res["tokens"])
    except www.WWWError as e:
        sys.stderr.write("ERROR: {}\n".format(e))
        sys.exit(1)
    except (KeyError, TypeError):
        sys.stderr.write("ERROR: invalid token list\n")
        sys.exit(1)


@cli.command("add-server")
@click.option("--public-key", required=True)
@click.pass_obj
def add_server(options: Dict[str, str], public_key: str) -> None:
    url = "{url}/server".format(**options)
    admin_token = options["admin_token"]

    if public_key.startswith("@"):
        try:
            with open(public_key[1:], "r") as f:
                public_key = f.readline().strip()
        except IOError as e:
            sys.stderr.write("ERROR: {}\n".format(e))
            sys.exit(1)

    try:
        res = www.post(url, admin_token, public_key=public_key)
        print("server: {message}".format(**res))
    except www.WWWError as e:
        sys.stderr.write("ERROR: {}\n".format(e))
        sys.exit(1)
    except (KeyError, TypeError):
        sys.stderr.write("ERROR: invalid response\n")
        sys.exit(1)


@cli.command("list-servers")
@click.pass_obj
def list_servers(options: Dict[str, str]) -> None:
    url = "{url}/server".format(**options)
    admin_token = options["admin_token"]

    try:
        res = www.get(url, admin_token)
        headers = [
            "id",
            "token_id",
            "ip",
            "port",
            "key_type",
            "public_key",
            "created"]
        tabulate(headers, res["servers"])
    except www.WWWError as e:
        sys.stderr.write("ERROR: {}\n".format(e))
        sys.exit(1)
    except (KeyError, TypeError):
        sys.stderr.write("ERROR: invalid server list\n")
        sys.exit(1)


def tabulate(header: List[str], rows: List[Dict[str, str]]) -> None:
    """
    Print rows as a table with the given headers.
    """
    table = texttable.Texttable()
    table.set_deco(table.HEADER | table.VLINES)
    table.header(header)
    for row in rows:
        table.add_row([row[key] for key in header])
    print(table.draw())

import configparser
import getpass
import os
import sys
from typing import Dict

import click

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
    except www.WWWError as e:
        sys.stderr.write("ERROR: {}\n".format(e))
        sys.exit(1)

    print("{} token: {token}".format(role, **res))

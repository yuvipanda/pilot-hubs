#!/usr/bin/env python3
"""
Simple utility to decrypt secrets sent to `support@2i2c.org` via `age`
"""
import pathlib
import subprocess
import sys

import typer

from .cli_app import app
from .file_acquisition import get_decrypted_file

DEFAULT_KEY_PATH = pathlib.Path(__file__).parent.parent.joinpath(
    "config/secrets/enc-age-private.secret.key.json"
)


@app.command()
def decrypt_age(
    encrypted_file: str = typer.Argument(
        None,
        help="Path to age-encrypted file sent by user. Leave empty to read from stdin",
    ),
    key_path: str = typer.Option(
        DEFAULT_KEY_PATH,
        help="Path to sops encrypted age private key to be used to decrypt",
    ),
):

    if not encrypted_file:
        # No file specified
        print("Paste the encrypted file contents, hit enter and then press Ctrl+D")
        encrypted_contents = sys.stdin.read().encode()
    else:
        # rb so it doesn't try to decode to utf-8, in case we have a non-armored file
        with open(encrypted_file, "rb") as f:
            encrypted_contents = f.read()

    with get_decrypted_file(key_path) as decrypted_age_key:
        cmd = ["age", "--decrypt", "--identity", decrypted_age_key]

        subprocess.run(cmd, input=encrypted_contents, check=True)

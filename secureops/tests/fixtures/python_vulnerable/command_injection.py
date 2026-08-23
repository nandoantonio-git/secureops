"""Vulnerable Python fixture: untrusted input reaches a shell command."""

import subprocess


def resize_image(image_path: str, output_path: str):
    command = f"convert {image_path} -resize 200x200 {output_path}"
    return subprocess.run(command, shell=True, check=True)

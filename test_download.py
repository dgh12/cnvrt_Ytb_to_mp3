"""import and test the download function for downloading a video."""

import os
import subprocess
import asyncio
import shutil
from pathlib import Path
import pytest
from convert import download_url, validate_file_path, validate_url


@pytest.mark.asyncio
async def download(test_path):
    """manages the download process to simplify the run function
      and handle any errors that occur during the download process."""
    _url = "https://www.youtube.com/shorts/jWgaqwczsPk"
    _dwnload_playlist = False
    file_type = "mp3"
    file_path = test_path
    verbose = "v"
    is_valid = []

    is_valid.append(validate_file_path(file_path))
    value, title, urls, dwnload_playlist = \
        validate_url(_url, not _dwnload_playlist, verbose)
    is_valid.append(value)

    if False not in is_valid:
        kwargs = {
            "verbose": verbose,
            "file_type": file_type,
            "is_playlist": not dwnload_playlist,
            "title": title,
            "file_path": file_path,
        }
        success = download_url(urls, kwargs)
        if not success:
            return False, None
    else:
        return False, None
    return True, title


@pytest.mark.asyncio
async def test_download():
    """run test"""
    os.mkdir(f"{Path.home()}/test")
    os.chdir(os.path.abspath(f"{Path.home()}/test"))
    print(os.getcwd())
    exists = ""
    _download = asyncio.create_task(download("/test"))
    downloaded, title = await _download

    try:
        subprocess.run(["ffplay", f"'{title}.mp3'"], check=True)
        exists = True
    except subprocess.CalledProcessError:
        exists = False
    shutil.rmtree(f"{Path.home()}/test")
    assert downloaded and exists

"""import and test the download function for downloading a video."""

import os
import asyncio
import shutil
from pathlib import Path
import pytest
from convert import download_url, validate_user_input

@pytest.mark.asyncio
async def download(test_path):
    """manages the download process to simplify the run function
      and handle any errors that occur during the download process."""
    _url = "https://www.youtube.com/shorts/jWgaqwczsPk"
    _dwnload_playlist = False
    file_type = "mp3"
    file_path = test_path
    verbose = "v"

    _success, title, urls, dwnload_playlist = \
    validate_user_input(_url, _dwnload_playlist, file_type, file_path, verbose)
    if not _success:
        return False, None
    kwargs = {
        "is_playlist": not dwnload_playlist,
        "file_type": file_type,
        "file_path": file_path,
        "title": title,
        "verbose": verbose
    }
    success = download_url(urls, kwargs)
    if not success:
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
        os.system(f"ffplay '{title}.mp3")
        exists =  True
    except FileExistsError:
        exists = False
    shutil.rmtree(f"{Path.home()}/test")
    assert downloaded and exists

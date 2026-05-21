"""This program allows the user to download YouTube videos as audio files in a
 specified file type and file path.The program uses the yt_dlp library to
 download the audio from the YouTube video and convert it to the specified file
 type.The program also keeps a log of the downloads, including the title of the
 video, the time of the download, and any errors that occur during the download
 process. The log is stored in a CSV file (music_download_log.csv) and keeps
 the most recent 20 entries."""

import csv
import io
import os
from os.path import abspath
import datetime
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
import sys
from unidecode import unidecode
from yt_dlp.utils import ExtractorError, DownloadError
import yt_dlp
from custom_error import UrlError, InvalidFileTypeError


def run():
    """main function to run the program. It will get the user input,
      download the YouTube video as an audio file,
    and handle any errors that occur during the download process."""
    display_header()
    display_menu()
    try:
        while True:
            command = input(
                "\nenter command or type 'h' for the list of commands\n>>")
            if command == "1":
                if not manage_download():
                    continue
            elif command == "2":
                if authenticate():
                    rows = read_log()
                    for val in rows.values():
                        print(val)

            elif command == "3":
                end_program()

            elif command == "h":
                display_menu()

            else:
                print("Invalid command. Please try again.")
    except KeyboardInterrupt:
        print("\n")
        end_program()


def display_header():
    """displays the header for the program."""
    print("The YouTube Video Downloader Program\n")


def display_menu():
    """displays the menu for the program."""
    print("Commands:")
    print("Begin download   --------- enter '1'")
    print("view the download log  --- enter '2'")
    print("exit the program   ------- enter '3'")


def manage_download():
    """manages the download process to simplify the run function
      and handle any errors that occur during the download process."""
    dwnload_playlist, file_type, file_path, title, urls, verbose = \
        get_user_input()
    titles = []
    for url in urls:
        titles.append(url["title"])
    print("Downloading...")
    kwargs = {
        "is_playlist": not dwnload_playlist,
        "file_type": file_type,
        "file_path": file_path,
        "title": title,
        "verbose": verbose
    }
    if not verbose:
        print("This may take a few minuites.")
    success = download_url(urls, kwargs)
    if success:
        print("Download successful!")
        if dwnload_playlist:
            handle_merge(title, titles, file_type, file_path)
    else:
        print("Download failed. Please check the log for more details.")
        return False
    return True


def handle_merge(title, titles, file_type, file_path):
    """handles the merging of files if the user downloaded a playlist."""
    error = ""
    while True:
        merge = input(
            "You downloaded a playlist." +
            " Do you want to merge the files into one file? [Y/n]: ") or "y"
        if merge.lower() in ["y", "n"]:
            if merge.lower() == "y":
                merge_filename = input(
                    "What is the name of the file to merge the files into? " +
                    f"(default: {title}): ") or title
                print("Merging files...")
                success, error = merge_files(merge_filename, titles,
                                             file_type, file_path)
                if success:
                    print("Files merged successfully!")
                else:
                    print(
                        "Failed to merge files. " +
                        "Please check the log for more details.")
                    write_log(title, str(datetime.datetime.now()), error)
            break
        print("Invalid input. Please enter 'y' or 'n.'")


def get_user_input():
    """get the user input for the YouTube URL, file type, and file path.
    The function will validate the input and return the values as a tuple. """
    file_path = ""
    file_type = ""
    title = ""
    download_as_playlist = ""
    urls = []
    vals = ["mp3", "wav", "flac", "acc", "ogg", "m4a", "opus"]
    dwnlod_playlist = bool()
    verbose = "n"
    input_valid = False
    # a while loop is used to repeatedly prompt
    # the user for input until valid input is provided.
    while not input_valid:
        try:
            url = ""
            file_type = ""
            file_path = ""
            is_playlist = ""
            while url == "":
                url = str(input("Enter the YouTube URL: "))
            while is_playlist not in ["y", "n"]:
                is_playlist = (str(input(
                    "Download as playlist? [y/N] : ")) or "n").lower()
            while file_type not in vals:
                file_type = str(input("Enter the file type\n" +
                                      "accepted formats: mp3, wav, " +
                                      "flac, aac, ogg, m4a, or opus " +
                                      "(default: mp3): ")) or "mp3"
            while file_path == "":
                file_path = str(input("Enter the file path: "))
            useript = input("\nTo return to the main menu enter '2.'\
                             \nTo reenter the input enter '1.'\
                             \nPress enter to continue to download\n>>")
            if useript == "1":
                continue
            if useript == "2":
                return None, None, None, None, [], None
            print("Continuing with the download process...")
            if file_path[0] != "/":
                file_path = f"/{file_path}"
            dwnlod_playlist = bool(is_playlist.lower() == "y")
            while verbose not in ["v", ""]:
                verbose = input("Press 'v' for a verbose output or " +
                                "press enter to continue\n>> ")
            # input is validated separately to simplify the error handling
            # and provide more specific error messages to the user.
            success, title, urls, download_as_playlist = validate_user_input(
                url, dwnlod_playlist, file_type, file_path, verbose)
            if success:
                input_valid = True
        except (ValueError, FileNotFoundError) as error:
            if isinstance(error, ValueError):
                print("Invalid input type. Please enter valid values.")
            print("File not found. Please enter valid file path.")
    return download_as_playlist, file_type, file_path, title, urls, verbose


def validate_user_input(url, dwnload_playlist, file_type, file_path, verbose):
    """validates the user input for the YouTube URL,
      file type, and file path."""
    print("Validating input...\n")
    title = ""
    try:
        os.chdir(abspath(f"{Path.home()}{file_path}"))
        os.chdir(os.path.dirname(abspath(__file__)))

        if file_type not in ["mp3", "wav", "flac",
                             "aac", "ogg", "m4a", "opus"]:
            raise InvalidFileTypeError("Invalid file type.")
        print("input valid\n")
        print("Validating url...\n")
        success, title, urls, download_as_playlist =\
            validate_url(url, not dwnload_playlist, verbose)
        if success:
            return True, title, urls, download_as_playlist

    except (FileNotFoundError, UrlError,
            InvalidFileTypeError, ExtractorError, DownloadError) as error:
        if isinstance(error, FileNotFoundError):
            print("File not found. Please enter valid file path.")
        elif isinstance(error, UrlError):
            print("Invalid URL provided. Please enter a valid URL.")
        elif isinstance(error, InvalidFileTypeError):
            print("Invalid file type. Please enter a valid file type.")
        elif isinstance(error, DownloadError):
            print(str(error))
        else:
            print(f"An unexpected error occurred: {error}")
    return False, None, [], None


def validate_url(url, is_not_playlist, verbose):
    """validates the YouTube URL by trying to extract the information from the
       URL using yt_dlp."""
    title = ""
    urls = []
    try:
        if url:
            if verbose != "v":
                print("This may take a moment...\n")
                with io.StringIO() as buf, \
                        redirect_stderr(buf), redirect_stdout(buf):
                    with yt_dlp.YoutubeDL({"noplaylist":
                                           is_not_playlist}) as ydl:
                        info = ydl.extract_info(url, download=False)
                        title = info.get("title", None) or ""
                        titles_array = info.get("entries", [])
            else:
                with yt_dlp.YoutubeDL({"noplaylist": is_not_playlist}) as ydl:
                    info = ydl.extract_info(url, download=False)
                    title = info.get("title", None) or ""
                    titles_array = info.get("entries", [])
            if len(titles_array) > 0:
                dwnload_as_playlist = True
                for entry in titles_array:
                    _title = entry["title"]
                    __title = make_ascii_compatable(_title)
                    urls.append({"url": entry["original_url"],
                                 "title": __title})
            else:
                dwnload_as_playlist = False
                _title = title
                __title = make_ascii_compatable(_title)
                urls.append({"url": info.get("original_url"),
                             "title": __title})
            print("url check successful!\n")
            return True, title, urls, dwnload_as_playlist
        raise UrlError("No URL provided.")
    except (UrlError, ExtractorError, DownloadError) as error:
        if isinstance(error, UrlError):
            print("Invalid URL provided. Please enter a valid URL.")
        elif isinstance(error, DownloadError):
            print(str(error))
        else:
            print(f"An unexpected error occurred: \
                  \n {type(error).__name__}: {error}")
    return False, None, [], None


def authenticate():
    """authenticates if the user can view the logs by asking for a password."""
    password = input("Enter the password to view the logs: ")
    if password == "password":
        return True
    print("Incorrect password. Access denied.")
    return False


def end_program():
    """ends the program and prints a message to the user."""
    print("Ending Music Downloading Program")
    sys.exit()


def write_log(title, time, error="None"):
    """writes the log file with the title, time, and error if there is one.
      The log file will keep the most recent 20 entries."""
    try:
        rows = read_log()
    except FileNotFoundError:
        rows = {}
    rows[time] = {"Time": time, "Title": title, "Error": error}
    while len(rows) > 20:
        rows.pop((min(rows)))
    with open("music_download_log.csv", "w",
              newline="", encoding="utf-8") as log_file:
        writer = csv.DictWriter(log_file, fieldnames=["Time",
                                                      "Title", "Error"])
        writer.writeheader()
        for val in rows.values():
            writer.writerow(val)


def read_log():
    """reads the log file"""
    os.chdir(os.path.dirname(abspath(__file__)))
    rows = {}
    with open("music_download_log.csv", "r", encoding="utf-8") as log_file:
        reader = csv.DictReader(log_file)
        for row in reader:
            rows[row["Time"]] = row
    return rows


def download_url(urls, kwargs):
    """Implementation for downloading YouTube video as audio file using yt_dlp
  This function takes the URL and the user input as an argument dictionary"""
    title = kwargs["title"]
    to_download = []
    exists = []
    path_to_deno = abspath(".local/bin/deno")
    set_time = str(datetime.datetime.now())
    file_path = os.path.dirname(abspath(__file__))
    os.chdir(abspath(f"{Path.home()}{kwargs['file_path']}"))
    for url in urls:
        print(url["title"])
        if os.path.exists(f"{Path.home()}{kwargs['file_path']}/" +
                          f"{url['title']}.{kwargs['file_type']}"):
            print("File already exists. Skipping download.\n")
            exists.append(True)
        else:
            print("File not found. We will download it.\n")
            exists.append(False)
            to_download.append({"url": url["url"], "title": url["title"]})
    if False not in exists and len(exists) > 0:
        print("All files already exist. Skipping download.")
        os.chdir(file_path)
        return True
    print()
    # set the options for yt_dlp
    try:
        for url in to_download:
            ydl_otps = {
                "format": "bestaudio/best",
                "postprocessors": [{
                    "key": "FFmpegExtractAudio",
                    "preferredcodec": kwargs["file_type"],
                    "preferredquality": "320",
                }],
                "noplaylist": kwargs["is_playlist"],
                "js-runtimes": {"deno": {"path": path_to_deno}},
                "outtmpl": f"{url['title']}.%(ext)s",
                "quiet": False,
                "display-progress": True,

            }
            if kwargs["verbose"] != "v":
                with io.StringIO() as buf, \
                        redirect_stderr(buf), redirect_stdout(buf):
                    with yt_dlp.YoutubeDL(ydl_otps) as ydl:
                        ydl.download([url["url"]])
            else:
                with yt_dlp.YoutubeDL(ydl_otps) as ydl:
                    ydl.download([url["url"]])
        write_log(title, set_time)
    except (DownloadError, ExtractorError) as error:
        write_log(title, set_time, str(error))
        os.chdir(file_path)
        return False
    os.chdir(file_path)
    return True


def merge_files(merge_filename, titles, filetype, file_path):
    """merges the playlist files downloaded into one file."""
    remove = ""
    while remove not in ["y", "n"]:
        remove = (input("Do you want to remove the individual playlist files" +
                        "[Y/n] : ") or "n").lower()
    try:
        for title in titles:
            print(f"{title}.{filetype}")

        os.chdir(abspath(f"{Path.home()}{file_path}"))

        if os.path.exists(f"{merge_filename}.{filetype}"):
            print(f"File {merge_filename}.{filetype} already exists. " +
                  "Skipping merge.")
            if remove:
                for title in titles:
                    os.remove(f"{title}.{filetype}")
            return True, ""

        with open("merge.txt", "w", encoding="utf-8") as f:
            for title in titles:
                f.write(f"file '{title}.{filetype}'\n")

        os.system("ffmpeg -f concat -safe 0 -i merge.txt -c copy " +
                  f"'{merge_filename}.{filetype}'")
        os.remove("merge.txt")

        if remove == "y":
            for title in titles:
                os.remove(f"{title}.{filetype}")

        return True, ""
    except (FileNotFoundError, FileExistsError) as error:
        return False, str(error)


def make_ascii_compatable(_title):
    "this function makes the title returned ascii compatable"
    os.chdir(abspath(f"{Path.home()}/Music/"))
    chardict = {"-": "*"}
    title = ''
    for nascii, iascii in chardict.items():
        title = _title.replace(nascii, iascii)
    return unidecode(title, errors="strict")


if __name__ == "__main__":
    run()

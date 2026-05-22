"""This program allows the user to download YouTube videos as audio files in a
 specified file type and file path.The program uses the yt_dlp library to
 download the audio from the YouTube video and convert it to the specified file
 type.The program also keeps a log of the downloads, including the title of the
 video, the time of the download, and any errors that occur during the download
 process. The log is stored in a CSV file (music_download_log.csv) and keeps
 the most recent 20 entries."""

# most of these modules are imported for utitlty reasons.
# the only modules that are needed for the functionallity are CSV, yt-dlp, and
# custom_error
# the other modules help with adding the file to the right place and with the
# CLI  type UI
import csv
import io
import os
import shutil
import subprocess
from os.path import abspath
import datetime
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
import sys
from unidecode import unidecode
from yt_dlp.utils import ExtractorError, DownloadError
from yt_dlp import YoutubeDL


# function that runs and coordinates the access to the logging and downloading
# functions; it also terminates the program gracefully.
def run():
    """main function to run the program. It will get the user input,
      download the YouTube video as an audio file,
    and handle any errors that occur during the download process."""
    # these two functions display the header and the menu so the user knows
    #  what to do
    display_header()
    display_menu()
    # the try block is to end the program gracefully if the user gets tired
    # waiting and types Ctrl C
    try:
        # the program always si waiting for the user input after the
        # first task is done.
        while True:
            # command is the variable that holds the command entered
            # by the user
            command = input(
                "\nenter command or type 'h' for the list of commands\n>>")
            # command 1 begins the download process
            if command == "1":
                # the user continually is asked for a new URL unless there is
                # an error
                if not manage_download():
                    continue
            # command 2 opens the log file
            elif command == "2":
                rows = read_log()
                for val in rows.values():
                    print(val)
            # command 3 ends the program
            elif command == "3":
                end_program()
            # h displays the menu again if the user forgot it
            elif command == "h":
                display_menu()
            # if the command is not valid the user is told so
            else:
                print("Invalid command. Please try again.")
    # the KeyboardInterrupt is when the user forces the program to end
    except KeyboardInterrupt:
        print("\n")
        end_program()


# function that displays the header
def display_header():
    """displays the header for the program."""
    print("The YouTube Video Downloader Program\n")


# function that displays the menu for the program
def display_menu():
    """displays the menu for the program."""
    print("Commands:")
    print("Begin download   --------- enter '1'")
    print("view the download log  --- enter '2'")
    print("exit the program   ------- enter '3'")


# function that manages the download process by
# routing the data to the right function.
def manage_download():
    """manages the download process to simplify the run function
      and handle any errors that occur during the download process."""
    # the user's input is returned validated already.
    dwnload_playlist, file_type, file_path, title, urls, verbose = \
        get_user_input()
    titles = []
    # if the user decided to return to the main menu return True
    if not urls:
        return True
    # if the user downloads a playlist the titles are send in a dict with the
    # url they are separated so they can be sent to the merge function.
    for url in urls:
        titles.append(url["title"])
    print("Downloading...")
    # arguments for the download function are sent in as a dictionary to
    # decrease the number of variables
    kwargs = {
        "is_playlist": not dwnload_playlist,
        "file_type": file_type,
        "file_path": file_path,
        "title": title,
        "verbose": verbose
    }
    # if the output is not verbose the user is told he will have to wait
    if not verbose:
        print("This may take a few minuites.")
    success = download_url(urls, kwargs)
    # if the url downloaded successfully the user is told so
    if success:
        print("Download successful!")
        # if the user downloaded a playlist the playlist may be merged
        if dwnload_playlist:
            handle_merge(title, titles, file_type, file_path)
    # if the download failed the user is told and the function returns false.
    else:
        print("Download failed. Please check the log for more details.")
        return False
    # if there was no problem the function returns true
    return True


# function that handles the merge process for if the
# user wants to merge the files of a playlist
def handle_merge(title, titles, file_type, file_path):
    """handles the merging of files if the user downloaded a playlist.
       and handles any errors found during the merge process."""
    error = ""
    merge = ""
    # the user is prompted to see if they want to merge the playlist as one
    # file
    while True:
        merge = input(
            "You downloaded a playlist. " +
            "Do you want to merge the files into one file? [Y/n]: ") or "y"
        # if the input is valid the function continues.
        if merge.lower() in ["y", "n"]:
            break
        print("Invalid input. Please enter 'y' or 'n.'")
    # if the user wants to merge the files...
    if merge.lower() == "y":
        # title of the playlist is set as the default merge name
        merge_filename = input(
            "What is the name of the file to merge the files into? " +
            f"(default: {title}): ") or title
        print("Merging files...")
        # the files are merged
        error = merge_files(merge_filename, titles,
                            file_type, file_path)
        # if the files are merged successfully tell the user
        if len(error) < 0:
            print("Files merged successfully!")
        # else tell the user there was an error and write the error to the
        # log
        else:
            print(
                "Failed to merge files. " +
                "Please check the log for more details.")
            write_log(title, str(datetime.datetime.now()), error)


# function that gets the users input for the download process
def get_user_input():
    """get the user input for the YouTube URL, file type, and file path.
    The function will validate the input and return the values as a tuple. """
    # initiate the user input variables as empty
    file_path = ""
    file_type = ""
    title = ""
    download_as_playlist = ""
    urls = []
    vals = ["mp3", "wav", "flac", "aac", "ogg", "m4a", "opus"]
    dwnlod_playlist = bool()
    verbose = "n"
    input_valid = False
    # a while loop is used to repeatedly prompt
    # the user for input until valid input is provided.
    while not input_valid:
        # if the user enters the wrong type of value or no file path
        # there is an error, this handles it
        try:
            # each iteration of the while loop sets the values to
            # blank variables to get all of the input again
            url = ""
            file_type = ""
            file_path = ""
            is_playlist = ""
            is_valid = []
            # if the url is empty prompt for it again...
            while url == "":
                url = str(input("Enter the YouTube URL: "))
            # if the value for playlist is wrong prompt for it again...
            while is_playlist not in ["y", "n"]:
                is_playlist = (str(input(
                    "Download as playlist? [y/N] : ")) or "n").lower()
            # fi the file type is not right prompt for it again...
            while file_type not in vals:
                file_type = str(input("Enter the file type\n" +
                                      "accepted formats: mp3, wav, " +
                                      "flac, aac, ogg, m4a, or opus " +
                                      "(default: mp3): ")) or "mp3"
            # if the file path is empty prompt for it again...
            while file_path == "":
                file_path = str(input("Enter the file path: "))
            useript = input("\nTo return to the main menu enter '2.'\
                             \nTo reenter the input enter '1.'\
                             \nPress enter to continue to download\n>>")
            # if the user wants to reenter the input re-start the process
            if useript == "1":
                continue
            # if the user wants to return to the main menu returm empty values
            if useript == "2":
                return None, None, None, None, [], None
            print("Continuing with the download process...")
            # if the path does not begin with a slash add one
            if file_path[0] != "/":
                file_path = f"/{file_path}"
            # set dwnlod_playlist to true or false depending on if it
            # equals "y" on not
            dwnlod_playlist = bool(is_playlist.lower() == "y")
            # while verbose is not valid ask for it again.
            while verbose not in ["v", ""]:
                verbose = input("Press 'v' for a verbose output or " +
                                "press enter to continue\n>> ")
            # file path is validated sepatately
            is_valid.append(validate_file_path(file_path))
            # url is validated separately
            value, title, urls, download_as_playlist = \
                validate_url(url, not dwnlod_playlist, verbose)
            is_valid.append(value)
            # verify input is valid
            if False not in is_valid:
                break
            print("Input is not valid.")
        # ValueError is raised when the input is the wrong type.
        except ValueError:
            print("Invalid input type. Please enter valid values.")
    # after the user input is collected and validated return it
    return download_as_playlist, file_type, file_path, title, urls, verbose


# function that validates the input from the user.
# Note: the URL is validated separately because of complexity.
def validate_file_path(file_path):
    """validates the user input for the YouTube URL,
      file type, and file path."""
    # if the file is not found an error is raised
    try:
        # first the program verifies that the file path exists
        os.chdir(abspath(f"{Path.home()}{file_path}"))
        os.chdir(os.path.dirname(abspath(__file__)))
        return True
    except FileNotFoundError as error:
        if isinstance(error, FileNotFoundError):
            print("File not found. Please enter valid file path.")
    return False


# function that tries to get the url
# and check its contents to make sure it works
def validate_url(url, is_not_playlist, verbose):
    """validates the YouTube URL by trying to extract the information from the
       URL using yt_dlp."""
    title = ""
    urls = []
    print("Validating url...\n")
    # if the URL is not valid several errors are raised
    try:
        # if the user does not  perfer verbose output...
        if verbose != "v":
            print("This may take a moment...\n")
            # then extract the url silently
            with io.StringIO() as buf, \
                    redirect_stderr(buf), redirect_stdout(buf):
                with YoutubeDL({"noplaylist":
                                is_not_playlist}) as ydl:
                    info = ydl.extract_info(url, download=False)
                    title = info.get("title", None) or ""
                    titles_array = info.get("entries", [])
        # otherwise...
        else:
            # extract the url verbosly
            with YoutubeDL({"noplaylist": is_not_playlist}) as ydl:
                info = ydl.extract_info(url, download=False)
                title = info.get("title", None) or ""
                titles_array = info.get("entries", [])
        # if the user downloaded a playlist (the entries array is not empty)...
        if len(titles_array) > 0:
            # set download_as_playlist to true
            dwnload_as_playlist = True
            # for each entry in the titles_array..
            for entry in titles_array:
                # the title is extracted and made ascii compatable...
                _title = make_ascii_compatable(entry["title"])
                # and then added to the urls array
                urls.append({"url": entry["original_url"],
                             "title": _title})
        # otherwise...
        else:
            # set dwnload_as_playlist to true
            dwnload_as_playlist = False
            # the title is made ascii compatable...
            _title = make_ascii_compatable(title)
            # and then added to the urls array
            urls.append({"url": info.get("original_url"),
                         "title": _title})
        print("url check successful!\n")
        # True is returned because the url was added successfully,
        # the title and the urls that were extracted are returned so as
        # to not extract them twice, and dwnnload_as_playlist
        return True, title, urls, dwnload_as_playlist
    # ExtractorError DownloadError are raised if the url does not exist.
    except (ExtractorError, DownloadError) as error:
        # if the error is DownloadError...
        if isinstance(error, DownloadError):
            # print it
            print(str(error))
        # otherwise...
        else:
            # the error is not expected
            print(f"An unexpected error occurred: \
                  \n {type(error).__name__}: {error}")
    # if the url is not valid return false
    return False, None, [], None


# gracefully ends program
def end_program():
    """ends the program and prints a message to the user."""
    print("Ending Music Downloading Program")
    sys.exit()


# writes to the log file
def write_log(title, time, error="None"):
    """writes the log file with the title, time, and error if there is one.
      The log file will keep the most recent 20 entries."""
    # read the log to rows
    rows = read_log()
    # add the logged content to the rows
    rows[time] = {"Time": time, "Title": title, "Error": error}
    # filter for the 40 most recent rows
    while len(rows) > 40:
        rows.pop((min(rows)))
    # open the log file to write to it
    with open("music_download_log.csv", "w",
              newline="", encoding="utf-8") as log_file:
        # write to the log file in csv format
        writer = csv.DictWriter(log_file, fieldnames=["Time",
                                                      "Title", "Error"])
        writer.writeheader()
        for val in rows.values():
            writer.writerow(val)


# reads the log file
def read_log():
    """reads the log file"""
    # set rows to empty
    rows = {}
    # try to open file...
    try:
        with open("music_download_log.csv", "r", encoding="utf-8") as log_file:
            reader = csv.DictReader(log_file)
            # if the file opens each row in the file is added to rows
            for row in reader:
                rows[row["Time"]] = row
    # unless the file is not found
    except FileNotFoundError:
        # then rows are set to empty
        rows = {}
    # rows is then returned
    return rows


# downloads the url and saves the file to the location provided
def download_url(urls, kwargs):
    """Implementation for downloading YouTube video as audio file using yt_dlp
  This function takes the URL and the user input as an argument dictionary"""
    # initialize the variables needed
    title = kwargs["title"]
    to_download = []
    exists = []
    path_to_deno = shutil.which("deno")
    set_time = str(datetime.datetime.now())
    file_path = os.path.dirname(abspath(__file__))
    # go through each url...
    for url in urls:
        # print its title...
        print(url["title"])
        # and verify if it exists
        if os.path.exists(f"{Path.home()}{kwargs['file_path']}/" +
                          f"{url['title']}.{kwargs['file_type']}"):
            print("File already exists. Skipping download.\n")
            # if the file exists add true to list "exists"
            exists.append(True)
        else:
            print("File not found. We will download it.\n")
            # other wise add false to list "exists"
            exists.append(False)
            # and add the url and title to list "to_download"
            to_download.append({"url": url["url"], "title": url["title"]})

    # check if all the files exist
    if False not in exists and len(exists) > 0:
        print("All files already exist. Skipping download.")
        # if they all exist change the working directory to the directory
        # of the current file and return true to indicate success
        os.chdir(file_path)
        return True

    # try to download the url...
    try:
        # for each url to download...
        for url in to_download:
            # initialize the yt_dlp options "dict"
            ydl_otps = {
                "format": "bestaudio/best",
                "postprocessors": [{
                    "key": "FFmpegExtractAudio",
                    "preferredcodec": (kwargs["file_type"] or "mp3"),
                    "preferredquality": "320",
                }],
                "noplaylist": True,
                "js-runtimes": {"deno": {"path": path_to_deno}},
                "outtmpl": f"{Path.home()}{kwargs['file_path']}" +
                           f"/{url['title']}.%(ext)s",
                "quiet": False,
                "display-progress": True,

            }
            # if the download is not set to verbose...
            if kwargs["verbose"] != "v":
                # download quietly
                with io.StringIO() as buf, \
                        redirect_stderr(buf), redirect_stdout(buf):
                    with YoutubeDL(ydl_otps) as ydl:
                        ydl.download([url["url"]])
            else:
                # otherwise download verbosly
                with YoutubeDL(ydl_otps) as ydl:
                    ydl.download([url["url"]])
        # if there are no errors
        # write to the log the title and the time downloaded
        write_log(title, set_time)
    # except if there are any errors...
    except (DownloadError, ExtractorError) as error:
        # if there are errors write them to the log and...
        write_log(title, set_time, str(error))
        # change the working directory to the directory of the current file
        # and return false to indicate failure
        os.chdir(file_path)
        return False
    # if the files downloaded successfully change the working directory
    # to the directory of the current file and return true to indicate success
    os.chdir(file_path)
    return True


# merges the files downloaded form a playlist to one single file.
def merge_files(merge_filename, titles, filetype, file_path):
    """merges the playlist files downloaded into one file."""
    remove = ""
    # ask the user if he wants to remove the individual files
    # and continue asking until he answers correctly
    while remove not in ["y", "n"]:
        remove = (input("Do you want to remove the individual playlist files" +
                        "[Y/n] : ") or "n").lower()
    # try to merge the files...
    try:
        # print each title in the playlist.
        for title in titles:
            print(f"{title}.{filetype}")
        # change working directory to the directory of the files
        os.chdir(abspath(f"{Path.home()}{file_path}"))

        # check if the merge file already exists...
        if os.path.exists(f"{merge_filename}.{filetype}"):
            # alert the user it does and...
            print(f"File {merge_filename}.{filetype} already exists. " +
                  "Skipping merge.")
            # if the user wants to remove the individual playlist files...
            if remove == "y":
                # remove each individual file and..
                for title in titles:
                    os.remove(f"{title}.{filetype}")
            # finish by changing the working directory
            # to the directory of the current file and...
            os.chdir(os.path.dirname(abspath(__file__)))
            # indicate success by returning no error
            return ""

        # otherwise open and write the titles to the merge.txt and...
        with open("merge.txt", "w", encoding="utf-8") as f:
            for title in titles:
                f.write(f"file '{title}.{filetype}'\n")

        # use ffmpeg to join the files and...
        subprocess.run(["ffmpeg", "-f", "concat", "-safe", "0", "-i",
                        "merge.txt", "-c", "copy",
                        f"'{merge_filename}.{filetype}'"],
                       check=True, cwd=f"{Path.home()}{file_path}",)
        # remove merge.txt
        os.remove("merge.txt")

        # if the user wants to remove the playlist files...
        if remove == "y":
            # remove each individual file
            for title in titles:
                os.remove(f"{title}.{filetype}")

        # indicate success by returning no error
        return ""
    # except if there is an error
    except (FileNotFoundError, FileExistsError) as error:

        # indicate failure by returning an error
        return str(error)


# some of the videos have titles that are not ASCII compatable
# this causes problems so they are converted to ASCII compatable characters.
def make_ascii_compatable(_title):
    """this function makes the title returned ascii compatable it
       takes the argument _title which is the title to be normalized"""

    # the character "-" is not supported by ffmpeg so it is replaced with "*"
    chardict = {"-": "*"}
    title = ''
    # the characters that are not accepted are changed
    # for the accepted versions of them
    for nascii, iascii in chardict.items():
        title = _title.replace(nascii, iascii)
    # unidecode then ends the filtering
    return unidecode(title, errors="strict")


if __name__ == "__main__":
    run()

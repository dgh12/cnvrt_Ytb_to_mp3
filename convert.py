"""This program allows the user to download YouTube videos as audio files in a specified file type and file path.
The program uses the yt_dlp library to download the audio from the YouTube video and convert it to the specified file type.
The program also keeps a log of the downloads, including the title of the video, the time of the download, and any errors
that occur during the download process. The log is stored in a CSV file (music_download_log.csv) and keeps the most recent 20 entries."""

import csv
import os
from os.path import abspath
import datetime
import io
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from tomlkit import key
import yt_dlp

def run():
    """main function to run the program. It will get the user input, download the YouTube video as an audio file,
    and handle any errors that occur during the download process."""
    display_header()
    display_menu()
    while True:
        command = input("\nenter command or type 'h' for the list of commands\n>>")
        if command == "1":
            url, fileType, filePath = get_user_input()
            if not url or not fileType or not filePath:
                continue
            print("Downloading...")
            success = download_url(url, fileType, filePath)
            if success:
                print("Download successful!")
            else:
                print("Download failed. Please check the log for more details.")
        elif command == "2":
            if authenticate():
                rows = read_log()
                for row in rows:
                    print("\n", rows[row])
        elif command == "3":
            end_program()
        elif command == "h":
            display_menu()
        else:
            print("Invalid command. Please try again.")
    
def display_header():
    """displays the header for the program."""
    print("The YouTube Video Downloader Program\n")
    
def display_menu():
    """displays the menu for the program."""
    print("Commands:")
    print("Begin download   --------- enter '1'")
    print("view the download log  --- enter '2'")
    print("exit the program   ------- enter '3'")

def get_user_input():
    """get the user input for the YouTube URL, file type, and file path. 
    The function will validate the input and return the values as a tuple. """
    url = ""
    fileType = ""
    filePath = ""
    input_valid = False
    #a while loop is used to repeatedly prompt the user for input until valid input is provided.
    while not input_valid:
        try:
            url = str(input("Enter the YouTube URL: "))
            fileType = str(input("Enter the file type \naccepted formats: mp3, wav, flac, aac, ogg, m4a, or opus (default: mp3): ")) or "mp3"
            filePath = str(input("Enter the file path: "))
            useript =  input("To continue enter '1.'\
                             \nTo reenter the input enter '2.'\
                             \nTo return to the main menu enter '3.'\n>>")
            if useript == "1":
                pass
            elif useript == "2":
                continue
            elif useript == "3":
                return None, None, None
            if filePath[0] != "/":
                filePath = f"/{filePath}"
        except ValueError:
            print("Invalid input. Please enter valid values.")
        if url and fileType and filePath:
            input_valid = True
    return url, fileType, filePath

def authenticate():
    """authenticates if the user can view the logs by asking for a password."""
    password = input("Enter the password to view the logs: ")
    if password == "password":
        return True
    else:
        print("Incorrect password. Access denied.")
        return False

def end_program():
    """ends the program and prints a message to the user."""
    print("Ending Music Downloading Program")
    exit()

def write_log(title, time, error = "None"):
    """writes the log file with the title, time, and error if there is one. The log file will keep the most recent 20 entries."""
    rows = read_log()
    rows[time] = {"Time": time, "Title": title, "Error": error}
    while len(rows) > 20:
        rows.pop((min(rows)))
    with open("music_download_log.csv", "w", newline="") as log_file:
        writer = csv.DictWriter(log_file, fieldnames=["Time", "Title", "Error"])
        writer.writeheader()
        for row in rows:
            writer.writerow(rows[row])
            

def read_log():
    """reads the log file"""
    os.chdir(os.path.dirname(abspath(__file__)))
    rows = {}
    with open("music_download_log.csv", "r") as log_file:
        reader = csv.DictReader(log_file)
        for row in reader:
            rows[row["Time"]] = row
    return rows

def download_url(url, fileType, filePath):
    """Implementation for downloading YouTube video as audio file using yt_dlp"""
    path_to_deno = abspath(".local/bin/deno")
    setTime = str(datetime.datetime.now())
    title = ""
    download_path = os.path.dirname(abspath(__file__))
    os.chdir(abspath(f"{Path.home()}{filePath}"))
    #set the options for yt_dlp
    ydl_otps = {
        "format": "bestaudio/best",
        "postprocessors": [{
            "key": "FFmpegExtractAudio",
            "preferredcodec": fileType,
            "preferredquality": "320",
        }],
        "js-runtimes": {"deno" : {"path": path_to_deno}},
        "outtmpl": f"%(title)s.%(ext)s",
        "download_archive": f"{download_path}/downloaded.txt",
        "quiet": False,
        "display-progress": True,

    }
    
    try:
        #run yt_dlp and suppress the output and error messages to avoid cluttering the console.
        #any errors that occur during the download process are logged.
        #    print variable "f" to view the output and error messages from yt_dlp for debugging purposes.
        f = io.StringIO()
        with redirect_stdout(f), redirect_stderr(f):
            with yt_dlp.YoutubeDL() as ydl:
                print("before creating file")
                title = ydl.extract_info(url, download=False).get("title",None)
                print("after creating file")
            with yt_dlp.YoutubeDL(ydl_otps) as ydl:
                ydl.download([url])
                write_log(title, setTime)
#        print(f.getvalue())
        
    except Exception as e:
        write_log(title, setTime, str(e))
        return False
    return True

run()

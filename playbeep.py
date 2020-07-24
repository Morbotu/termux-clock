import subprocess


def playbeep():
    subprocess.call(["termux-media-player", "play", "/data/data/com.termux/files/home/intervalTimer/sounds/beep-09.mp3"],
                    stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT)

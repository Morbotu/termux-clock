from playbeep import playbeep
import subprocess
import sys
from art import text2art
from datetime import datetime, timedelta
import time
import json
import os


def displayText(text, color):
    linesProcess = subprocess.Popen(
        "tput lines", stdout=subprocess.PIPE, shell=True)
    lines = int(linesProcess.stdout.read()[:-1])
    columnsProcess = subprocess.Popen(
        "tput cols", stdout=subprocess.PIPE, shell=True)
    columns = int(columnsProcess.stdout.read()[:-1])

    text = text2art(text).split("\n")
    del text[-1]

    output = []
    spaceAboveTime = int(lines/2) - int(len(text)/2)
    spaceUnderTime = spaceAboveTime
    if lines % 2 != 0:
        spaceUnderTime += 1
    for i in range(spaceAboveTime):
        output.append(" " * columns)

    for i in text:
        restSpace = " " * (int(columns/2) - int(len(i)/2))
        output.append(restSpace + i[:-1] + restSpace)

    for i in range(spaceUnderTime):
        output.append(" " * columns)

    output = "\n".join(output)
    if color == "green":
        return "\u001b[42;1m" + output + "\u001b[0m"
    if color == "red":
        return "\u001b[41;1m" + output + "\u001b[0m"
    if color == "yellow":
        return "\u001b[43;1m" + output + "\u001b[0m"
    if color == "black":
        return "\u001b[40;1m" + output + "\u001b[0m"


def timeToSeconds(normalTime):
    normalTime = normalTime.split(":")
    timeInMillis = 0
    timeInMillis += int(normalTime[0]) * 3600
    timeInMillis += int(normalTime[1]) * 60
    timeInMillis += int(normalTime[2])
    return timeInMillis


def timer():
    timerTime = subprocess.getoutput(
        "termux-dialog -t 'Select time' -i 'Format like h:m:s'")
    timerTime = timeToSeconds(json.loads(timerTime)["text"])
    endTime = round(time.time()) + timerTime

    while 1:
        time.sleep(0.1)
        timeLeft = endTime-round(time.time())
        if timeLeft > 5:
            color = "green"
        elif timeLeft <= 0:
            color = "red"
        else:
            color = "yellow"
        sys.stdout.write(
            "\u001b[1000D" + displayText(str(timedelta(seconds=timeLeft)), color))
        sys.stdout.flush()
        if color == "red":
            break
    alarm()


def alarm(showTime=False):
    turnOff = subprocess.Popen(
        "termux-dialog confirm -t 'Turn off' -i ''", stdout=subprocess.PIPE, shell=True)
    subprocess.call("termux-notification -t 'Alarm' --button1 'Stop alarm' --button1-action 'echo \"Pressed\" > /data/data/com.termux/files/home/intervalTimer/pressed.txt' --on-delete 'echo \"Pressed\" > /data/data/com.termux/files/home/intervalTimer/pressed.txt' -i 1204", shell=True)

    while 1:
        playbeep()
        if showTime:
            sys.stdout.write(
                "\u001b[1000D" + displayText(datetime.now().strftime("%H:%M:%S"), "black"))
            sys.stdout.flush()
        turnOff.poll()
        if turnOff.returncode != None:
            if json.loads(turnOff.stdout.read())["text"] == "yes":
                subprocess.call("termux-notification-remove 1204", shell=True)
                break
            else:
                turnOff = subprocess.Popen(
                    "termux-dialog confirm -t 'Turn off' -i ''", stdout=subprocess.PIPE, shell=True)
        try:
            with open("/data/data/com.termux/files/home/intervalTimer/pressed.txt", "r") as f:
                if f.read() == "Pressed\n":
                    subprocess.call(
                        "termux-notification-remove 1204", shell=True)
                    os.remove(
                        "/data/data/com.termux/files/home/intervalTimer/pressed.txt")
                    break
        except:
            pass


def alarmClock():
    alarmTime = subprocess.getoutput("termux-dialog time -t 'Alarm'")
    alarmTime = json.loads(alarmTime)["text"]
    while 1:
        time.sleep(0.1)
        sys.stdout.write(
            "\u001b[1000D" + displayText(datetime.now().strftime("%H:%M:%S"), "black"))
        sys.stdout.flush()
        if datetime.now().strftime("%H:%M") == alarmTime:
            break
    alarm(True)


subprocess.call("clear")
option = subprocess.getoutput("termux-dialog radio -v 'Timer,Alarm'")
option = json.loads(option)["text"]
if option == "Timer":
    timer()
if option == "Alarm":
    alarmClock()

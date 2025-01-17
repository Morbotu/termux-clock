import subprocess
import sys
from art import text2art
from datetime import datetime, timedelta
import time
import json
import os
import tty
import fcntl


def playbeep():
    subprocess.call(["termux-media-player", "play", "/data/data/com.termux/files/home/termux-clock/sounds/beep-09.mp3"],
                    stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT)


def playbeepWithOutPause():
    subprocess.Popen("termux-media-player stop && termux-media-player play /data/data/com.termux/files/home/termux-clock/sounds/beep-06.mp3",
                     stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT, shell=True)


def displayText(text, color):
    getLines = subprocess.Popen(
        "tput lines", stdout=subprocess.PIPE, shell=True)
    lines = int(getLines.stdout.read()[:-1])
    getColumns = subprocess.Popen(
        "tput cols", stdout=subprocess.PIPE, shell=True)
    columns = int(getColumns.stdout.read()[:-1])

    text = text2art(text).split("\n")
    del text[-1]

    spaceAboveTime = int(lines/2) - int(len(text)/2)
    spaceUnderTime = spaceAboveTime
    if lines % 2 != 0:
        spaceUnderTime += 1

    output = []
    for i in range(spaceAboveTime):
        output.append(" " * columns)
    for i in text:
        spaceLeft = " " * (int(columns/2) - int(len(i)/2))
        spaceRight = " " * (columns - len(i) - len(spaceLeft) + 1)
        output.append(spaceLeft + i[:-1] + spaceRight)
    for i in range(spaceUnderTime):
        output.append(" " * columns)
    output = "\n".join(output)

    # \u001b[0;0H moves the cursor to location 0,0.
    # The \u001b[{n};1m with n a number representing a
    # color in the if statement changes the color of the
    # output.
    if color == "green":
        return "\u001b[0;0H\u001b[42;1m" + output + "\u001b[0m"
    if color == "red":
        return "\u001b[0;0H\u001b[41;1m" + output + "\u001b[0m"
    if color == "yellow":
        return "\u001b[0;0H\u001b[43;1m" + output + "\u001b[0m"
    if color == "black":
        return "\u001b[0;0H\u001b[40;1m" + output + "\u001b[0m"


def timeToSeconds(normalTime, noHours=False):
    normalTime = normalTime.split(":")

    timeInMillis = 0
    if noHours:
        timeInMillis += int(normalTime[0]) * 60
        timeInMillis += int(normalTime[1])
        return timeInMillis
    timeInMillis += int(normalTime[0]) * 3600
    timeInMillis += int(normalTime[1]) * 60
    timeInMillis += int(normalTime[2])
    return timeInMillis


def timer():
    timerTime = json.loads(subprocess.getoutput(
        "termux-dialog -t 'Select time' -i 'Format like h:m:s'"))["text"]
    if len([i for i in timerTime.split(":") if i.isdigit()]) != 3:
        return
    timerTime = timeToSeconds(timerTime)

    endTime = round(time.time()) + timerTime
    quit = False
    while True:
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

        keyInput = sys.stdin.read(1)
        if keyInput == "q":
            quit = True
            break
        if keyInput == "p":
            while 1:
                keyInput = sys.stdin.read(1)
                if keyInput == "p":
                    break
                if keyInput == "q":
                    quit = True
                    break
            if quit:
                break
            endTime = round(time.time()) + timeLeft
    if not quit:
        alarm()


def alarm(showTime=False, enableSnooze=False):
    turnOff = subprocess.Popen(
        "termux-dialog confirm -t 'Turn off' -i ''", stdout=subprocess.PIPE, shell=True)

    notification = "termux-notification -t 'Alarm' " + \
        "--button1 'Stop alarm' --button1-action 'echo \"Alarm closed\" > /data/data/com.termux/files/home/termux-clock/alarmOutput.txt' " + \
        "--on-delete 'echo \"Alarm closed\" > /data/data/com.termux/files/home/termux-clock/alarmOutput.txt' " + "-i 1204"

    if enableSnooze:
        notification += " --button2 'Snooze alarm' " + \
            "--button2-action 'echo \"Alarm snoozed\" > /data/data/com.termux/files/home/termux-clock/alarmOutput.txt'"

    try:
        subprocess.call(notification, shell=True)
    except:
        with open("/data/data/com.termux/files/home/termux-clock/log.txt", "w") as f:
            f.write("Error: NotificationError at line 135\nLast call: subprocess.call(notification, shell=True)\n")
    while True:
        playbeep()
        if showTime:
            sys.stdout.write(
                displayText(datetime.now().strftime("%H:%M:%S"), "black"))
            sys.stdout.flush()

        turnOff.poll()
        if turnOff.returncode != None:
            if json.loads(turnOff.stdout.read())["text"] == "yes":
                subprocess.call("termux-notification-remove 1204", shell=True)
                break
            else:
                turnOff = subprocess.Popen(
                    "termux-dialog confirm -t 'Turn off' -i ''", stdout=subprocess.PIPE, shell=True)

        if sys.stdin.read(1) == "q":
            subprocess.call(
                "termux-notification-remove 1204", shell=True)
            break

        try:
            with open("/data/data/com.termux/files/home/termux-clock/alarmOutput.txt", "r") as f:
                output = f.read()
                if output == "Alarm closed\n":
                    subprocess.call(
                        "termux-notification-remove 1204", shell=True)
                    os.remove(
                        "/data/data/com.termux/files/home/termux-clock/alarmOutput.txt")
                    break
                if output == "Alarm snoozed\n":
                    subprocess.call(
                        "termux-notification-remove 1204", shell=True)
                    os.remove(
                        "/data/data/com.termux/files/home/termux-clock/alarmOutput.txt")
                    return True
        except:
            continue
    return False


def alarmClock():
    alarmTime = json.loads(subprocess.getoutput(
        "termux-dialog time -t 'Alarm'"))["text"]
    if len([i for i in alarmTime.split(":") if i.isdigit()]) != 2:
        return
    alarmTime = datetime.strptime(alarmTime, "%H:%M")
    openSuperop = json.loads(subprocess.getoutput(
        "termux-dialog confirm -t 'Open superop' -i ''"))["text"]

    showAlarmTime = False
    while True:
        if showAlarmTime:
            sys.stdout.write(displayText(alarmTime.strftime("%H:%M"), "black"))
        else:
            sys.stdout.write(displayText(
                datetime.now().strftime("%H:%M:%S"), "black"))
        sys.stdout.flush()

        if datetime.now().strftime("%H:%M") == alarmTime.strftime("%H:%M"):
            snooze = alarm(True, True)
            if snooze:
                alarmTime = datetime.now() + timedelta(minutes=5)
            else:
                break

        keyInput = sys.stdin.read(1)
        if keyInput == "q":
            break
        if keyInput == "s":
            showAlarmTime = not showAlarmTime

    if openSuperop == "yes":
        subprocess.call(
            "bash -c '. ~/storage/shared/termuxlauncher/.apps-launcher; launch superop'", shell=True)


def intervalTimer():
    intervalOption = json.loads(subprocess.getoutput(
        "termux-dialog radio -v 'Interval repeat,Interval variable'"))["text"]

    intervals = int(json.loads(subprocess.getoutput(
        "termux-dialog counter -r '1,100,2' -t 'Intervals'"))["text"])

    if intervalOption == "Interval repeat":
        work = json.loads(subprocess.getoutput(
            "termux-dialog -t 'Work' -i 'Format like m:s'"))["text"]
        if len([i for i in work.split(":") if i.isdigit()]) != 2:
            return
        rest = json.loads(subprocess.getoutput(
            "termux-dialog -t 'Rest' -i 'Format like m:s'"))["text"]
        if len([i for i in rest.split(":") if i.isdigit()]) != 2:
            return
        work = timeToSeconds(work, True)
        rest = timeToSeconds(rest, True)

    if intervalOption == "Interval variable":
        work = []
        rest = []
        for i in range(intervals):
            work.append(json.loads(subprocess.getoutput(
                "termux-dialog -t 'Work' -i 'Format like m:s'"))["text"])
            if len([i for i in work[i].split(":") if i.isdigit()]) != 2:
                return
            work[i] = timeToSeconds(work[i], True)
            rest.append(json.loads(subprocess.getoutput(
                "termux-dialog -t 'Rest' -i 'Format like m:s'"))["text"])
            if len([i for i in rest[i].split(":") if i.isdigit()]) != 2:
                return
            rest[i] = timeToSeconds(rest[i], True)

    subprocess.Popen("termux-tts-speak 'prepare'", shell=True)
    currentAction = "prepare"
    beepsDone = [False, False, False]
    endTime = round(time.time()) + 10
    quit = False
    while True:
        timeLeft = endTime-round(time.time())

        if currentAction == "work":
            color = "red"
        elif currentAction == "rest" or currentAction == "prepare":
            color = "green"

        if timeLeft <= 3 and not beepsDone[timeLeft-1]:
            playbeepWithOutPause()
            beepsDone[timeLeft-1] = True

        sys.stdout.write(
            "\u001b[1000D" + displayText((datetime.strptime("0:0", "%M:%S") + timedelta(seconds=timeLeft)).strftime("%M:%S"), color))
        sys.stdout.flush()

        if timeLeft <= 0:
            for i in range(3):
                beepsDone[i] = False

            if currentAction == "prepare":
                if intervalOption == "Interval repeat":
                    endTime = round(time.time()) + work
                if intervalOption == "Interval variable":
                    endTime = round(time.time()) + work[0]
                currentAction = "work"
                subprocess.Popen("termux-tts-speak 'work'", shell=True)
            elif currentAction == "rest":
                intervals -= 1
                if intervals == 0:
                    break
                if intervalOption == "Interval repeat":
                    endTime = round(time.time()) + work
                if intervalOption == "Interval variable":
                    endTime = round(time.time()) + work[-intervals]
                currentAction = "work"
                subprocess.Popen("termux-tts-speak 'work'", shell=True)
            elif currentAction == "work":
                if intervalOption == "Interval repeat":
                    endTime = round(time.time()) + rest
                if intervalOption == "Interval variable":
                    endTime = round(time.time()) + rest[-intervals]
                currentAction = "rest"
                subprocess.Popen("termux-tts-speak 'rest'", shell=True)

        keyInput = sys.stdin.read(1)
        if keyInput == "q":
            quit = True
            break
        if keyInput == "p":
            while 1:
                keyInput = sys.stdin.read(1)
                if keyInput == "p":
                    break
                if keyInput == "q":
                    quit = True
                    break
            if quit:
                break
            endTime = round(time.time()) + timeLeft
    if not quit:
        subprocess.call("termux-tts-speak 'done'", shell=True)


def clock():
    while True:
        sys.stdout.write(displayText(
            datetime.now().strftime("%H:%M:%S"), "black"))
        sys.stdout.flush()

        if sys.stdin.read(1) == "q":
            break

subprocess.call("termux-wake-lock")

# This part enable sys.stdout.read(1)
# to read one character without stopping.
fd = sys.stdin.fileno()
fl = fcntl.fcntl(fd, fcntl.F_GETFL)
fcntl.fcntl(fd, fcntl.F_SETFL, fl | os.O_NONBLOCK)
old = tty.tcgetattr(fd)
tty.setcbreak(fd)

# \033[?25l makes curser invisible.
# \033[?47 saves current window.
# \u001b[0m resets all colors.
sys.stdout.write("\033[?25l\033[?47h\u001b[0m")

option = json.loads(subprocess.getoutput(
    "termux-dialog radio -v 'Timer,Alarm,Clock,Interval'"))["text"]
if option == "Timer":
    timer()
if option == "Alarm":
    alarmClock()
if option == "Clock":
    clock()
if option == "Interval":
    intervalTimer()

# \033[?47l loads window saved in the beginning.
# \033[?25h makes curser visible.
sys.stdout.write("\033[?47l\033[?25h")

# Stop input mode
tty.tcsetattr(fd, tty.TCSAFLUSH, old)

subprocess.call("termux-wake-unlock")

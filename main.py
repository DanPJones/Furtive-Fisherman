import PySimpleGUI as sg
import time
import random
import threading
import ctypes
import win32con
from PIL import Image
import mss
import mss.tools
import win32api
import win32gui

scaleFactor = ctypes.windll.shcore.GetScaleFactorForDevice(0) / 100

gui_width = int(round(282 * scaleFactor))
gui_height = int(round(374 * scaleFactor))

graph_width = int(round(282 * scaleFactor))
graph_height = int(round(374 * scaleFactor))

margins = 5 * scaleFactor

padding = int(round(5 * scaleFactor))

# global vars
x, y = 0, 0
found = 0
missed = 0
quit = False

menu_def = [['File', ['Open', 'Save', 'Settings', ]],
            ['Edit', ['Paste', ['Special', 'Normal', ], 'Undo'], ],
            ['Help', 'About...'], ]

sg.ChangeLookAndFeel('LightGreen2')
sg.SetOptions(margins=(margins, margins), element_padding=(0, 0))
layout = [[sg.Menu(menu_def)],
          [sg.Button('Start'), sg.Button('Stop'), sg.Text('Fish to catch:'), sg.Input(key='-TIMER-')],
          [sg.Text('Caught: ' + str(found), key='-FISHED-', size=(10, 0)),
           sg.Text('Missed: ' + str(missed), key='-MISSED-', size=(10, 0)),
           sg.Text('Input:'), sg.Input(key='-INPUT-', default_text='1')],
          [sg.Text('-Red to begin-', key='-CONSOLE-', size=(100, 0))],
          [sg.Graph((graph_width, graph_height), (0, 0), (100, 100), background_color='red', key='-GRAPH-')]]

# CHANGE PADDING TO OCIJASO AND MAKE FUNCTION THAT GETS X AND Y TO GRAPH
window = sg.Window('Fisherman', layout, icon='me.ico', size=(gui_width, gui_height), transparent_color='red',
                   keep_on_top=True, element_padding=(padding, padding), grab_anywhere=True)


# returns the horizontal and vertical pixels in between the graph and window.CurrentLocation()
# and maybe returns graph width and height

def get_graph_dimensions():
    xg, yg = window.current_location()      # vars that will find the dims of the graph
    origin_x, origin_y = xg, yg             # winLoc

    xg += gui_width / 2
    yg += scaleFactor + gui_height / 2
    # change xg/yg for different monitors

    window['-GRAPH-'].update(background_color='blue')
    window.refresh()

    # get image
    with mss.mss() as sct:
        current_display = get_windows_display(origin_x, origin_y)
        sct_img = sct.grab(sct.monitors[current_display])
        img2 = Image.frombytes("RGB", sct_img.size, sct_img.bgra, "raw", "BGRX")
    rg, gg, bg = img2.getpixel((x, y))

    # fix xg, yg if not on primary monitor
    xg -= sct.monitors[current_display]["left"]
    yg -= sct.monitors[current_display]["top"]

    # move to top of graph
    while rg != 182 and gg != 206 and bg != 206:
        yg -= 1
        rg, gg, bg = img2.getpixel((xg, yg))
    yg += 1
    top = yg


    # move to top left
    rg, gg, bg = img2.getpixel((xg, yg))
    while rg != 182 and gg != 206 and bg != 206:
        xg -= 1
        rg, gg, bg = img2.getpixel((xg, yg))
    xg += 1
    left = xg

    # move to top right
    rg, gg, bg = img2.getpixel((xg, yg))
    while rg != 182 and gg != 206 and bg != 206:
        xg += 1
        rg, gg, bg = img2.getpixel((xg, yg))
    xg -= 1
    right = xg

    # move to bottom
    rg, gg, bg = img2.getpixel((xg, yg))
    while rg != 182 and gg != 206 and bg != 206:
        yg += 1
        rg, gg, bg = img2.getpixel((xg, yg))
    yg -= 1
    bottom = yg

    window['-GRAPH-'].update(background_color='red')
    window.refresh()

    # return the ranges of the graph
    return int(left - origin_x), int(right - origin_x), int(top - origin_y), int(bottom - origin_y)


def get_windows_display(x, y):
    display_list = win32api.EnumDisplayMonitors()
    for i in range(0, len(display_list)):
        if display_list[i][2][0] < x < display_list[i][2][2]:
            if display_list[i][2][1] < y < display_list[i][2][3]:
                return i + 1


def color_to_tuple(RGBint):
    blue = RGBint & 255
    green = (RGBint >> 8) & 255
    red = (RGBint >> 16) & 255
    return red, green, blue


def splash_finder(good, bad, x1, x2, y1, y2):
    stop()
    start = time.time()
    time.sleep(0.1)
    end = time.time()

    x1, x2, y1, y2 = get_graph_dimensions()

    while start - end > - random.uniform(23, 25):

        x, y = window.CurrentLocation()
       #  print('TEST_WINDOW:', x,y)

        # get monitor window is on
        with mss.mss() as sct:
            current_display = get_windows_display(x, y)
            # grab screenshot
            sct_img = sct.grab(sct.monitors[current_display])
            img = Image.frombytes("RGB", sct_img.size, sct_img.bgra, "raw", "BGRX")
            img.save('farquiqui.png')

            stop()
            frame_start = time.time()
            for i in range(int(y+y1), int(y+y2)):
                for j in range(int(x+x1), int(x+x2)):
                    # print('TEST_GETPIXEL:', '\n', x, x1, "\n", y, y1)
                    r, g, b = img.getpixel((j, i))
                    if (r + g + b) > 540:
                        c_sum = r + g + b

                        # alternatively, trying looking for number of lighter pixels relative to the darker. Look
                        # for checkerboard pattern, and the colors can be variables computed on the fly

                        # count up the 3x3 square around the bright pixel
                        for k in range(j - 1, j + 2):
                            for l in range(i - 1, i + 2):
                                rd, bd, gd = img.getpixel((k, l))

                                c_sum += rd + bd + gd

                            # if square brightness is splash-bright
                            if c_sum > 4500:
                                good += 1
                                window['-FISHED-'].update('Caught: ' + str(good))
                                print(j, i)
                                return j + sct.monitors[current_display]["left"], i+10 + sct.monitors[current_display]["top"], good, bad
            # cap fps to ~20fps
            # now = time.time()
            # if (now - frame_start) < 0.05:
            #     time.sleep(0.05 - (now - frame_start))




        end = time.time()
        stop()
    bad += 1
    window['-MISSED-'].update('Missed: ' + str(bad))
    return x + random.randrange(150, 300), y + random.randrange(150, 300), good, bad


def click_splash(hwnd, x, y):
    x, y = win32gui.ScreenToClient(hwnd, (x, y))
    coord = win32api.MAKELONG(x, y)
    win32gui.PostMessage(hwnd, win32con.WM_RBUTTONDOWN, 0, coord)
    win32gui.PostMessage(hwnd, win32con.WM_RBUTTONUP, 0, coord)


def fisher(found, missed):
    ftc = values['-TIMER-']
    unlim = True
    intFTC = -1

    if len(ftc) > 0:
        unlim = False
        try:
            intFTC = int(ftc)
        except:
            window['-CONSOLE-'].update('-Timer must have int-')
            raise ValueError('Timer value must be int.')
        intFTC = int(ftc)

    print(intFTC)

    runs = 0

    # run loop
    while unlim or intFTC > 0:
        stop()

        # vars
        good = found
        bad = missed

        # switch later
        input_key = values['-INPUT-']
        stop()

        # get wow handle
        hwnd = win32gui.FindWindow('GxWindowClass', 'World of Warcraft')

        # tap 1 (currently 1 is hardcoded)
        win32api.PostMessage(hwnd, win32con.WM_KEYDOWN, 0x31, 0)
        win32api.PostMessage(hwnd, win32con.WM_KEYUP, 0x31, 0)

        # find splash
        bx, by, found, missed = splash_finder(good, bad, x1, x2, y1, y2)
        stop()

        # add reaction time
        time.sleep(random.uniform(0.2, 0.6))

        #click splash
        click_splash(hwnd, bx, by)

        # update timer if applicable
        timer = values['-TIMER-']
        if len(timer) > 0:
            intFTC -= 1
            window['-TIMER-'].update(str(intFTC))
        if intFTC == 0:
            window['-CONSOLE-'].update('-Completed-')
            raise ValueError('Thread is useless.')
        window.refresh()
        stop()
        time.sleep(random.uniform(1, 2))
        runs += 1


def stop():
    if quit:
        window['-CONSOLE-'].update('-Stopped-')
        window['-FISHED-'].update('Caught: 0')
        window['-MISSED-'].update('Missed: 0')
        raise ValueError('A very specific bad thing happened.')


# event loop
x1, x2, y1, y2 = 0, 0, 0, 0
while True:
    event, values = window.read()

    if event is None:
        break
    if event == 'Start':
        window['-CONSOLE-'].update('-Running-')
        quit = False
        # create thread
        if threading.active_count() < 2:
            window['-CONSOLE-'].update('-Running-')
            window['-FISHED-'].update('Caught: 0')
            window['-MISSED-'].update('Missed: 0')

            fisher_args = [found, missed]
            fish_fucker = threading.Thread(target=fisher, daemon=True, args=fisher_args)
            fish_fucker.start()

    if event == 'Stop':
        window['-CONSOLE-'].update('-Stopping...-')
        print(window.current_location())
        if threading.active_count() < 2:
            window['-CONSOLE-'].update('-Stopped-')

        quit = True

    startup = True
window.close()

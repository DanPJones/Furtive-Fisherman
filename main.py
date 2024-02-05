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
import requests
import jwt
import datetime

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

menu_def = [
            ['File', ['Open', 'Save', 'Settings', ]],
            ['Edit', ['Paste', ['Special', 'Normal', ], 'Undo'], ],
            ['Account', ['Log In', 'Sign Up', 'Log Out']],
            ['Help', 'About...'], 
            ]

sg.ChangeLookAndFeel('LightGreen2')
sg.SetOptions(margins=(margins, margins), element_padding=(0, 0))
layout = [[sg.Menu(menu_def)],
          [sg.Button('Start', key='-START-'), sg.Button('Stop'), sg.Text('Fish to catch:'), sg.Input(key='-TIMER-')],
          [sg.Text('Caught: ' + str(found), key='-FISHED-', size=(10, 0)),
           sg.Text('Missed: ' + str(missed), key='-MISSED-', size=(10, 0)),
           sg.Text('Input:'), sg.Input(key='-INPUT-', default_text='1')],
          [sg.Text('-Sign In-', key='-CONSOLE-', size=(100, 0))],
          [sg.Graph((graph_width, graph_height), (0, 0), (100, 100), background_color='red', key='-GRAPH-')]]

# CHANGE PADDING TO OCIJASO AND MAKE FUNCTION THAT GETS X AND Y TO GRAPH
window = sg.Window('Fisherman', layout, icon='flasher.ico', size=(gui_width, gui_height), transparent_color='red',
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

def getAvgBrightness(x1, x2, y1, y2):
    # get monitor   window is on
    sum = 0
    counter = 0
    with mss.mss() as sct:
        current_display = get_windows_display(x, y)
        # grab screenshot
        sct_img = sct.grab(sct.monitors[current_display])
        img = Image.frombytes("RGB", sct_img.size, sct_img.bgra, "raw", "BGRX")
        for i in range(int(y+y1), int(y+y2)):
            for j in range(int(x+x1), int(x+x2)):
                r, g, b = img.getpixel((j, i))
                sum += r + b + g
                counter += 1
    
    return sum / counter

def splash_finder(good, bad, x1, x2, y1, y2):
    stop()
    start = time.time()
    time.sleep(0.1)
    end = time.time()
    init = True
    global maxSum
    maxSum = 0

    x1, x2, y1, y2 = get_graph_dimensions()

    # avgBril = getAvgBrightness(x1, x2, y1, y2)
    # print("avgggg: ", avgBril)

    while start - end > - random.uniform(28, 32):

        x, y = window.CurrentLocation()

        # get monitor window is on
        with mss.mss() as sct:
            current_display = get_windows_display(x, y)
            # grab screenshot
            sct_img = sct.grab(sct.monitors[current_display])
            img = Image.frombytes("RGB", sct_img.size, sct_img.bgra, "raw", "BGRX")
            # img.save('farquiqui.png')

            # get max brightness val
            if init:
                for i in range(int(y+y1), int(y+y2)):
                    for j in range(int(x+x1), int(x+x2)):
                        r, g, b = img.getpixel((j, i))
                        maxSum = max(r + b + g, maxSum)
                init = False
                print("GINGO", maxSum)

            



            stop()
            frame_start = time.time()
            for i in range(int(y+y1), int(y+y2)):
                for j in range(int(x+x1), int(x+x2)):
                    r, g, b = img.getpixel((j, i))
                    if (r + g + b) >= min(maxSum + 10, 255 * 3):
                        c_sum = r + g + b

                        # alternatively, trying looking for number of lighter pixels relative to the darker. Look
                        # for checkerboard pattern, and the colors can be variables computed on the fly

                        # count up the 3x3 square around the bright pixel
                        for k in range(j - 1, j + 2):
                            for l in range(i - 1, i + 2):
                                rd, bd, gd = img.getpixel((k, l))

                                c_sum += rd + bd + gd

                            # if square brightness is splash-bright
                            if c_sum > maxSum * 10:
                                good += 1
                                window['-FISHED-'].update('Caught: ' + str(good))
                                return j + sct.monitors[current_display]["left"], i+10 + sct.monitors[current_display]["top"], good, bad
            # cap fps to ~20fps
            now = time.time()
            if (now - frame_start) < 0.05:
                time.sleep(0.05 - (now - frame_start))




        end = time.time()
        stop()
    bad += 1
    window['-MISSED-'].update('Missed: ' + str(bad))
    return x + random.randrange(150, 300), y + random.randrange(150, 300), good, bad


def click_splash(hwnd, x, y):
    x, y = win32gui.ScreenToClient(hwnd, (x, y))
    coord = win32api.MAKELONG(x, y)
    win32gui.PostMessage(hwnd, win32con.WM_KEYDOWN, 0x48, 0)
    win32gui.PostMessage(hwnd, win32con.WM_KEYUP, 0x48, 0)



def fisher(found, missed):

    global token

    ftc = values['-TIMER-']
    unlim = True
    intFTC = -1

    if len(ftc) > 0:
        unlim = False
        try:
            intFTC = int(ftc)
        except:
            window['-CONSOLE-'].update('-Timer must be a number-')
            raise ValueError('Timer value must be int.')
        intFTC = int(ftc)


    runs = 0

    # run loop
    while unlim or intFTC > 0:
        stop()

        if (not token ): 
            window['-CONSOLE-'].update('-Log in to fish-')
            break

        try:
            exp = getExpTime()
            if (exp < 600):
                print('new token pls. time left: ', exp)
                login(username, password)

        except Exception as e:
            window['-CONSOLE-'].update("-Bad Token: Sign in -")
            break

            
        # vars
        good = found
        bad = missed

        # switch later
        input_key = values['-INPUT-']
        stop()

        # get wow handle
        hwnd = win32gui.FindWindow('GxWindowClass', 'World of Warcraft')

        county = 0
        timeS = time.time()
        # tap 1 (currently 1 is hardcoded)
        for x in range(0, random.randrange(20,40)):
            win32api.PostMessage(hwnd, win32con.WM_KEYDOWN, 0x31, 0)
            win32api.PostMessage(hwnd, win32con.WM_KEYUP, 0x31, 0)
            time.sleep(random.uniform(0.02, 0.05))

        # waiting for bauber to become opaque after spawning
        while time.time() - timeS < 2.3:
            county += 1
            time.sleep(0.1)

        print('mmhmm yess', county)


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

def login(email, password):
    global token
    # The URL of the Flask API endpoint
    url = 'http://23.245.220.91:5000/login'

    # Data to be sent in the POST request
    payload = {
        'email': email,
        'password': password
    }

    # Make the POST request and get the response
    response = requests.post(url, json=payload)

    if response.ok:
        r_data = response.json()
        token = r_data['token']
        if not window['-CONSOLE-'].get() == "-Running-":
            window['-CONSOLE-'].update('-Signed In-')
    elif response.status_code == 400:
        window['-CONSOLE-'].update('-Bad Credentials-')
    else:
        window['-CONSOLE-'].update('-Error Signing In-')



def signUp(email, password):
    global token
    # The URL of the Flask API endpoint
    url = 'http://23.245.220.91:5000/signUp'

    # Data to be sent in the POST request
    data = {
        'email': email,
        'password': password
    }

    # Make the POST request and get the response
    response = requests.post(url, json=data)



    if response.ok:
        window['-CONSOLE-'].update('-Account Created-')
        r_data = response.json()
        token = r_data['token']
    elif response.status_code == 401:
        window['-CONSOLE-'].update('-Account Already Exists-')
    else:
        window['-CONSOLE-'].update('-Error Creating Account-')
def loginWindow():

    uname = ''
    pword = ''

    login_layout = [
        [sg.Text('Sign In', font=(30), pad=(0, 5,))],
        [sg.Text('Username: '), sg.Push(), sg.Input(key='-email-', size=(30,0))],
        [sg.Text('Password: '), sg.Push(), sg.Input(key='-password-', password_char='*', size=(30,0))],
        [sg.Push(), sg.Button('Submit')],
    ]

    x, y = window.current_location()
    login_window = sg.Window('Fisherman', login_layout, icon='flasher.ico', modal=True, keep_on_top=True, element_justification='center', element_padding=(0, 3), margins=(20, 20), location=(x - 50, y + 50))

    while True:
        event, values = login_window.read()
        if event is None:
            break
        elif event == 'Submit':
            uname = values['-email-']
            pword = values['-password-']
            break
    
    login_window.close()
    return uname, pword

def signUpWindow():

    uname = ''
    pword = ''

    signup_layout = [
        [sg.Text('Sign Up', font=(30), pad=(0, 5,))],
        [sg.Text('Username: '), sg.Push(), sg.Input(key='-email-', size=(30,0))],
        [sg.Text('Password: '), sg.Push(), sg.Input(key='-password-', password_char='*', size=(30,0))],
        [sg.Push(), sg.Button('Submit')],
    ]

    x, y = window.current_location()
    signUp_window = sg.Window('Fisherman', signup_layout, icon='flasher.ico', modal=True, keep_on_top=True, element_justification='center', element_padding=(0, 3), margins=(20, 20), location=(x - 50, y + 50))

    while True:
        event, values = signUp_window.read()
        if event is None:
            break
        elif event == 'Submit':
            uname = values['-email-']
            pword = values['-password-']
            if uname and pword: window['-CONSOLE-'].update('Creating user, logging in...')

            break
    
    signUp_window.close()
    return uname, pword


def connectToServer():
    pass

def getExpTime():
    global token
    payload = jwt.decode(token, options={"verify_signature": False})
    exp = payload.get('exp')
    return exp - time.time()

# event loop
x1, x2, y1, y2 = 0, 0, 0, 0
username, password = '', ''
SECRET_KEY = '9PVQWd22nq8ues0KJTSGLsor3KEQ1pksYKLZ9JEJFag'
token = ''
loggedIn = False
while True:
    event, values = window.read()

    if event is None:
        break
    if event == 'Log In':
        username, password = loginWindow()

        if username and password :
            login(username, password)
 
    if event == 'Sign Up':
        username, password = signUpWindow()
        if username and password :
            signUp(username, password)


    if event == '-START-':
        if not (username or password) or not token:
            username, password = loginWindow()
            if username and password:
                login(username, password)

        window['-CONSOLE-'].update('-Running-')
        window['-START-'].update(disabled=True)

        quit = False
        # create thread
        if threading.active_count() < 2:
            window['-CONSOLE-'].update('-Running-')
            window['-FISHED-'].update('Caught: 0')
            window['-MISSED-'].update('Missed: 0')

            fisher_args = [found, missed]
            fish_fucker = threading.Thread(target=fisher, daemon=True, args=fisher_args)
            fish_fucker.start()

    if event == 'Log Out':
        token = ''
        window['-CONSOLE-'].update('-Log in to fish-')


    if event == 'Stop':
        window['-CONSOLE-'].update('-Stopping...-')
        window['-START-'].update(disabled=False)
        if threading.active_count() < 2:
            window['-CONSOLE-'].update('-Stopped-')

        quit = True

    startup = True
window.close()

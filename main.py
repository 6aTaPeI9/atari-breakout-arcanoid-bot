import cv2
import random
import win32api
import numpy as np
from collections import deque

import keyboard
import time

from matplotlib import pyplot as plt
from PIL import ImageGrab

MONITORS = win32api.EnumDisplayMonitors()

# Отсчет от 0
GAME_MONITOR = 0
SCREEN_WIDHT = MONITORS[GAME_MONITOR][2][2]
SCREEN_HEIGHT = MONITORS[GAME_MONITOR][2][3]
SCREEN_START_X = MONITORS[GAME_MONITOR][2][0]
SCREEN_START_Y = MONITORS[GAME_MONITOR][2][1]

THRESHOLD = 0.8
BALL_TMPL = cv2.imread('templates/ball.png', 0)
ball_w, ball_h = BALL_TMPL.shape[::-1]
BALL_TMPL = cv2.resize(BALL_TMPL, (ball_w // 4, ball_h // 4))
ball_w, ball_h = BALL_TMPL.shape[::-1]

BALL_QUEUE = deque(maxlen=2)

PLATFORM_TMPL = cv2.imread('templates/platform_3.png', 0)
platform_w, platform_h = PLATFORM_TMPL.shape[::-1]
PLATFORM_TMPL = cv2.resize(PLATFORM_TMPL, (platform_w // 4, platform_h // 4))

PLATFORM_TMPL_SMALL = cv2.imread('templates/platform_small.png', 0)
platform_w_s, platform_h_s = PLATFORM_TMPL_SMALL.shape[::-1]
PLATFORM_TMPL_SMALL = cv2.resize(PLATFORM_TMPL_SMALL, (platform_w_s // 4, platform_h_s // 4))

PLATFORM_LINE = None

WORK_STATUS = True
EXIT_STATUS = True

def line_intersection(line1, line2):
    xdiff = (line1[0][0] - line1[1][0], line2[0][0] - line2[1][0])
    ydiff = (line1[0][1] - line1[1][1], line2[0][1] - line2[1][1])

    def det(a, b):
        return a[0] * b[1] - a[1] * b[0]

    div = det(xdiff, ydiff)
    if div == 0:
       return None

    d = (det(*line1), det(*line2))
    x = det(d, xdiff) / div
    y = det(d, ydiff) / div
    return int(x), int(y)

def exit():
    global EXIT_STATUS
    EXIT_STATUS = False

def run():
    global WORK_STATUS
    WORK_STATUS = not WORK_STATUS

keyboard.add_hotkey(';', lambda: exit())
keyboard.add_hotkey('l', lambda: run())

LAST_REMEMBER_POS = None

while EXIT_STATUS:
    if not WORK_STATUS:
        cv2.waitKey(500)
        continue

    img = ImageGrab.grab(bbox=(SCREEN_START_X, SCREEN_START_Y, SCREEN_WIDHT, SCREEN_HEIGHT))
    img = img.resize((img.size[0] // 4, img.size[1] // 4))
    img_np = np.array(img)
    img_rgb = cv2.cvtColor(img_np, cv2.COLOR_BGR2RGB)
    img_gray = cv2.cvtColor(img_np, cv2.COLOR_BGR2GRAY)

    res = cv2.matchTemplate(img_gray, BALL_TMPL, cv2.TM_CCOEFF_NORMED)
    ball_loc = np.where(res >= THRESHOLD)
    ball_pos = None
    for pos in zip(*ball_loc[::-1]):
        ball_pos = pos
        BALL_QUEUE.append((pos[0] + ball_w // 2, pos[1] + ball_h // 2))
        cv2.rectangle(img_rgb, pos, (pos[0] + ball_w, pos[1] + ball_h), (0,0,255), 2)
        break

    platform_pos = None

    for platform_t in [PLATFORM_TMPL, PLATFORM_TMPL_SMALL]:
        if platform_pos:
            break

        platform_w, platform_h = platform_t.shape[::-1]
        res = cv2.matchTemplate(img_gray, platform_t, cv2.TM_CCOEFF_NORMED)
        platform_loc = np.where(res >= THRESHOLD)

        for pos in zip(*platform_loc[::-1]):
            platform_pos = pos
            cv2.rectangle(img_rgb, pos, (pos[0] + platform_w, pos[1] + platform_h), (0,0,255), 2)

            if not PLATFORM_LINE:
                PLATFORM_LINE = [(0, pos[1]), (img_rgb.shape[1], pos[1])]
            break

    print(platform_pos, PLATFORM_LINE)

    if PLATFORM_LINE:
        cv2.line(img_rgb, PLATFORM_LINE[0], PLATFORM_LINE[1], (0,0,255), thickness=2)

    if platform_pos:
        platform_center_x = platform_pos[0] + (platform_w // 2)

    if len(BALL_QUEUE) == 2:
        if BALL_QUEUE[0][1] > BALL_QUEUE[1][1]:
            LAST_REMEMBER_POS = BALL_QUEUE[1]
        else:
            intersect_point = line_intersection(PLATFORM_LINE, BALL_QUEUE)
            LAST_REMEMBER_POS = intersect_point
            cv2.line(img_rgb, intersect_point, BALL_QUEUE[1], (0,0,255), thickness=2)

    if LAST_REMEMBER_POS:
        operator = random.choice([1, -1])
        rand_scale = random.randint(20, 45)
        win32api.SetCursorPos((LAST_REMEMBER_POS[0] * 4 + rand_scale * operator, PLATFORM_LINE[0][0] * 4))
        # if LAST_REMEMBER_POS[0] < (platform_center_x):
        #     keyboard.press('ф')
        # elif LAST_REMEMBER_POS[0] > (platform_center_xфф):
        #     keyboard.press('в')
        # else:
        #     keyboard.release('ф')
        #     keyboard.release('в')

    cv2.imshow('bot', img_rgb)
    cv2.waitKey(1)

cv2.destroyAllWindows()
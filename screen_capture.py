import win32api, win32gui
import cv2
import numpy as np
from PIL import ImageGrab

WIN_NAME = 'Capture'

def select_screen_area():
    cursor_hold = False
    window_img = None
    start_pos = None
    cur_pos = None

    while True:
        state_left = win32api.GetKeyState(0x01)

        if not cursor_hold and (state_left < 0):
            cursor_hold = True
            start_pos = win32gui.GetCursorPos()
            window_img = ImageGrab.grab()

        if cursor_hold:
            cur_pos = win32gui.GetCursorPos()
            img_np = np.array(window_img)
            img_rgb = cv2.cvtColor(img_np, cv2.COLOR_BGR2RGB)
            cv2.namedWindow(WIN_NAME, cv2.WND_PROP_FULLSCREEN)
            cv2.setWindowProperty(WIN_NAME, cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)
            cv2.setWindowProperty(WIN_NAME, cv2.WND_PROP_TOPMOST, 1)
            cv2.rectangle(img_rgb, start_pos, cur_pos, (0,0,255), 2)
            cv2.imshow(WIN_NAME, img_rgb)

        if cursor_hold and (state_left >= 0):
            window_img = None
            cursor_hold = False
            cv2.destroyAllWindows()
            break

        cv2.waitKey(20)

    return start_pos, cur_pos
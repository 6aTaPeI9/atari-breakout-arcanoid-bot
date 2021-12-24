import cv2
import os
import random
import win32api
import numpy as np
import traceback

from PIL import ImageGrab
from collections import deque
from screen_capture import select_screen_area
from help_funcs import line_intersection, sides_by_coord
from key_state import KeyStateStorage
from collections import namedtuple

EXIT_KEY = 'esc'
RUN_KEY = 'l'
SELECT_AREA = ';'

THRESHOLD = 0.8
WIN_SCALE = 2

CV_DELAY = 20

BALL_QUEUE = deque(maxlen=3)
BALL_DIRECTION = 'downward'
LAST_REMEMBER_POS = None

# Если шаблоны были заменены, вместо в значение поставить None.
TEMPLATE_SOURCE_SIZE = None
# TEMPLATE_SOURCE_SIZE = (1920, 1080)

TEMPLATES = [
    'templates/ball_2.png',
    'templates/platform_2.png',
    'templates/platform_small.png'
]

def prepare_templates(scale = None, source_size = None, win_size = None):
    TmplInfo = namedtuple('TmplInfo', ('img', 'width', 'height', 'orig_size'))

    if not scale:
        scale = 1

    source_scale_w = 1
    source_scale_h = 1

    if source_size and win_size:
        source_scale_w = win_size[0] / TEMPLATE_SOURCE_SIZE[0]
        source_scale_h = win_size[1] / TEMPLATE_SOURCE_SIZE[1]

    result = {}

    for tmpl_path in TEMPLATES:
        tmpl = cv2.imread(tmpl_path, 0)
        tmpl_name, _ = os.path.splitext(os.path.basename(tmpl_path))

        orig_size = tmpl.shape[::-1]
        size = (
            int(orig_size[0] * source_scale_w // scale),
            int(orig_size[1] * source_scale_h // scale)
        )

        tmpl = cv2.resize(tmpl, size)
        result[tmpl_name] = TmplInfo(tmpl, size[0], size[1], orig_size)

    return result


def match(screen, templates):
    def find_by_tmpl(src_img, tmpl_info, mark = True, mark_img = None):
        res = cv2.matchTemplate(src_img, tmpl_info.img, cv2.TM_CCOEFF_NORMED)
        pos = np.where(res >= THRESHOLD)

        if pos[0].size == 0:
            return None

        pos = pos[::-1]
        pos = (pos[0][0], pos[1][0])

        if mark and mark_img is not None:
            cv2.rectangle(mark_img, pos, (pos[0] + tmpl_info.width, pos[1] + tmpl_info.height), (0,0,255), 2)

        return pos

    global LAST_REMEMBER_POS, BALL_DIRECTION
    win_width, win_height = sides_by_coord(*screen)

    img = ImageGrab.grab(bbox=screen)
    img = img.resize((img.size[0] // WIN_SCALE, img.size[1] // WIN_SCALE))
    img_np = np.array(img)
    img_rgb = cv2.cvtColor(img_np, cv2.COLOR_BGR2RGB)
    img_gray = cv2.cvtColor(img_np, cv2.COLOR_BGR2GRAY)

    ball_pos = find_by_tmpl(img_gray, templates['ball_2'], True, img_rgb)

    if ball_pos:
        BALL_QUEUE.append((ball_pos[0] + templates['ball_2'].width // 2, ball_pos[1] + templates['ball_2'].height))

    for platform in [templates['platform_2'], templates['platform_small']]:
        platform_pos = find_by_tmpl(img_gray, platform, True, img_rgb)

        if platform_pos:
            break
    try:
        platform_line = (0, platform_pos[1]), (win_width, platform_pos[1])
        if platform_pos:
            cv2.line(img_rgb, *platform_line, (0,0,255), thickness=2)


        if len(BALL_QUEUE) == BALL_QUEUE.maxlen:
            if BALL_QUEUE[0][1] > BALL_QUEUE[-1][1]:
                direct = 'upward'
            else:
                direct = 'downward'

            if BALL_DIRECTION != direct:
                LAST_REMEMBER_POS = BALL_QUEUE[-1]
                BALL_QUEUE.clear ()
                BALL_DIRECTION = direct
            else:
                if BALL_QUEUE[0][1] >= BALL_QUEUE[-1][1]:
                    LAST_REMEMBER_POS = BALL_QUEUE[-1]
                else:
                    intersect_point = line_intersection(platform_line, (BALL_QUEUE[0], BALL_QUEUE[-1]))
                    LAST_REMEMBER_POS = intersect_point
                    cv2.line(img_rgb, intersect_point, BALL_QUEUE[-1], (0,0,255), thickness=2)

        if LAST_REMEMBER_POS:
            operator = random.choice([1, -1])
            rand_scale = random.randint(10, 30)
            win32api.SetCursorPos((
                LAST_REMEMBER_POS[0] * WIN_SCALE + rand_scale * operator + screen[0],
                platform_line[0][1] * WIN_SCALE + screen[1]
            ))
    except Exception:
        print(traceback.format_exc())
        # platform_center_x = platform_pos[0] + (platform_w // 2)
        # if LAST_REMEMBER_POS[0] < (platform_center_x):
        #     keyboard.press('ф')
        # elif LAST_REMEMBER_POS[0] > (platform_center_x):
        #     keyboard.press('в')
        # else:
        #     keyboard.release('ф')
        #     keyboard.release('в')

    cv2.imshow('bot', img_rgb)


def run_command():
    keys = KeyStateStorage()
    keys.add_key_listener(EXIT_KEY)
    keys.add_key_listener(RUN_KEY)
    keys.add_key_listener(SELECT_AREA)

    game_area = select_screen_area()
    game_area = (*game_area[0], *game_area[1])

    templates = prepare_templates(
        WIN_SCALE,
        TEMPLATE_SOURCE_SIZE,
        sides_by_coord(*game_area)
    )

    while not keys[EXIT_KEY]:
        if not keys[RUN_KEY]:
            match(game_area, templates)

        if keys[SELECT_AREA]:
            cv2.destroyAllWindows()
            game_area = select_screen_area()

        cv2.waitKey(CV_DELAY)

if __name__ == '__main__':
    run_command()
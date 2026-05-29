import os
import cv2
import subprocess
import importlib
from util import EasyDict
import pprint
import tkinter as tk
from tkinter import filedialog
import numpy as np
import shutil


class NerfViewer:
    def __init__(self):
        self.CONFIG_PATH = "configs/viewer_config.py"
        self.RUNTIME_CONFIG_PATH = "configs/viewer_config_runtime.py" 
        self.PATCH_TYPE = "logs/fur" # Target_path in config
        self.OUTPUT_DIR = self.PATCH_TYPE + "/media/test/"
        self.DEFAULT_IMG = self.OUTPUT_DIR + "default.png"
        self.RENDERED_IMG = self.OUTPUT_DIR + "0.png"

        self.PATCHES = {
            "plush": {
                "target_path": "logs/plush",
                "n_parameters": [1, 4],
                "constants": [[0,.5,0,-.707,.707]] # [1,.5,0,-.707,.707] # Second row
            },

            "fur": {
                "target_path": "logs/fur",
                "n_parameters": [1, 4],
                "constants": [[0,.5,0,-.707,.707]] # [1,.5,0,-.707,.707] # Second row
            },

            "pinkfur": {
                "target_path": "logs/pinkfur",
                "n_parameters": [4, 3],
                "constants": [[0.8, 0.9, 0.7, 0.1, 0.0, -0.7, 0.7]]
            },

            "orangefur": {
                "target_path": "logs/pinkfur",
                "n_parameters": [4, 3],
                "constants": [[1.0, 0.5, 0.5, 0.2,  0.0, -0.7, 0.7]] 
            },

            "carpet": {
                "target_path": "logs/carpet",
                "n_parameters": [1, 6],
                "constants": [[1, 1, 1, .1, 0, 0, 1]] 
            },

            "grass": {
                "target_path": "logs/grass",
                "n_parameters": [1, 4], 
                "constants": [[0,.5,0,-.707,.707]]
            },

            "curls": {
                "target_path": "logs/curls",
                "n_parameters": [4, 3], 
                "constants": [[0.8, 0.97, 0.736, 0.138, 0.7077, 0.656, 0.73]]   
            }
        }

        self.patch_icons = {}
        for name in self.PATCHES:
            path = f"patches/{name}.png"

            if os.path.exists(path):
                icon = cv2.imread(path, cv2.IMREAD_UNCHANGED)
                icon = cv2.resize(icon, (100, 100))
                self.patch_icons[name] = icon

        self.WINDOW_NAME = "Real-time NeRF-Tex Renderer"
        root = tk.Tk()
        root.withdraw()
        self.SCREEN_W = root.winfo_screenwidth()
        self.SCREEN_H = root.winfo_screenheight()
        root.destroy()
        self.WINDOW_W = self.SCREEN_W
        self.WINDOW_H = self.SCREEN_H

        self.FONT = cv2.FONT_HERSHEY_SIMPLEX
        self.PINK_COLOR = (170, 128, 255)
        self.YELLOW_COLOR = (128, 244, 255)
        self.BLUE_COLOR = (255, 223, 128)
        self.DARK_BG = (35, 30, 30)
        self.LIGHT_BG = (230, 230, 230)
        self.DARK_PANEL = (50, 45, 45)
        self.LIGHT_PANEL = (186, 186, 186)
        self.DARK_TEXT = (230, 230, 230)
        self.LIGHT_TEXT = (0, 0, 0)
        self.DARK_BORDER_HOVER = (80, 70, 70)
        self.LIGHT_BORDER_HOVER  = (110, 110, 110)

        self.BG_COLOR = self.DARK_BG
        self.PANEL_COLOR = self.DARK_PANEL
        self.TEXT_COLOR = self.DARK_TEXT
        self.BORDER_HOVER_COLOR = self.DARK_BORDER_HOVER 
        
        # Camera - u,v range in config
        #0.5 and 0.0 = front view = 'u_range': (0.5, 0.5), 'v_range': (0.0, 0.0)
        #0.5 and 0.5 = back view
        #1.0 and 0.5 = bottom view
        #0.0 and 0.5 = top view
        #0.5 and 0.7 = left side
        #0.5 and 0.25 = right side
        self.u_coord = 0.5
        self.v_coord = 0.0

        self.dragging = False
        self.last_x = 0
        self.last_y = 0
        self.mouse_x = 0
        self.mouse_y = 0

        self.zoom = 1.0
        self.min_zoom = 1.0
        self.max_zoom = 6.0
        self.crop_x = 0
        self.crop_y = 0
        self.zoom_slider_rect = None
        self.zoom_dragging = False

        self.needs_render = False
        self.light_mode = "directional"
        self.light_button_label = "Point"
        self.current_patch = "fur"
        self.menu_open = False
        self.dark_mode = True

        config_module = importlib.import_module("configs.viewer_config")
        self.config = EasyDict(config_module.config)

        root = tk.Tk()
        root.withdraw()
        self.SCREEN_W = root.winfo_screenwidth()
        self.SCREEN_H = root.winfo_screenheight()
        root.destroy()

        self.init_window()

    # ------------------------------------------------------------------
    def init_window(self):
        cv2.namedWindow(self.WINDOW_NAME, cv2.WINDOW_NORMAL)
        cv2.setWindowProperty(self.WINDOW_NAME, cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)
        cv2.setMouseCallback(self.WINDOW_NAME, self.mouse_callback)

    # ------------------------------------------------------------------
    def run_render(self):
        print("---> Rendering...")

        result = subprocess.run(
            ["python", "main.py", self.RUNTIME_CONFIG_PATH],
            capture_output = True,
            text = True
        )

        print(result.stdout)
        print(result.stderr)

        print("---> Rendering done")

    # ------------------------------------------------------------------
    def overlay_image(self, canvas, img, x, y):
        h, w = img.shape[:2]
        canvas_h, canvas_w = canvas.shape[:2]

        if ((x >= canvas_w) or (y >= canvas_h)):
            return  # completely outside

        w = min(w, canvas_w - x)
        h = min(h, canvas_h - y)

        img = img[:h, :w]

        if (img.shape[2] == 4):
            alpha = img[:, :, 3] / 255.0
            rgb = img[:, :, :3]

            for c in range(3):
                canvas[y:y+h, x:x+w, c] = (alpha * rgb[:, :, c] + (1 - alpha) * canvas[y:(y + h), x:(x + w), c])
        else:
            canvas[y:(y + h), x:(x + w)] = img

    # ------------------------------------------------------------------
    def load_image(self, default = False):
        files = sorted(os.listdir(self.OUTPUT_DIR))
        if not files:
            return None

        if default:
            img_path = self.DEFAULT_IMG
        else:
            img_path = self.RENDERED_IMG

        print("---> Loading image: ", img_path)
        return cv2.imread(img_path, cv2.IMREAD_UNCHANGED)

    # ------------------------------------------------------------------
    def update_camera(self):
        pose = self.config.test_dataset_config['data_loader_config']['pose_dist_config']
        pose['u_range'] = (self.u_coord, self.u_coord)
        pose['v_range'] = (self.v_coord, self.v_coord)

    # ------------------------------------------------------------------
    def update_mesh(self, path):
        self.config.renderer_config['instancer_config']['mesh_path'] = path

    # ------------------------------------------------------------------
    # Texture in config
    def update_pattern(self, path):
        textures = self.config.renderer_config['instancer_config']['textures']
        textures[1] = path

    # ------------------------------------------------------------------
    def update_light(self, light_type):
        textures = self.config.renderer_config['instancer_config']['textures']
        textures[1] = light_type

    # ------------------------------------------------------------------
    # Which trained patch to use, matches with data from training
    def update_patch(self, patch_name):
        changes = self.PATCHES[patch_name]

        self.PATCH_TYPE = changes["target_path"]
        self.OUTPUT_DIR = self.PATCH_TYPE + "/media/test/"
        self.RENDERED_IMG = self.OUTPUT_DIR + "0.png"
        print("---> Changing patch type to: ", self.PATCH_TYPE)

        self.config['target_path'] = changes["target_path"]
        self.config['model_config']['n_parameters'] = changes["n_parameters"]
        self.config['test_dataset_config']['data_loader_config']['parameter_dist_config']['constants'] = changes["constants"]

    # ------------------------------------------------------------------
    def save_config(self):
        with open(self.RUNTIME_CONFIG_PATH, "w") as f:
            f.write("config = ")
            pprint.pprint(dict(self.config), stream = f)

    # ------------------------------------------------------------------
    def pick_file(self, file_type, directory = ''):
        root = tk.Tk()
        root.withdraw()
        
        file_types = ((file_type + ' files', '*.' + file_type), ('All files', '*.*'))
        file_name = filedialog.askopenfilename(
            title = 'Choose a file',
            initialdir = directory + '/',
            filetypes = file_types)

        root.destroy()

        return file_name

    # ------------------------------------------------------------------
    def change_color_mode(self):
        if self.dark_mode:
            self.BG_COLOR = self.DARK_BG
            self.PANEL_COLOR = self.DARK_PANEL
            self.TEXT_COLOR = self.DARK_TEXT
            self.BORDER_HOVER_COLOR = self.DARK_BORDER_HOVER 
        else:
            self.BG_COLOR = self.LIGHT_BG
            self.PANEL_COLOR = self.LIGHT_PANEL
            self.TEXT_COLOR = self.LIGHT_TEXT
            self.BORDER_HOVER_COLOR = self.LIGHT_BORDER_HOVER

    # ------------------------------------------------------------------
    def center_crop(self, img_w, img_h, zoom_w, zoom_h):
        self.crop_x = max(0, (img_w - zoom_w) // 2)
        self.crop_y = max(0, (img_h - zoom_h) // 2)

    # ------------------------------------------------------------------
    def update_zoom_from_mouse(self, x1, x2, mx):
        t = (mx - x1) / float(x2 - x1)
        t = max(0.0, min(1.0, t))

        self.zoom = self.min_zoom + t * (self.max_zoom - self.min_zoom)
        #self.zoom = self.min_zoom * (self.max_zoom / self.min_zoom) ** t

    # ------------------------------------------------------------------
    def draw_top_menu(self, canvas):
        bar_h = 40
        cv2.rectangle(canvas, (0, 0), (self.WINDOW_W // 3 * 2, bar_h), self.PANEL_COLOR, -1)

        file_rect = (10, 5, 80, 35)
        hovered = ((file_rect[0] <= self.mouse_x <= file_rect[2]) and (file_rect[1] <= self.mouse_y <= file_rect[3]))

        color = self.BG_COLOR
        if hovered:
            color = self.BORDER_HOVER_COLOR 

        cv2.rectangle(canvas, (file_rect[0], file_rect[1]), (file_rect[2], file_rect[3]), color, -1)
        cv2.putText(canvas, "File", (file_rect[0] + 10, file_rect[1] + 23), self.FONT, 0.6, self.TEXT_COLOR, 1, cv2.LINE_AA)
        self.button_regions.append((file_rect, "menu_file"))

        color_mode_rect = (100, 5, 240, 35)
        hovered = ((color_mode_rect[0] <= self.mouse_x <= color_mode_rect[2]) and (color_mode_rect[1] <= self.mouse_y <= color_mode_rect[3]))

        color = self.BG_COLOR
        if hovered:
            color = self.BORDER_HOVER_COLOR 

        cv2.rectangle(canvas, (color_mode_rect[0], color_mode_rect[1]), (color_mode_rect[2], color_mode_rect[3]), color, -1)
        button_text = "Dark mode"
        if self.dark_mode:
            button_text = "Light mode"

        cv2.putText(canvas, button_text, (color_mode_rect[0] + 10, color_mode_rect[1] + 23), self.FONT, 0.6, self.TEXT_COLOR, 1, cv2.LINE_AA)
        self.button_regions.append((color_mode_rect, "menu_color_mode"))

        if self.menu_open:
            options = [
                ("Save Config", "save_config"),
                ("Save Image", "save_image"),
            ]

            w = 180
            h = 35

            for i, (label, action) in enumerate(options):
                x0 = 10
                y0 = bar_h + i * h

                rect = (x0, y0, x0 + w, y0 + h)

                hovered = ((rect[0] <= self.mouse_x <= rect[2]) and (rect[1] <= self.mouse_y <= rect[3]))

                color = self.BG_COLOR
    
                if hovered:
                    color = self.BORDER_HOVER_COLOR

                cv2.rectangle(canvas, (rect[0], rect[1]), (rect[2], rect[3]), color, -1)
                cv2.putText(canvas, label, (x0 + 10, y0 + 22), self.FONT, 0.5, self.TEXT_COLOR, 1, cv2.LINE_AA)

                self.button_regions.append((rect, action))

        close_button_w = 50
        close_button_h = 35
        close_button_rect = (self.WINDOW_W - close_button_w, 0, self.WINDOW_W, close_button_h)
        hovered = ((close_button_rect[0] <= self.mouse_x <= close_button_rect[2]) and (close_button_rect[1] <= self.mouse_y <= close_button_rect[3]))
        color = self.BG_COLOR
        if hovered:
            color = (70, 70, 180)

        cv2.rectangle(canvas, (close_button_rect[0], close_button_rect[1]), (close_button_rect[2], close_button_rect[3]), color, -1)
        cv2.putText(canvas, "X", (close_button_rect[0] + 18, close_button_rect[1] + 24), self.FONT, 0.7, self.TEXT_COLOR, 1, cv2.LINE_AA)

        self.button_regions.append((close_button_rect, "exit_app"))

    # ------------------------------------------------------------------
    def draw_compass(self, canvas, cx, cy):
        radius = 80

        cv2.circle(canvas, (cx, cy), radius, self.BORDER_HOVER_COLOR, -1)
        cv2.circle(canvas, (cx, cy), radius, self.BG_COLOR, 3)

        cv2.line(canvas, ((cx - radius), cy), ((cx + radius), cy), self.PINK_COLOR, 1)  # X
        cv2.line(canvas, (cx, (cy - radius)), (cx, (cy + radius)), self.BLUE_COLOR, 1)  # Y

        vx = -self.v_coord
        if (vx < -0.5):
            vx += 1.0
        elif (vx > 0.5):
            vx -= 1.0

        uy = self.u_coord - 0.5
        ux = vx * 2.0
        vy = (uy) * 2.0
        length = np.sqrt(ux * ux + vy * vy)

        if (length > 1.0):
            ux /= length
            vy /= length

        px = int(cx + ux * radius)
        py = int(cy + vy * radius)
        cv2.circle(canvas, (px, py), 6, self.YELLOW_COLOR, -1)

        cv2.putText(canvas, "X", ((cx + radius + 5), cy), cv2.FONT_HERSHEY_COMPLEX, 0.7, self.PINK_COLOR, 1)
        cv2.putText(canvas, "Y", (cx, (cy - radius - 5)), cv2.FONT_HERSHEY_COMPLEX, 0.7, self.BLUE_COLOR, 1)

        return canvas

    # ------------------------------------------------------------------
    def draw_zoom_slider(self, canvas, x, y):
        w, h = 500, 20
        min_zoom, max_zoom = self.min_zoom, self.max_zoom

        line_y = y + h // 2
        cv2.line(canvas, (x, line_y), (x + w, line_y), self.BORDER_HOVER_COLOR, 2)

        minus_rect = (x - 30, y, x - 5, y + h)
        plus_rect = (x + w + 5, y, x + w + 30, y + h)
        cv2.putText(canvas, "-", (x - 22, y + 15), self.FONT, 0.6, self.TEXT_COLOR, 2)
        cv2.putText(canvas, "+", (x + w + 12, y + 15), self.FONT, 0.6, self.TEXT_COLOR, 2)

        t = (self.zoom - min_zoom) / (max_zoom - min_zoom)
        knob_x = int(x + t * w)
        cv2.circle(canvas, (knob_x, line_y), 7, self.TEXT_COLOR, -1)

        self.zoom_slider_rect = (x, y, x + w, y + h, minus_rect, plus_rect, knob_x, line_y)

    # ------------------------------------------------------------------
    def get_regions(self):
        panel_width = self.WINDOW_W // 3
        img = self.load_image(default = False)

        if (img is None):
            return {}

        img_h, img_w = img.shape[:2]

        x0 = (self.WINDOW_W - panel_width - img_w) // 2
        y0 = (self.WINDOW_H - img_h) // 2

        return {
            "image": {
                "x0": x0,
                "y0": y0,
                "x1": (x0 + img_w),
                "y1": (y0 + img_h)
            }
        }

    # ------------------------------------------------------------------
    def draw_buttons(self, canvas, panel_x0, panel_width):
        self.button_regions = []
        compass_size = 120
        control_h = 45
        control_w = 200
        control_gap = 10
        patch_w = 160
        patch_h = 120
        patch_gap = 15
        cols = 2

        patches = [
            ("plush", "Plush"),
            ("fur", "Fur"),
            ("pinkfur", "Pink spikes"),
            ("orangefur", "Orange spikes"),
            ("carpet", "Carpet"),
            ("curls", "Curls"),
            ("grass", "Grass"),
        ]

        n_patch_rows = (len(patches) + cols - 1) // cols
        patches_height = n_patch_rows * patch_h + (n_patch_rows - 1) * patch_gap
        controls_height = control_h
        total_height = (compass_size + 30 + controls_height + 30 + patches_height)

        compass_radius = 80
        group_width = 360
        group_height = 180
        group_x0 = panel_x0 + (panel_width - group_width) // 2
        group_y0 = 40

        compass_cx = group_x0 + compass_radius
        compass_cy = group_y0 + group_height // 2
        self.draw_compass(canvas, compass_cx, compass_cy)

        center_x = compass_cx + 220
        center_y = compass_cy
        size = 22     
        offset = 95    
        length = 55    

        arrows = [(
                np.array([
                    [center_x, center_y - offset],
                    [center_x - size, center_y - offset + length],
                    [center_x + size, center_y - offset + length]]),
                "rotate_up"),

                (
                np.array([
                    [center_x, center_y + offset],
                    [center_x - size, center_y + offset - length],
                    [center_x + size, center_y + offset - length]]),
                "rotate_down"),

                (
                np.array([
                    [center_x - offset, center_y],
                    [center_x - offset + length, center_y - size],
                    [center_x - offset + length, center_y + size]]),
                "rotate_left"),

                (
                np.array([
                    [center_x + offset, center_y],
                    [center_x + offset - length, center_y - size],
                    [center_x + offset - length, center_y + size]]),
                "rotate_right")
                ]

        for pts, action in arrows:
            hovered = cv2.pointPolygonTest(pts.astype(np.int32), (self.mouse_x, self.mouse_y), False) >= 0

            color = self.BG_COLOR
            if hovered:
                color = self.BORDER_HOVER_COLOR

            outline_color = self.BORDER_HOVER_COLOR
            if hovered:
                outline_color = self.PINK_COLOR

            cv2.fillPoly(canvas, [pts], color)
            cv2.polylines(canvas, [pts], isClosed=True, color=outline_color, thickness=2)

            x1 = np.min(pts[:, 0])
            y1 = np.min(pts[:, 1])
            x2 = np.max(pts[:, 0])
            y2 = np.max(pts[:, 1])

            self.button_regions.append(((x1, y1, x2, y2), action))

        controls = [
            ("Change model", "mesh"),
            ("Choose pattern", "pattern"),
            (f"{self.light_button_label} light", "light_toggle"),
        ]

        control_w = 170
        control_h = 45
        control_gap_x = 10
        control_gap_y = 10
        control_cols = 2
        controls_start_y = compass_cy + compass_radius + 50

        for i, (label, action) in enumerate(controls):
            row = i // control_cols
            col = i % control_cols
            total_row_width = (control_cols * control_w + (control_cols - 1) * control_gap_x)
            start_x_controls = (panel_x0 + (panel_width - total_row_width) // 2)
            x0 = start_x_controls + col * (control_w + control_gap_x)
            y0 = controls_start_y + row * (control_h + control_gap_y)
            rect = (x0, y0, x0 + control_w, y0 + control_h)
            hovered = ((rect[0] <= self.mouse_x <= rect[2]) and (rect[1] <= self.mouse_y <= rect[3]))

            color = self.BG_COLOR
            if hovered:
                color = self.BORDER_HOVER_COLOR

            cv2.rectangle(canvas, (rect[0], rect[1]), (rect[2], rect[3]), color, -1)
            cv2.putText(canvas, label, (x0 + 10, y0 + 28), self.FONT, 0.5, self.TEXT_COLOR, 1, cv2.LINE_AA)
            self.button_regions.append((rect, action))

        total_patch_width = cols * patch_w + (cols - 1) * patch_gap
        start_x_patches = panel_x0 + (panel_width - total_patch_width) // 2
        y_start_patches = controls_start_y + 2 * (control_h + control_gap_y) + 20

        for i, (name, label) in enumerate(patches):
            col = i % cols
            row = i // cols
            x0 = start_x_patches + col * (patch_w + patch_gap)
            y0 = y_start_patches + row * (patch_h + patch_gap)
            rect = (x0, y0, x0 + patch_w, y0 + patch_h)

            hovered = rect[0] <= self.mouse_x <= rect[2] and rect[1] <= self.mouse_y <= rect[3]
            color = self.BG_COLOR
            if hovered:
                color = self.BORDER_HOVER_COLOR

            cv2.rectangle(canvas, (rect[0], rect[1]), (rect[2], rect[3]), color, -1)

            if (name == self.current_patch):
                cv2.rectangle(canvas, (x0, y0), (x0 + patch_w, y0 + patch_h), self.PINK_COLOR, 2)

            if (name in self.patch_icons):
                icon = self.patch_icons[name]
                ih, iw = icon.shape[:2]
                icon_x = x0 + (patch_w - iw) // 2
                icon_y = y0 + 10

                self.overlay_image(canvas, icon, icon_x, icon_y)

            (text_w, text_h), _ = cv2.getTextSize(label, self.FONT, 0.5, 1)
            text_x = x0 + (patch_w - text_w) // 2
            text_y = y0 + patch_h - 15
            cv2.putText(canvas, label, (text_x, text_y), self.FONT, 0.5, self.TEXT_COLOR, 1, cv2.LINE_AA)
            self.button_regions.append((rect, f"patch_{name}"))

    # ------------------------------------------------------------------
    def handle_ui_action(self, action):
        render_needed = False

        if (action == "mesh"):
            path = self.pick_file('ply', 'meshes')
            if path:
                self.update_mesh(path)
            else:
                return
            render_needed = True

        elif (action == "pattern"):
            path = self.pick_file('png', 'textures')
            if path:
                self.update_pattern(path)
            else:
                return
            render_needed = True

        elif (action == "light_toggle"):
            if (self.light_mode == "directional"):
                self.update_light("point")
                self.light_mode = "point"
                self.light_button_label = "Directional"
            else:
                self.update_light("light")
                self.light_mode = "directional"
                self.light_button_label = "Point"
            render_needed = True

        elif (action == "rotate_left"):
            self.v_coord += 0.25
            if (self.v_coord > 1.0):
                self.v_coord -= 1.0
            render_needed = True

        elif (action == "rotate_right"):
            self.v_coord -= 0.25
            if (self.v_coord < 0.0):
                self.v_coord += 1.0
            render_needed = True

        elif action == "rotate_up":
            self.u_coord -= 0.25
            if (self.u_coord < 0.0):
                self.u_coord += 1.0
            render_needed = True

        elif action == "rotate_down":
            self.u_coord += 0.25
            if (self.u_coord > 1.0):
                self.u_coord -= 1.0
            render_needed = True

        elif (action == "patch_plush"):
            self.update_patch("plush")
            self.current_patch = "plush"
            render_needed = True

        elif (action == "patch_fur"):
            self.update_patch("fur")
            self.current_patch = "fur"
            render_needed = True

        elif (action == "patch_pinkfur"):
            self.update_patch("pinkfur")
            self.current_patch = "pinkfur"
            render_needed = True

        elif (action == "patch_carpet"):
            self.update_patch("carpet")
            self.current_patch = "carpet"
            render_needed = True

        elif (action == "patch_grass"):
            self.update_patch("grass")
            self.current_patch = "grass"
            render_needed = True

        elif (action == "patch_curls"):
            self.update_patch("curls")
            self.current_patch = "curls"
            render_needed = True

        elif (action == "patch_orangefur"):
            self.update_patch("orangefur")
            self.current_patch = "orangefur"
            render_needed = True

        elif (action == "menu_file"):
            self.menu_open = not self.menu_open

        elif (action == "save_config"):
            self.save_config()
            print("Saved config")

        elif (action == "save_image"):
            img = self.load_image()
            if img is not None:
                cv2.imwrite("saved_image.png", img)
                print("Saved image")

        elif (action == "exit_app"):
            self.reset_runtime_config()
            exit()

        elif (action == "menu_color_mode"):
            self.dark_mode = not self.dark_mode
            self.change_color_mode()

        self.needs_render = render_needed
        if self.needs_render:
            self.zoom = 1.0
            self.crop_x = 0
            self.crop_y = 0
            self.update_camera()

    # ------------------------------------------------------------------
    def mouse_callback(self, event, x, y, flags, param):
        if (event == cv2.EVENT_MOUSEMOVE):
            self.mouse_x, self.mouse_y = x, y

            if self.dragging:
                dx = x - self.last_x
                dy = y - self.last_y

                self.u_coord += dx / self.WINDOW_W * 1.5
                self.v_coord += dy / self.WINDOW_H * 1.5
                self.v_coord = max(0.05, min(0.95, self.v_coord))

                self.last_x, self.last_y = x, y

            if (self.zoom_dragging and self.zoom_slider_rect):
                x1, _, x2, _, _, _, _, _ = self.zoom_slider_rect
                self.update_zoom_from_mouse(x1, x2, x)

        # -------------------------
        elif (event == cv2.EVENT_LBUTTONDOWN):
            self.dragging = False

            for (x1, y1, x2, y2), action in getattr(self, "button_regions", []):
                if ((x1 <= x <= x2) and (y1 <= y <= y2)):
                    self.handle_ui_action(action)
                    return

            self.menu_open = False
            regions = self.get_regions()

            if ("image" in regions):
                image_region = regions["image"]

                if ((image_region["x0"] <= x <= image_region["x1"]) and (image_region["y0"] <= y <= image_region["y1"])):
                    self.dragging = True
                    self.last_x, self.last_y = x, y

            if self.zoom_slider_rect:
                x1, y1, x2, y2, minus_rect, plus_rect, _, _ = self.zoom_slider_rect

                if ((x1 <= x <= x2) and (y1 <= y <= y2)):
                    self.zoom_dragging = True
                    self.update_zoom_from_mouse(x1, x2, x)
                    return

        # -------------------------
        elif (event == cv2.EVENT_LBUTTONUP):
            if self.dragging:
                self.needs_render = True

            self.dragging = False
            self.zoom_dragging = False

    # ------------------------------------------------------------------
    def build_ui(self, img):
        canvas = np.full((self.WINDOW_H, self.WINDOW_W, 3), self.BG_COLOR, dtype = np.uint8)

        if (img is None):
            print("ERROR: No rendered image found!")
            return canvas

        img_h, img_w = img.shape[:2]
        panel_width = self.WINDOW_W // 3
        view_w = img_w
        view_h = img_h
        available_w = self.WINDOW_W - panel_width
        x0 = (available_w - view_w) // 2
        y0 = (self.WINDOW_H - view_h) // 2
        zoom_w = int(img_w / self.zoom)
        zoom_h = int(img_h / self.zoom)

        self.crop_x = max(0, min(self.crop_x, (img_w - zoom_w)))
        self.crop_y = max(0, min(self.crop_y, (img_h - zoom_h)))
        cropped = img[self.crop_y:(self.crop_y + zoom_h), self.crop_x:(self.crop_x + zoom_w)]
        display = cv2.resize(cropped, (view_w, view_h))
        self.overlay_image(canvas, display, x0, y0)

        cv2.rectangle(canvas, ((x0 - 2), (y0 - 2)), ((x0 + img_w + 2), (y0 + img_h + 2)), self.BORDER_HOVER_COLOR, 2)

        slider_x = x0 + (view_w - 500) // 2
        slider_y = y0 + img_h + 60
        self.draw_zoom_slider(canvas, slider_x, slider_y)

        if self.needs_render:
            text = "...RENDERING CHANGES..."
            (tw, th), _ = cv2.getTextSize(text, self.FONT, 0.6, 2)
            text_x = x0 + (view_w - tw) // 2
            text_y = slider_y + 55
            cv2.putText(canvas, text, (text_x, text_y), self.FONT, 0.6, self.PINK_COLOR, 1, cv2.LINE_AA)

        panel_width = self.WINDOW_W // 3
        panel_x0 = self.WINDOW_W - panel_width
        panel_x1 = self.WINDOW_W
        cv2.rectangle(canvas, (panel_x0, 0), (panel_x1, self.WINDOW_H), self.PANEL_COLOR, -1)

        self.draw_buttons(canvas, panel_x0, panel_width)
        self.draw_top_menu(canvas)

        return canvas

    # ------------------------------------------------------------------
    # Changes back to default config 
    def reset_runtime_config(self):
        shutil.copy(self.CONFIG_PATH, self.RUNTIME_CONFIG_PATH)

    # ------------------------------------------------------------------
    def run(self):
        img = self.load_image(default=True)
        
        if (img is None):
            print("ERROR: No rendered image found!")
            return

        img_h, img_w = img.shape[:2]
        zoom_w = int(img_w / self.zoom)
        zoom_h = int(img_h / self.zoom)
        self.center_crop(img_w, img_h, zoom_w, zoom_h)

        while True:
            canvas = self.build_ui(img)
            cv2.imshow(self.WINDOW_NAME, canvas)

            key = cv2.waitKey(1)
            step = 10  
            if (key == 27): 
                self.reset_runtime_config()
                break

            elif (key in [81, 2424832]):
                self.crop_x -= step

            elif (key in [83, 2555904]):
                self.crop_x += step

            elif (key in [82, 2490368]):
                self.crop_y -= step

            elif (key in [84, 2621440]):
                self.crop_y += step

            key = cv2.waitKey(1)

            if self.needs_render:
                self.update_camera()
                self.save_config()
                render_canvas = self.build_ui(img)
                cv2.imshow(self.WINDOW_NAME, render_canvas)
                cv2.waitKey(1)
                self.run_render()
                self.needs_render = False
                img = self.load_image()

                if (img is None):
                    print("ERROR: No rendered image found!")

        cv2.destroyAllWindows()

# ----------------------------------------------------------------------
if __name__ == "__main__":
    viewer = NerfViewer()
    viewer.run()
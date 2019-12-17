
import time
import logging

from kivy.app import App
from kivy.animation import Animation
from kivy import platform
from kivy.lang import Builder
from kivy.event import EventDispatcher
from kivy.properties import (
    ObjectProperty, StringProperty, ListProperty, BooleanProperty, NumericProperty)
from kivy.graphics.texture import Texture
from kivy.graphics import Fbo, Callback, Rectangle
from kivy.clock import Clock
from kivy.uix.widget import Widget
from kivy.uix.stencilview import StencilView
from kivy.uix.floatlayout import FloatLayout

from colourswidget import ColourShaderWidget
from widgets import ColouredToggleButtonContainer

logger = logging.getLogger(__file__)
logger.setLevel(logging.DEBUG)
handler = logging.StreamHandler()
handler.setLevel(logging.DEBUG)
logger.addHandler(handler)

if platform == "android":
    from camera2 import PyCameraInterface

class ColourBlindnessSelectionButton(ColouredToggleButtonContainer):
    has_red = BooleanProperty(True)
    has_green = BooleanProperty(True)
    has_blue = BooleanProperty(True)
    text = StringProperty()
    texture_size = ListProperty([0, 0])

class RootLayout(FloatLayout):
    buttons_visible = BooleanProperty(True)

    _buttons_visible_fraction = NumericProperty(1.0)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.anim_to_1 = Animation(_buttons_visible_fraction=1.0, duration=0.5)
        self.anim_to_0 = Animation(_buttons_visible_fraction=0.0, duration=0.5)

    def hide_buttons(self):
        self.buttons_visible = False

    def show_buttons(self):
        self.buttons_visible = True

    def on_touch_down(self, touch):
        if self.ids.buttons_dropdown.collide_point(*touch.pos):
            return self.ids.buttons_dropdown.on_touch_down(touch)

        touch.ud["show_buttons"] = True

    def on_touch_up(self, touch):
        if touch.ud.get("show_buttons", False):
            self.buttons_visible = True
        return super().on_touch_up(touch)

    def on_buttons_visible(self, instance, value):
        Animation.cancel_all(self, "_buttons_visible_fraction")
        Animation(_buttons_visible_fraction=value, duration=0.55, t="out_cubic").start(self)

class CameraDisplayWidget(StencilView):
    texture = ObjectProperty(None, allownone=True)

    resolution = ListProperty([1, 1])

    tex_coords = ListProperty([0.0, 0.0, 1.0, 0.0, 1.0, 1.0, 0.0, 1.0])
    correct_camera = BooleanProperty(False)

    _rect_pos = ListProperty([0, 0])
    _rect_size = ListProperty([1, 1])

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.bind(
            pos=self._update_rect,
            size=self._update_rect,
            resolution=self._update_rect,
        )

    def on_correct_camera(self, instance, correct):
        print("Correct became", correct)
        if correct:
            self.tex_coords = [1.0, 0.0, 0.0, 0.0, 0.0, 1.0, 1.0, 1.0]
            print("Set 0!")
        else:
            self.tex_coords = [0.0, 0.0, 1.0, 0.0, 1.0, 1.0, 0.0, 1.0]
            print("Set 1!")

    def on_tex_coords(self, instance, value):
        print("tex_coords became", self.tex_coords)

    def _update_rect(self, *args):
        self._update_rect_to_fill()

    def _update_rect_to_fit(self, *args):
        w, h = self.resolution
        aspect_ratio = h / w

        aspect_width = self.width
        aspect_height = self.width * h / w
        if aspect_height > self.height:
            aspect_height = self.height
            aspect_width = aspect_height * w / h

        aspect_height = int(aspect_height)
        aspect_width = int(aspect_width)

        self._rect_pos = [self.center_x - aspect_width / 2,
                          self.center_y - aspect_height / 2]

        self._rect_size = [aspect_width, aspect_height]

    def _update_rect_to_fill(self, *args):
        w, h = self.resolution

        aspect_ratio = h / w

        aspect_width = self.width
        aspect_height = self.width * h / w
        if aspect_height < self.height:
            aspect_height = self.height
            aspect_width = aspect_height * w / h

        aspect_height = int(aspect_height)
        aspect_width = int(aspect_width)

        self._rect_pos = [self.center_x - aspect_width / 2,
                          self.center_y - aspect_height / 2]

        self._rect_size = [aspect_width, aspect_height]

class CameraApp(App):
    texture = ObjectProperty(None, allownone=True)
    camera_resolution = ListProperty([1920, 1080])

    current_camera = ObjectProperty(None, allownone=True)

    cameras_to_use = ListProperty()

    def build(self):
        Builder.load_file("androidcamera.kv")

        root = RootLayout()

        self.camera_interface = PyCameraInterface()

        Clock.schedule_interval(self.update, 0)

        self.debug_print_camera_info()

        self.inspect_cameras()

        self.restart_stream()

        return root

    def inspect_cameras(self):
        cameras = self.camera_interface.cameras

        for camera in cameras:
            if camera.facing == "BACK":
                self.cameras_to_use.append(camera)
        for camera in cameras:
            if camera.facing == "FRONT":
                self.cameras_to_use.append(camera)

    def rotate_cameras(self):
        self.ensure_camera_closed()
        self.cameras_to_use = self.cameras_to_use[1:] + [self.cameras_to_use[0]]
        self.stream_camera(self.cameras_to_use[0])

    def restart_stream(self):
        self.ensure_camera_closed()
        Clock.schedule_once(self._restart_stream, 0)

    def _restart_stream(self, dt):
        self.stream_camera(self.cameras_to_use[0])

    def debug_print_camera_info(self):
        cameras = self.camera_interface.cameras
        camera_infos = ["Camera ID {}, facing {}".format(c.camera_id, c.facing) for c in cameras]
        for camera in cameras:
            print("Camera ID {}, facing {}, resolutions {}".format(
                camera.camera_id, camera.facing, camera.supported_resolutions))

    def stream_camera_index(self, index):
        self.stream_camera(self.camera_interface.cameras[index])

    def stream_camera(self, camera):
        resolution = (1920, 1080)
        self.camera_resolution = resolution
        camera.open()
        time.sleep(0.5)
        if camera.facing == "FRONT":
            self.root.ids.cdw.correct_camera = True
        else:
            self.root.ids.cdw.correct_camera = False
        self.texture = camera.start_preview(resolution)

        self.current_camera = camera

    def on_texture(self, instance, value):
        print("App texture changed to {}".format(value))

    def update(self, dt):
        self.root.canvas.ask_update()

    def ensure_camera_closed(self):
        if self.current_camera is not None:
            self.current_camera.close()
            self.current_camera = None

    def on_pause(self):

        logger.info("Closing camera due to pause")
        self.ensure_camera_closed()

        return super().on_pause()

    def on_resume(self):
        logger.info("Opening camera due to resume")
        self.restart_stream()


if __name__ == "__main__":
    CameraApp().run()

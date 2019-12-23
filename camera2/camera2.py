from kivy.event import EventDispatcher
from kivy.graphics.texture import Texture
from kivy.graphics import Fbo, Callback, Rectangle
from kivy.properties import (BooleanProperty, StringProperty, ObjectProperty, OptionProperty, ListProperty)
from kivy.clock import Clock

from jnius import autoclass, cast, PythonJavaClass, java_method, JavaClass, MetaJavaClass, JavaMethod

import logging
from enum import Enum

logger = logging.getLogger(__file__)
logger.setLevel(logging.DEBUG)
handler = logging.StreamHandler()
handler.setLevel(logging.DEBUG)
logger.addHandler(handler)

CameraManager = autoclass("android.hardware.camera2.CameraManager")
PythonActivity = autoclass("org.kivy.android.PythonActivity")
Context = autoclass("android.content.Context")
context = cast("android.content.Context", PythonActivity.mActivity)

CameraDevice = autoclass("android.hardware.camera2.CameraDevice")
CaptureRequest = autoclass("android.hardware.camera2.CaptureRequest")
CameraCharacteristics = autoclass("android.hardware.camera2.CameraCharacteristics")

ArrayList = autoclass('java.util.ArrayList')
JavaArray = autoclass('java.lang.reflect.Array')

SurfaceTexture = autoclass('android.graphics.SurfaceTexture')
Surface = autoclass('android.view.Surface')
GL_TEXTURE_EXTERNAL_OES = autoclass(
    'android.opengl.GLES11Ext').GL_TEXTURE_EXTERNAL_OES
ImageFormat = autoclass('android.graphics.ImageFormat')

Handler = autoclass("android.os.Handler")
Looper = autoclass("android.os.Looper")

MyStateCallback = autoclass("net.inclem.camera2.MyStateCallback")
CameraActions = autoclass("net.inclem.camera2.MyStateCallback$CameraActions")
# MyStateCallback = autoclass("org.kivy.android.MyStateCallback")

MyCaptureSessionCallback = autoclass("net.inclem.camera2.MyCaptureSessionCallback")
CameraCaptureEvents = autoclass("net.inclem.camera2.MyCaptureSessionCallback$CameraCaptureEvents")

_global_handler = Handler(Looper.getMainLooper())

class LensFacing(Enum):
    """Values copied from CameraCharacteristics api doc, as pyjnius
    lookup doesn't work on some devices.
    """
    LENS_FACING_FRONT = 0
    LENS_FACING_BACK = 1
    LENS_FACING_EXTERNAL = 2

class ControlAfMode(Enum):
    CONTROL_AF_MODE_CONTINUOUS_PICTURE = 4

class ControlAeMode(Enum):
    CONTROL_AE_MODE_ON = 1

class Runnable(PythonJavaClass):
    __javainterfaces__ = ['java/lang/Runnable']

    def __init__(self, func):
        super(Runnable, self).__init__()
        self.func = func

    @java_method('()V')
    def run(self):
        try:
            self.func()
        except:
            import traceback
            traceback.print_exc()


class PyCameraInterface(EventDispatcher):
    """
    Provides an API for querying details of the cameras available on Android.
    """

    camera_ids = []

    cameras = ListProperty()

    java_camera_characteristics = {}

    java_camera_manager = ObjectProperty()

    def __init__(self):
        super().__init__()
        logger.info("Starting camera interface init")
        self.java_camera_manager = cast("android.hardware.camera2.CameraManager",
                                    context.getSystemService(Context.CAMERA_SERVICE))

        self.camera_ids = self.java_camera_manager.getCameraIdList()
        characteristics_dict = self.java_camera_characteristics
        camera_manager = self.java_camera_manager
        logger.info("Got basic java objects")
        for camera_id in self.camera_ids:
            logger.info(f"Getting data for camera {camera_id}")
            characteristics_dict[camera_id] = camera_manager.getCameraCharacteristics(camera_id)
            logger.info("Got characteristics dict")

            self.cameras.append(PyCameraDevice(
                camera_id=camera_id,
                java_camera_manager=camera_manager,
                java_camera_characteristics=characteristics_dict[camera_id],
            ))
            logger.info(f"Finished interpreting camera {camera_id}")

    def select_cameras(self, **conditions):
        options = self.cameras
        outputs = []
        for camera in cameras:
            for key, value in conditions.items():
                if getattr(camera, key) != value:
                    break
            else:
                outputs.append(camera)

        return outputs

class PyCameraDevice(EventDispatcher):

    camera_id = StringProperty()

    output_texture = ObjectProperty(None, allownone=True)

    preview_active = BooleanProperty(False)
    preview_texture = ObjectProperty(None, allownone=True)
    preview_resolution = ListProperty()
    preview_fbo = ObjectProperty(None, allownone=True)
    java_preview_surface_texture = ObjectProperty(None)
    java_preview_surface = ObjectProperty(None)
    java_capture_request = ObjectProperty(None)
    java_surface_list = ObjectProperty(None)
    java_capture_session = ObjectProperty(None)

    connected = BooleanProperty(False)

    supported_resolutions = ListProperty()
    # TODO: populate this

    facing = OptionProperty("UNKNOWN", options=["UNKNOWN", "FRONT", "BACK", "EXTERNAL"])

    java_camera_characteristics = ObjectProperty()
    java_camera_manager = ObjectProperty()
    java_camera_device = ObjectProperty()
    java_stream_configuration_map = ObjectProperty()

    _open_callback = ObjectProperty(None, allownone=True)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.register_event_type("on_opened")
        self.register_event_type("on_closed")
        self.register_event_type("on_disconnected")
        self.register_event_type("on_error")

        self._java_state_callback_runnable = Runnable(self._java_state_callback)
        self._java_state_java_callback = MyStateCallback(self._java_state_callback_runnable)

        self._java_capture_session_callback_runnable = Runnable(self._java_capture_session_callback)
        self._java_capture_session_java_callback = MyCaptureSessionCallback(
            self._java_capture_session_callback_runnable)

        self._populate_camera_characteristics()

    def on_opened(self, instance):
        pass
    def on_closed(self, instance):
        pass
    def on_disconnected(self, instance):
        pass
    def on_error(self, instance, error):
        pass

    def close(self):
        self.java_camera_device.close()

    def _populate_camera_characteristics(self):
        logger.info("Populating camera characteristics")
        self.java_stream_configuration_map = self.java_camera_characteristics.get(
            CameraCharacteristics.SCALER_STREAM_CONFIGURATION_MAP)
        logger.info("Got stream configuration map")

        self.supported_resolutions = [
            (size.getWidth(), size.getHeight()) for size in
            self.java_stream_configuration_map.getOutputSizes(SurfaceTexture(0).getClass())]
        logger.info("Got supported resolutions")

        facing = self.java_camera_characteristics.get(
            CameraCharacteristics.LENS_FACING)
        logger.info(f"Got facing: {facing}")
        if facing == LensFacing.LENS_FACING_BACK.value:  # CameraCharacteristics.LENS_FACING_BACK:
            self.facing = "BACK"
        elif facing == LensFacing.LENS_FACING_FRONT.value:  # CameraCharacteristics.LENS_FACING_FRONT:
            self.facing = "FRONT"
        elif facing == LensFacing.LENS_FACING_EXTERNAL.value:  # CameraCharacteristics.LENS_FACING_EXTERNAL:
            self.facing = "EXTERNAL"
        else:
            raise ValueError("Camera id {} LENS_FACING is unknown value {}".format(self.camera_id, facing))
        logger.info(f"Finished initing camera {self.camera_id}")

    def __str__(self):
        return "<PyCameraDevice facing={}>".format(self.facing)
    def __repr__(self):
        return str(self)

    def open(self, callback=None):
        self._open_callback = callback
        self.java_camera_manager.openCamera(
            self.camera_id,
            self._java_state_java_callback,
            _global_handler
        )

    def _java_state_callback(self, *args, **kwargs):
        action = MyStateCallback.camera_action.toString()
        camera_device = MyStateCallback.camera_device

        self.java_camera_device = camera_device

        logger.info("CALLBACK: camera event {}".format(action))
        if action == "OPENED":
            self.dispatch("on_opened", self)
            self.connected = True
        elif action == "DISCONNECTED":
            self.dispatch("on_disconnected", self)
            self.connected = False
        elif action == "CLOSED":
            self.dispatch("on_closed", self)
            self.connected = False
        elif action == "ERROR":
            error = MyStateCallback.camera_error
            self.dispatch("on_error", self, error)
            self.connected = False
        elif action == "UNKNOWN":
            print("UNKNOWN camera state callback item")
            self.connected = False
        else:
            raise ValueError("Received unknown camera action {}".format(action))

        if self._open_callback is not None:
            self._open_callback(self, action)

    def start_preview(self, resolution):
        if self.java_camera_device is None:
            raise ValueError("Camera device not yet opened, cannot create preview stream")

        if resolution not in self.supported_resolutions:
            raise ValueError(
                "Tried to open preview with resolution {}, not in supported resolutions {}".format(
                    resolution, self.supported_resolutions))

        if self.preview_active:
            raise ValueError("Preview already active, can't start again without stopping first")

        logger.info("Creating capture stream with resolution {}".format(resolution))

        self.preview_resolution = resolution
        self._prepare_preview_fbo(resolution)
        self.preview_texture = Texture(
            width=resolution[0], height=resolution[1], target=GL_TEXTURE_EXTERNAL_OES, colorfmt="rgba")
        logger.info("Texture id is {}".format(self.preview_texture.id))
        self.java_preview_surface_texture = SurfaceTexture(int(self.preview_texture.id))
        self.java_preview_surface_texture.setDefaultBufferSize(*resolution)
        self.java_preview_surface = Surface(self.java_preview_surface_texture)

        self.java_capture_request = self.java_camera_device.createCaptureRequest(CameraDevice.TEMPLATE_PREVIEW)
        self.java_capture_request.addTarget(self.java_preview_surface)
        self.java_capture_request.set(
            CaptureRequest.CONTROL_AF_MODE, ControlAfMode.CONTROL_AF_MODE_CONTINUOUS_PICTURE.value)  # CaptureRequest.CONTROL_AF_MODE_CONTINUOUS_PICTURE)
        self.java_capture_request.set(
            CaptureRequest.CONTROL_AE_MODE, ControlAeMode.CONTROL_AE_MODE_ON.value)  # CaptureRequest.CONTROL_AE_MODE_ON)

        self.java_surface_list = ArrayList()
        self.java_surface_list.add(self.java_preview_surface)

        self.java_camera_device.createCaptureSession(
            self.java_surface_list,
            self._java_capture_session_java_callback,
            _global_handler,
        )

        return self.preview_fbo.texture

    def _prepare_preview_fbo(self, resolution):
        self.preview_fbo = Fbo(size=resolution)
        self.preview_fbo['resolution'] = [float(f) for f in resolution]
        self.preview_fbo.shader.fs = """
            #extension GL_OES_EGL_image_external : require
            #ifdef GL_ES
                precision highp float;
            #endif

            /* Outputs from the vertex shader */
            varying vec4 frag_color;
            varying vec2 tex_coord0;

            /* uniform texture samplers */
            uniform sampler2D texture0;
            uniform samplerExternalOES texture1;
            uniform vec2 resolution;

            void main()
            {
                gl_FragColor = texture2D(texture1, tex_coord0);
            }
        """
        with self.preview_fbo:
            Rectangle(size=resolution)

    def _java_capture_session_callback(self, *args, **kwargs):
        event = MyCaptureSessionCallback.camera_capture_event.toString()
        logger.info("CALLBACK: capture event {}".format(event))

        self.java_capture_session = MyCaptureSessionCallback.camera_capture_session

        if event == "READY":
            logger.info("Doing READY actions")
            self.java_capture_session.setRepeatingRequest(self.java_capture_request.build(), None, None)
            Clock.schedule_interval(self._update_preview, 0.)

    def _update_preview(self, dt):
        self.java_preview_surface_texture.updateTexImage()
        self.preview_fbo.ask_update()
        self.preview_fbo.draw()
        self.output_texture = self.preview_fbo.texture

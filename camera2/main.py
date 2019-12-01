
from kivy.app import App
from kivy import platform
from kivy.lang import Builder
from kivy.event import EventDispatcher
from kivy.properties import (ObjectProperty, StringProperty, ListProperty)
from kivy.graphics.texture import Texture
from kivy.graphics import Fbo, Callback, Rectangle
from kivy.clock import Clock

if platform == "android":
    from jnius import autoclass, cast, PythonJavaClass, java_method, JavaClass, MetaJavaClass, JavaMethod
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


# class StateCallback(JavaClass, metaclass=MetaJavaClass):
#     __javaclass__ = "android/hardware/camera2/CameraDevice.StateCallback"
#     # __metaclass__ = MetaJavaClass  # py2


#     def __init__(self, callback):
#         super(StateCallback, self).__init__()
#         self._callback = callback

#     @java_method("(Landroid/hardware/camera2/CameraDevice;)V")
#     def onClosed(self, camera_device):
#         print("Closed {}".format(camera_device))
#         self.camera_device = None

#     @java_method("(Landroid/hardware/camera2/CameraDevice;)V")
#     def onDisconnected(self, camera_device):
#         print("Disconnected {}".format(camera_device))
#         pass

#     @java_method("(Landroid/hardware/camera2/CameraDevice;I)V")
#     def onOpened(self, camera_device, error_code):
#         print("Opened {}".format(camera_device))
#         self.camera_device = camera_device
#         self._callback(self.camera_device)

#     @java_method("(Landroid/hardware/camera2/CameraDevice;)V")
#     def onError(self, camera_device):
#         print("Error {}".format(camera_device))
#         pass


class AndroidCamera2(EventDispatcher):
    camera_device = ObjectProperty(None, allownone=True)

    preview_surface_texture = ObjectProperty(None, allownone=True)
    preview_surface = ObjectProperty(None, allownone=True)
    preview_texture = ObjectProperty(None, allownone=True)

    texture = ObjectProperty(None, allownone=True)

    def __init__(self):
        super().__init__()
        self.camera_device = None

        self.camera_manager = cast("android.hardware.camera2.CameraManager",
                                    context.getSystemService(Context.CAMERA_SERVICE))

        self.handler = Handler(Looper.getMainLooper())

        self.state_runnable = Runnable(self.state_callback)
        self.state_callback = MyStateCallback(self.state_runnable)

        self.capture_session_runnable = Runnable(self.capture_session_callback_method)
        self.capture_session_callback = MyCaptureSessionCallback(self.capture_session_runnable)

        self.resolution = (1920, 1080)

        width, height = self.resolution
        self.preview_texture = Texture(
            width=width, height=height, target=GL_TEXTURE_EXTERNAL_OES, colorfmt="rgba")

        self.prepare_texture()

    def prepare_texture(self):
        self.fbo = Fbo(size=self.resolution)
        self.fbo['resolution'] = [float(f) for f in self.resolution]
        self.fbo.shader.fs = """
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
                vec2 coord = vec2(
                    tex_coord0.y * (resolution.y / resolution.x),
                    1. -tex_coord0.x
                    );
                gl_FragColor = texture2D(texture1, tex_coord0);
            }
        """
        with self.fbo:
            Rectangle(size=self.resolution)

    def update(self, dt):
        self.preview_surface_texture.updateTexImage()
        self.fbo.ask_update()
        self.fbo.draw()
        self.texture = self.fbo.texture

    def on_texture(self, *args):
        App.get_running_app().texture = self.texture

    def state_callback(self, *args, **kwargs):
        # print("test callback called with args {} kwargs {}".format(args, kwargs))
        # print("MyStateCallback.camera_device is {}".format(MyStateCallback.camera_device))
        # print("action is", MyStateCallback.camera_action)
        # print("error is", MyStateCallback.camera_error)

        action = MyStateCallback.camera_action.toString()
        camera_device = MyStateCallback.camera_device
        self.camera_device = camera_device
        if action == "OPENED":
            self.callback_camera_opened(camera_device)
        elif action == "DISCONNECTED":
            self.callback_camera_disconnected(camera_device)
        elif action == "CLOSED":
            self.callback_camera_closed(camera_device)
        elif action == "ERROR":
            error = MyStateCallback.camera_error
            self.callback_camera_error(camera_device, error)
        elif action == "UNKNOWN":
            self.callback_camera_opened(camera_device)
        else:
            print('COULD NOT RECOGNISE CAMERA_ACTION', action)

    def capture_session_callback_method(self, *args, **kwargs):
        print("MyCaptureSessionCallback: event is {}".format(
            MyCaptureSessionCallback.camera_capture_event.toString()))

        if MyCaptureSessionCallback.camera_capture_event.toString() == "READY":
            print("Starting update")

            self.the_capture_session = MyCaptureSessionCallback.camera_capture_session
            self.the_capture_session.setRepeatingRequest(self.capture_request.build(), None, None)

            Clock.schedule_interval(self.update, 1./30.)

    def callback_camera_opened(self, camera_device):
        print('Opened callback', camera_device)

    def callback_camera_closed(self, camera_device):
        print('Closed callback', camera_device)
        self.camera_device = None

    def callback_camera_error(self, camera_device, error):
        print('Error callback', camera_device, error)
        self.camera_device = None

    def callback_camera_disconnected(self, camera_device):
        print('Disconnected callback', camera_device)
        self.camera_device = None

    def camera_ids(self):
        return self.camera_manager.getCameraIdList()

    def get_characteristics(self, camera_id):
        characteristics = self.camera_manager.getCameraCharacteristics(camera_id)
        return characteristics

    def open_camera(self, index):
        camera_id = self.camera_ids()[index]

        self.characteristics = self.get_characteristics(camera_id)

        self.camera_manager.openCamera(camera_id, self.state_callback, self.handler)

    def create_preview_stream(self):
        if self.camera_device is None:
            raise ValueError("Cannot open preview without a camera opened")

        if self.preview_surface_texture is not None:
            raise ValueError("Cannot open preview, a preview surface already exists")


        self.preview_surface_texture = SurfaceTexture(int(self.preview_texture.id))
        self.preview_surface_texture.setDefaultBufferSize(*self.resolution)

        self.stream_configuration_map = self.characteristics.get(CameraCharacteristics.SCALER_STREAM_CONFIGURATION_MAP)

        print("output sizes are",
              [(size.getWidth(), size.getHeight()) for size in self.stream_configuration_map.getOutputSizes(self.preview_surface_texture.getClass())])

        self.preview_surface = Surface(self.preview_surface_texture)

        self.capture_request = self.camera_device.createCaptureRequest(CameraDevice.TEMPLATE_PREVIEW)
        self.capture_request.addTarget(self.preview_surface)
        self.capture_request.set(CaptureRequest.CONTROL_AF_MODE, CaptureRequest.CONTROL_AF_MODE_CONTINUOUS_PICTURE)
        self.capture_request.set(CaptureRequest.CONTROL_AE_MODE, CaptureRequest.CONTROL_AE_MODE_ON)

        self.surface_list = ArrayList()
        self.surface_list.add(self.preview_surface)
        self.camera_device.createCaptureSession(
            self.surface_list,
            self.capture_session_callback,
            self.handler)




class CameraApp(App):
    texture = ObjectProperty(None, allownone=True)
    def build(self):
        if platform == "android":
            root = Builder.load_file("androidcamera.kv")

            self.camera_interface = AndroidCamera2()

            Clock.schedule_interval(self.update, 0)

            return root

    def print_camera_info(self):
        camera_ids = self.camera_interface.camera_ids()
        print("ids are", camera_ids, type(camera_ids))

        for camera_id in camera_ids:
            characteristics = self.camera_interface.get_characteristics(camera_id)
            print("Camera id {} characteristics are {}".format(camera_id, characteristics.getKeys()))

    def open_camera(self, index):
        self.camera_interface.open_camera(index)

    def create_preview_stream(self):
        if self.camera_interface.camera_device is None:
            self.camera_interface.open_camera(0)
        self.camera_interface.create_preview_stream()

    def update(self, dt):
        self.root.canvas.ask_update()


if __name__ == "__main__":
    CameraApp().run()

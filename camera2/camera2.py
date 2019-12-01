from kivy.event import EventDispatcher

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


class PyCameraInterface(object):
    """
    Provides an API for querying details of the cameras available on Android.
    """

    camera_ids = []

    camera_characteristics = {}

    java_camera_manager = ObjectProperty()

class PyCameraDevice(EventDispatcher):

    texture = ObjectProperty(None, allownone=True)
    """
    Texture holding the current drawing output of the camera, if any.
    """

    characteristics = ObjectProperty()

    java_camera_manager = ObjectProperty()

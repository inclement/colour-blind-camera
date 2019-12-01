
package net.inclem.camera2;

import android.hardware.camera2.CameraCaptureSession;
import java.lang.Runnable;
import android.util.Log;
import android.view.Surface;


public class MyCaptureSessionCallback extends CameraCaptureSession.StateCallback {
	private static final String TAG = "pythonMyCaptureSessionCallback";

    Runnable callback;

    public enum CameraCaptureEvents {
        ACTIVE,
        CAPTURE_QUEUE_EMPTY,
        CLOSED,
        CONFIGURE_FAILED,
        CONFIGURED,
        READY,
        SURFACE_PREPARED,
        UNKNOWN
    }

    public static CameraCaptureSession camera_capture_session = null;
    public static CameraCaptureEvents camera_capture_event = CameraCaptureEvents.UNKNOWN;

    public MyCaptureSessionCallback(Runnable the_callback)
    {
        callback = the_callback;
    }

    @Override
    public void onActive(CameraCaptureSession session)
    {
        this.camera_capture_session = session;
        this.camera_capture_event = CameraCaptureEvents.ACTIVE;
        this.callback.run();
    }

    @Override
    public void onCaptureQueueEmpty(CameraCaptureSession session)
    {
        this.camera_capture_session = session;
        this.camera_capture_event = CameraCaptureEvents.CAPTURE_QUEUE_EMPTY;
        this.callback.run();
    }

    @Override
    public void onClosed(CameraCaptureSession session)
    {
        this.camera_capture_session = session;
        this.camera_capture_event = CameraCaptureEvents.CLOSED;
        this.callback.run();
    }

    public void onConfigureFailed(CameraCaptureSession session)
    {
        this.camera_capture_session = session;
        this.camera_capture_event = CameraCaptureEvents.CONFIGURE_FAILED;
        this.callback.run();
    }

    public void onConfigured(CameraCaptureSession session)
    {
        this.camera_capture_session = session;
        this.camera_capture_event = CameraCaptureEvents.CONFIGURED;
        this.callback.run();
    }

    @Override
    public void onReady(CameraCaptureSession session)
    {
        this.camera_capture_session = session;
        this.camera_capture_event = CameraCaptureEvents.READY;
        this.callback.run();
    }

    @Override
    public void onSurfacePrepared(CameraCaptureSession session, Surface surface)
    {
        this.camera_capture_session = session;
        this.camera_capture_event = CameraCaptureEvents.SURFACE_PREPARED;
        this.callback.run();
    }
}

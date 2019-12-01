package net.inclem.camera2;

import android.hardware.camera2.CameraDevice;
import java.lang.Runnable;
import android.util.Log;


public class MyStateCallback extends CameraDevice.StateCallback {
	private static final String TAG = "pythonMyStateCallback";

    Runnable callback;

    public enum CameraActions {
        CLOSED,
        DISCONNECTED,
        OPENED,
        ERROR,
        UNKNOWN
    };

    public static CameraDevice camera_device = null;
    public static CameraActions camera_action = CameraActions.UNKNOWN;
    public static int camera_error = 0;

    public MyStateCallback(Runnable the_callback)
    {
        callback = the_callback;
    }

    public void onClosed(CameraDevice cam)
    {
        Log.v(TAG, "onClosed");
        this.camera_device = cam;
        this.camera_action = CameraActions.CLOSED;
        this.callback.run();
    }

    public void onDisconnected(CameraDevice cam)
    {
        Log.v(TAG, "onDisconnected");
        this.camera_device = cam;
        this.camera_action = CameraActions.DISCONNECTED;
        this.callback.run();
    }

    public void onOpened(CameraDevice cam)
    {
        Log.v(TAG, "onOpened");
        this.camera_device = cam;
        this.camera_action = CameraActions.OPENED;
        this.callback.run();
    }

    @Override
    public void onError(CameraDevice cam, int error)
    {
        Log.v(TAG, "onError");
        this.camera_device = cam;
        this.camera_action = CameraActions.ERROR;
        this.camera_error = error;
        this.callback.run();
    }
}

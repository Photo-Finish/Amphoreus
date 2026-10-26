package com.amphoreus.sanctuary;

import android.Manifest;
import android.app.Activity;
import android.app.AlertDialog;
import android.content.Intent;
import android.content.SharedPreferences;
import android.content.pm.PackageManager;
import android.graphics.Color;
import android.graphics.Typeface;
import android.net.Uri;
import android.os.Build;
import android.os.Bundle;
import android.view.Gravity;
import android.view.View;
import android.view.ViewGroup;
import android.view.Window;
import android.view.WindowManager;
import android.view.inputmethod.EditorInfo;
import android.webkit.DownloadListener;
import android.webkit.PermissionRequest;
import android.webkit.ValueCallback;
import android.webkit.WebChromeClient;
import android.webkit.WebResourceError;
import android.webkit.WebResourceRequest;
import android.webkit.WebSettings;
import android.webkit.WebView;
import android.webkit.WebViewClient;
import android.widget.Button;
import android.widget.EditText;
import android.widget.FrameLayout;
import android.widget.LinearLayout;
import android.widget.ProgressBar;
import android.widget.TextView;
import android.widget.Toast;

/**
 * Project Amphoreus — the phone's door into the Sanctuary.
 *
 * The Sanctuary is a Streamlit application; this shell points a WebView at it, so
 * every screen and every administrator command the network UI has is available
 * unchanged — Visit, Walk the Land, the Gazette, the Map, the Galgame view,
 * An Eternal Page, the Admin Console and the Control Panel all speak to the same
 * local server. Nothing is reimplemented here, and nothing is cached or uploaded:
 * the app is a window, not a second copy of the world.
 *
 * What the shell adds beyond a browser tab:
 *  - remembers the server address, so the phone opens straight into the world;
 *  - keeps every link inside the app instead of handing the session to Chrome;
 *  - unlocks the pieces a phone needs for the senses — the file picker for
 *    pictures, music and video, and the microphone for speech;
 *  - a small gear for reload / change server / open in the system browser.
 *
 * LAN only: the address is a plain http:// host:port on the same network. The
 * app requests nothing from the internet and holds no credentials — the login
 * gate is the server's own.
 */
public class MainActivity extends Activity {

    private static final String PREFS = "amphoreus";
    private static final String KEY_URL = "server_url";
    private static final int REQ_FILE = 1001;
    private static final int REQ_MIC = 1002;

    private SharedPreferences prefs;
    private FrameLayout root;
    private WebView web;
    private ProgressBar bar;
    private ValueCallback<Uri[]> pendingFile;
    private PermissionRequest pendingPermission;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        prefs = getSharedPreferences(PREFS, MODE_PRIVATE);

        Window window = getWindow();
        window.setStatusBarColor(Color.parseColor("#0b1224"));
        window.setNavigationBarColor(Color.parseColor("#0b1224"));
        if (Build.VERSION.SDK_INT >= 28) {
            window.getAttributes().layoutInDisplayCutoutMode =
                    WindowManager.LayoutParams.LAYOUT_IN_DISPLAY_CUTOUT_MODE_SHORT_EDGES;
        }

        root = new FrameLayout(this);
        root.setBackgroundColor(Color.parseColor("#0b1224"));
        setContentView(root);

        String saved = prefs.getString(KEY_URL, "");
        if (saved != null && !saved.isEmpty()) {
            loadSanctuary(saved);
        } else {
            showSetup(null);
        }
    }

    // ---------------------------------------------------------------- setup

    /** A small native screen: the phone needs an address before the world opens. */
    private void showSetup(final String suggested) {
        root.removeAllViews();
        web = null;

        LinearLayout box = new LinearLayout(this);
        box.setOrientation(LinearLayout.VERTICAL);
        box.setGravity(Gravity.CENTER_VERTICAL);
        int pad = (int) (24 * getResources().getDisplayMetrics().density);
        box.setPadding(pad, pad, pad, pad);

        TextView title = new TextView(this);
        title.setText("The Sanctuary");
        title.setTextSize(26);
        title.setTextColor(Color.parseColor("#f7edd2"));
        title.setTypeface(Typeface.create("serif", Typeface.BOLD));
        box.addView(title);

        TextView blurb = new TextView(this);
        blurb.setText("Where is the little Amphoreus running? Enter the address of "
                + "the computer that serves it, on this same network.");
        blurb.setTextSize(15);
        blurb.setTextColor(Color.parseColor("#a9b4c8"));
        blurb.setPadding(0, pad / 3, 0, pad);
        box.addView(blurb);

        final EditText field = new EditText(this);
        field.setSingleLine(true);
        field.setHint("http://192.168.1.20:8501");
        field.setTextColor(Color.WHITE);
        field.setHintTextColor(Color.parseColor("#5b6a84"));
        field.setInputType(android.text.InputType.TYPE_TEXT_VARIATION_URI);
        field.setImeOptions(EditorInfo.IME_ACTION_GO);
        if (suggested != null && !suggested.isEmpty()) {
            field.setText(suggested);
        }
        box.addView(field);

        Button connect = new Button(this);
        connect.setText("Enter the Sanctuary");
        connect.setAllCaps(false);
        connect.setOnClickListener(new View.OnClickListener() {
            @Override
            public void onClick(View v) {
                String url = normalize(field.getText().toString());
                if (url.isEmpty()) {
                    Toast.makeText(MainActivity.this, "Enter an address first.",
                            Toast.LENGTH_SHORT).show();
                    return;
                }
                prefs.edit().putString(KEY_URL, url).apply();
                loadSanctuary(url);
            }
        });
        LinearLayout.LayoutParams lp = new LinearLayout.LayoutParams(
                ViewGroup.LayoutParams.MATCH_PARENT, ViewGroup.LayoutParams.WRAP_CONTENT);
        lp.topMargin = pad / 2;
        box.addView(connect, lp);

        TextView hint = new TextView(this);
        hint.setText("On the computer:  python tools\\serve_for_phone.py\n"
                + "The address it prints is the one to type here.");
        hint.setTextSize(12);
        hint.setTextColor(Color.parseColor("#7f8a9e"));
        hint.setPadding(0, pad / 2, 0, 0);
        hint.setTypeface(Typeface.MONOSPACE);
        box.addView(hint);

        root.addView(box);
    }

    /** Tolerate what people actually type: bare host, trailing slash, no scheme. */
    private String normalize(String raw) {
        String url = raw == null ? "" : raw.trim();
        if (url.isEmpty()) {
            return "";
        }
        if (!url.startsWith("http://") && !url.startsWith("https://")) {
            url = "http://" + url;
        }
        while (url.endsWith("/")) {
            url = url.substring(0, url.length() - 1);
        }
        return url;
    }

    // ------------------------------------------------------------- the page

    private void loadSanctuary(String url) {
        root.removeAllViews();

        web = new WebView(this);
        web.setBackgroundColor(Color.parseColor("#0b1224"));
        WebSettings s = web.getSettings();
        s.setJavaScriptEnabled(true);
        s.setDomStorageEnabled(true);
        s.setDatabaseEnabled(true);
        s.setLoadWithOverviewMode(true);
        s.setUseWideViewPort(true);
        s.setBuiltInZoomControls(true);
        s.setDisplayZoomControls(false);
        s.setMediaPlaybackRequiresUserGesture(false);
        s.setAllowFileAccess(false);
        s.setAllowContentAccess(true);
        s.setMixedContentMode(WebSettings.MIXED_CONTENT_COMPATIBILITY_MODE);
        if (Build.VERSION.SDK_INT >= 29) {
            s.setForceDark(WebSettings.FORCE_DARK_AUTO);
        }

        web.setWebViewClient(new WebViewClient() {
            @Override
            public boolean shouldOverrideUrlLoading(WebView view, WebResourceRequest req) {
                Uri u = req.getUrl();
                String scheme = u == null ? "" : u.getScheme();
                if ("http".equals(scheme) || "https".equals(scheme)) {
                    return false;   // stay in the app: the whole world is here
                }
                try {
                    startActivity(new Intent(Intent.ACTION_VIEW, u));
                } catch (Exception ignored) {
                }
                return true;
            }

            @Override
            public void onReceivedError(WebView view, WebResourceRequest req,
                                        WebResourceError err) {
                if (req == null || !req.isForMainFrame()) {
                    return;
                }
                String host = prefs.getString(KEY_URL, "");
                showOffline(host, String.valueOf(err == null ? "" : err.getDescription()));
            }
        });

        web.setWebChromeClient(new WebChromeClient() {
            @Override
            public void onProgressChanged(WebView view, int progress) {
                if (bar != null) {
                    bar.setVisibility(progress >= 100 ? View.GONE : View.VISIBLE);
                    bar.setProgress(progress);
                }
            }

            @Override
            public boolean onShowFileChooser(WebView view, ValueCallback<Uri[]> callback,
                                             FileChooserParams params) {
                // The senses: a picture, a piece of music, a video.
                if (pendingFile != null) {
                    pendingFile.onReceiveValue(null);
                }
                pendingFile = callback;
                try {
                    Intent i = params.createIntent();
                    i.addCategory(Intent.CATEGORY_OPENABLE);
                    startActivityForResult(i, REQ_FILE);
                    return true;
                } catch (Exception e) {
                    pendingFile = null;
                    return false;
                }
            }

            @Override
            public void onPermissionRequest(final PermissionRequest request) {
                // The microphone, for speech the Heirs can hear.
                boolean wantsAudio = false;
                for (String r : request.getResources()) {
                    if (PermissionRequest.RESOURCE_AUDIO_CAPTURE.equals(r)) {
                        wantsAudio = true;
                    }
                }
                if (!wantsAudio) {
                    request.deny();
                    return;
                }
                if (checkSelfPermission(Manifest.permission.RECORD_AUDIO)
                        == PackageManager.PERMISSION_GRANTED) {
                    request.grant(request.getResources());
                    return;
                }
                pendingPermission = request;
                requestPermissions(new String[]{Manifest.permission.RECORD_AUDIO}, REQ_MIC);
            }

            @Override
            public boolean onConsoleMessage(android.webkit.ConsoleMessage m) {
                return true;   // the page's own console belongs to the page
            }
        });

        web.setDownloadListener(new DownloadListener() {
            @Override
            public void onDownloadStart(String url, String ua, String cd, String mime,
                                        long len) {
                try {
                    startActivity(new Intent(Intent.ACTION_VIEW, Uri.parse(url)));
                } catch (Exception ignored) {
                }
            }
        });

        bar = new ProgressBar(this, null, android.R.attr.progressBarStyleHorizontal);
        FrameLayout.LayoutParams barLp = new FrameLayout.LayoutParams(
                ViewGroup.LayoutParams.MATCH_PARENT, (int) (3 * getResources()
                .getDisplayMetrics().density));
        barLp.gravity = Gravity.TOP;

        root.addView(web, new FrameLayout.LayoutParams(
                ViewGroup.LayoutParams.MATCH_PARENT, ViewGroup.LayoutParams.MATCH_PARENT));
        root.addView(bar, barLp);
        addGear();
        web.loadUrl(url);
    }

    /** A small gear over the page: reload, change server, or leave for a browser. */
    private void addGear() {
        TextView gear = new TextView(this);
        gear.setText("⚙");
        gear.setTextSize(18);
        gear.setTextColor(Color.parseColor("#f7edd2"));
        gear.setGravity(Gravity.CENTER);
        int size = (int) (40 * getResources().getDisplayMetrics().density);
        gear.setAlpha(0.55f);
        FrameLayout.LayoutParams lp = new FrameLayout.LayoutParams(size, size);
        lp.gravity = Gravity.TOP | Gravity.END;
        lp.topMargin = (int) (8 * getResources().getDisplayMetrics().density);
        lp.rightMargin = (int) (8 * getResources().getDisplayMetrics().density);
        gear.setOnClickListener(new View.OnClickListener() {
            @Override
            public void onClick(View v) {
                menu();
            }
        });
        root.addView(gear, lp);
    }

    private void menu() {
        final String url = prefs.getString(KEY_URL, "");
        final String[] items = {"Reload the page", "Change the server address",
                "Open in the system browser"};
        new AlertDialog.Builder(this)
                .setTitle("Amphoreus")
                .setItems(items, new android.content.DialogInterface.OnClickListener() {
                    @Override
                    public void onClick(android.content.DialogInterface d, int which) {
                        if (which == 0 && web != null) {
                            web.reload();
                        } else if (which == 1) {
                            showSetup(url);
                        } else {
                            try {
                                startActivity(new Intent(Intent.ACTION_VIEW, Uri.parse(url)));
                            } catch (Exception ignored) {
                            }
                        }
                    }
                })
                .show();
    }

    private void showOffline(final String url, String detail) {
        if (root == null) {
            return;
        }
        root.removeAllViews();
        web = null;

        LinearLayout box = new LinearLayout(this);
        box.setOrientation(LinearLayout.VERTICAL);
        box.setGravity(Gravity.CENTER_VERTICAL);
        int pad = (int) (24 * getResources().getDisplayMetrics().density);
        box.setPadding(pad, pad, pad, pad);

        TextView title = new TextView(this);
        title.setText("The Sanctuary is not answering");
        title.setTextSize(22);
        title.setTextColor(Color.parseColor("#f7edd2"));
        title.setTypeface(Typeface.create("serif", Typeface.BOLD));
        box.addView(title);

        TextView why = new TextView(this);
        why.setText("Tried " + url + "\n" + detail
                + "\n\nIs the computer running the server, and is this phone on "
                + "the same network?");
        why.setTextSize(14);
        why.setTextColor(Color.parseColor("#a9b4c8"));
        why.setPadding(0, pad / 3, 0, pad / 2);
        box.addView(why);

        Button retry = new Button(this);
        retry.setText("Try again");
        retry.setAllCaps(false);
        retry.setOnClickListener(new View.OnClickListener() {
            @Override
            public void onClick(View v) {
                loadSanctuary(url);
            }
        });
        box.addView(retry);

        Button change = new Button(this);
        change.setText("Change the address");
        change.setAllCaps(false);
        change.setOnClickListener(new View.OnClickListener() {
            @Override
            public void onClick(View v) {
                showSetup(url);
            }
        });
        box.addView(change);

        root.addView(box);
    }

    // ----------------------------------------------------------- the phone

    @Override
    public void onBackPressed() {
        if (web != null && web.canGoBack()) {
            web.goBack();
            return;
        }
        if (web == null) {
            String url = prefs.getString(KEY_URL, "");
            if (url != null && !url.isEmpty()) {
                loadSanctuary(url);
                return;
            }
        }
        super.onBackPressed();
    }

    @Override
    protected void onActivityResult(int requestCode, int resultCode, Intent data) {
        if (requestCode == REQ_FILE) {
            if (pendingFile != null) {
                pendingFile.onReceiveValue(
                        WebChromeClient.FileChooserParams.parseResult(resultCode, data));
                pendingFile = null;
            }
            return;
        }
        super.onActivityResult(requestCode, resultCode, data);
    }

    @Override
    public void onRequestPermissionsResult(int requestCode, String[] permissions,
                                           int[] grantResults) {
        if (requestCode == REQ_MIC && pendingPermission != null) {
            if (grantResults.length > 0
                    && grantResults[0] == PackageManager.PERMISSION_GRANTED) {
                pendingPermission.grant(pendingPermission.getResources());
            } else {
                pendingPermission.deny();
            }
            pendingPermission = null;
            return;
        }
        super.onRequestPermissionsResult(requestCode, permissions, grantResults);
    }

    @Override
    protected void onDestroy() {
        if (web != null) {
            root.removeView(web);
            web.destroy();
            web = null;
        }
        super.onDestroy();
    }
}

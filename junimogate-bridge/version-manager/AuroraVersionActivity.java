package org.junimogate.aurora;

import android.app.Activity;
import android.app.AlertDialog;
import android.app.PendingIntent;
import android.content.Context;
import android.content.Intent;
import android.content.SharedPreferences;
import android.content.pm.PackageInfo;
import android.content.pm.PackageInstaller;
import android.content.pm.PackageManager;
import android.database.Cursor;
import android.net.Uri;
import android.os.Build;
import android.os.Bundle;
import android.os.Handler;
import android.os.Looper;
import android.provider.OpenableColumns;
import android.provider.Settings;
import android.graphics.Color;
import android.graphics.Typeface;
import android.graphics.drawable.GradientDrawable;
import android.view.View;
import android.widget.Button;
import android.widget.EditText;
import android.widget.LinearLayout;
import android.widget.ScrollView;
import android.widget.TextView;
import android.widget.Toast;
import java.io.File;
import java.io.FileOutputStream;
import java.io.IOException;
import java.io.InputStream;
import java.io.OutputStream;
import java.net.URI;
import java.security.MessageDigest;
import java.util.Arrays;
import java.util.HashMap;
import java.util.HashSet;
import java.util.Map;
import java.util.Set;
import java.util.zip.ZipEntry;
import java.util.zip.ZipFile;

/**
 * Java entry screen packaged into the existing Aurora/JunimoGate APK.
 * Original managed SMAPI/GameHost/CLR files remain byte-identical.
 * No paid game binary or public mirror is embedded in this code.
 */
public final class AuroraVersionActivity extends Activity {
    private static final int PICK_GAME_ARCHIVE = 5035;
    private static final String CALLBACK = "org.junimogate.aurora.SPLIT_INSTALL_CALLBACK";
    private static final String PREFS = "aurora-local-version-source";
    private static final String SOURCE_KEY = "version-1.6.15.3-build245-link";
    private static final String GAME_ID = "com.chucklefish.stardewvalley";
    private static final long MAX_ARCHIVE = 350_000_000L;
    private static final int BG = Color.rgb(17, 18, 28);
    private static final int CARD = Color.rgb(32, 32, 49);
    private static final int TEXT = Color.rgb(238, 237, 251);
    private static final int SUB = Color.rgb(180, 176, 200);
    private static final int MINT = Color.rgb(117, 233, 190);
    private static final String[][] BUILD_245 = {
        {"base.apk", "4858693", "763c2dc5681ec8f079d0b8be590b77d12c76027769ccef957f3ae4357c120837"},
        {"split_config.arm64_v8a.apk", "53857797", "efa488b4ba5d5bead3924276a565eb992f022e11e03c7688b6921a484612eeb3"},
        {"split_content.apk", "361158047", "a90797b428249e040ecfc724168ba1310858855990136b5f813da6d456872d25"}
    };
    private final Handler main = new Handler(Looper.getMainLooper());
    private TextView status;
    private boolean busy;

    @Override public void onCreate(Bundle state) {
        super.onCreate(state);
        getWindow().setStatusBarColor(BG);
        getWindow().setNavigationBarColor(BG);
        buildScreen();
        processInstallCallback(getIntent());
    }

    @Override protected void onNewIntent(Intent intent) {
        super.onNewIntent(intent);
        setIntent(intent);
        processInstallCallback(intent);
    }

    private void buildScreen() {
        ScrollView scroll = new ScrollView(this);
        scroll.setFillViewport(true);
        scroll.setBackgroundColor(BG);
        LinearLayout body = new LinearLayout(this);
        body.setOrientation(LinearLayout.VERTICAL);
        int gutter = dp(20);
        body.setPadding(gutter, dp(28), gutter, dp(35));
        scroll.addView(body);
        label(body, "SMAPI  AURORA", 13, MINT, Typeface.BOLD, 0);
        label(body, "Stardew Valley", 28, TEXT, Typeface.BOLD, 13);
        label(body, "Центр запуска и выбора версии", 14, SUB, Typeface.NORMAL, 4);

        LinearLayout launch = card(body);
        label(launch, "SMAPI GAMEHOST", 12, MINT, Typeface.BOLD, 0);
        label(launch, "Оригинальное ядро JunimoGate 4.5.2", 15, TEXT, Typeface.NORMAL, 7);
        label(launch, "Этот экран не изменяет проверку подписи игры и не гарантирует совместимость модов.", 12, SUB, Typeface.NORMAL, 8);
        button(launch, "Запустить SMAPI Aurora", true, this::launchSmapi);

        LinearLayout build = card(body);
        label(build, "ИГРА · КАТАЛОГ", 12, MINT, Typeface.BOLD, 0);
        label(build, "Stardew Valley 1.6.15.3", 20, TEXT, Typeface.BOLD, 6);
        label(build, "build 245  ·  ARM64  ·  3 APK (299 МБ архив)", 13, SUB, Typeface.NORMAL, 4);
        label(build, gameVersion(), 13, MINT, Typeface.NORMAL, 10);
        button(build, "Скачать из моего Google Диска", true, this::openSavedLink);
        button(build, "Указать личную ссылку", false, this::editSavedLink);
        button(build, "Выбрать скачанный .apks и установить", false, this::chooseArchive);
        button(build, "Обновить игру в Google Play", false, this::openGooglePlay);

        LinearLayout info = card(body);
        label(info, "ПЕРЕД УСТАНОВКОЙ", 12, MINT, Typeface.BOLD, 0);
        label(info, "Для Android потребуется подтверждение установки. При замене или откате версии заранее сохрани игровые сохранения.", 13, SUB, Typeface.NORMAL, 9);
        label(info, "Твой личный файл не загружается в репозиторий, а доступ к нему не передаётся другим пользователям Aurora.", 13, SUB, Typeface.NORMAL, 8);
        status = label(body, "Готово к выбору версии", 12, SUB, Typeface.NORMAL, 15);
        setContentView(scroll);
    }

    private String gameVersion() {
        try {
            PackageInfo p = getPackageManager().getPackageInfo(GAME_ID, 0);
            return "Установленная игра: " + p.versionName + " (code " + (
                Build.VERSION.SDK_INT >= 28 ? p.getLongVersionCode() : p.versionCode) + ")";
        } catch (PackageManager.NameNotFoundException e) {
            return "Игра ещё не обнаружена на телефоне";
        }
    }

    private LinearLayout card(LinearLayout root) {
        LinearLayout l = new LinearLayout(this);
        l.setOrientation(LinearLayout.VERTICAL);
        l.setPadding(dp(17), dp(19), dp(17), dp(19));
        GradientDrawable shape = new GradientDrawable();
        shape.setColor(CARD);
        shape.setCornerRadius(dp(17));
        shape.setStroke(dp(1), Color.rgb(67, 64, 91));
        l.setBackground(shape);
        LinearLayout.LayoutParams lp = new LinearLayout.LayoutParams(-1, -2);
        lp.topMargin = dp(17);
        root.addView(l, lp);
        return l;
    }

    private TextView label(LinearLayout root, String value, int sp, int color, int style, int topDp) {
        TextView text = new TextView(this);
        text.setText(value);
        text.setTextColor(color);
        text.setTextSize(sp);
        text.setTypeface(Typeface.DEFAULT, style);
        LinearLayout.LayoutParams params = new LinearLayout.LayoutParams(-1, -2);
        params.topMargin = dp(topDp);
        root.addView(text, params);
        return text;
    }

    private void button(LinearLayout root, String text, boolean primary, Runnable clicked) {
        Button b = new Button(this);
        b.setText(text);
        b.setAllCaps(false);
        b.setTextSize(13);
        b.setTextColor(primary ? BG : TEXT);
        GradientDrawable background = new GradientDrawable();
        background.setColor(primary ? MINT : Color.rgb(51, 49, 72));
        background.setCornerRadius(dp(12));
        b.setBackground(background);
        LinearLayout.LayoutParams p = new LinearLayout.LayoutParams(-1, dp(51));
        p.topMargin = dp(11);
        root.addView(b, p);
        b.setOnClickListener(v -> {
            if (busy) { toast("Операция ещё выполняется"); return; }
            clicked.run();
        });
    }

    private int dp(int n) { return Math.round(getResources().getDisplayMetrics().density * n); }
    private void toast(String msg) { Toast.makeText(this, msg, Toast.LENGTH_LONG).show(); }
    private void report(String msg) {
        main.post(() -> { if (status != null) status.setText(msg); toast(msg); });
    }

    private void launchSmapi() {
        try {
            Intent i = new Intent();
            i.setClassName(getPackageName(), "org.junimogate.app.MainActivity");
            startActivity(i);
        } catch (Exception e) {
            report("Не удалось открыть SMAPI: " + e.getClass().getSimpleName());
        }
    }

    private void openGooglePlay() {
        try {
            startActivity(new Intent(Intent.ACTION_VIEW, Uri.parse("market://details?id=" + GAME_ID)));
        } catch (Exception e) {
            startActivity(new Intent(Intent.ACTION_VIEW,
                Uri.parse("https://play.google.com/store/apps/details?id=" + GAME_ID)));
        }
    }

    private String savedLink() {
        return getSharedPreferences(PREFS, MODE_PRIVATE).getString(SOURCE_KEY, "");
    }
    private boolean validDriveUrl(String link) {
        try {
            URI u = URI.create(link);
            return "https".equalsIgnoreCase(u.getScheme())
                && "drive.google.com".equalsIgnoreCase(u.getHost())
                && u.getRawUserInfo() == null
                && u.getPath().startsWith("/file/d/")
                && u.getPath().length() > "/file/d/".length();
        } catch (RuntimeException e) { return false; }
    }
    private void editSavedLink() {
        final EditText entry = new EditText(this);
        entry.setSingleLine(true);
        entry.setText(savedLink());
        entry.setHint("https://drive.google.com/file/d/.../view");
        new AlertDialog.Builder(this)
            .setTitle("Личная ссылка на Stardew Valley 1.6.15.3")
            .setMessage("Вставь ссылку на свой файл Google Диска. Она сохраняется только на этом устройстве и не публикуется в APK.")
            .setView(entry)
            .setNegativeButton("Отмена", null)
            .setPositiveButton("Сохранить", (d, which) -> {
                String text = entry.getText().toString().trim();
                if (!validDriveUrl(text)) { toast("Необходима ссылка drive.google.com/file/d/..."); return; }
                getSharedPreferences(PREFS, MODE_PRIVATE).edit().putString(SOURCE_KEY, text).apply();
                report("Личная ссылка сохранена");
            }).show();
    }
    private void openSavedLink() {
        String url = savedLink();
        if (!validDriveUrl(url)) { editSavedLink(); return; }
        try {
            startActivity(new Intent(Intent.ACTION_VIEW, Uri.parse(url)));
            report("После скачивания открой .apks через кнопку установки");
        } catch (Exception e) { report("Не удалось открыть Google Диск"); }
    }
    private void chooseArchive() {
        Intent i = new Intent(Intent.ACTION_OPEN_DOCUMENT);
        i.addCategory(Intent.CATEGORY_OPENABLE);
        i.setType("*/*");
        startActivityForResult(i, PICK_GAME_ARCHIVE);
    }

    @Override protected void onActivityResult(int request, int result, Intent data) {
        super.onActivityResult(request, result, data);
        if (request != PICK_GAME_ARCHIVE || result != RESULT_OK || data == null || data.getData() == null)
            return;
        Uri source = data.getData();
        new AlertDialog.Builder(this)
            .setTitle("Проверить и установить комплект?")
            .setMessage("Будут проверены все три APK и их SHA-256, после чего Android предложит подтвердить установку. Убедись, что сохранения скопированы. Aurora не отключает защиту подписи.")
            .setNegativeButton("Отмена", null)
            .setPositiveButton("Продолжить", (d, which) -> stageInstall(source)).show();
    }

    private void stageInstall(Uri content) {
        if (Build.VERSION.SDK_INT >= 26 && !getPackageManager().canRequestPackageInstalls()) {
            new AlertDialog.Builder(this)
                .setTitle("Разрешение на установку APK")
                .setMessage("Android должен разрешить Aurora запрашивать установку приложений. Разрешение не обеспечивает автоматическую установку: подтверждение Android всё равно понадобится.")
                .setNegativeButton("Отмена", null)
                .setPositiveButton("Настройки Android", (d, w) -> {
                    Intent i = new Intent(Settings.ACTION_MANAGE_UNKNOWN_APP_SOURCES,
                        Uri.parse("package:" + getPackageName()));
                    startActivity(i);
                }).show();
            return;
        }
        busy = true;
        report("Проверка архива и подготовка установщика…");
        new Thread(() -> {
            try {
                installVerifiedBuild(content);
                report("Комплект проверен и передан Android — подтверди установку");
            } catch (Exception e) {
                report("Не удалось установить комплект: " + e.getMessage());
            } finally { busy = false; }
        }, "AuroraSplitInstall").start();
    }

    private void installVerifiedBuild(Uri uri) throws Exception {
        File temp = File.createTempFile("aurora-version-", ".apks", getCacheDir());
        int sessionId = -1;
        boolean committed = false;
        PackageInstaller installer = getPackageManager().getPackageInstaller();
        try {
            long copied = 0;
            try (InputStream in = getContentResolver().openInputStream(uri);
                 OutputStream out = new FileOutputStream(temp)) {
                if (in == null) throw new IOException("Документ недоступен");
                byte[] buf = new byte[131072];
                int n;
                while ((n = in.read(buf)) != -1) {
                    copied += n;
                    if (copied > MAX_ARCHIVE) throw new IOException("Слишком большой архив");
                    out.write(buf, 0, n);
                }
            }
            if (copied < 200_000_000) throw new IOException("Неполный .apks файл");
            try (ZipFile zip = new ZipFile(temp)) {
                if (zip.size() != 3) throw new IOException("Нужен комплект ровно из трёх APK");
                Map<String,String[]> expected = new HashMap<>();
                long total = 0;
                for (String[] row : BUILD_245) {
                    expected.put(row[0],row);
                    total += Long.parseLong(row[1]);
                }
                Set<String> found = new HashSet<>();
                for (java.util.Enumeration<? extends ZipEntry> it = zip.entries(); it.hasMoreElements();) {
                    ZipEntry e = it.nextElement();
                    String[] entry = expected.get(e.getName());
                    if (entry == null || e.isDirectory() || !found.add(e.getName())
                        || e.getSize() != Long.parseLong(entry[1]) || e.getCompressedSize() <= 0)
                        throw new IOException("Неверный состав архива " + e.getName());
                }
                if (found.size() != 3) throw new IOException("Отсутствуют части APK");
                PackageInstaller.SessionParams params =
                    new PackageInstaller.SessionParams(PackageInstaller.SessionParams.MODE_FULL_INSTALL);
                params.setAppPackageName(GAME_ID);
                params.setSize(total);
                if (Build.VERSION.SDK_INT >= 31)
                    params.setRequireUserAction(PackageInstaller.SessionParams.USER_ACTION_REQUIRED);
                sessionId = installer.createSession(params);
                try (PackageInstaller.Session session = installer.openSession(sessionId)) {
                    for (String[] row : BUILD_245) {
                        ZipEntry entry = zip.getEntry(row[0]);
                        MessageDigest digest = MessageDigest.getInstance("SHA-256");
                        long count = 0;
                        try (InputStream src = zip.getInputStream(entry);
                             OutputStream dest = session.openWrite(row[0], 0, Long.parseLong(row[1]))) {
                            byte[] buf = new byte[131072];
                            int n;
                            while ((n=src.read(buf))!=-1) {
                                count += n;
                                if (count > Long.parseLong(row[1])) throw new IOException("Неверный размер APK");
                                digest.update(buf,0,n);
                                dest.write(buf,0,n);
                            }
                            session.fsync(dest);
                        }
                        if (count != Long.parseLong(row[1])
                            || !hex(digest.digest()).equals(row[2]))
                            throw new IOException("SHA-256 не совпадает: " + row[0]);
                    }
                    Intent callback = new Intent(this, AuroraVersionActivity.class);
                    callback.setAction(CALLBACK);
                    callback.addFlags(Intent.FLAG_ACTIVITY_SINGLE_TOP | Intent.FLAG_ACTIVITY_CLEAR_TOP);
                    PendingIntent pending = PendingIntent.getActivity(this, sessionId, callback,
                        PendingIntent.FLAG_UPDATE_CURRENT | PendingIntent.FLAG_MUTABLE);
                    session.commit(pending.getIntentSender());
                    committed = true;
                }
            }
        } finally {
            if (sessionId >= 0 && !committed) {
                try { installer.abandonSession(sessionId); } catch (RuntimeException ignore) {}
            }
            if (!temp.delete()) temp.deleteOnExit();
        }
    }

    private static String hex(byte[] digest) {
        final char[] digits = "0123456789abcdef".toCharArray();
        char[] out = new char[digest.length*2];
        for (int i=0;i<digest.length;i++) {
            int b = digest[i] & 255;
            out[2*i] = digits[b>>4];
            out[2*i+1] = digits[b&15];
        }
        return new String(out);
    }

    private void processInstallCallback(Intent i) {
        if (i == null || !CALLBACK.equals(i.getAction())) return;
        setIntent(new Intent(this, AuroraVersionActivity.class));
        int code = i.getIntExtra(PackageInstaller.EXTRA_STATUS, PackageInstaller.STATUS_FAILURE);
        if (code == PackageInstaller.STATUS_PENDING_USER_ACTION) {
            Intent confirmation;
            if (Build.VERSION.SDK_INT >= 33)
                confirmation = i.getParcelableExtra(Intent.EXTRA_INTENT, Intent.class);
            else confirmation = i.getParcelableExtra(Intent.EXTRA_INTENT);
            if (confirmation != null) {
                try { startActivity(confirmation); }
                catch (Exception e) { report("Android не открыл подтверждение установки"); }
            }
        } else if (code == PackageInstaller.STATUS_SUCCESS) {
            report("Stardew Valley установлена — теперь попробуй запустить SMAPI");
            buildScreen();
        } else {
            report("Android отклонил установку: " +
                i.getStringExtra(PackageInstaller.EXTRA_STATUS_MESSAGE));
        }
    }
}

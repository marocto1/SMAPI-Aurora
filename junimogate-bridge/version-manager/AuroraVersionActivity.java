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
import android.content.pm.Signature;
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
import java.net.URL;
import java.net.HttpURLConnection;
import java.util.List;
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
    private static final String KNOWN_PLAY_CERT = "c7b27f1faf2f350e3c117875bde2353cea837ebe1b3c2ce23513bb191d95852d";
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
    private TextView gameIdentityStatus;
    private boolean busy;

    @Override public void onCreate(Bundle state) {
        super.onCreate(state);
        getWindow().setStatusBarColor(BG);
        getWindow().setNavigationBarColor(BG);
        buildScreen();
        processInstallCallback(getIntent());
    }

    @Override protected void onResume() {
        super.onResume();
        if (gameIdentityStatus != null)
            gameIdentityStatus.setText(gameVersion());
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
        label(body, "Играй с модами — без лишних настроек", 14, SUB, Typeface.NORMAL, 4);

        LinearLayout launch = card(body);
        label(launch, "SMAPI GAMEHOST", 12, MINT, Typeface.BOLD, 0);
        label(launch, "Stardew Valley  +  SMAPI 4.5.2", 15, TEXT, Typeface.NORMAL, 7);
        label(launch, gameVersion(), 13, SUB, Typeface.NORMAL, 8);
        button(launch, "Играть с модами", true, this::launchSmapi);
        button(launch, "Запустить обычную Stardew Valley", false, this::launchOriginalGame);

        LinearLayout build = card(body);
        label(build, "УПРАВЛЕНИЕ ВЕРСИЯМИ", 12, MINT, Typeface.BOLD, 0);
        label(build, "Stardew Valley 1.6.15.3", 20, TEXT, Typeface.BOLD, 6);
        label(build, "build 245  ·  Android ARM64", 13, SUB, Typeface.NORMAL, 4);
        gameIdentityStatus = label(build, gameVersion(), 12, MINT, Typeface.NORMAL, 10);
        button(build, "Скачать и установить выбранную версию", true, this::downloadAndInstallFromDrive);
        button(build, "Источник для скачивания (настраивается один раз)", false, this::editSavedLink);
        button(build, "Установить уже скачанный .apks", false, this::chooseArchive);
        button(build, "Stardew Valley в Google Play", false, this::openGooglePlay);

        LinearLayout info = card(body);
        label(info, "ПОДСКАЗКА", 12, MINT, Typeface.BOLD, 0);
        label(info, "Если Stardew Valley уже установлена, просто нажми «Играть с модами». Загрузка игры не требуется.", 13, SUB, Typeface.NORMAL, 9);
        label(info, "Для установки другой версии Android запросит подтверждение. Перед заменой сохрани игровые данные.", 13, SUB, Typeface.NORMAL, 8);
        status = label(body, "Готово к запуску", 12, SUB, Typeface.NORMAL, 15);
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


    /**
     * Compare Android's verified installed signer (not filename, size or web link)
     * with the tested JunimoGate Google Play certificate. Rotation is recognized
     * only when SigningInfo provides a verified chain with the known signer.
     *
     * Return [state, installedDigest, detail].
     * Never accept unknown APK signing certificates in the managed GameHost.
     */
    private String[] installedGameIdentity() {
        try {
            PackageInfo pkg = getPackageManager().getPackageInfo(
                GAME_ID,
                Build.VERSION.SDK_INT >= 28
                    ? PackageManager.GET_SIGNING_CERTIFICATES
                    : PackageManager.GET_SIGNATURES);
            Signature[] current;
            Signature[] history = null;
            if (Build.VERSION.SDK_INT >= 28) {
                if (pkg.signingInfo == null)
                    return new String[]{"unknown", "", "Android не вернул SigningInfo"};
                current = pkg.signingInfo.getApkContentsSigners();
                if (!pkg.signingInfo.hasMultipleSigners())
                    history = pkg.signingInfo.getSigningCertificateHistory();
            } else {
                current = pkg.signatures;
            }
            if (current == null || current.length != 1 || current[0] == null)
                return new String[]{"unknown", "", "Отсутствует единственная проверенная подпись"};
            String sha = hex(MessageDigest.getInstance("SHA-256").digest(
                current[0].toByteArray()));
            if (KNOWN_PLAY_CERT.equals(sha))
                return new String[]{"trusted", sha, "Подпись совпадает с проверенной Google Play"};
            if (history != null && history.length > 1) {
                for (int i = 0; i < history.length - 1; i++) {
                    if (history[i] != null &&
                        KNOWN_PLAY_CERT.equals(hex(MessageDigest.getInstance("SHA-256")
                            .digest(history[i].toByteArray()))))
                        return new String[]{"trusted", sha,
                            "Android подтвердил смену подписи от проверенного сертификата"};
                }
            }
            return new String[]{"mismatch", sha,
                "Подпись установленной игры НЕ совпадает с проверенной"};
        } catch (PackageManager.NameNotFoundException e) {
            return new String[]{"missing", "", "Stardew Valley не установлена"};
        } catch (Exception e) {
            return new String[]{"unknown", "", "Не удалось прочитать подпись: "
                + e.getClass().getSimpleName()};
        }
    }

    private String formatCertificateStatus() {
        String[] check = installedGameIdentity();
        if ("trusted".equals(check[0]))
            return "✓ " + check[2] + "\nSHA-256: " + check[1];
        if ("mismatch".equals(check[0]))
            return "⚠ " + check[2] + "\nSHA-256: " + check[1]
                + "\nSMAPI откажет в запуске до установки подходящей версии.";
        return check[2];
    }

    private void showCertificateDetails() {
        String[] current = installedGameIdentity();
        String message = "Статус: " + current[2]
            + "\n\nТекущая подпись (SHA-256): "
            + (current[1].isEmpty() ? "не определена" : current[1])
            + "\n\nОжидаемая подпись тестовой Google Play сборки:\n"
            + KNOWN_PLAY_CERT
            + "\n\nЕсли сертификаты различаются, Android не позволит обновить"
            + " установленную игру APK с другой подписью."
            + " Нельзя исправить это заменой SMAPI или обходом его проверки."
            + "\n\nСначала сохрани игровые сохранения. Затем используй"
            + " Google Play или свой проверенный комплект .apks."
            + " При конфликте подписи замена игры возможна только через"
            + " подтверждённые действия Android после сохранения данных.";
        new AlertDialog.Builder(this)
            .setTitle("Проверка подписи Stardew Valley")
            .setMessage(message)
            .setNegativeButton("Закрыть", null)
            .setNeutralButton("Настройки игры", (d, w) -> openGameAppDetails())
            .setPositiveButton("Google Play", (d, w) -> openGooglePlay())
            .show();
    }

    private void openGameAppDetails() {
        try {
            Intent i = new Intent(Settings.ACTION_APPLICATION_DETAILS_SETTINGS,
                Uri.parse("package:" + GAME_ID));
            startActivity(i);
        } catch (Exception e) {
            report("Не удалось открыть настройки Stardew Valley");
        }
    }

    private void explainSignatureMismatch() {
        new AlertDialog.Builder(this)
            .setTitle("Другая подпись Stardew Valley")
            .setMessage("На устройстве уже установлена Stardew Valley с другой"
                + " цифровой подписью. Android не позволит установить проверенные"
                + " split APK поверх неё, а SMAPI остановит запуск."
                + "\n\nAurora не будет удалять игру или её сохранения."
                + " Сначала сделай резервную копию всех сохранений."
                + " Затем открой сведения об установленной игре и реши,"
                + " как заменить её через Android или Google Play."
                + "\n\nНи автоматического удаления, ни обхода цифровой подписи нет.")
            .setNegativeButton("Отмена", null)
            .setNeutralButton("Настройки игры", (d, w) -> openGameAppDetails())
            .setPositiveButton("Google Play", (d, w) -> openGooglePlay())
            .show();
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

    private void launchOriginalGame() {
        try {
            Intent i = getPackageManager().getLaunchIntentForPackage(GAME_ID);
            if (i == null) { report("Stardew Valley не найдена на устройстве"); return; }
            startActivity(i);
        } catch (Exception e) {
            report("Не удалось запустить игру: " + e.getClass().getSimpleName());
        }
    }

    private void openGooglePlay() {
        try {
            startActivity(new Intent(Intent.ACTION_VIEW, Uri.parse("market://details?id=" + GAME_ID)));
        } catch (Exception e) {
            try {
                startActivity(new Intent(Intent.ACTION_VIEW,
                    Uri.parse("https://play.google.com/store/apps/details?id=" + GAME_ID)));
            } catch (Exception failure) {
                report("Не удалось открыть Google Play");
            }
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
                report("Источник сохранён — кнопка загрузки скачает и проверит архив автоматически");
            }).show();
    }
    /** Automatically retrieve the owner's own .apks source without a browser or file picker.
     * The personal source is stored on-device, not hard-coded into public APKs.
     * HTTPS certificate and redirect host validation remain enabled.
     */
    private void downloadAndInstallFromDrive() {
        String source = savedLink();
        if (!validDriveUrl(source)) {
            report("Для этой установки личный источник ещё не настроен.");
            editSavedLink();
            return;
        }
        if (Build.VERSION.SDK_INT >= 26 && !getPackageManager().canRequestPackageInstalls()) {
            new AlertDialog.Builder(this)
                .setTitle("Разрешение Android")
                .setMessage("Разреши Aurora запрашивать установку APK. Android всё равно потребует твоего подтверждения.")
                .setNegativeButton("Отмена", null)
                .setPositiveButton("Настройки", (d, w) -> startActivity(new Intent(
                    Settings.ACTION_MANAGE_UNKNOWN_APP_SOURCES,
                    Uri.parse("package:" + getPackageName()))))
                .show();
            return;
        }
        busy = true;
        new Thread(() -> {
            File downloaded = null;
            try {
                downloaded = fetchPersonalDriveArchive(source);
                installVerifiedBuild(Uri.fromFile(downloaded));
                report("SHA-256 проверен; Android запросит подтверждение установки");
            } catch (Exception e) {
                report("Загрузка/установка не удалась: " + e.getMessage());
            } finally {
                if (downloaded != null && downloaded.exists() && !downloaded.delete())
                    downloaded.deleteOnExit();
                busy = false;
            }
        }, "AuroraDriveDownload").start();
    }

    private void downloadProgress(String msg) {
        main.post(() -> { if (status != null) status.setText(msg); });
    }

    private boolean approvedDownloadHost(String host) {
        if (host == null) return false;
        host = host.toLowerCase(java.util.Locale.ROOT);
        return host.equals("drive.google.com")
            || host.equals("drive.usercontent.google.com")
            || host.equals("docs.google.com")
            || host.equals("googleusercontent.com")
            || host.endsWith(".googleusercontent.com");
    }

    private File fetchPersonalDriveArchive(String source) throws Exception {
        if (!validDriveUrl(source))
            throw new IOException("Неверный адрес Google Drive");
        List<String> segments = Uri.parse(source).getPathSegments();
        if (segments.size() < 3 || !"file".equals(segments.get(0)) ||
            !"d".equals(segments.get(1)) || !segments.get(2).matches("[A-Za-z0-9_-]{10,}"))
            throw new IOException("Не найден идентификатор файла Google Drive");
        String id = segments.get(2);
        String link = "https://drive.usercontent.google.com/download?id=" +
            id + "&export=download&confirm=t";
        File temp = File.createTempFile("aurora-drive-", ".apks", getCacheDir());
        boolean complete = false;
        try {
            downloadProgress("Подключение к Google Drive…");
            for (int redirect = 0; redirect < 9; redirect++) {
                URL endpoint = new URL(link);
                if (!"https".equalsIgnoreCase(endpoint.getProtocol()) ||
                    !approvedDownloadHost(endpoint.getHost()))
                    throw new IOException("Небезопасное перенаправление Google Drive");
                HttpURLConnection connection = (HttpURLConnection) endpoint.openConnection();
                connection.setInstanceFollowRedirects(false);
                connection.setConnectTimeout(20000);
                connection.setReadTimeout(120000);
                connection.setRequestProperty("User-Agent", "Mozilla/5.0 SMAPI-Aurora/0.8.3");
                try {
                    int code = connection.getResponseCode();
                    if (code == 301 || code == 302 || code == 303 || code == 307 || code == 308) {
                        String next = connection.getHeaderField("Location");
                        if (next == null) throw new IOException("Перенаправление без адреса");
                        link = new URL(endpoint, next).toString();
                        continue;
                    }
                    if (code != 200) {
                        if (code == 403) throw new IOException("Нет доступа к файлу Google Drive");
                        if (code == 404) throw new IOException("Файл Google Drive не найден");
                        throw new IOException("Google Drive вернул HTTP " + code);
                    }
                    String mime = connection.getContentType();
                    if (mime != null && (mime.toLowerCase(java.util.Locale.ROOT).contains("text/html")
                        || mime.toLowerCase(java.util.Locale.ROOT).contains("application/json")))
                        throw new IOException("Google Drive требует входа или подтверждения; нужна доступная прямая ссылка");
                    long expected = connection.getContentLengthLong();
                    if (expected > MAX_ARCHIVE)
                        throw new IOException("Файл превышает лимит безопасной загрузки");
                    long received = 0;
                    int lastPercent = -1;
                    try (InputStream in = connection.getInputStream();
                         OutputStream out = new FileOutputStream(temp)) {
                        byte[] buffer = new byte[131072];
                        int n;
                        while ((n = in.read(buffer)) != -1) {
                            received += n;
                            if (received > MAX_ARCHIVE)
                                throw new IOException("Файл больше ожидаемого размера");
                            out.write(buffer, 0, n);
                            if (expected > 0) {
                                int percent = (int) Math.min(100, (received * 100) / expected);
                                if (percent / 5 != lastPercent / 5) {
                                    lastPercent = percent;
                                    downloadProgress("Загрузка .apks из Google Drive: " + percent + "%");
                                }
                            } else if (received % (5 * 1024 * 1024) < n) {
                                downloadProgress("Загружено: " + (received / (1024 * 1024)) + " МБ");
                            }
                        }
                    }
                    if (expected > 0 && received != expected)
                        throw new IOException("Загрузка прервана: получен неполный архив");
                    if (received < 200_000_000)
                        throw new IOException("Слишком маленький файл: вероятно, Drive прислал страницу вместо .apks");
                    try (java.io.RandomAccessFile check = new java.io.RandomAccessFile(temp, "r")) {
                        if (check.readUnsignedByte() != 'P' || check.readUnsignedByte() != 'K')
                            throw new IOException("Google Drive вернул не ZIP/APKS архив");
                    }
                    downloadProgress("Архив скачан. Проверка трёх APK и SHA-256…");
                    complete = true;
                    return temp;
                } finally {
                    connection.disconnect();
                }
            }
            throw new IOException("Слишком много перенаправлений Google Drive");
        } finally {
            if (!complete && temp.exists()) temp.delete();
        }
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

package org.junimogate.aurora;

import android.app.Activity;
import android.app.AlertDialog;
import android.content.ActivityNotFoundException;
import android.content.Context;
import android.content.Intent;
import android.graphics.Typeface;
import android.graphics.drawable.GradientDrawable;
import android.net.Uri;
import android.os.Bundle;
import android.text.InputType;
import android.view.Gravity;
import android.view.View;
import android.view.ViewGroup;
import android.view.inputmethod.InputMethodManager;
import android.webkit.CookieManager;
import android.webkit.DownloadListener;
import android.webkit.SslErrorHandler;
import android.webkit.WebChromeClient;
import android.webkit.WebResourceError;
import android.webkit.WebResourceRequest;
import android.webkit.WebView;
import android.webkit.WebViewClient;
import android.net.http.SslError;
import android.widget.Button;
import android.widget.EditText;
import android.widget.LinearLayout;
import android.widget.ProgressBar;
import android.widget.TextView;

import java.net.URLEncoder;
import java.nio.charset.StandardCharsets;
import java.util.Locale;

/**
 * Native, in-app Nexus Workshop. No API key, no Nexus API calls, no HTML
 * scraping, no automated download bypass. Only official Nexus website.
 *
 * Browser-assisted downloads are handled by the user's browser so Nexus can
 * apply its normal authentication, file policies and rate limits. The
 * ORIGINAL .NET Mods->Import transaction is the only mod installer.
 */
public final class AuroraWorkshopActivity extends Activity {
    private static final String BASE = "https://www.nexusmods.com/stardewvalley/mods/";
    private WebView browser;
    private TextView status;
    private EditText search;
    private ProgressBar progress;
    private boolean destroyed;
    private int surface, panel, text, muted, primary, primaryContainer;

    @Override public void onCreate(Bundle state) {
        super.onCreate(state);
        setTitle("Aurora · Workshop");
        surface = color("junimo_surface", 0xfff7f9f4);
        panel = color("junimo_surface_container_low", 0xfff2f5ef);
        text = color("junimo_on_surface", 0xff1a2018);
        muted = color("junimo_on_surface_variant", 0xff586256);
        primary = color("junimo_primary", 0xff52733d);
        primaryContainer = color("junimo_primary_container", 0xffdfefd2);
        draw();
        browser.loadUrl(BASE);
    }

    private void draw() {
        LinearLayout page = new LinearLayout(this);
        page.setOrientation(LinearLayout.VERTICAL);
        page.setBackgroundColor(surface);
        page.setPadding(dp(12), dp(10), dp(12), dp(8));

        LinearLayout titleBar = row();
        TextView back = clickableLabel("‹  Моды", muted, primaryContainer);
        titleBar.addView(back, new LinearLayout.LayoutParams(0, dp(48), 1));
        back.setOnClickListener(v -> finish());

        TextView title = clickableLabel("Workshop · Nexus", primary, primaryContainer);
        title.setTypeface(Typeface.DEFAULT, Typeface.BOLD);
        titleBar.addView(title, new LinearLayout.LayoutParams(0, dp(48), 2));
        page.addView(titleBar);

        LinearLayout find = row();
        search = new EditText(this);
        search.setTextSize(14);
        search.setSingleLine(true);
        search.setHint("Название мода");
        search.setTextColor(text);
        search.setHintTextColor(muted);
        search.setInputType(InputType.TYPE_CLASS_TEXT);
        search.setPadding(dp(13), dp(2), dp(11), dp(2));
        search.setBackground(shape(panel));
        find.addView(search, new LinearLayout.LayoutParams(0, dp(48), 2));

        Button go = button("Найти", () -> {
            String query = search.getText().toString().trim();
            if (query.isEmpty()) {
                browser.loadUrl(BASE);
                return;
            }
            try {
                browser.loadUrl(BASE + "?title=" +
                    URLEncoder.encode(query, StandardCharsets.UTF_8.name()));
                ((InputMethodManager)getSystemService(Context.INPUT_METHOD_SERVICE))
                    .hideSoftInputFromWindow(search.getWindowToken(), 0);
            } catch (Exception error) {
                status.setText("Не удалось выполнить поиск.");
            }
        });
        LinearLayout.LayoutParams goParams = new LinearLayout.LayoutParams(0, dp(48), 1);
        goParams.leftMargin = dp(8);
        find.addView(go, goParams);
        LinearLayout.LayoutParams findParams = new LinearLayout.LayoutParams(-1, dp(48));
        findParams.topMargin = dp(8);
        page.addView(find, findParams);

        LinearLayout controls = row();
        controls.addView(button("Главная Nexus", () -> browser.loadUrl(BASE)), weighted());
        controls.addView(button("В браузере", this::openCurrentInBrowser), weighted());
        controls.addView(button("Импорт ZIP", this::showImport), weighted());
        LinearLayout.LayoutParams controlParams = new LinearLayout.LayoutParams(-1, dp(50));
        controlParams.topMargin = dp(6);
        page.addView(controls, controlParams);
        LinearLayout quick = row();
        quick.addView(button("Категории", this::showCategories), weighted());
        quick.addView(button("☆ В избранное", this::addFavorite), weighted());
        quick.addView(button("Избранное", this::showFavorites), weighted());
        LinearLayout.LayoutParams quickParams = new LinearLayout.LayoutParams(-1, dp(48));
        quickParams.topMargin = dp(5);
        page.addView(quick, quickParams);

        Button curated = button("Проверенные моды · Скачать из GitHub", this::showCuratedMods);
        LinearLayout.LayoutParams curatedParams = new LinearLayout.LayoutParams(-1, dp(50));
        curatedParams.topMargin = dp(7);
        page.addView(curated, curatedParams);

        status = label("Nexus Mods открывается внутри Aurora. Без API и без входа через Aurora.", 12, muted);
        status.setPadding(dp(4), dp(8), dp(4), dp(5));
        page.addView(status);
        progress = new ProgressBar(this, null, android.R.attr.progressBarStyleHorizontal);
        progress.setIndeterminate(true);
        progress.setVisibility(View.GONE);
        page.addView(progress, new LinearLayout.LayoutParams(-1, dp(3)));

        browser = new WebView(this);
        browser.setBackgroundColor(surface);
        browser.setWebViewClient(new WebViewClient() {
            @Override public boolean shouldOverrideUrlLoading(WebView view, WebResourceRequest request) {
                return intercept(request.getUrl());
            }
            @Override public boolean shouldOverrideUrlLoading(WebView view, String url) {
                return intercept(Uri.parse(url));
            }
            @Override public void onPageStarted(WebView view, String url, android.graphics.Bitmap icon) {
                if (!destroyed) {
                    status.setText("Открывается Nexus Mods…");
                    progress.setVisibility(View.VISIBLE);
                }
            }
            @Override public void onPageFinished(WebView view, String url) {
                if (!destroyed) {
                    progress.setVisibility(View.GONE);
                    status.setText("Файлы → Manual Download. Затем «Импорт ZIP» в Aurora.");
                }
            }
            @Override public void onReceivedError(WebView view,
                WebResourceRequest request, WebResourceError error) {
                if (!destroyed && request.isForMainFrame()) {
                    progress.setVisibility(View.GONE);
                    status.setText("Nexus не открылся внутри приложения. Попробуй «В браузере».");
                }
            }
            @Override public void onReceivedSslError(WebView view, SslErrorHandler handler, SslError error) {
                handler.cancel(); // never weaken HTTPS
                if (!destroyed) status.setText("Ошибка HTTPS — открой Nexus в обычном браузере.");
            }
        });
        browser.setWebChromeClient(new WebChromeClient());
        browser.getSettings().setJavaScriptEnabled(true); // needed by official Nexus site
        browser.getSettings().setDomStorageEnabled(true);
        browser.getSettings().setAllowFileAccess(false);
        browser.getSettings().setAllowContentAccess(false);
        browser.getSettings().setJavaScriptCanOpenWindowsAutomatically(false);
        browser.getSettings().setSupportMultipleWindows(false);
        browser.getSettings().setMixedContentMode(android.webkit.WebSettings.MIXED_CONTENT_NEVER_ALLOW);
        android.webkit.WebView.setWebContentsDebuggingEnabled(false);
        CookieManager.getInstance().setAcceptCookie(true);
        CookieManager.getInstance().setAcceptThirdPartyCookies(browser, false);

        // We do NOT synthesise Nexus download URLs or call their private API.
        browser.setDownloadListener((url, userAgent, contentDisposition, mimeType, contentLength) -> {
            Uri target = Uri.parse(url);
            if (!"https".equalsIgnoreCase(target.getScheme())) {
                status.setText("Небезопасная загрузка отклонена. Скачай архив через официальный браузер.");
                return;
            }
            new AlertDialog.Builder(this)
                .setTitle("Скачать файл с Nexus?")
                .setMessage("Откроем загрузку в браузере, чтобы Nexus применил стандартные правила. " +
                    "После скачивания вернись и нажми «Импорт ZIP».")
                .setPositiveButton("Скачать", (d, which) -> openExternal(url))
                .setNegativeButton("Отмена", null).show();
        });
        page.addView(browser, new LinearLayout.LayoutParams(-1, 0, 1));
        setContentView(page);
    }

    /** Redirect user-initiated external links, nxm links and non-Nexus hosts. */
    private boolean intercept(Uri uri) {
        String scheme = uri.getScheme();
        String host = uri.getHost();
        if ("https".equalsIgnoreCase(scheme) && host != null &&
            (host.equalsIgnoreCase("nexusmods.com") ||
             host.toLowerCase(Locale.ROOT).endsWith(".nexusmods.com"))) {
            return false;
        }
        if ("nxm".equalsIgnoreCase(scheme)) {
            new AlertDialog.Builder(this)
                .setTitle("Nexus Mod Manager Download")
                .setMessage("NXM-загрузка требует официальной интеграции с Nexus и подтверждения прав аккаунта. " +
                    "Используй Files → Manual Download, затем импортируй ZIP в Aurora.")
                .setPositiveButton("Понятно", null).show();
            return true;
        }
        if ("http".equalsIgnoreCase(scheme)) {
            status.setText("Небезопасный HTTP-переход заблокирован.");
            return true;
        }
        if ("https".equalsIgnoreCase(scheme)) {
            openExternal(uri.toString());
            return true;
        }
        return true; // block intent:, file:, javascript:, content: etc.
    }

    private void openCurrentInBrowser() {
        String current = browser.getUrl();
        if (current == null || !current.startsWith("https://")) current = BASE;
        openExternal(current);
    }

    private void openExternal(String url) {
        if (!url.startsWith("https://")) return;
        try {
            Intent intent = new Intent(Intent.ACTION_VIEW, Uri.parse(url));
            intent.addCategory(Intent.CATEGORY_BROWSABLE);
            startActivity(intent);
        } catch (ActivityNotFoundException e) {
            status.setText("Нет браузера для открытия ссылки.");
        }
    }


    // Nexus discovery uses public web pages only; no API key or scraping.
    private void showCategories() {
        String[] categories = {
            "Content Patcher", "UI", "Portraits", "Buildings",
            "Visuals", "Gameplay", "Framework"
        };
        new AlertDialog.Builder(this).setTitle("Категории Nexus Mods")
            .setItems(categories, (dialog, which) -> {
                try {
                    browser.loadUrl(BASE + "?title=" +
                        URLEncoder.encode(categories[which], "UTF-8"));
                } catch (Exception ignored) {
                    status.setText("Не удалось открыть категорию.");
                }
            })
            .setNegativeButton("Назад", null).show();
    }

    private static boolean safeFavoriteUrl(String candidate) {
        if (candidate == null || candidate.length() > 1024) return false;
        Uri uri = Uri.parse(candidate);
        String host = uri.getHost();
        return "https".equalsIgnoreCase(uri.getScheme()) && host != null &&
            (host.equalsIgnoreCase("www.nexusmods.com") ||
             host.equalsIgnoreCase("nexusmods.com")) &&
            uri.getUserInfo() == null && uri.getPort() == -1 &&
            uri.getPath() != null && uri.getPath().startsWith("/stardewvalley/");
    }

    private void addFavorite() {
        String url = browser.getUrl();
        if (!safeFavoriteUrl(url)) {
            status.setText("Избранное доступно только для страниц Stardew Valley на Nexus.");
            return;
        }
        java.util.Set<String> favorites = new java.util.TreeSet<>(
            getSharedPreferences("aurora-workshop-favorites", MODE_PRIVATE)
                .getStringSet("urls", java.util.Collections.emptySet()));
        if (favorites.size() >= 40 && !favorites.contains(url)) {
            status.setText("В избранном максимум 40 страниц."); return;
        }
        favorites.add(url);
        getSharedPreferences("aurora-workshop-favorites", MODE_PRIVATE)
            .edit().putStringSet("urls", favorites).apply();
        status.setText("Страница добавлена в избранное Aurora.");
    }

    private void showFavorites() {
        java.util.Set<String> stored = getSharedPreferences(
            "aurora-workshop-favorites", MODE_PRIVATE)
            .getStringSet("urls", java.util.Collections.emptySet());
        java.util.ArrayList<String> entries = new java.util.ArrayList<>();
        for (String url: stored) if (safeFavoriteUrl(url)) entries.add(url);
        java.util.Collections.sort(entries);
        if (entries.isEmpty()) {
            new AlertDialog.Builder(this).setTitle("Избранное")
                .setMessage("Пока нет сохранённых страниц.")
                .setPositiveButton("Понятно", null).show();
            return;
        }
        String[] titles = new String[entries.size()];
        for (int i=0;i<entries.size();i++) {
            String path = Uri.parse(entries.get(i)).getPath();
            titles[i] = path.length() > 64 ? path.substring(0,64) + "…" : path;
        }
        new AlertDialog.Builder(this).setTitle("Избранное Aurora")
            .setItems(titles,(dialog,which) -> browser.loadUrl(entries.get(which)))
            .setNeutralButton("Очистить избранное",(dialog,which) ->
                new AlertDialog.Builder(this)
                    .setTitle("Удалить избранные ссылки?")
                    .setPositiveButton("Удалить", (d, n) ->
                        getSharedPreferences("aurora-workshop-favorites", MODE_PRIVATE)
                            .edit().remove("urls").apply())
                    .setNegativeButton("Отмена", null).show())
            .setNegativeButton("Закрыть", null).show();
    }

    /** Only author-controlled direct links with pinned SHA-256 enter this flow. */
    private void showCuratedMods() {
        AuroraDirectDownloads.Entry[] available = AuroraDirectDownloads.CURATED;
        String[] labels = new String[available.length];
        for (int i = 0; i < available.length; i++) {
            labels[i] = available[i].name + " · v" + available[i].version;
        }
        new AlertDialog.Builder(this)
            .setTitle("Проверенные моды · GitHub")
            .setMessage("Этот каталог содержит только разрешённые публичные ZIP-архивы с зафиксированной SHA-256. " +
                "Список пока тестовый; обычные моды с Nexus доступны в браузере выше.")
            .setItems(labels, (dialog, index) -> confirmDirectDownload(available[index]))
            .setNegativeButton("Назад", null).show();
    }

    private void confirmDirectDownload(AuroraDirectDownloads.Entry entry) {
        new AlertDialog.Builder(this).setTitle(entry.name)
            .setMessage(entry.description + "\n\nИсточник: " + entry.source +
                "\nВерсия: " + entry.version +
                "\\nSHA-256 проверяется перед сохранением. " +
                "После загрузки Aurora откроет штатный импорт ZIP, где установка подтверждается отдельно.")
            .setPositiveButton("Скачать архив", (dialog, action) -> {
                status.setText("Загрузка " + entry.name + "…");
                AuroraDirectDownloads.download(this, entry, new AuroraDirectDownloads.Listener() {
                    @Override public void onProgress(String message) {
                        status.setText(message);
                    }
                    @Override public void onReady(Uri uri, String filename) {
                        status.setText("ZIP проверен и сохранён: Загрузки/Aurora/" + filename);
                        new AlertDialog.Builder(AuroraWorkshopActivity.this)
                            .setTitle("Архив загружен и проверен")
                            .setMessage("Мод ещё НЕ установлен. Архив в Загрузки/Aurora/" +
                                filename + ".\n\nОткрыть стандартный безопасный установщик Aurora?")
                            .setPositiveButton("Импортировать ZIP", (d, which) -> {
                                boolean picker = AuroraWorkshopTabsView.requestOriginalZipImport();
                                finish();
                                if (!picker) {
                                    android.widget.Toast.makeText(getApplicationContext(),
                                        "Открой Моды → Импорт и выбери ZIP из Загрузки/Aurora",
                                        android.widget.Toast.LENGTH_LONG).show();
                                }
                            })
                            .setNegativeButton("Позже", null).show();
                    }
                    @Override public void onFailure(String message) {
                        status.setText(message);
                        new AlertDialog.Builder(AuroraWorkshopActivity.this)
                            .setTitle("Не удалось скачать")
                            .setMessage(message)
                            .setPositiveButton("Закрыть", null).show();
                    }
                });
            })
            .setNegativeButton("Отмена", null).show();
    }

    private void showImport() {
        new AlertDialog.Builder(this)
            .setTitle("Установка скачанного ZIP")
            .setMessage("1. На Nexus открой Files → Manual Download.\n" +
                "2. Скачай ZIP в обычном браузере.\n" +
                "3. В Aurora → Моды → Импорт выбери архив из Загрузок.\n" +
                "4. Добавь мод в активную группу и проверь зависимости.\n\n" +
                "Без официального Nexus API нельзя безопасно получить защищённый " +
                "адрес загрузки и автоматически поставить любой мод. " +
                "Workshop не обходит ограничения Nexus.")
            .setPositiveButton("Выбрать ZIP в Aurora", (d, w) -> {
                boolean canOpenPicker = AuroraWorkshopTabsView.requestOriginalZipImport();
                finish();
                if (!canOpenPicker) {
                    Intent main = new Intent();
                    main.setClassName(getPackageName(), "org.junimogate.app.MainActivity");
                    main.addFlags(Intent.FLAG_ACTIVITY_CLEAR_TOP | Intent.FLAG_ACTIVITY_SINGLE_TOP);
                    try { startActivity(main); }
                    catch (RuntimeException error) {
                        // User can still launch Aurora normally and select Mods > Import.
                    }
                }
            })
            .setNegativeButton("Продолжить просмотр", null).show();
    }

    private int color(String name, int fallback) {
        return AuroraWorkshopTabsView.themeColor(this, name, fallback);
    }
    private LinearLayout row() {
        LinearLayout result = new LinearLayout(this);
        result.setOrientation(LinearLayout.HORIZONTAL);
        result.setGravity(Gravity.CENTER_VERTICAL);
        return result;
    }
    private LinearLayout.LayoutParams weighted() {
        return new LinearLayout.LayoutParams(0, dp(48), 1);
    }
    private Button button(String caption, Runnable action) {
        Button b = new Button(this);
        b.setText(caption);
        b.setTextSize(12);
        b.setAllCaps(false);
        b.setOnClickListener(v -> action.run());
        return b;
    }
    private TextView label(String caption, int sp, int shade) {
        TextView t = new TextView(this);
        t.setText(caption);
        t.setTextSize(sp);
        t.setTextColor(shade);
        t.setGravity(Gravity.CENTER_VERTICAL);
        return t;
    }
    private TextView clickableLabel(String caption, int shade, int background) {
        TextView t = label(caption, 14, shade);
        t.setGravity(Gravity.CENTER);
        t.setBackground(shape(background));
        return t;
    }
    private GradientDrawable shape(int shade) {
        GradientDrawable d = new GradientDrawable();
        d.setColor(shade);
        d.setCornerRadius(dp(12));
        return d;
    }
    private int dp(int n) {
        return Math.round(n * getResources().getDisplayMetrics().density);
    }

    @Override public void onBackPressed() {
        if (browser != null && browser.canGoBack()) browser.goBack();
        else super.onBackPressed();
    }
    @Override public void onDestroy() {
        destroyed = true;
        if (browser != null) {
            ViewGroup parent = (ViewGroup) browser.getParent();
            if (parent != null) parent.removeView(browser);
            browser.stopLoading();
            browser.destroy();
            browser = null;
        }
        super.onDestroy();
    }
}

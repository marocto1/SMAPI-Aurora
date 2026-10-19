package org.junimogate.aurora;

import android.app.Activity;
import android.app.AlertDialog;
import android.content.ActivityNotFoundException;
import android.content.Intent;
import android.graphics.Color;
import android.graphics.Typeface;
import android.graphics.drawable.GradientDrawable;
import android.net.Uri;
import android.os.Bundle;
import android.text.InputType;
import android.view.Gravity;
import android.view.View;
import android.widget.Button;
import android.widget.EditText;
import android.widget.LinearLayout;
import android.widget.ScrollView;
import android.widget.TextView;

import org.json.JSONArray;
import org.json.JSONObject;

import java.io.ByteArrayOutputStream;
import java.io.InputStream;
import java.net.HttpURLConnection;
import java.net.URL;
import java.nio.charset.StandardCharsets;
import java.util.Locale;

/**
 * Companion Workshop for Stardew Valley, not an unauthorised file mirror.
 * 
 * Nexus personal API keys are MEMORY ONLY and used solely on explicit taps
 * during QA. Register a public application with Nexus before production.
 * Download remains on official Nexus webpage. Imported ZIP is installed by
 * the ORIGINAL JunimoGate C# Mods manager's safe transactional importer.
 *
 * No mod archive scraping, no credentials persisted, no direct file-system
 * edits, no auto-install and no misleading "installed" success state.
 */
public final class AuroraWorkshopActivity extends Activity {
    private static final String NEXUS_WEB = "https://www.nexusmods.com/games/stardewvalley/mods";
    private static final String NEXUS_API = "https://api.nexusmods.com/v1/games/stardewvalley/mods/";
    private static final int DARK = 0xff121a22;
    private static final int CARD = 0xff23303c;
    private static final int PRIMARY = 0xffe9f4ff;
    private static final int SECONDARY = 0xffb8c9d5;
    private static final int ACCENT = 0xff91d8af;
    private static final int MAX_RESPONSE = 1024 * 1024;
    private static final int MAX_MODS = 30;

    private volatile boolean closed;
    private String personalApiKey; // memory-only; never send to logs, storage or website
    private LinearLayout feed;
    private TextView status;
    private EditText search;
    private int requestGeneration;

    @Override public void onCreate(Bundle state) {
        super.onCreate(state);
        setTitle("Aurora · Workshop");
        draw();
    }

    @Override protected void onDestroy() {
        closed = true;
        personalApiKey = null;
        requestGeneration++;
        super.onDestroy();
    }

    private void draw() {
        LinearLayout shell = new LinearLayout(this);
        shell.setOrientation(LinearLayout.VERTICAL);
        shell.setBackgroundColor(DARK);
        shell.setPadding(dp(15), dp(16), dp(15), dp(12));

        shell.addView(label("AURORA  /  WORKSHOP", 21, PRIMARY, true));
        TextView intro = label(
            "Официальный Nexus Mods · Stardew Valley. Моды скачиваются с Nexus, а ZIP устанавливаются штатным менеджером Aurora.",
            13, SECONDARY, false);
        intro.setPadding(0, dp(6), 0, dp(12));
        shell.addView(intro);

        LinearLayout nav = horizontal();
        nav.addView(makeButton("Мои моды", () -> {
            startActivity(new Intent(this, AuroraModOverviewActivity.class));
            finish();
        }), weighted());
        nav.addView(makeButton("Вкладка «Моды»", this::openAurora), weighted());
        shell.addView(nav);

        search = new EditText(this);
        search.setSingleLine(true);
        search.setHint("Найти мод на Nexus Mods");
        search.setTextColor(PRIMARY);
        search.setHintTextColor(SECONDARY);
        search.setTextSize(14);
        search.setPadding(dp(12), dp(5), dp(12), dp(5));
        search.setBackground(panel());
        LinearLayout.LayoutParams searchParams = new LinearLayout.LayoutParams(-1, dp(48));
        searchParams.topMargin = dp(12);
        shell.addView(search, searchParams);

        LinearLayout actions = horizontal();
        actions.addView(makeButton("Поиск", this::openSearch), weighted());
        actions.addView(makeButton("Все моды", () -> openNexus(NEXUS_WEB)), weighted());
        shell.addView(actions);

        LinearLayout sections = horizontal();
        sections.addView(makeButton("Популярные", () -> requestFeed("trending.json")), weighted());
        sections.addView(makeButton("Новинки", () -> requestFeed("latest_added.json")), weighted());
        shell.addView(sections);

        LinearLayout categories = horizontal();
        categories.addView(makeButton("Интерфейс", () -> openNexus(NEXUS_WEB + "?title=interface")), weighted());
        categories.addView(makeButton("Графика", () -> openNexus(NEXUS_WEB + "?title=visual")), weighted());
        shell.addView(categories);

        status = label(
            "Для встроенного каталога можно подключить личный Nexus API-ключ (только для тестирования). " +
            "Без него работает поиск и просмотр Nexus в браузере.",
            12, SECONDARY, false);
        status.setPadding(dp(3), dp(8), dp(3), dp(8));
        shell.addView(status);

        LinearLayout keyActions = horizontal();
        keyActions.addView(makeButton("Nexus API", this::promptForKey), weighted());
        keyActions.addView(makeButton("Как установить?", this::showInstallHelp), weighted());
        shell.addView(keyActions);

        ScrollView scroller = new ScrollView(this);
        feed = new LinearLayout(this);
        feed.setOrientation(LinearLayout.VERTICAL);
        feed.setPadding(0, dp(12), 0, dp(12));
        scroller.addView(feed);
        shell.addView(scroller, new LinearLayout.LayoutParams(-1, 0, 1));
        renderWelcome();
        setContentView(shell);
    }

    private void renderWelcome() {
        feed.removeAllViews();
        addPanel(
            "1 · Найди мод",
            "Ищи через Nexus или открой «Популярные» / «Новинки» с личным API-ключом.");
        addPanel(
            "2 · Скачай ZIP",
            "На официальной странице Nexus открой Files и выбери Manual Download. " +
            "Сайт сам применяет свои правила аккаунта и скачивания.");
        addPanel(
            "3 · Установи в Aurora",
            "Вернись в Aurora → Моды → Импорт → выбери скачанный ZIP, " +
            "затем добавь мод в активную группу. Перезапусти игру.");
        addPanel(
            "Проверка совместимости",
            "Не все моды для ПК совместимы с Android. Следи за обязательными " +
            "зависимостями и журналом SMAPI после запуска.");
    }

    private void showInstallHelp() {
        new AlertDialog.Builder(this).setTitle("Установка модов из Nexus")
            .setMessage("1. Открой мод в Workshop.\n" +
                "2. На Nexus Mods открой Files → Manual Download.\n" +
                "3. Дождись скачивания ZIP в браузере.\n" +
                "4. Вернись в Aurora → Моды → Импорт, выбери ZIP.\n" +
                "5. Активируй мод и его зависимости в нужной группе.\n\n" +
                "Автоматическая установка из Nexus в текущей QA-сборке ещё не поддерживается. " +
                "Не скачивай исполняемые APK под видом Stardew-модов.")
            .setPositiveButton("Открыть Aurora", (d, w) -> openAurora())
            .setNegativeButton("Закрыть", null).show();
    }

    private void openSearch() {
        String term = search.getText().toString().trim();
        if (term.isEmpty()) {
            openNexus(NEXUS_WEB);
            return;
        }
        try {
            String q = java.net.URLEncoder.encode(term, "UTF-8");
            openNexus(NEXUS_WEB + "?title=" + q);
        } catch (Exception error) {
            status.setText("Неправильный запрос");
        }
    }

    private void openNexus(String link) {
        if (!link.startsWith("https://www.nexusmods.com/")) {
            status.setText("Заблокирована небезопасная ссылка.");
            return;
        }
        try {
            Intent intent = new Intent(Intent.ACTION_VIEW, Uri.parse(link));
            intent.addCategory(Intent.CATEGORY_BROWSABLE);
            startActivity(intent);
        } catch (ActivityNotFoundException error) {
            new AlertDialog.Builder(this).setMessage("Не найден браузер для открытия Nexus Mods.")
                .setPositiveButton("OK", null).show();
        }
    }

    private void openAurora() {
        Intent main = new Intent();
        main.setClassName(getPackageName(), "org.junimogate.app.MainActivity");
        main.addFlags(Intent.FLAG_ACTIVITY_CLEAR_TOP | Intent.FLAG_ACTIVITY_SINGLE_TOP);
        try {
            startActivity(main);
            finish();
        } catch (RuntimeException error) {
            new AlertDialog.Builder(this).setMessage("Не удалось открыть Aurora: " + error.getClass().getSimpleName())
                .setPositiveButton("OK", null).show();
        }
    }

    private void promptForKey() {
        EditText input = new EditText(this);
        input.setSingleLine(true);
        input.setInputType(InputType.TYPE_CLASS_TEXT | InputType.TYPE_TEXT_VARIATION_PASSWORD);
        input.setHint("Nexus personal API key");
        input.setPadding(dp(18), dp(8), dp(18), dp(8));
        new AlertDialog.Builder(this).setTitle("Каталог Nexus · тестовый доступ")
            .setMessage("Личный API-ключ временно хранится только в памяти Aurora, не сохраняется на диске " +
                "и отправляется только напрямую api.nexusmods.com по HTTPS. Не используй чужой ключ. " +
                "Для публичного релиза потребуется регистрация приложения в Nexus.")
            .setView(input)
            .setPositiveButton("Подключить", (dialog, which) -> {
                String supplied = input.getText().toString().trim();
                input.getText().clear();
                if (supplied.length() < 16 || supplied.length() > 256 ||
                    !supplied.matches("[A-Za-z0-9_-]+")) {
                    status.setText("Некорректный формат ключа. Ключ не сохранён.");
                    personalApiKey = null;
                    return;
                }
                personalApiKey = supplied;
                status.setText("Nexus API-ключ активен только для этой сессии. Выбери «Популярные» или «Новинки».");
                requestFeed("trending.json");
            })
            .setNeutralButton("Удалить ключ", (dialog, which) -> {
                personalApiKey = null;
                requestGeneration++;
                status.setText("Личный ключ отключён.");
            })
            .setNegativeButton("Отмена", null).show();
    }

    private void requestFeed(String kind) {
        // Fixed allowlist, no arbitrary API URL construction from external data.
        if (!"trending.json".equals(kind) && !"latest_added.json".equals(kind)) return;
        String key = personalApiKey;
        if (key == null || key.isEmpty()) {
            status.setText("Для ленты нужен личный Nexus API-ключ. Открой Nexus API или используй поиск в браузере.");
            return;
        }
        final int generation = ++requestGeneration;
        status.setText("Получаем данные с Nexus Mods…");
        new Thread(() -> {
            try {
                JSONArray entries = getFeed(kind, key);
                runOnUiThread(() -> {
                    if (closed || generation != requestGeneration) return;
                    showFeed(entries, kind);
                });
            } catch (Exception error) {
                final String message = (error instanceof java.io.IOException) ?
                    "Nexus API недоступен или отклонил запрос. Проверь ключ, интернет и ограничения аккаунта." :
                    "Не удалось обработать ответ Nexus. Можно открыть сайт через поиск.";
                runOnUiThread(() -> {
                    if (!closed && generation == requestGeneration) status.setText(message);
                });
            }
        }, "AuroraNexusRequest").start();
    }

    private static JSONArray getFeed(String kind, String key) throws Exception {
        HttpURLConnection connection = null;
        try {
            URL url = new URL(NEXUS_API + kind);
            if (!"api.nexusmods.com".equalsIgnoreCase(url.getHost()) ||
                !"https".equalsIgnoreCase(url.getProtocol())) {
                throw new java.io.IOException("Not Nexus HTTPS API");
            }
            connection = (HttpURLConnection)url.openConnection();
            connection.setInstanceFollowRedirects(false); // NEVER forward API key to redirects
            connection.setRequestMethod("GET");
            connection.setConnectTimeout(9000);
            connection.setReadTimeout(12000);
            connection.setRequestProperty("apikey", key);
            connection.setRequestProperty("Application-Name", "SMAPI-Aurora");
            connection.setRequestProperty("Application-Version", "0.9.3-workshop-qa");
            connection.setRequestProperty("Accept", "application/json");
            if (connection.getResponseCode() != 200)
                throw new java.io.IOException("Nexus API HTTP " + connection.getResponseCode());
            try (InputStream stream = connection.getInputStream();
                 ByteArrayOutputStream out = new ByteArrayOutputStream()) {
                byte[] buffer = new byte[4096];
                int amount;
                while ((amount = stream.read(buffer)) != -1) {
                    if (out.size() + amount > MAX_RESPONSE)
                        throw new java.io.IOException("Nexus response too large");
                    out.write(buffer, 0, amount);
                }
                return new JSONArray(new String(out.toByteArray(), StandardCharsets.UTF_8));
            }
        } finally {
            if (connection != null) connection.disconnect();
        }
    }

    private void showFeed(JSONArray entries, String kind) {
        feed.removeAllViews();
        int displayed = 0;
        for (int i = 0; i < Math.min(entries.length(), MAX_MODS); i++) {
            JSONObject mod = entries.optJSONObject(i);
            if (mod == null) continue;
            int id = mod.optInt("mod_id", -1);
            if (id <= 0) continue;
            String title = mod.optString("name", "Мод #" + id);
            String author = mod.optString("author", "Не указан");
            String version = mod.optString("version", "");
            String desc = mod.optString("summary", "");
            if (title.length() > 160) title = title.substring(0, 160);
            if (desc.length() > 300) desc = desc.substring(0, 300);
            String page = "https://www.nexusmods.com/stardewvalley/mods/" + id + "?tab=files";
            addClickablePanel(title + " · " + version, "Автор: " + author + "\n" + desc +
                "\nНажми, чтобы открыть файлы мода на Nexus.", () -> openNexus(page));
            displayed++;
        }
        status.setText(("trending.json".equals(kind) ? "Популярные" : "Новые") +
            " моды на Nexus · показано " + displayed +
            ". Загрузка и установка требуют подтверждения пользователя на официальном сайте.");
        if (displayed == 0) addPanel("Ничего не найдено", "Открой общий каталог через поиск.");
    }

    private void addPanel(String name, String description) {
        addClickablePanel(name, description, null);
    }

    private void addClickablePanel(String name, String description, Runnable action) {
        LinearLayout panel = new LinearLayout(this);
        panel.setPadding(dp(13), dp(13), dp(13), dp(13));
        panel.setOrientation(LinearLayout.VERTICAL);
        panel.setBackground(panel());
        panel.addView(label(name, 16, PRIMARY, true));
        TextView summary = label(description, 13, SECONDARY, false);
        summary.setPadding(0, dp(5), 0, 0);
        panel.addView(summary);
        if (action != null) panel.setOnClickListener(view -> action.run());
        LinearLayout.LayoutParams params = new LinearLayout.LayoutParams(-1, -2);
        params.bottomMargin = dp(9);
        feed.addView(panel, params);
    }

    private LinearLayout horizontal() {
        LinearLayout row = new LinearLayout(this);
        row.setOrientation(LinearLayout.HORIZONTAL);
        return row;
    }

    private LinearLayout.LayoutParams weighted() {
        return new LinearLayout.LayoutParams(0, dp(48), 1);
    }

    private Button makeButton(String caption, Runnable action) {
        Button button = new Button(this);
        button.setText(caption);
        button.setTextSize(12);
        button.setAllCaps(false);
        button.setOnClickListener(view -> action.run());
        return button;
    }

    private TextView label(String caption, int size, int color, boolean bold) {
        TextView view = new TextView(this);
        view.setText(caption);
        view.setTextSize(size);
        view.setTextColor(color);
        if (bold) view.setTypeface(Typeface.DEFAULT, Typeface.BOLD);
        return view;
    }

    private GradientDrawable panel() {
        GradientDrawable gradient = new GradientDrawable();
        gradient.setColor(CARD);
        gradient.setCornerRadius(dp(12));
        return gradient;
    }
    private int dp(int n) { return Math.round(n * getResources().getDisplayMetrics().density); }
}

package org.junimogate.aurora;

import android.app.Activity;
import android.app.AlertDialog;
import android.content.Intent;
import android.graphics.Color;
import android.graphics.Typeface;
import android.graphics.drawable.GradientDrawable;
import android.os.Bundle;
import android.text.Editable;
import android.text.TextWatcher;
import android.view.View;
import android.widget.Button;
import android.widget.EditText;
import android.widget.LinearLayout;
import android.widget.ScrollView;
import android.widget.TextView;

import org.json.JSONArray;
import org.json.JSONException;
import org.json.JSONObject;

import java.io.ByteArrayOutputStream;
import java.io.File;
import java.io.FileInputStream;
import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.util.ArrayList;
import java.util.Collections;
import java.util.Comparator;
import java.util.HashMap;
import java.util.HashSet;
import java.util.List;
import java.util.Locale;
import java.util.Map;
import java.util.Set;

/**
 * Aurora v0.9.1: safe, strictly READ-ONLY companion to the original JunimoGate
 * Mods / Groups editors. Android launcher long-press shortcut opens this screen.
 *
 * Never writes the JunimoGate mod library, profiles or active selection: those
 * are versioned, transactional C# repositories and MUST be mutated through the
 * stock native SMAPI manager. No network / game mutations / new permissions.
 */
public final class AuroraModOverviewActivity extends Activity {
    private static final int BACKGROUND = 0xff131820;
    private static final int PANEL = 0xff202b38;
    private static final int TEXT = 0xfff0f3f7;
    private static final int MUTED = 0xffa5b4c4;
    private static final int GOOD = 0xff86d4a4;
    private static final int WARN = 0xffffc077;
    private static final int MAX_INDEX_BYTES = 8 * 1024 * 1024;
    private static final int MAX_PROFILE_BYTES = 1024 * 1024;
    private static final int MAX_ITEMS = 4096;
    private static final int MAX_VISIBLE = 200;

    private final List<ModRow> rows = new ArrayList<>();
    private LinearLayout listContainer;
    private TextView summary;
    private EditText search;
    private String activeGroupName = "";
    private boolean failed;

    private static final class ModRow {
        String id, name, author, version, libraryId, kind, status, details;
        boolean enabled, issue;
        final List<String> dependencies = new ArrayList<>();
    }

    private static final class ProfileMember {
        String uniqueId, libraryId;
        boolean enabled;
    }

    @Override
    protected void onCreate(Bundle state) {
        super.onCreate(state);
        setTitle("Aurora — менеджер модов");
        buildUi();
        refresh();
    }

    @Override
    protected void onResume() {
        super.onResume();
        if (summary != null) refresh();
    }

    private void buildUi() {
        LinearLayout page = new LinearLayout(this);
        page.setOrientation(LinearLayout.VERTICAL);
        page.setBackgroundColor(BACKGROUND);
        page.setPadding(dp(16), dp(16), dp(16), dp(12));

        TextView heading = text("AURORA  ·  MOD MANAGER", 20, TEXT, true);
        page.addView(heading);
        TextView description = text(
            "Состояние библиотеки и активной группы. Для установки ZIP, включения, удаления и редактирования — оригинальная вкладка «Моды» Aurora.",
            13, MUTED, false);
        description.setPadding(0, dp(8), 0, dp(12));
        page.addView(description);

        summary = text("Чтение библиотеки…", 14, TEXT, true);
        summary.setPadding(dp(12), dp(12), dp(12), dp(12));
        summary.setBackground(panel());
        page.addView(summary);

        LinearLayout actions = new LinearLayout(this);
        actions.setOrientation(LinearLayout.HORIZONTAL);
        actions.setPadding(0, dp(12), 0, dp(8));
        Button manager = button("Открыть Aurora");
        Button reload = button("Обновить");
        actions.addView(manager, new LinearLayout.LayoutParams(0, dp(52), 2));
        LinearLayout.LayoutParams reloadParams = new LinearLayout.LayoutParams(0, dp(52), 1);
        reloadParams.leftMargin = dp(8);
        actions.addView(reload, reloadParams);
        page.addView(actions);
        manager.setOnClickListener(view -> {
            Intent main = new Intent();
            main.setClassName(getPackageName(), "org.junimogate.app.MainActivity");
            main.addFlags(Intent.FLAG_ACTIVITY_CLEAR_TOP | Intent.FLAG_ACTIVITY_SINGLE_TOP);
            try {
                startActivity(main);
                finish();
            } catch (RuntimeException error) {
                new AlertDialog.Builder(this).setMessage("Не получилось открыть Aurora: " + error.getMessage())
                    .setPositiveButton("OK", null).show();
            }
        });
        reload.setOnClickListener(view -> refresh());

        search = new EditText(this);
        search.setSingleLine(true);
        search.setTextColor(TEXT);
        search.setHintTextColor(MUTED);
        search.setHint("Поиск по названию, ID или статусу");
        search.setTextSize(14);
        search.setPadding(dp(12), dp(4), dp(12), dp(4));
        search.setBackground(panel());
        page.addView(search, new LinearLayout.LayoutParams(-1, dp(46)));
        search.addTextChangedListener(new TextWatcher() {
            @Override public void beforeTextChanged(CharSequence s, int start, int count, int after) {}
            @Override public void onTextChanged(CharSequence s, int start, int before, int count) { render(); }
            @Override public void afterTextChanged(Editable value) {}
        });

        ScrollView scroll = new ScrollView(this);
        listContainer = new LinearLayout(this);
        listContainer.setOrientation(LinearLayout.VERTICAL);
        listContainer.setPadding(0, dp(10), 0, dp(14));
        scroll.addView(listContainer);
        page.addView(scroll, new LinearLayout.LayoutParams(-1, 0, 1));
        setContentView(page);
    }

    private void refresh() {
        rows.clear();
        failed = false;
        try {
            File root = new File(getNoBackupFilesDir(), "junimogate/user-data");
            File indexFile = new File(root, "mods/library-index.json");
            if (!indexFile.isFile()) {
                summary.setText("Библиотека пока пуста или ещё не создана.\nОткрой вкладку «Моды» в Aurora для импорта ZIP.");
                render();
                return;
            }
            JSONObject index = readJson(indexFile, MAX_INDEX_BYTES);
            if (!"junimogate-mod-library/v1".equals(index.optString("schema"))) {
                throw new IOException("Неизвестный формат индекса библиотеки");
            }
            JSONArray items = index.getJSONArray("items");
            if (items.length() > MAX_ITEMS) throw new IOException("Библиотека превышает безопасный лимит");

            File profileRoot = new File(root, "profiles");
            String activeId = "default";
            File selectionPath = new File(profileRoot, "active-profile.json");
            if (selectionPath.isFile()) {
                JSONObject selection = readJson(selectionPath, 16384);
                if (!"junimogate-active-mod-profile/v1".equals(selection.optString("schema"))) {
                    throw new IOException("Неизвестный формат выбора группы");
                }
                activeId = selection.getString("activeProfileId");
            }
            if (!activeId.matches("[A-Za-z0-9_-]{1,80}")) {
                throw new IOException("Некорректное имя активной группы");
            }
            File profilePath = new File(new File(profileRoot, activeId), "profile.json");
            JSONObject profile = profilePath.isFile() ? readJson(profilePath, MAX_PROFILE_BYTES) : null;
            if (profile != null && !"junimogate-mod-profile/v2".equals(profile.optString("schema"))) {
                throw new IOException("Неизвестный формат группы модов");
            }
            activeGroupName = profile != null ? profile.optString("displayName", activeId) : activeId;
            Map<String, ProfileMember> selected = new HashMap<>();
            if (profile != null) {
                JSONArray members = profile.getJSONArray("members");
                if (members.length() > MAX_ITEMS) throw new IOException("Группа слишком большая");
                for (int i = 0; i < members.length(); i++) {
                    JSONObject member = members.getJSONObject(i);
                    ProfileMember m = new ProfileMember();
                    m.uniqueId = member.getString("uniqueId");
                    m.libraryId = member.optString("libraryItemId", "");
                    m.enabled = member.optBoolean("enabled", false);
                    selected.put(m.uniqueId.toLowerCase(Locale.ROOT), m);
                }
            }

            Map<String, ModRow> byLibraryId = new HashMap<>();
            for (int i = 0; i < items.length(); i++) {
                JSONObject item = items.getJSONObject(i);
                JSONObject manifest = item.getJSONObject("manifest");
                ModRow row = new ModRow();
                row.libraryId = item.getString("libraryItemId");
                row.id = manifest.getString("uniqueId");
                row.name = manifest.optString("name", row.id);
                row.author = manifest.optString("author", "");
                row.version = manifest.optString("version", "?");
                row.kind = !manifest.isNull("contentPackForUniqueId") &&
                    !manifest.optString("contentPackForUniqueId").isEmpty() ? "Content Pack" : "C# мод";
                row.status = "В библиотеке · не активирован";
                row.details = "";
                JSONArray dependencies = manifest.optJSONArray("dependencies");
                if (dependencies != null) {
                    for (int j = 0; j < dependencies.length(); j++) {
                        JSONObject dep = dependencies.getJSONObject(j);
                        if (dep.optBoolean("isRequired", true)) {
                            String min = dep.isNull("minimumVersion") ? "" : dep.optString("minimumVersion", "");
                            row.dependencies.add(dep.optString("uniqueId") + "\t" + min);
                        }
                    }
                }
                String forId = manifest.isNull("contentPackForUniqueId") ? "" :
                    manifest.optString("contentPackForUniqueId", "");
                if (!forId.isEmpty()) row.dependencies.add(forId + "\t");
                ProfileMember member = selected.get(row.id.toLowerCase(Locale.ROOT));
                if (member != null && row.libraryId.equals(member.libraryId)) {
                    row.enabled = member.enabled;
                    row.status = row.enabled ? "В активной группе · включён" : "В активной группе · выключен";
                }
                rows.add(row);
                byLibraryId.put(row.libraryId, row);
            }

            // Missing bindings are visible, not silently considered installed.
            for (ProfileMember member : selected.values()) {
                if (member.enabled && !byLibraryId.containsKey(member.libraryId)) {
                    ModRow missing = new ModRow();
                    missing.id = member.uniqueId;
                    missing.name = member.uniqueId;
                    missing.version = "—";
                    missing.author = "";
                    missing.kind = "Отсутствует";
                    missing.status = "Ошибка: включён, но нужная версия не установлена";
                    missing.details = "Добавь нужную версию через Моды → Импорт ZIP или замени версию в редакторе группы.";
                    missing.issue = true;
                    rows.add(missing);
                }
            }
            Map<String, ModRow> enabled = new HashMap<>();
            for (ModRow row : rows) if (row.enabled) enabled.put(row.id.toLowerCase(Locale.ROOT), row);
            for (ModRow row : rows) {
                if (!row.enabled) continue;
                for (String token : row.dependencies) {
                    String[] bits = token.split("\t", -1);
                    String needed = bits[0].trim();
                    String minimum = bits.length > 1 ? bits[1].trim() : "";
                    if (needed.equalsIgnoreCase(row.id)) continue;
                    ModRow dependency = enabled.get(needed.toLowerCase(Locale.ROOT));
                    if (dependency == null) {
                        row.issue = true;
                        row.details += "Нет активной зависимости: " + needed +
                            (minimum.isEmpty() ? "" : " (от " + minimum + ")") + "\n";
                    } else if (!minimum.isEmpty() && compareVersions(dependency.version, minimum) < 0) {
                        row.issue = true;
                        row.details += "Версия зависимости " + needed + ": " + dependency.version +
                            ", нужна " + minimum + " или новее\n";
                    }
                }
                if (row.issue) row.status = "Включён · проверь зависимости";
            }
            Collections.sort(rows, Comparator.comparing((ModRow r) -> !r.issue)
                .thenComparing(r -> !r.enabled)
                .thenComparing(r -> r.name.toLowerCase(Locale.ROOT)));
            int active = 0, issues = 0;
            for (ModRow row : rows) {
                if (row.enabled) active++;
                if (row.issue) issues++;
            }
            summary.setText("Группа: " + activeGroupName + "\nВ библиотеке: " + items.length() +
                " · Включено: " + active + " · Замечаний: " + issues +
                "\nОценка основана на метаданных; итоговую совместимость проверяй в журнале SMAPI.");
        } catch (Exception error) {
            failed = true;
            rows.clear();
            summary.setText("Не удалось прочитать библиотеку модов: " + error.getMessage() +
                "\nНичего не изменено. Открой оригинальную вкладку «Моды».");
        }
        render();
    }

    /** Conservative numeric-component check; prereleases never satisfy a stable minimum. */
    private static int compareVersions(String installed, String required) {
        String[] a = installed.split("[.-]", -1);
        String[] b = required.split("[.-]", -1);
        for (int i = 0; i < Math.max(a.length, b.length); i++) {
            String x = i < a.length ? a[i] : "0";
            String y = i < b.length ? b[i] : "0";
            if (!x.matches("[0-9]+") || !y.matches("[0-9]+")) return -1;
            try {
                int cmp = Long.compare(Long.parseLong(x), Long.parseLong(y));
                if (cmp != 0) return cmp;
            } catch (NumberFormatException error) {
                return -1;
            }
        }
        return 0;
    }

    private static JSONObject readJson(File file, int limit) throws IOException, JSONException {
        if (!file.isFile() || file.length() > limit || file.length() < 2) {
            throw new IOException("Недоступен файл " + file.getName());
        }
        try (FileInputStream input = new FileInputStream(file);
             ByteArrayOutputStream output = new ByteArrayOutputStream()) {
            byte[] buffer = new byte[8192];
            int count;
            while ((count = input.read(buffer)) >= 0) {
                if (output.size() + count > limit) throw new IOException("Слишком большой файл");
                output.write(buffer, 0, count);
            }
            return new JSONObject(new String(output.toByteArray(), StandardCharsets.UTF_8));
        }
    }

    private void render() {
        if (listContainer == null) return;
        listContainer.removeAllViews();
        if (failed || rows.isEmpty()) {
            TextView empty = text(failed ? "Диагностика недоступна." : "Пока нет модов для отображения.",
                14, MUTED, false);
            listContainer.addView(empty);
            return;
        }
        String needle = search == null ? "" : search.getText().toString().trim().toLowerCase(Locale.ROOT);
        int shown = 0, total = 0;
        for (ModRow row : rows) {
            if (!(row.name + " " + row.id + " " + row.status + " " + row.author)
                .toLowerCase(Locale.ROOT).contains(needle)) continue;
            total++;
            if (shown >= MAX_VISIBLE) continue;
            shown++;
            LinearLayout card = new LinearLayout(this);
            card.setOrientation(LinearLayout.VERTICAL);
            card.setPadding(dp(12), dp(12), dp(12), dp(12));
            card.setBackground(panel());
            TextView title = text(row.name + "  " + row.version, 16, TEXT, true);
            card.addView(title);
            TextView subtitle = text(row.kind + " · " + row.id, 12, MUTED, false);
            card.addView(subtitle);
            TextView status = text(row.status, 13, row.issue ? WARN : row.enabled ? GOOD : MUTED, false);
            status.setPadding(0, dp(6), 0, 0);
            card.addView(status);
            card.setOnClickListener(view -> {
                String details = "ID: " + row.id + "\nАвтор: " + row.author +
                    "\nВерсия: " + row.version + "\nТип: " + row.kind +
                    "\nСостояние: " + row.status +
                    (row.details.isEmpty() ? "" : "\n\n" + row.details);
                new AlertDialog.Builder(this).setTitle(row.name).setMessage(details)
                    .setPositiveButton("Закрыть", null).show();
            });
            LinearLayout.LayoutParams p = new LinearLayout.LayoutParams(-1, -2);
            p.bottomMargin = dp(8);
            listContainer.addView(card, p);
        }
        if (total > shown) {
            listContainer.addView(text("Показано " + shown + " из " + total + ". Уточни поиск.",
                13, MUTED, false));
        } else if (total == 0) {
            listContainer.addView(text("Ничего не найдено.", 13, MUTED, false));
        }
    }

    private TextView text(String value, int size, int color, boolean bold) {
        TextView label = new TextView(this);
        label.setText(value);
        label.setTextSize(size);
        label.setTextColor(color);
        if (bold) label.setTypeface(Typeface.DEFAULT, Typeface.BOLD);
        return label;
    }

    private Button button(String value) {
        Button button = new Button(this);
        button.setText(value);
        button.setAllCaps(false);
        return button;
    }

    private GradientDrawable panel() {
        GradientDrawable shape = new GradientDrawable();
        shape.setColor(PANEL);
        shape.setCornerRadius(dp(12));
        return shape;
    }

    private int dp(int value) { return Math.round(value * getResources().getDisplayMetrics().density); }
}

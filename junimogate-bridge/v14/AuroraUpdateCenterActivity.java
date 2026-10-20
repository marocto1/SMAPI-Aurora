package org.junimogate.aurora;

import android.app.Activity;
import android.app.AlertDialog;
import android.content.ActivityNotFoundException;
import android.content.Intent;
import android.content.pm.PackageInfo;
import android.content.pm.PackageManager;
import android.graphics.Typeface;
import android.graphics.drawable.GradientDrawable;
import android.net.Uri;
import android.os.Bundle;
import android.widget.Button;
import android.widget.LinearLayout;
import android.widget.ScrollView;
import android.widget.TextView;

/**
 * v1.4 Safe Update Center: the *Android platform* remains the only APK
 * installer and enforces app identity/signature. Do not bypass Android.
 * Future installer is blocked until a long-lived signing key is configured.
 * Coop readiness is an informational checklist, NOT a VPN or multiplayer.
 */
public final class AuroraUpdateCenterActivity extends Activity {
    private static final String RELEASES =
        "https://github.com/marocto1/SMAPI-Aurora/releases";
    private static final String GAME_PACKAGE = "com.chucklefish.stardewvalley";
    private int surface, panel, onSurface, secondary, accent;

    @Override public void onCreate(Bundle state) {
        super.onCreate(state);
        setTitle("Aurora · Update Center");
        surface = color("junimo_surface", 0xff111422);
        panel = color("junimo_surface_container", 0xff222b40);
        onSurface = color("junimo_on_surface", 0xffeceefa);
        secondary = color("junimo_on_surface_variant", 0xffbfc5de);
        accent = color("junimo_primary", 0xffb8c5ff);
        draw();
    }

    private void draw() {
        ScrollView scroller = new ScrollView(this);
        scroller.setFillViewport(true);
        scroller.setBackgroundColor(surface);
        LinearLayout shell = new LinearLayout(this);
        shell.setOrientation(LinearLayout.VERTICAL);
        shell.setPadding(dp(17), dp(24), dp(17), dp(24));
        scroller.addView(shell);

        heading(shell, "AURORA  /  UPDATE CENTER");
        sub(shell,"Обновления, защита данных и подготовка кооператива");
        LinearLayout info = card(shell);
        info.addView(label("Установленная Aurora", 16, onSurface, true));
        info.addView(label(launcherInfo(), 14, secondary, false));
        info.addView(label("Stardew Valley: " + installedGameInfo(), 13, secondary, false));

        LinearLayout safe = card(shell);
        safe.addView(label("Обновление без потери данных", 16, onSurface, true));
        safe.addView(label(
            "Проверка подписи APK выполняется Android. Тестовые версии Aurora могли быть подписаны разными ключами: " +
            "не удаляй рабочую сборку без отдельно проверенной копии модов, профилей и сохранений. " +
            "Постоянная подпись для будущих релизов ещё не объявлена.",
            13, secondary, false));
        safe.addView(button("Резервная копия и проверка ZIP", () ->
            startActivity(new Intent(this, AuroraBackupActivity.class))));
        safe.addView(button("Релизы Aurora на GitHub", this::openReleases));

        LinearLayout mods = card(shell);
        mods.addView(label("Совместимость модов", 16, onSurface, true));
        mods.addView(label(
            "Проверь активный профиль, зависимости и журнал SMAPI. " +
            "Обзор модов читает библиотеку, но не удаляет и не изменяет её.",
            13, secondary, false));
        mods.addView(button("Открыть диагностику", () ->
            startActivity(new Intent(this, AuroraModOverviewActivity.class))));

        LinearLayout coop = card(shell);
        coop.addView(label("Aurora Coop · подготовка Android ↔ ПК", 16, onSurface, true));
        coop.addView(label(
            "Сейчас Aurora НЕ создаёт виртуальную сеть и НЕ обеспечивает Android ↔ ПК кооператив. " +
            "Для будущего подключения потребуется отдельно проверить поддержку мультиплеера игровыми сборками, " +
            "сетевое соединение и совместимость модов на двух устройствах.",
            13, secondary, false));
        coop.addView(button("Поделиться версиями для совместимости", this::shareSetup));
        coop.addView(button("Подробнее о кооперативе", this::explainCoop));

        shell.addView(button("Вернуться в Aurora", this::finish));
        setContentView(scroller);
    }

    private String launcherInfo() {
        try {
            PackageInfo p = getPackageManager().getPackageInfo(getPackageName(), 0);
            return (p.versionName == null ? "неизвестная версия" : p.versionName) +
                " · Android package " + p.packageName;
        } catch (PackageManager.NameNotFoundException e) {
            return "Версия лаунчера недоступна";
        }
    }

    private String installedGameInfo() {
        try {
            PackageInfo p = getPackageManager().getPackageInfo(GAME_PACKAGE, 0);
            return p.versionName != null ? p.versionName : "неизвестная версия";
        } catch (PackageManager.NameNotFoundException e) {
            // Android package visibility may hide even an installed game.
            return "не определена или не видна приложению";
        }
    }

    private void shareSetup() {
        Intent send = new Intent(Intent.ACTION_SEND);
        send.setType("text/plain");
        send.putExtra(Intent.EXTRA_SUBJECT, "Aurora · Coop compatibility");
        send.putExtra(Intent.EXTRA_TEXT,
            "Aurora compatibility information\n" +
            "Launcher: " + launcherInfo() + "\n" +
            "Game version: " + installedGameInfo() + "\n" +
            "Device: Android\n" +
            "Multiplayer: not implemented by Aurora launcher\n" +
            "Before pairing: compare Stardew build, SMAPI build, and active mod lists.\n" +
            "No private profiles, account credentials or save files attached.");
        try {
            startActivity(Intent.createChooser(send, "Поделиться сведениями Aurora"));
        } catch (ActivityNotFoundException e) {
            message("Нет приложения для отправки сведений.");
        }
    }

    private void openReleases() {
        try {
            Intent intent=new Intent(Intent.ACTION_VIEW, Uri.parse(RELEASES));
            intent.addCategory(Intent.CATEGORY_BROWSABLE);
            startActivity(intent);
        } catch (ActivityNotFoundException e) {
            message("Не найден браузер. GitHub: " + RELEASES);
        }
    }
    private void explainCoop() {
        new AlertDialog.Builder(this)
            .setTitle("Aurora Coop — не включён в RC")
            .setMessage("План: сравнение версии игры/SMAPI/модов, проверка поддержки мультиплеера " +
                "на Android и ПК, затем отдельный согласованный протокол подключения. " +
                "VPN-туннель и автоматическое подключение пока не реализованы. " +
                "Лаунчер не станет утверждать, что кооператив запущен, без реального соединения.")
            .setPositiveButton("Понятно", null).show();
    }
    private void message(String value) {
        new AlertDialog.Builder(this).setMessage(value)
            .setPositiveButton("OK", null).show();
    }
    private int color(String key,int backup) {
        return AuroraWorkshopTabsView.themeColor(this,key,backup);
    }
    private LinearLayout card(LinearLayout parent) {
        LinearLayout result=new LinearLayout(this);
        result.setOrientation(LinearLayout.VERTICAL);
        result.setPadding(dp(15),dp(17),dp(15),dp(17));
        GradientDrawable background=new GradientDrawable();
        background.setColor(panel);
        background.setCornerRadius(dp(17));
        result.setBackground(background);
        LinearLayout.LayoutParams p=new LinearLayout.LayoutParams(-1,-2);
        p.topMargin=dp(14);
        parent.addView(result,p);
        return result;
    }
    private void heading(LinearLayout box,String title) {
        box.addView(label(title,21,onSurface,true));
    }
    private void sub(LinearLayout box,String value) {
        TextView t=label(value,13,secondary,false);
        t.setPadding(0,dp(7),0,0);
        box.addView(t);
    }
    private TextView label(String value,int sp,int color,boolean bold) {
        TextView t=new TextView(this);
        t.setText(value);
        t.setTextSize(sp);
        t.setTextColor(color);
        if(bold)t.setTypeface(Typeface.DEFAULT,Typeface.BOLD);
        t.setPadding(0,dp(5),0,dp(7));
        return t;
    }
    private Button button(String title,Runnable action) {
        Button b=new Button(this);
        b.setText(title);
        b.setAllCaps(false);
        b.setOnClickListener(v -> action.run());
        return b;
    }
    private int dp(int n){return Math.round(n*getResources().getDisplayMetrics().density);}
}

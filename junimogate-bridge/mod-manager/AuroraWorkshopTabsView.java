package org.junimogate.aurora;

import android.app.Activity;
import android.content.Context;
import android.content.ContextWrapper;
import android.content.Intent;
import android.graphics.Color;
import android.graphics.Typeface;
import android.graphics.drawable.GradientDrawable;
import android.util.AttributeSet;
import android.util.TypedValue;
import android.view.Gravity;
import android.view.View;
import android.widget.LinearLayout;
import android.widget.TextView;
import java.lang.ref.WeakReference;

/**
 * Native workshop navigation inside the ORIGINAL stock Mods fragment.
 * Loaded through a single XML view in fragment_mods.xml, with no changes to
 * the compiled Xamarin/SMAPI .NET launcher or mod repository.
 */
public final class AuroraWorkshopTabsView extends LinearLayout {
    private static WeakReference<Activity> originalModsActivity = new WeakReference<>(null);
    public AuroraWorkshopTabsView(Context context) {
        this(context, null);
    }

    public AuroraWorkshopTabsView(Context context, AttributeSet attrs) {
        super(context, attrs);
        setOrientation(VERTICAL);
        setPadding(dp(12), dp(4), dp(12), dp(4));
        setBackgroundColor(themeColor(context, "junimo_surface", 0xfff7f9f4));

        LinearLayout primary = new LinearLayout(context);
        primary.setOrientation(HORIZONTAL);
        TextView installed = tab("Установленные", true);
        installed.setContentDescription("Текущая вкладка: установленные моды");
        primary.addView(installed, new LayoutParams(0, dp(46), 1));
        TextView workshop = tab("Workshop", false);
        workshop.setContentDescription("Workshop внутри Aurora");
        primary.addView(workshop, new LayoutParams(0, dp(46), 1));
        workshop.setOnClickListener(v -> openWorkshop());
        addView(primary,new LayoutParams(LayoutParams.MATCH_PARENT,dp(46)));

        LinearLayout utilities=new LinearLayout(context);
        utilities.setOrientation(HORIZONTAL);
        TextView backups=tab("Копии",false);
        TextView versions=tab("Версии",false);
        TextView diagnostics=tab("Диагностика",false);
        backups.setContentDescription("Резервное копирование и восстановление Aurora");
        versions.setContentDescription("Настройки версий Stardew Valley");
        diagnostics.setContentDescription("Анализ зависимостей модов и экспорт отчёта");
        utilities.addView(backups,new LayoutParams(0,dp(42),1));
        utilities.addView(versions,new LayoutParams(0,dp(42),1));
        utilities.addView(diagnostics,new LayoutParams(0,dp(42),1));
        addView(utilities,new LayoutParams(LayoutParams.MATCH_PARENT,dp(42)));
        backups.setOnClickListener(v -> context.startActivity(
            new Intent(context,AuroraBackupActivity.class)));
        versions.setOnClickListener(v -> context.startActivity(
            new Intent(context,AuroraVersionActivity.class)));
        diagnostics.setOnClickListener(v -> context.startActivity(
            new Intent(context,AuroraModOverviewActivity.class)));

        setContentDescription("Вкладки Aurora: моды, Workshop, копии, версии, диагностика");
    }

    private TextView tab(String text, boolean selected) {
        TextView view = new TextView(getContext());
        view.setText(text);
        view.setGravity(Gravity.CENTER);
        view.setTextSize(TypedValue.COMPLEX_UNIT_SP, 14);
        view.setTypeface(Typeface.DEFAULT, selected ? Typeface.BOLD : Typeface.NORMAL);
        int green = themeColor(getContext(), "junimo_primary", 0xff52733d);
        int muted = themeColor(getContext(), "junimo_on_surface_variant", 0xff586256);
        view.setTextColor(selected ? green : muted);
        GradientDrawable background = new GradientDrawable();
        background.setColor(themeColor(getContext(),
            selected ? "junimo_primary_container" : "junimo_surface_container_low", 
            selected ? 0xffdfefd2 : 0xfff2f5ef));
        background.setCornerRadius(dp(14));
        view.setBackground(background);
        return view;
    }

    private void openWorkshop() {
        Context context = getContext();
        originalModsActivity = new WeakReference<>(findActivity(context));
        Intent intent = new Intent(context, AuroraWorkshopActivity.class);
        if (findActivity(context) == null) intent.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK);
        context.startActivity(intent);
    }

    /**
     * Return to the original C# Mods screen and invoke its existing import
     * button, letting the STOCK ModArchiveInstallTransaction safely scan the
     * user's picked ZIP. Never write directly into the mod library.
     */
    static boolean requestOriginalZipImport() {
        Activity host = originalModsActivity.get();
        if (host == null || host.isFinishing() || host.isDestroyed()) return false;
        int importId = host.getResources().getIdentifier(
            "mods_import", "id", host.getPackageName());
        if (importId == 0) return false;
        View root = host.getWindow().getDecorView();
        root.postDelayed(() -> {
            if (host.isFinishing() || host.isDestroyed()) return;
            View button = host.findViewById(importId);
            if (button != null && button.isShown() && button.isEnabled()) {
                button.performClick(); // stock Aurora picker and transaction
            }
        }, 400L);
        return true;
    }

    static Activity findActivity(Context context) {
        for (int i = 0; i < 8 && context instanceof ContextWrapper; i++) {
            if (context instanceof Activity) return (Activity) context;
            Context next = ((ContextWrapper) context).getBaseContext();
            if (next == context) break;
            context = next;
        }
        return context instanceof Activity ? (Activity) context : null;
    }

    static int themeColor(Context context, String color, int fallback) {
        int id = context.getResources().getIdentifier(color, "color", context.getPackageName());
        if (id == 0) return fallback;
        try { return context.getColor(id); } catch (RuntimeException error) { return fallback; }
    }

    private int dp(int amount) {
        return Math.round(amount * getResources().getDisplayMetrics().density);
    }
}

package com.marocto.smapi.aurora.preview;

import android.content.Context;
import android.content.Intent;
import android.content.pm.ApplicationInfo;
import android.content.pm.PackageInfo;
import android.content.pm.PackageManager;
import android.content.pm.ResolveInfo;
import android.os.Build;
import java.io.File;
import java.io.IOException;
import java.util.ArrayList;
import java.util.Collections;
import java.util.Comparator;
import java.util.HashSet;
import java.util.List;
import java.util.Locale;
import java.util.Set;
import java.util.zip.ZipEntry;
import java.util.zip.ZipFile;

final class GameScanner {
    static final String PLAY = "com.chucklefish.stardewvalley";
    static final String SAMSUNG = "com.chucklefish.stardewvalleysamsung";

    static final class Candidate {
        final String packageName;
        final String label;
        Candidate(String pkg, String title) { packageName = pkg; label = title; }
        @Override public String toString() { return label + "\n" + packageName; }
    }

    static final class Report {
        String packageName = "";
        String label = "";
        String version = "";
        String contentApk = "";
        int apkCount = 0;
        int assemblyApks = 0;
        final List<String> warnings = new ArrayList<>();
        boolean valid() { return warnings.isEmpty(); }
        String summary() {
            if (packageName.isEmpty()) return "Игра пока не выбрана";
            if (valid()) return "Структура APK распознана";
            return warnings.get(0);
        }
        String detail() {
            StringBuilder s = new StringBuilder();
            s.append("Приложение: ").append(label).append("\nПакет: ").append(packageName);
            s.append("\nВерсия: ").append(version).append("\nAPK-файлов: ").append(apkCount);
            s.append("\nРесурсы Content: ").append(contentApk.isEmpty() ? "не обнаружены" : new File(contentApk).getName());
            s.append("\nАрхивов .NET-сборок: ").append(assemblyApks);
            if (!warnings.isEmpty()) {
                s.append("\n\nОбнаруженные проблемы:");
                for (String w : warnings) s.append("\n• ").append(w);
            }
            s.append("\n\nЭто проверка структуры APK, а не подлинности, лицензии или работоспособности SMAPI.");
            return s.toString();
        }
    }

    static List<Candidate> candidates(Context ctx) {
        PackageManager pm = ctx.getPackageManager();
        List<Candidate> found = new ArrayList<>();
        Set<String> visited = new HashSet<>();
        Intent main = new Intent(Intent.ACTION_MAIN);
        main.addCategory(Intent.CATEGORY_LAUNCHER);
        List<ResolveInfo> result = pm.queryIntentActivities(main, 0);
        for (ResolveInfo activity : result) {
            if (activity.activityInfo == null || activity.activityInfo.packageName == null) continue;
            String pkg = activity.activityInfo.packageName;
            if (!visited.add(pkg)) continue;
            CharSequence display = activity.loadLabel(pm);
            found.add(new Candidate(pkg, display == null ? pkg : display.toString()));
        }
        for (String official : new String[] { PLAY, SAMSUNG }) {
            if (!visited.contains(official)) {
                try {
                    getInfo(pm, official);
                    found.add(new Candidate(official, "Stardew Valley"));
                } catch (Exception ignored) { }
            }
        }
        Collections.sort(found, (a,b) -> {
            boolean x = resemblesStardew(a), y = resemblesStardew(b);
            if (x != y) return x ? -1 : 1;
            return a.label.compareToIgnoreCase(b.label);
        });
        return found;
    }

    static boolean resemblesStardew(Candidate c) {
        return c.label.toLowerCase(Locale.ROOT).contains("stardew") ||
               c.packageName.toLowerCase(Locale.ROOT).contains("stardew") ||
               c.packageName.equals(PLAY) || c.packageName.equals(SAMSUNG);
    }

    private static PackageInfo getInfo(PackageManager pm, String pkg) throws PackageManager.NameNotFoundException {
        if (Build.VERSION.SDK_INT >= 33)
            return pm.getPackageInfo(pkg, PackageManager.PackageInfoFlags.of(0));
        return pm.getPackageInfo(pkg, 0);
    }

    static Report scan(Context ctx, String pkg) {
        Report out = new Report();
        if (pkg == null || pkg.trim().isEmpty()) {
            out.warnings.add("Выбери установленную игру");
            return out;
        }
        out.packageName = pkg;
        PackageManager pm = ctx.getPackageManager();
        try {
            PackageInfo info = getInfo(pm, pkg);
            ApplicationInfo application = info.applicationInfo;
            out.label = application == null ? pkg : pm.getApplicationLabel(application).toString();
            out.version = info.versionName == null ? "неизвестна" : info.versionName;
            List<String> apks = new ArrayList<>();
            if (application != null && application.sourceDir != null)
                apks.add(application.sourceDir);
            if (application != null && application.splitSourceDirs != null)
                for (String split : application.splitSourceDirs)
                    if (!apks.contains(split)) apks.add(split);
            if (apks.isEmpty()) out.warnings.add("Файлы APK недоступны");
            for (String path : apks) {
                if (!new File(path).isFile()) {
                    out.warnings.add("Невозможно прочитать APK: " + new File(path).getName());
                    continue;
                }
                try (ZipFile archive = new ZipFile(path)) {
                    out.apkCount++;
                    boolean content = false, assemblies = false;
                    java.util.Enumeration<? extends ZipEntry> entries = archive.entries();
                    while (entries.hasMoreElements()) {
                        String name = entries.nextElement().getName().toLowerCase(Locale.ROOT);
                        if (name.startsWith("assets/content/")) content = true;
                        if ((name.startsWith("assemblies/") && name.endsWith(".blob")) ||
                            (name.startsWith("lib/") && name.contains("libassemblies.") && name.endsWith(".blob.so")))
                            assemblies = true;
                    }
                    if (content && out.contentApk.isEmpty()) out.contentApk = path;
                    if (assemblies) out.assemblyApks++;
                } catch (IOException ex) {
                    out.warnings.add("Ошибка чтения APK: " + new File(path).getName());
                }
            }
            if (out.contentApk.isEmpty()) out.warnings.add("В APK нет assets/Content/");
            if (out.assemblyApks == 0) out.warnings.add("В APK нет .NET assembly store");
            if (!minimumVersion(out.version, 1, 6, 15, 3))
                out.warnings.add("Требуется версия игры не ниже 1.6.15.3");
        } catch (PackageManager.NameNotFoundException ex) {
            out.warnings.add("Приложение не установлено или скрыто настройками Android");
        } catch (Exception ex) {
            out.warnings.add("Ошибка проверки: " + ex.getClass().getSimpleName());
        }
        return out;
    }

    static boolean minimumVersion(String version, int... minimum) {
        if (version == null) return false;
        String[] values = version.split("[.\\-]");
        for (int i=0; i<minimum.length; i++) {
            int v;
            try { v = i<values.length ? Integer.parseInt(values[i]) : 0; }
            catch (NumberFormatException e) { return false; }
            if (v > minimum[i]) return true;
            if (v < minimum[i]) return false;
        }
        return true;
    }
}

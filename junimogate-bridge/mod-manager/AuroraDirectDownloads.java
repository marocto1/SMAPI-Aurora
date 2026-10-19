package org.junimogate.aurora;

import android.app.Activity;
import android.content.ContentResolver;
import android.content.ContentValues;
import android.net.Uri;
import android.os.Build;
import android.os.Handler;
import android.os.Looper;
import android.provider.MediaStore;

import java.io.File;
import java.io.FileInputStream;
import java.io.FileOutputStream;
import java.io.InputStream;
import java.io.OutputStream;
import java.net.HttpURLConnection;
import java.net.URL;
import java.security.MessageDigest;
import java.util.Locale;
import java.util.zip.ZipEntry;
import java.util.zip.ZipInputStream;

/**
 * Download ONLY explicitly curated, author-permitted public GitHub Release ZIPs.
 * Does not attempt protected Nexus file links, does not scrape and NEVER edits
 * SMAPI's private ModLibrary/Profile JSON or game saves. The original
 * ModsFragment->Import picker remains the actual transactional installer.
 */
public final class AuroraDirectDownloads {
    private static final long MAX_ZIP_BYTES = 64L * 1024 * 1024;
    private static final long MAX_UNCOMPRESSED_BYTES = 256L * 1024 * 1024;
    private static final int MAX_ZIP_ENTRIES = 4096;
    private static final int MAX_REDIRECTS = 6;
    private static final Handler MAIN = new Handler(Looper.getMainLooper());

    private AuroraDirectDownloads() {}

    public static final class Entry {
        public final String name, version, source, url, sha256, fileName, description;
        public Entry(String name, String version, String source, String url,
                     String sha256, String fileName, String description) {
            this.name = name;
            this.version = version;
            this.source = source;
            this.url = url;
            this.sha256 = sha256;
            this.fileName = fileName;
            this.description = description;
        }
    }

    /** Controlled by the Aurora authors. Future entries require author consent. */
    public static final Entry[] CURATED = new Entry[] {
        new Entry(
            "Aurora SMAPI Launch Smoke Test", "1.0.0", "Aurora / GitHub Releases",
            "https://github.com/marocto1/SMAPI-Aurora/releases/download/" +
                "v0.8.8-smapi-smoke-qa/Aurora-SMAPI-Smoke-Mod-v1.0.0.zip",
            "c314427ab39d5c061938fccf50a089c811040a8087a7cd946489d69561e67268",
            "Aurora-SMAPI-Smoke-Mod-v1.0.0.zip",
            "Безопасный C# тест SMAPI: выводит диагностические события. Не меняет сохранение.")
    };

    public interface Listener {
        void onProgress(String message);
        void onReady(Uri publicDownloadsUri, String fileName);
        void onFailure(String message);
    }

    public static void download(Activity activity, Entry item, Listener listener) {
        if (Build.VERSION.SDK_INT < 29) {
            listener.onFailure("Прямая загрузка поддерживается на Android 10+.");
            return;
        }
        if (!isCuratedEntry(item)) {
            listener.onFailure("Мод отсутствует в проверенном каталоге.");
            return;
        }
        final File cacheDir = new File(activity.getCacheDir(), "aurora-workshop");
        new Thread(() -> {
            File stage = null;
            Uri record = null;
            try {
                if (!cacheDir.isDirectory() && !cacheDir.mkdirs()) {
                    throw new IllegalStateException("Cannot create temporary cache");
                }
                stage = File.createTempFile("verified-", ".zip", cacheDir);
                post(activity, () -> listener.onProgress("Загрузка с официального GitHub…"));
                downloadVerified(item, stage);
                post(activity, () -> listener.onProgress("Архив проверен. Сохранение в Загрузки…"));

                ContentResolver resolver = activity.getContentResolver();
                ContentValues values = new ContentValues();
                values.put(MediaStore.Downloads.DISPLAY_NAME, item.fileName);
                values.put(MediaStore.Downloads.MIME_TYPE, "application/zip");
                values.put(MediaStore.Downloads.RELATIVE_PATH, "Download/Aurora");
                values.put(MediaStore.Downloads.IS_PENDING, 1);
                record = resolver.insert(MediaStore.Downloads.EXTERNAL_CONTENT_URI, values);
                if (record == null) throw new IllegalStateException("Cannot allocate download");
                try (FileInputStream input = new FileInputStream(stage);
                     OutputStream output = resolver.openOutputStream(record, "w")) {
                    if (output == null) throw new IllegalStateException("Cannot open download");
                    copy(input, output, MAX_ZIP_BYTES);
                }
                values.clear();
                values.put(MediaStore.Downloads.IS_PENDING, 0);
                if (resolver.update(record, values, null, null) < 1)
                    throw new IllegalStateException("Cannot publish download");
                Uri ready = record;
                record = null;
                post(activity, () -> listener.onReady(ready, item.fileName));
            } catch (Exception error) {
                if (record != null) {
                    try { activity.getContentResolver().delete(record, null, null); }
                    catch (Exception ignored) {}
                }
                post(activity, () -> listener.onFailure(
                    "Загрузка не выполнена или проверка не пройдена. " +
                    "Библиотека модов не изменена."));
            } finally {
                if (stage != null && stage.exists()) stage.delete();
            }
        }, "AuroraVerifiedDownload").start();
    }

    private static boolean isCuratedEntry(Entry entry) {
        if (entry == null) return false;
        for (Entry candidate : CURATED) {
            if (candidate == entry && candidate.sha256.matches("[a-f0-9]{64}") &&
                candidate.fileName.matches("[A-Za-z0-9._-]+[.]zip"))
                return true;
        }
        return false;
    }

    private static void downloadVerified(Entry entry, File outputFile) throws Exception {
        URL link = new URL(entry.url);
        for (int redirect = 0; redirect <= MAX_REDIRECTS; redirect++) {
            if (!allowedGithubReleaseHost(link))
                throw new SecurityException("Untrusted download host");
            HttpURLConnection connection = (HttpURLConnection) link.openConnection();
            connection.setConnectTimeout(10000);
            connection.setReadTimeout(20000);
            connection.setInstanceFollowRedirects(false);
            connection.setRequestMethod("GET");
            connection.setRequestProperty("Accept", "application/octet-stream");
            try {
                int status = connection.getResponseCode();
                if (status == 301 || status == 302 || status == 303 || status == 307 || status == 308) {
                    String location = connection.getHeaderField("Location");
                    if (location == null || redirect == MAX_REDIRECTS)
                        throw new SecurityException("Invalid download redirect");
                    link = new URL(link, location);
                    continue;
                }
                if (status != 200)
                    throw new IllegalStateException("Download unavailable: HTTP " + status);
                long declared = connection.getContentLengthLong();
                if (declared > MAX_ZIP_BYTES)
                    throw new SecurityException("Archive exceeds size limit");
                MessageDigest digest = MessageDigest.getInstance("SHA-256");
                long size = 0;
                try (InputStream input = connection.getInputStream();
                     FileOutputStream output = new FileOutputStream(outputFile)) {
                    byte[] buffer = new byte[32768];
                    int count;
                    while ((count = input.read(buffer)) != -1) {
                        size += count;
                        if (size > MAX_ZIP_BYTES)
                            throw new SecurityException("Archive exceeds size limit");
                        digest.update(buffer, 0, count);
                        output.write(buffer, 0, count);
                    }
                    output.getFD().sync();
                }
                if (size == 0) throw new SecurityException("Empty ZIP");
                String actualHash = asHex(digest.digest());
                if (!MessageDigest.isEqual(actualHash.getBytes(java.nio.charset.StandardCharsets.US_ASCII),
                        entry.sha256.getBytes(java.nio.charset.StandardCharsets.US_ASCII)))
                    throw new SecurityException("SHA-256 mismatch");
                validateArchive(outputFile);
                return;
            } finally {
                connection.disconnect();
            }
        }
        throw new IllegalStateException("Too many redirects");
    }

    private static boolean allowedGithubReleaseHost(URL url) {
        if (!"https".equalsIgnoreCase(url.getProtocol())) return false;
        String host = url.getHost().toLowerCase(Locale.ROOT);
        if (url.getPort() != -1 && url.getPort() != 443) return false;
        return host.equals("github.com") ||
            host.equals("release-assets.githubusercontent.com") ||
            host.equals("objects.githubusercontent.com");
    }

    private static void validateArchive(File file) throws Exception {
        long totalExpanded = 0;
        int count = 0;
        boolean manifest = false;
        java.util.HashSet<String> entries = new java.util.HashSet<>();
        try (ZipInputStream zip = new ZipInputStream(new FileInputStream(file))) {
            ZipEntry entry;
            while ((entry = zip.getNextEntry()) != null) {
                count++;
                if (count > MAX_ZIP_ENTRIES)
                    throw new SecurityException("Too many ZIP entries");
                String name = entry.getName().replace('\\', '/');
                if (name.length() > 1024 || name.startsWith("/") ||
                    name.matches("^[A-Za-z]:.*") || name.indexOf('\u0000') >= 0 ||
                    !entries.add(name.toLowerCase(Locale.ROOT))) {
                    throw new SecurityException("Invalid archive path");
                }
                String[] parts = name.split("/");
                for (String part : parts) {
                    if (part.equals("..") || part.equals("."))
                        throw new SecurityException("ZIP traversal");
                }
                if (name.equalsIgnoreCase("manifest.json") ||
                    name.toLowerCase(Locale.ROOT).endsWith("/manifest.json")) {
                    manifest = true;
                }
                if (!entry.isDirectory()) {
                    byte[] buffer = new byte[16384];
                    int n;
                    while ((n = zip.read(buffer)) != -1) {
                        totalExpanded += n;
                        if (totalExpanded > MAX_UNCOMPRESSED_BYTES)
                            throw new SecurityException("Expanded ZIP too large");
                    }
                }
                zip.closeEntry();
            }
        }
        if (count == 0 || !manifest) throw new SecurityException("No SMAPI manifest");
        // This is an early screening. The C# archive transaction has final say.
    }

    private static void copy(InputStream in, OutputStream out, long limit) throws Exception {
        byte[] buffer = new byte[16384];
        long count = 0;
        int n;
        while ((n = in.read(buffer)) != -1) {
            count += n;
            if (count > limit) throw new SecurityException("Copy size limit");
            out.write(buffer, 0, n);
        }
        out.flush();
    }

    private static String asHex(byte[] input) {
        char[] alphabet = "0123456789abcdef".toCharArray();
        char[] result = new char[input.length * 2];
        for (int i = 0; i < input.length; i++) {
            result[2 * i] = alphabet[(input[i] >>> 4) & 0x0f];
            result[2 * i + 1] = alphabet[input[i] & 0x0f];
        }
        return new String(result);
    }

    private static void post(Activity activity, Runnable result) {
        MAIN.post(() -> {
            if (!activity.isFinishing() && !activity.isDestroyed()) result.run();
        });
    }
}

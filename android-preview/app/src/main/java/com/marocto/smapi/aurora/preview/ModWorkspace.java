package com.marocto.smapi.aurora.preview;

import android.content.ContentResolver;
import android.content.Context;
import android.database.Cursor;
import android.net.Uri;
import android.provider.DocumentsContract;
import org.json.JSONObject;
import org.json.JSONArray;
import java.io.ByteArrayOutputStream;
import java.io.File;
import java.io.FileOutputStream;
import java.io.InputStream;
import java.io.OutputStream;
import java.io.IOException;
import java.util.ArrayList;
import java.util.Enumeration;
import java.util.HashMap;
import java.util.HashSet;
import java.util.List;
import java.util.Map;
import java.util.Set;
import java.util.zip.ZipEntry;
import java.util.zip.ZipFile;

final class ModWorkspace {
    static final class Mod {
        String name = "(без названия)";
        String version = "?";
        String uniqueId = "";
        String folder = "";
        boolean enabled = true;
        Uri folderDocument;
        Uri parentDocument;
        final List<String> requiredIds = new ArrayList<>();
        final List<String> issues = new ArrayList<>();
        boolean rootFolder() { return parentDocument == null; }
    }
    private static final String FOLDER = DocumentsContract.Document.MIME_TYPE_DIR;
    private final Context ctx;
    private Uri tree;

    ModWorkspace(Context context, Uri uri) {
        ctx = context.getApplicationContext();
        tree = uri;
    }
    boolean connected() { return tree != null; }

    private Uri root() {
        return DocumentsContract.buildDocumentUriUsingTree(tree, DocumentsContract.getTreeDocumentId(tree));
    }

    private static final class Child {
        final String id, name, mime;
        Child(String i, String n, String m) { id=i; name=n; mime=m; }
    }

    private List<Child> children(Uri dir) throws Exception {
        String parentId = DocumentsContract.getDocumentId(dir);
        Uri uri = DocumentsContract.buildChildDocumentsUriUsingTree(tree, parentId);
        List<Child> result = new ArrayList<>();
        try (Cursor cursor = ctx.getContentResolver().query(uri, new String[] {
                DocumentsContract.Document.COLUMN_DOCUMENT_ID,
                DocumentsContract.Document.COLUMN_DISPLAY_NAME,
                DocumentsContract.Document.COLUMN_MIME_TYPE
            }, null, null, null)) {
            if (cursor == null) throw new IOException("Не удаётся прочитать папку через Android Files");
            while (cursor.moveToNext())
                result.add(new Child(cursor.getString(0), cursor.getString(1), cursor.getString(2)));
        }
        return result;
    }

    private Uri doc(Child child) {
        return DocumentsContract.buildDocumentUriUsingTree(tree, child.id);
    }
    private Child find(Uri folder, String name) throws Exception {
        for (Child c : children(folder)) if (name.equals(c.name)) return c;
        return null;
    }

    List<Mod> scan() throws Exception {
        List<Mod> result = new ArrayList<>();
        if (!connected()) return result;
        scanDir(root(), null, "", result, new int[] {0}, 0);
        analyze(result);
        return result;
    }

    private void scanDir(Uri folder, Uri parent, String name, List<Mod> result, int[] examined, int depth) throws Exception {
        if (depth > 5 || examined[0]++ > 650) return;
        List<Child> members = children(folder);
        for (Child child : members) {
            if (child.name.equalsIgnoreCase("manifest.json") && !FOLDER.equals(child.mime)) {
                Mod mod = new Mod();
                mod.folder = name.isEmpty() ? "(root)" : name;
                mod.folderDocument = folder;
                mod.parentDocument = parent;
                mod.enabled = !new File(name).getName().startsWith(".");
                try (InputStream stream = ctx.getContentResolver().openInputStream(doc(child))) {
                    if (stream == null) throw new IOException("Не удаётся открыть manifest.json");
                    ByteArrayOutputStream output = new ByteArrayOutputStream();
                    byte[] buffer = new byte[4096];
                    int n;
                    while ((n = stream.read(buffer)) != -1) {
                        if (output.size() + n > 128 * 1024)
                            throw new IOException("manifest.json слишком большой");
                        output.write(buffer, 0, n);
                    }
                    JSONObject json = new JSONObject(output.toString("UTF-8"));
                    mod.name = json.optString("Name", mod.folder);
                    mod.version = json.optString("Version", "?");
                    mod.uniqueId = json.optString("UniqueID", "").trim();
                    JSONArray deps = json.optJSONArray("Dependencies");
                    if (deps != null) for (int i=0; i<deps.length(); i++) {
                        JSONObject d = deps.optJSONObject(i);
                        if (d == null) continue;
                        String id = d.optString("UniqueID", "").trim();
                        if (d.optBoolean("IsRequired", true) && !id.isEmpty())
                            mod.requiredIds.add(id);
                    }
                    JSONObject framework = json.optJSONObject("ContentPackFor");
                    if (framework != null) {
                        String id=framework.optString("UniqueID", "").trim();
                        if (!id.isEmpty()) mod.requiredIds.add(id);
                    }
                } catch (Exception e) {
                    mod.name = "Ошибка manifest.json";
                    mod.issues.add("Ошибка чтения манифеста: " + e.getMessage());
                }
                result.add(mod);
                return;
            }
        }
        for (Child child : members) {
            if (FOLDER.equals(child.mime))
                scanDir(doc(child), folder, name.isEmpty()?child.name:name+"/"+child.name, result, examined, depth+1);
        }
    }

    static void analyze(List<Mod> mods) {
        Map<String, Mod> byId = new HashMap<>();
        for (Mod mod : mods) {
            if (mod.uniqueId.isEmpty()) {
                mod.issues.add("Нет UniqueID в manifest.json");
                continue;
            }
            String key = mod.uniqueId.toLowerCase(java.util.Locale.ROOT);
            Mod previous = byId.putIfAbsent(key, mod);
            if (previous != null) {
                mod.issues.add("Повторяющийся UniqueID: " + mod.uniqueId);
                previous.issues.add("Повторяющийся UniqueID: " + mod.uniqueId);
            }
        }
        for (Mod mod : mods) {
            for (String id : mod.requiredIds) {
                // SMAPI itself is part of the runtime, not a folder in Mods.
                if (id.equalsIgnoreCase("Pathoschild.SMAPI")) continue;
                Mod dependency = byId.get(id.toLowerCase(java.util.Locale.ROOT));
                if (dependency == null) mod.issues.add("Отсутствует зависимость: " + id);
                else if (!dependency.enabled) mod.issues.add("Отключена зависимость: " + id);
            }
        }
    }

    private void assertSelectedMod(Mod mod) throws Exception {
        if (!connected() || mod == null || mod.rootFolder() || mod.folderDocument == null)
            throw new IOException("Нельзя изменять корневую папку Mods");
        Child old = find(mod.parentDocument, new File(mod.folder).getName());
        if (old == null || !DocumentsContract.getDocumentId(mod.folderDocument).equals(old.id))
            throw new IOException("Папка мода изменилась — обнови список");
        if (find(mod.folderDocument, "manifest.json") == null)
            throw new IOException("В папке больше нет manifest.json; действие отменено");
    }

    void setEnabled(Mod mod, boolean enabled) throws Exception {
        assertSelectedMod(mod);
        if (mod.enabled == enabled) return;
        String oldName = new File(mod.folder).getName();
        String baseName = oldName.startsWith(".") ? oldName.substring(1) : oldName;
        if (baseName.isEmpty()) throw new IOException("Некорректное имя папки мода");
        String next = enabled ? baseName : "." + baseName;
        if (find(mod.parentDocument, next) != null)
            throw new IOException("Папка " + next + " уже существует. Переименование отменено.");
        Uri renamed = DocumentsContract.renameDocument(ctx.getContentResolver(), mod.folderDocument, next);
        if (renamed == null) throw new IOException("Android запретил переименовать папку мода");
    }

    void deleteMod(Mod mod) throws Exception {
        assertSelectedMod(mod);
        if (!DocumentsContract.deleteDocument(ctx.getContentResolver(), mod.folderDocument))
            throw new IOException("Android запретил удалить папку мода");
    }

    /** Installs a validated ZIP into a user-selected SAF folder, without overwriting existing mod folders. */
    int installZip(Uri input, String suggestedName) throws Exception {
        if (!connected()) throw new IOException("Сначала выбери папку Mods");
        ContentResolver resolver = ctx.getContentResolver();
        File temp = File.createTempFile("aurora_", ".zip", ctx.getCacheDir());
        try {
            long length = 0;
            try (InputStream src = resolver.openInputStream(input); OutputStream out = new FileOutputStream(temp)) {
                if (src == null) throw new IOException("Не удалось открыть ZIP");
                byte[] buffer = new byte[64 * 1024];
                int got;
                while ((got = src.read(buffer)) != -1) {
                    length += got;
                    if (length > 64L * 1024 * 1024)
                        throw new IOException("ZIP слишком большой (лимит 64 МБ)");
                    out.write(buffer, 0, got);
                }
            }
            try (ZipFile zip = new ZipFile(temp)) {
                if (zip.size() < 1 || zip.size() > 5000) throw new IOException("Неподдерживаемое количество файлов ZIP");
                List<ZipEntry> entries = new ArrayList<>();
                long total = 0;
                boolean hasManifest = false;
                boolean rootManifest = false;
                Set<String> paths = new HashSet<>();
                Enumeration<? extends ZipEntry> enumeration = zip.entries();
                while (enumeration.hasMoreElements()) {
                    ZipEntry entry = enumeration.nextElement();
                    String name = entry.getName();
                    validatePath(name);
                    if (!paths.add(name)) throw new IOException("В ZIP повторяется файл: " + name);
                    if (name.equalsIgnoreCase("manifest.json")) rootManifest = true;
                    if (name.toLowerCase(java.util.Locale.ROOT).endsWith("/manifest.json") || rootManifest) hasManifest = true;
                    if (!entry.isDirectory()) {
                        long size = entry.getSize();
                        if (size < 0 || size > 128L*1024*1024) throw new IOException("Некорректный размер файла ZIP");
                        total += size;
                        if (total > 256L*1024*1024) throw new IOException("ZIP слишком большой после распаковки");
                    }
                    entries.add(entry);
                }
                if (!hasManifest) throw new IOException("В ZIP не найден manifest.json");
                String extra = rootManifest ? safeFolderName(suggestedName) : "";
                Set<String> roots = new HashSet<>();
                for (ZipEntry entry : entries) {
                    String name = extra.isEmpty() ? entry.getName() : extra+"/"+entry.getName();
                    roots.add(name.split("/")[0]);
                }
                Uri top = root();
                for (String candidate : roots) {
                    if (find(top, candidate) != null)
                        throw new IOException("Папка уже существует: "+candidate+" (импорт отменён во избежание перезаписи)");
                }

                Map<String, Uri> dirs = new HashMap<>();
                dirs.put("", top);
                int written = 0;
                for (ZipEntry entry : entries) {
                    String name = extra.isEmpty() ? entry.getName() : extra+"/"+entry.getName();
                    String trimmed = name.endsWith("/") ? name.substring(0,name.length()-1):name;
                    String[] components = trimmed.split("/");
                    String key = "";
                    Uri parent = top;
                    for (int i=0; i<components.length-1; i++) {
                        key = key.isEmpty()?components[i]:key+"/"+components[i];
                        Uri child = dirs.get(key);
                        if (child == null) {
                            child = DocumentsContract.createDocument(resolver, parent, FOLDER, components[i]);
                            if (child == null) throw new IOException("Не удалось создать папку "+key);
                            dirs.put(key,child);
                        }
                        parent = child;
                    }
                    if (entry.isDirectory()) {
                        if (!dirs.containsKey(trimmed)) {
                            Uri child = DocumentsContract.createDocument(resolver, parent,FOLDER,components[components.length-1]);
                            if (child == null) throw new IOException("Не удалось создать папку "+trimmed);
                            dirs.put(trimmed,child);
                        }
                        continue;
                    }
                    Uri target = DocumentsContract.createDocument(resolver,parent,"application/octet-stream",components[components.length-1]);
                    if (target == null) throw new IOException("Не удалось создать "+trimmed);
                    try (InputStream source = zip.getInputStream(entry);
                         OutputStream dest = resolver.openOutputStream(target,"w")) {
                        if (dest == null) throw new IOException("Не удалось записать "+trimmed);
                        byte[] buffer = new byte[32*1024];
                        long copied = 0;
                        int count;
                        while ((count=source.read(buffer))!=-1) {
                            copied += count;
                            if (copied > 128L * 1024 * 1024)
                                throw new IOException("Распакованный файл превышает ограничение");
                            dest.write(buffer,0,count);
                        }
                    }
                    written++;
                }
                return written;
            }
        } finally {
            temp.delete();
        }
    }

    private static void validatePath(String path) throws IOException {
        if (path.isEmpty() || path.startsWith("/") || path.contains("\\") || path.contains(":")
                || path.length() > 255) throw new IOException("Опасное имя файла в ZIP");
        String[] bits=path.split("/");
        for (String bit : bits)
            if (bit.equals("..") || bit.equals(".") || bit.isEmpty())
                throw new IOException("Некорректный путь ZIP: "+path);
    }

    private static String safeFolderName(String title) {
        String name=title.replaceAll("(?i)\\.zip$","").replaceAll("[^a-zA-Z0-9_\\- .]","_").trim();
        if(name.isEmpty()) name="ImportedMod";
        return name.length()>64 ? name.substring(0,64):name;
    }
}

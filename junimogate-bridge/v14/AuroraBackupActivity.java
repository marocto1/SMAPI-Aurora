package org.junimogate.aurora;

import android.app.Activity;
import android.app.AlertDialog;
import android.content.Intent;
import android.net.Uri;
import android.os.Bundle;
import android.os.Handler;
import android.os.Looper;
import android.widget.Button;
import android.widget.LinearLayout;
import android.widget.ScrollView;
import android.widget.TextView;
import android.graphics.Typeface;
import android.graphics.drawable.GradientDrawable;
import org.json.JSONArray;
import org.json.JSONObject;
import java.io.*;
import java.nio.file.Files;
import java.security.MessageDigest;
import java.util.*;
import java.util.zip.*;

/**
 * Aurora v1 backup/import QA.
 * File owner: app-private JunimoGate user-data and external app-specific Saves.
 * No ADB, root, cloud upload, Play verification, private permissions or keys.
 *
 * Creates SAF archive with per-file SHA256 manifest; restore verifies all
 * files before explicit confirmation and retains pre-restore folders for
 * recovery (no silent deletion). Never touches Stardew Valley APK.
 */
public final class AuroraBackupActivity extends Activity {
    private static final int EXPORT = 8101, IMPORT = 8102;
    private static final String MANIFEST = "aurora-backup-manifest.json";
    private static final int LIMIT_ENTRIES = 30000;
    private static final long LIMIT_BYTES = 2L * 1024 * 1024 * 1024;
    private static final long LIMIT_SINGLE_FILE = 512L * 1024 * 1024;
    private static final Handler UI = new Handler(Looper.getMainLooper());
    private static final char[] HEX = "0123456789abcdef".toCharArray();
    private static final String ROOT_USER = "userdata/", ROOT_SAVES = "saves/";
    private TextView status;
    private volatile boolean busy;

    @Override public void onCreate(Bundle state) {
        super.onCreate(state);
        setTitle("Aurora · Backup & Restore");
        LinearLayout page = new LinearLayout(this);
        page.setPadding(dp(18),dp(24),dp(18),dp(16));
        page.setOrientation(LinearLayout.VERTICAL);
        page.setBackgroundColor(palette("junimo_surface",0xfff7f9f4));
        TextView h = text("AURORA  /  BACKUP & RESTORE",20,true);
        page.addView(h);
        TextView note=text(
          "Сохраняем моды, профили, конфиги и игровые сохранения в выбранный ZIP. " +
          "После записи Aurora повторно прочитает и проверит архив. " +
          "В этой тестовой сборке восстановление с заменой данных заблокировано, " +
          "пока не проверены сценарии аварийного сбоя на устройстве. Закрой игру перед экспортом.",
          14,false);
        note.setPadding(0,dp(16),0,dp(16));
        page.addView(note);
        page.addView(button("Экспортировать полную резервную копию",this::pickExport));
        page.addView(button("Проверить ZIP по SHA-256 (без восстановления)",this::pickImport));
        page.addView(button("Открыть Aurora",this::openMain));
        status = text("Данные не изменены.",13,false);
        status.setPadding(0,dp(16),0,0);
        page.addView(status);
        setContentView(page);
    }

    private File userData() { return new File(new File(getNoBackupFilesDir(),"junimogate"),"user-data"); }
    private File saves() {
        File external = getExternalFilesDir(null);
        return external == null ? null : new File(external,"Saves");
    }
    private void pickExport() {
        if (busy) return;
        Intent intent = new Intent(Intent.ACTION_CREATE_DOCUMENT);
        intent.addCategory(Intent.CATEGORY_OPENABLE);
        intent.setType("application/zip");
        intent.putExtra(Intent.EXTRA_TITLE,"Aurora-Full-Backup.zip");
        startActivityForResult(intent,EXPORT);
    }
    private void pickImport() {
        if (busy) return;
        Intent intent = new Intent(Intent.ACTION_OPEN_DOCUMENT);
        intent.addCategory(Intent.CATEGORY_OPENABLE);
        intent.setType("*/*");
        intent.putExtra(Intent.EXTRA_MIME_TYPES,new String[]{"application/zip","application/octet-stream"});
        startActivityForResult(intent,IMPORT);
    }
    @Override protected void onActivityResult(int request,int result,Intent data) {
        super.onActivityResult(request,result,data);
        if (result != RESULT_OK || data == null || data.getData() == null || busy) return;
        Uri uri=data.getData();
        if (request == EXPORT) doExport(uri);
        if (request == IMPORT) doVerify(uri);
    }
    private void doExport(Uri uri) {
        busy=true;
        status.setText("Экспорт ZIP, затем повторная проверка SHA-256…");
        new Thread(() -> {
            try {
                File user=userData(), saves=saves();
                if (saves==null) throw new IOException("Каталог сохранений недоступен");
                LinkedHashMap<String,File> files=new LinkedHashMap<>();
                collect(user,ROOT_USER,files);
                collect(saves,ROOT_SAVES,files);
                if (files.isEmpty()) throw new IOException("Нет данных для полной резервной копии");
                JSONArray list=new JSONArray();
                long total=0;
                try (OutputStream raw=getContentResolver().openOutputStream(uri,"w")) {
                    if(raw==null)throw new IOException("Нельзя открыть выбранный файл");
                    try(ZipOutputStream zip=new ZipOutputStream(new BufferedOutputStream(raw))) {
                        for(Map.Entry<String,File> entry:files.entrySet()) {
                            File source=entry.getValue();
                            total+=source.length();
                            if(total>LIMIT_BYTES)throw new IOException("Архив превышает ограничение 2 ГБ");
                            MessageDigest sha=MessageDigest.getInstance("SHA-256");
                            zip.putNextEntry(new ZipEntry(entry.getKey()));
                            long written=0;
                            try(InputStream in=new BufferedInputStream(new FileInputStream(source))) {
                                byte[] chunk=new byte[32768];
                                int n;
                                while((n=in.read(chunk))!=-1) {
                                    written+=n;
                                    if(written>LIMIT_SINGLE_FILE)throw new IOException("Слишком большой файл");
                                    zip.write(chunk,0,n);sha.update(chunk,0,n);
                                }
                            }
                            zip.closeEntry();
                            if(written!=source.length())
                                throw new IOException("Файл изменился во время резервного копирования: "+entry.getKey());
                            list.put(new JSONObject().put("path",entry.getKey())
                                .put("bytes",written).put("sha256",hex(sha.digest())));
                        }
                        JSONObject manifest=new JSONObject()
                            .put("schema","smapi-aurora-full-backup/v1")
                            .put("fileCount",list.length())
                            .put("files",list);
                        zip.putNextEntry(new ZipEntry(MANIFEST));
                        zip.write(manifest.toString().getBytes("UTF-8"));
                        zip.closeEntry();
                    }
                }
                int verified=verifyArchive(uri);
                if(verified!=list.length())throw new IOException("Количество файлов после проверки не совпадает");
                message("Резервная копия готова и повторно проверена: "+verified+
                    " файлов, SHA-256 совпадают. Сохрани ZIP вне Aurora.");
            } catch(Exception ex) {
                message("Экспорт не завершён: "+safeError(ex)+
                    ". Не используй частично созданный архив для восстановления.");
            } finally {busy=false;}
        },"AuroraFullBackup").start();
    }

    private static void collect(File dir,String prefix,Map<String,File> result) throws Exception {
        if(dir==null || !dir.exists())return;
        if(!dir.isDirectory() || Files.isSymbolicLink(dir.toPath()))
            throw new IOException("Небезопасный корень данных");
        ArrayDeque<File> pending=new ArrayDeque<>();
        pending.push(dir);
        String base=dir.getCanonicalPath()+File.separator;
        while(!pending.isEmpty()) {
            File current=pending.pop();
            File[] children=current.listFiles();
            if(children==null)throw new IOException("Не удалось прочитать каталог данных");
            Arrays.sort(children,Comparator.comparing(File::getName));
            for(File child:children) {
                if(Files.isSymbolicLink(child.toPath()))throw new IOException("Ссылка запрещена");
                String canonical=child.getCanonicalPath();
                if(!canonical.startsWith(base))throw new IOException("Выход за пределы хранилища");
                if(child.isDirectory()) {pending.push(child);continue;}
                if(!child.isFile())throw new IOException("Неизвестный тип файла");
                if(child.length()>LIMIT_SINGLE_FILE)throw new IOException("Файл более 512 МБ");
                String path=prefix+canonical.substring(base.length()).replace(File.separatorChar,'/');
                validateName(path);
                if(result.put(path,child)!=null)throw new IOException("Дублированный путь");
                if(result.size()>LIMIT_ENTRIES)throw new IOException("Слишком много файлов");
            }
        }
    }

    /**
     * v1.4 fail-closed VERIFY-ONLY import: never stages into app-private
     * storage, never renames live Saves/mod profiles, never claims restore.
     */
    private void doVerify(Uri uri) {
        if (busy) return;
        busy = true;
        status.setText("Проверяю ZIP и SHA-256 без изменений сохранений…");
        new Thread(() -> {
            try {
                int count = verifyArchive(uri);
                message("ZIP прошёл проверку: " + count +
                    " файлов. Сохранения и моды не изменены. " +
                    "Автоматическое восстановление в этой QA-сборке отключено.");
            } catch (Exception error) {
                message("Архив НЕ прошёл проверку: " + safeError(error) +
                    ". Моды и сохранения не изменены.");
            } finally { busy = false; }
        },"AuroraVerifyBackupOnly").start();
    }

    private int verifyArchive(Uri uri) throws Exception {
        HashMap<String,String> digests = new HashMap<>();
        HashMap<String,Long> sizes = new HashMap<>();
        HashSet<String> normalized = new HashSet<>();
        JSONArray manifestFiles = null;
        int count=0;
        long totalBytes=0;
        final OutputStream discard = new OutputStream() {
            @Override public void write(int n) {}
            @Override public void write(byte[] b,int offset,int len) {}
        };
        try (InputStream source = getContentResolver().openInputStream(uri)) {
            if (source == null) throw new IOException("Файл не открывается");
            try (ZipInputStream zip = new ZipInputStream(new BufferedInputStream(source))) {
                ZipEntry entry;
                while ((entry = zip.getNextEntry()) != null) {
                    String name = entry.getName();
                    validateName(name);
                    if (!normalized.add(name.toLowerCase(Locale.ROOT)))
                        throw new IOException("Дубликат имени ZIP (без учёта регистра)");
                    if (++count > LIMIT_ENTRIES + 1)
                        throw new IOException("Слишком много элементов в ZIP");
                    if (entry.isDirectory())
                        throw new IOException("Неожиданная папка ZIP");
                    if (MANIFEST.equals(name)) {
                        if (manifestFiles != null)
                            throw new IOException("Повторяющийся манифест");
                        ByteArrayOutputStream contents = new ByteArrayOutputStream();
                        copyBounded(zip,contents,1024*1024,null);
                        JSONObject meta=new JSONObject(contents.toString("UTF-8"));
                        if (!"smapi-aurora-full-backup/v1".equals(meta.optString("schema")))
                            throw new IOException("Неподдерживаемый формат резервной копии");
                        manifestFiles=meta.getJSONArray("files");
                        if (meta.getInt("fileCount") != manifestFiles.length() ||
                            manifestFiles.length() > LIMIT_ENTRIES)
                            throw new IOException("Некорректное количество записей манифеста");
                    } else {
                        if(!name.startsWith(ROOT_USER) && !name.startsWith(ROOT_SAVES))
                            throw new IOException("Посторонний файл в резервной копии");
                        MessageDigest sha=MessageDigest.getInstance("SHA-256");
                        long size=copyBounded(zip,discard,LIMIT_SINGLE_FILE,sha);
                        totalBytes+=size;
                        if(totalBytes>LIMIT_BYTES)throw new IOException("ZIP более 2 ГБ");
                        digests.put(name,hex(sha.digest()));
                        sizes.put(name,size);
                    }
                    zip.closeEntry();
                }
            }
        }
        if(manifestFiles==null || manifestFiles.length()!=digests.size() || digests.isEmpty())
            throw new IOException("Список или содержимое резервной копии неполные");
        HashSet<String> declared = new HashSet<>();
        for(int i=0;i<manifestFiles.length();i++) {
            JSONObject row=manifestFiles.getJSONObject(i);
            String name=row.getString("path");
            validateName(name);
            String hash=row.getString("sha256");
            if(!hash.matches("[a-f0-9]{64}") || !declared.add(name) ||
               !digests.containsKey(name) || !digests.get(name).equals(hash) ||
               sizes.get(name).longValue()!=row.getLong("bytes"))
                throw new IOException("Несовпадение файла/контрольной суммы: "+name);
        }
        return digests.size();
    }

    private static void validateName(String name) throws IOException {
        if(name==null||name.isEmpty()||name.length()>1024||
            name.startsWith("/")||name.indexOf('\\')>=0||
            name.matches("(?i)^[a-z]:.*")||name.indexOf('\u0000')>=0)
            throw new IOException("Недопустимое имя файла");
        for(String part:name.split("/"))if(part.isEmpty()||part.equals("..")||part.equals("."))
            throw new IOException("Недопустимый путь в архиве");
    }
    private static long copyBounded(InputStream in,OutputStream out,long max,MessageDigest sha) throws IOException {
        byte[] bytes=new byte[32768];int n;long total=0;
        while((n=in.read(bytes))!=-1) {
            total+=n;
            if(total>max)throw new IOException("Превышен лимит файла");
            out.write(bytes,0,n);
            if(sha!=null)sha.update(bytes,0,n);
        }
        return total;
    }
    private static String hex(byte[] bytes) {
        StringBuilder b=new StringBuilder(bytes.length*2);
        for(byte x:bytes) {b.append(HEX[(x>>4)&15]);b.append(HEX[x&15]);}
        return b.toString();
    }
    private void message(String msg) {UI.post(() -> {
        if(!isFinishing()&&!isDestroyed())status.setText(msg);
    });}
    private String safeError(Exception x) {
        return x instanceof IOException ? x.getMessage() : x.getClass().getSimpleName();
    }
    private int palette(String color,int fallback) {
        return AuroraWorkshopTabsView.themeColor(this,color,fallback);
    }
    private TextView text(String value,int sp,boolean bold) {
        TextView t=new TextView(this);t.setText(value);t.setTextSize(sp);
        t.setTextColor(palette("junimo_on_surface",0xff1a2018));
        if(bold)t.setTypeface(Typeface.DEFAULT,Typeface.BOLD);
        return t;
    }
    private Button button(String name,Runnable click) {
        Button b=new Button(this);b.setText(name);b.setAllCaps(false);b.setOnClickListener(v->click.run());return b;
    }
    private int dp(int n){return Math.round(n*getResources().getDisplayMetrics().density);}
    private void openMain(){
        Intent main=new Intent();
        main.setClassName(getPackageName(),"org.junimogate.app.MainActivity");
        main.addFlags(Intent.FLAG_ACTIVITY_CLEAR_TOP|Intent.FLAG_ACTIVITY_SINGLE_TOP);
        startActivity(main);finish();
    }
}

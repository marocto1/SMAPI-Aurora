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
    private File stageUser, stageSaves;
    private JSONArray readyFiles;

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
          "В архив включаются моды, группы, настройки модов, резервные копии " +
          "и игровые сохранения. Перед экспортом закрой Stardew Valley и дождись записи сохранения.",
          14,false);
        note.setPadding(0,dp(16),0,dp(16));
        page.addView(note);
        page.addView(button("Экспортировать полную резервную копию",this::pickExport));
        page.addView(button("Проверить и восстановить архив",this::pickImport));
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
        if (request == IMPORT) doInspect(uri);
    }
    private void doExport(Uri uri) {
        busy=true;
        status.setText("Создание резервной копии и расчёт SHA-256…");
        new Thread(() -> {
            try {
                File user=userData(), saves=saves();
                if (saves==null) throw new IOException("Каталог сохранений недоступен");
                LinkedHashMap<String,File> files=new LinkedHashMap<>();
                collect(user,ROOT_USER,files);
                collect(saves,ROOT_SAVES,files);
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
                message("Экспортировано файлов: "+list.length()+
                    ". ZIP сохранён в выбранном месте. Обязательно сохрани его вне Aurora.");
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

    private void doInspect(Uri uri) {
        busy=true;
        status.setText("Проверка архива, всех SHA-256 и безопасности путей…");
        new Thread(() -> {
            File u=null,s=null;
            try {
                File user=userData(), saved=saves();
                if(saved==null)throw new IOException("Сохранения недоступны");
                File up=user.getParentFile(),sp=saved.getParentFile();
                if(up==null||sp==null)throw new IOException("Недоступны каталоги");
                if(!up.isDirectory()&&!up.mkdirs())throw new IOException("Каталог Aurora недоступен");
                if(!sp.isDirectory()&&!sp.mkdirs())throw new IOException("Каталог SDV недоступен");
                String token=UUID.randomUUID().toString();
                u=new File(up,".aurora-restore-user-"+token);
                s=new File(sp,".aurora-restore-saves-"+token);
                if(!u.mkdir()||!s.mkdir())throw new IOException("Нет места для проверки архива");
                LinkedHashMap<String,String> found=new LinkedHashMap<>();
                LinkedHashMap<String,Long> lengths=new LinkedHashMap<>();
                JSONArray listed=null;long overall=0;int count=0;
                try(InputStream input=getContentResolver().openInputStream(uri)) {
                    if(input==null)throw new IOException("Файл не открывается");
                    try(ZipInputStream zip=new ZipInputStream(new BufferedInputStream(input))) {
                        ZipEntry entry;
                        while((entry=zip.getNextEntry())!=null) {
                            if(++count>LIMIT_ENTRIES+1)throw new IOException("Слишком много файлов");
                            String name=entry.getName();
                            validateName(name);
                            if(entry.isDirectory()) {zip.closeEntry();continue;}
                            if(name.equals(MANIFEST)) {
                                if(listed!=null)throw new IOException("Дублированный манифест");
                                ByteArrayOutputStream blob=new ByteArrayOutputStream();
                                copyBounded(zip,blob,1024*1024,null);
                                JSONObject meta=new JSONObject(blob.toString("UTF-8"));
                                if(!"smapi-aurora-full-backup/v1".equals(meta.optString("schema")))
                                    throw new IOException("Неподдерживаемая версия архива");
                                listed=meta.getJSONArray("files");
                                if(listed.length()!=meta.getInt("fileCount"))
                                    throw new IOException("Список файлов повреждён");
                            } else {
                                if(!name.startsWith(ROOT_USER)&&!name.startsWith(ROOT_SAVES))
                                    throw new IOException("Чужой файл в архиве");
                                if(found.containsKey(name))throw new IOException("Повторяющиеся файлы");
                                File root=name.startsWith(ROOT_USER)?u:s;
                                String suffix=name.substring(name.indexOf('/')+1);
                                File target=new File(root,suffix);
                                String canonical=target.getCanonicalPath();
                                if(!canonical.startsWith(root.getCanonicalPath()+File.separator))
                                    throw new IOException("Небезопасный путь");
                                File parent=target.getParentFile();
                                if(!parent.isDirectory()&&!parent.mkdirs())throw new IOException("Нельзя подготовить файл");
                                MessageDigest sha=MessageDigest.getInstance("SHA-256");
                                long n;
                                try(OutputStream out=new BufferedOutputStream(new FileOutputStream(target))) {
                                    n=copyBounded(zip,out,LIMIT_SINGLE_FILE,sha);
                                }
                                overall+=n;
                                if(overall>LIMIT_BYTES)throw new IOException("Архив превышает 2 ГБ");
                                found.put(name,hex(sha.digest()));lengths.put(name,n);
                            }
                            zip.closeEntry();
                        }
                    }
                }
                if(listed==null||listed.length()!=found.size()||found.isEmpty())
                    throw new IOException("Нет корректного списка данных");
                HashSet<String> declared=new HashSet<>();
                for(int i=0;i<listed.length();i++) {
                    JSONObject row=listed.getJSONObject(i);
                    String name=row.getString("path");
                    if(!declared.add(name)||!found.containsKey(name)||
                        !found.get(name).equals(row.getString("sha256"))||
                        !lengths.get(name).equals(row.getLong("bytes")))
                        throw new IOException("Не совпадает контрольная сумма: "+name);
                }
                boolean hadUser=false,hadSaves=false;
                for(String p:found.keySet()) {
                    if(p.startsWith(ROOT_USER))hadUser=true;
                    if(p.startsWith(ROOT_SAVES))hadSaves=true;
                }
                // A backup with no saves must not silently erase saves made later.
                if(!hadUser && user.isDirectory() && user.list()!=null && user.list().length>0)
                    throw new IOException("В архиве нет userdata, а на устройстве есть моды/настройки");
                if(!hadSaves && saved.isDirectory() && saved.list()!=null && saved.list().length>0)
                    throw new IOException("В архиве нет сохранений, а на устройстве есть фермы");
                final File readyU=u,readyS=s;
                final int files=found.size();
                UI.post(() -> {
                    if(isFinishing()||isDestroyed()) {wipe(readyU);wipe(readyS);busy=false;return;}
                    stageUser=readyU;stageSaves=readyS;
                    status.setText("Архив проверен: "+files+" файлов. Текущие данные НЕ изменены.");
                    new AlertDialog.Builder(this)
                        .setTitle("Восстановить "+files+" файлов?")
                        .setMessage("Текущая библиотека модов и сохранения будут заменены архивными. " +
                            "Оригиналы сохранятся в скрытых папках восстановления. " +
                            "После завершения полностью перезапусти Aurora. " +
                            "Не выполняй восстановление во время запущенной игры.")
                        .setPositiveButton("Подтвердить замену", (d,w) -> commitRestore())
                        .setNegativeButton("Отмена", (d,w) -> discardStage()).show();
                });
            } catch(Exception error) {
                wipe(u);wipe(s);
                message("Восстановление заблокировано: "+safeError(error)+". Данные не изменены.");
                busy=false;
            }
        },"AuroraValidateBackup").start();
    }

    private synchronized void commitRestore() {
        File newU=stageUser,newS=stageSaves;
        stageUser=null;stageSaves=null;
        if(newU==null||newS==null){busy=false;return;}
        status.setText("Атомарная замена каталогов, создание откатных копий…");
        new Thread(() -> {
            File oldU=userData(),oldS=saves();
            String token=UUID.randomUUID().toString();
            File bu=new File(oldU.getParentFile(),".aurora-previous-user-"+token);
            File bs=new File(oldS.getParentFile(),".aurora-previous-saves-"+token);
            boolean movedU=false,movedS=false,installedU=false,installedS=false;
            try {
                if(oldU.exists()) {if(!oldU.renameTo(bu))throw new IOException("Резерв userdata не создан");movedU=true;}
                if(oldS.exists()) {if(!oldS.renameTo(bs))throw new IOException("Резерв saves не создан");movedS=true;}
                if(!newU.renameTo(oldU))throw new IOException("Сбой замены userdata");installedU=true;
                if(!newS.renameTo(oldS))throw new IOException("Сбой замены saves");installedS=true;
                message("Восстановление завершено. Полностью закрой и запусти Aurora заново. " +
                    "Предыдущие данные сохранены в .aurora-previous-*.");
            } catch(Exception error) {
                if(installedU&&oldU.exists())wipe(oldU);
                if(installedS&&oldS.exists())wipe(oldS);
                if(movedU)bu.renameTo(oldU);
                if(movedS)bs.renameTo(oldS);
                message("Восстановление не удалось: "+safeError(error)+
                    ". Выполнен откат. Проверь исходные каталоги до запуска игры.");
            } finally {
                wipe(newU);wipe(newS);busy=false;
            }
        },"AuroraRestoreCommit").start();
    }
    private synchronized void discardStage() {
        wipe(stageUser);wipe(stageSaves);stageUser=null;stageSaves=null;busy=false;
        if(status!=null)status.setText("Восстановление отменено. Данные не изменены.");
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
    private static void wipe(File root) {
        if(root==null||!root.exists())return;
        if(Files.isSymbolicLink(root.toPath())){root.delete();return;}
        if(root.isDirectory()) {
            File[] children=root.listFiles();
            if(children!=null)for(File f:children)wipe(f);
        }
        root.delete();
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
    @Override public void onDestroy() {
        if(stageUser!=null||stageSaves!=null)discardStage();
        super.onDestroy();
    }
}

package org.junimogate.aurora;

import android.app.Activity;
import android.app.AlertDialog;
import android.content.ClipData;
import android.content.ClipboardManager;
import android.content.Context;
import android.content.Intent;
import android.graphics.Typeface;
import android.os.Bundle;
import android.os.Handler;
import android.os.Looper;
import android.provider.Settings;
import android.widget.Button;
import android.widget.LinearLayout;
import android.widget.ScrollView;
import android.widget.TextView;

import org.json.JSONArray;
import org.json.JSONObject;
import java.io.File;
import java.io.FileOutputStream;
import java.io.InputStream;
import java.io.OutputStream;
import java.net.HttpURLConnection;
import java.net.URL;
import java.nio.charset.StandardCharsets;
import java.security.MessageDigest;
import java.util.Locale;

/** Version chooser for the owner's private backups — NO R2 keys in any UI.
 * An owner-pairing link is required once. Thereafter select version and tap
 * "Скачать и установить". Android still owns the system install confirmation.
 */
public final class AuroraOwnerVersionsActivity extends Activity {
    private static final Handler MAIN=new Handler(Looper.getMainLooper());
    private static final String R2_HOST="d0ab9fdebeadcc640b3fc0324da411b3.r2.cloudflarestorage.com";
    private static final String BUCKET_PREFIX="/aurora-downloads/";
    private static final String KNOWN_BUILD="sdv-1.6.15.3-b245";
    private static final long MAX_ARCHIVE=350_000_000L;
    private LinearLayout cards;
    private TextView state;
    private Button reload;
    private boolean working=false;
    private static final class Version {
        final String id,version,sha256;
        final long size;
        Version(String id,String version,String sha,long size){
            this.id=id;this.version=version;this.sha256=sha;this.size=size;
        }
    }

    @Override public void onCreate(Bundle saved) {
        super.onCreate(saved);
        setTitle("Aurora · Версии");
        draw();
        refresh();
    }
    private TextView label(LinearLayout parent,String text,int size) {
        TextView v=new TextView(this);
        v.setText(text);v.setTextSize(size);v.setTextColor(0xfff2f3ff);
        v.setPadding(0,13,0,10);parent.addView(v);
        return v;
    }
    private Button action(LinearLayout parent,String caption,Runnable fn) {
        Button b=new Button(this);
        b.setText(caption);b.setAllCaps(false);
        b.setOnClickListener(v->fn.run());parent.addView(b);
        return b;
    }
    private void draw() {
        ScrollView scroll=new ScrollView(this);scroll.setBackgroundColor(0xff111422);
        LinearLayout content=new LinearLayout(this);content.setOrientation(1);
        content.setPadding(24,28,24,32);scroll.addView(content);
        TextView title=label(content,"AURORA / ВЕРСИИ",24);
        title.setTypeface(Typeface.DEFAULT,Typeface.BOLD);
        label(content,"Выбери версию и нажми «Скачать и установить». "+
            "R2-ключи не вводятся. Архивы доступны только в твоей личной библиотеке.",13);
        state=label(content,"Проверка библиотеки…",14);
        reload=action(content,"Обновить версии",this::refresh);
        action(content,"Привязать мою библиотеку (один раз)",this::pastePairing);
        action(content,"Отключить личную библиотеку",()->{
            AuroraOwnerSession.clear(this);
            cards.removeAllViews();state.setText("Библиотека отключена.");
        });
        cards=new LinearLayout(this);cards.setOrientation(1);content.addView(cards);
        label(content,"При установке Android покажет системное подтверждение. "+
            "Разная подпись существующей игры может заблокировать обновление. "+
            "Перед сменой версии проверь резервные копии сохранений.",12);
        setContentView(scroll);
    }

    private void pastePairing() {
        if(working)return;
        ClipboardManager clipboard=(ClipboardManager)getSystemService(Context.CLIPBOARD_SERVICE);
        ClipData clip=clipboard==null?null:clipboard.getPrimaryClip();
        if(clip==null||clip.getItemCount()==0) {
            state.setText("Скопируй одноразовое приглашение владельца и нажми ещё раз.");return;
        }
        CharSequence value=clip.getItemAt(0).coerceToText(this);
        if(value==null||value.length()>600)return;
        String raw=value.toString().trim();
        String[] fields=raw.split("\\|",-1);
        if(fields.length!=3||!"AURORAPAIR".equals(fields[0])||
                !fields[2].matches("[a-zA-Z0-9_-]{20,120}")) {
            state.setText("В буфере нет одноразового приглашения Aurora.");return;
        }
        final String server;
        try{server=AuroraOwnerSession.validateServer(fields[1]);}
        catch(Exception invalid){state.setText("Недопустимый адрес Aurora-сервера.");return;}
        working=true;reload.setEnabled(false);
        state.setText("Привязываем личную библиотеку…");
        new Thread(()->{
            String error=null;
            try {
                JSONObject claim=new JSONObject();
                claim.put("pair_code",fields[2]);
                JSONObject result=call(server+"/v1/pair/claim",null,claim.toString());
                AuroraOwnerSession.save(this,server,result.getString("session"));
            }catch(Exception failure){error="Не удалось привязать библиотеку. Код мог истечь.";}
            final String problem=error;
            MAIN.post(()->{
                if(isFinishing()||isDestroyed())return;
                working=false;reload.setEnabled(true);
                if(problem!=null){state.setText(problem);return;}
                refresh();
            });
        },"AuroraPairOwner").start();
    }

    private static String receiveBounded(InputStream in,int limit) throws Exception {
        byte[] data=new byte[8192];int n;int size=0;
        java.io.ByteArrayOutputStream bytes=new java.io.ByteArrayOutputStream();
        while((n=in.read(data))!=-1){
            size+=n;
            if(size>limit)throw new IllegalArgumentException("Oversized Aurora response");
            bytes.write(data,0,n);
        }
        return bytes.toString("UTF-8");
    }
    private static JSONObject call(String path,String session,String jsonBody) throws Exception {
        URL url=new URL(path);
        String host=url.getHost().toLowerCase(Locale.ROOT);
        if(!"https".equals(url.getProtocol()) || url.getPort()!=-1 ||
            !(host.endsWith(".up.railway.app")||host.endsWith(".workers.dev")||host.endsWith(".onrender.com")))
            throw new IllegalArgumentException("Untrusted Aurora backend");
        HttpURLConnection conn=(HttpURLConnection)url.openConnection();
        conn.setInstanceFollowRedirects(false);
        conn.setConnectTimeout(10000);conn.setReadTimeout(20000);
        conn.setRequestProperty("Accept","application/json");
        conn.setRequestProperty("Accept-Encoding","identity");
        if(session!=null)conn.setRequestProperty("Authorization","Bearer "+session);
        if(jsonBody!=null){
            conn.setRequestMethod("POST");conn.setDoOutput(true);
            conn.setRequestProperty("Content-Type","application/json; charset=utf-8");
            try(OutputStream out=conn.getOutputStream()){
                out.write(jsonBody.getBytes(StandardCharsets.UTF_8));
            }
        }
        try {
            if(conn.getResponseCode()!=200)
                throw new IllegalStateException("Backend returned "+conn.getResponseCode());
            try(InputStream stream=conn.getInputStream()){
                return new JSONObject(receiveBounded(stream,65536));
            }
        }finally{conn.disconnect();}
    }

    private void refresh(){
        if(working)return;
        final String[] saved;
        try{saved=AuroraOwnerSession.load(this);}
        catch(Exception error) {
            state.setText("Сессия повреждена: отключи библиотеку и подключи заново.");
            return;
        }
        cards.removeAllViews();
        if(saved==null){
            state.setText("Личная библиотека не привязана. "+
                "Один раз открой приглашение администратора Aurora.");return;
        }
        working=true;reload.setEnabled(false);state.setText("Получаем доступные версии…");
        new Thread(()->{
            java.util.ArrayList<Version> list=new java.util.ArrayList<>();
            boolean ok=false;
            try{
                JSONObject result=call(saved[0]+"/v1/versions",saved[1],null);
                if(!"aurora-owner-versions/v1".equals(result.getString("schema")))
                    throw new IllegalStateException("Invalid Aurora catalog");
                JSONArray rows=result.getJSONArray("versions");
                if(rows.length()>30)throw new IllegalStateException("Too many versions");
                for(int i=0;i<rows.length();i++){
                    JSONObject item=rows.getJSONObject(i);
                    String id=item.getString("id");
                    String version=item.getString("version");
                    String sha=item.getString("sha256");
                    long size=item.getLong("size");
                    if(!id.matches("[A-Za-z0-9._-]{1,70}")||
                        !version.matches("[A-Za-z0-9._+-]{1,60}")||
                        !sha.matches("[a-fA-F0-9]{64}") ||
                        size<1_000_000||size>5_000_000_000L)
                        throw new IllegalStateException("Invalid catalog row");
                    list.add(new Version(id,version,sha,size));
                }
                ok=true;
            }catch(Exception ignored){}
            final boolean ready=ok;
            MAIN.post(()->{
                if(isFinishing()||isDestroyed())return;
                working=false;reload.setEnabled(true);
                if(!ready){state.setText("Каталог пока недоступен. Проверь соединение/привязку.");return;}
                state.setText("Доступные версии: "+list.size());
                for(Version v:list){
                    LinearLayout card=new LinearLayout(this);card.setOrientation(1);
                    card.setPadding(16,14,16,14);card.setBackgroundColor(0xff243149);
                    cards.addView(card);
                    label(card,"Stardew Valley "+v.version,18);
                    label(card,"Архив "+(v.size/1_000_000)+" МБ",12);
                    if(KNOWN_BUILD.equals(v.id))
                        action(card,"Скачать и установить",()->confirmDownload(v,saved));
                    else label(card,"Для этой версии пока нет проверенного установщика Aurora.",12);
                }
            });
        },"AuroraOwnerCatalog").start();
    }
    private void confirmDownload(Version v,String[] saved) {
        if(working)return;
        new AlertDialog.Builder(this).setTitle("Скачать и установить?")
            .setMessage("Версия "+v.version+". Файл будет скачан из твоего "+
                "закрытого архива. Перед установкой Aurora проверит SHA-256, "+
                "комплект APK и затем запросит подтверждение Android.")
            .setNegativeButton("Отмена",null)
            .setPositiveButton("Скачать и установить",(dialog,which)->download(v,saved))
            .show();
    }
    private void download(Version v,String[] saved) {
        if(working)return;
        working=true;reload.setEnabled(false);
        state.setText("Запрашиваем ссылку на версию "+v.version+"…");
        new Thread(()->{
            File output=new File(getCacheDir(),"aurora-version-download.apks");
            boolean ok=false;
            String error="Загрузка не удалась. Проверь соединение и доступное место.";
            try {
                JSONObject grant=call(saved[0]+"/v1/download?id="+
                    java.net.URLEncoder.encode(v.id,"UTF-8"),saved[1],null);
                if(grant.getLong("size")!=v.size||
                    !v.sha256.equalsIgnoreCase(grant.getString("sha256")))
                    throw new IllegalStateException("Catalog changed");
                URL url=new URL(grant.getString("url"));
                String host=url.getHost().toLowerCase(Locale.ROOT);
                if(!"https".equals(url.getProtocol())||url.getPort()!=-1||
                    !R2_HOST.equals(host)||!url.getPath().startsWith(BUCKET_PREFIX))
                    throw new IllegalArgumentException("Invalid R2 signed download destination");
                if(v.size>MAX_ARCHIVE)
                    throw new IllegalStateException("Version exceeds tested APK limit");
                HttpURLConnection conn=(HttpURLConnection)url.openConnection();
                conn.setInstanceFollowRedirects(false);
                conn.setConnectTimeout(12000);
                conn.setReadTimeout(30000);
                conn.setRequestProperty("Accept-Encoding","identity");
                try {
                    if(conn.getResponseCode()!=200)
                        throw new IllegalStateException("R2 download denied");
                    MessageDigest digest=MessageDigest.getInstance("SHA-256");
                    long count=0;
                    try(InputStream in=conn.getInputStream();
                        OutputStream out=new FileOutputStream(output,false)){
                        byte[] buffer=new byte[131072];int n;long prev=0;
                        while((n=in.read(buffer))!=-1){
                            count+=n;
                            if(count>v.size)throw new IllegalStateException("Unexpected archive size");
                            digest.update(buffer,0,n);
                            out.write(buffer,0,n);
                            if(count-prev>=5_000_000){
                                prev=count;
                                final long downloaded=count;
                                MAIN.post(()->{if(!isFinishing()&&!isDestroyed())
                                    state.setText("Скачано "+(downloaded/1_000_000)+
                                    " / "+(v.size/1_000_000)+" МБ");});
                            }
                        }
                    }
                    if(count!=v.size||!v.sha256.equalsIgnoreCase(toHex(digest.digest())))
                        throw new IllegalStateException("Archive checksum does not match");
                    ok=true;
                }finally{conn.disconnect();}
            }catch(Exception e){
                error="Загрузка или проверка файла не удалась. Файл не установлен.";
            }
            if(!ok)output.delete();
            final boolean success=ok;final String message=error;
            MAIN.post(()->{
                if(isFinishing()||isDestroyed())return;
                working=false;reload.setEnabled(true);
                if(!success){state.setText(message);return;}
                state.setText("Файл проверен. Передаём Android на установку…");
                Intent installer=new Intent(this,AuroraVersionActivity.class);
                installer.putExtra("aurora-owner-verified-archive",output.getAbsolutePath());
                startActivity(installer);
            });
        },"AuroraVersionDownload").start();
    }
    private static String toHex(byte[] bytes){
        StringBuilder b=new StringBuilder();
        for(byte n:bytes)b.append(String.format(Locale.ROOT,"%02x",n&255));
        return b.toString();
    }
}

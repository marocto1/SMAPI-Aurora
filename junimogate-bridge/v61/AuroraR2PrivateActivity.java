package org.junimogate.aurora;

import android.app.Activity;
import android.app.AlertDialog;
import android.content.Intent;
import android.graphics.Typeface;
import android.net.Uri;
import android.os.Bundle;
import android.os.Handler;
import android.os.Looper;
import android.text.InputType;
import android.view.WindowManager;
import android.widget.Button;
import android.widget.EditText;
import android.widget.LinearLayout;
import android.widget.ScrollView;
import android.widget.TextView;

import org.w3c.dom.Document;
import org.w3c.dom.Element;
import org.w3c.dom.NodeList;

import java.io.ByteArrayOutputStream;
import java.io.InputStream;
import java.io.OutputStream;
import java.net.HttpURLConnection;
import java.net.URL;
import java.net.URLDecoder;
import java.nio.charset.StandardCharsets;
import java.security.MessageDigest;
import java.time.Instant;
import java.util.ArrayList;
import java.util.Locale;
import java.util.Map;

import javax.xml.parsers.DocumentBuilderFactory;

/**
 * Personal private R2 browser (6.1 development preview).
 * Never enables public access, never ships credentials and never installs APK.
 * Only the user's read-only token is accepted in the on-device settings.
 */
public final class AuroraR2PrivateActivity extends Activity {
    private static final String DEFAULT_ACCOUNT="d0ab9fdebeadcc640b3fc0324da411b3";
    private static final String DEFAULT_BUCKET="aurora-downloads";
    private static final long MAX_FILE=5L*1024*1024*1024;
    private static final Handler MAIN=new Handler(Looper.getMainLooper());
    private static final int CREATE_DOCUMENT=611;
    private EditText account,bucket,access,secret;
    private TextView status;
    private LinearLayout items;
    private boolean busy=false;
    private String selectedKey,selectedName;
    private long selectedSize;
    private static final class ObjectRow {
        final String key;
        final long size;
        ObjectRow(String key,long size){this.key=key;this.size=size;}
    }

    @Override public void onCreate(Bundle state){
        super.onCreate(state);
        setTitle("Aurora · Private R2 Downloads");
        build();
    }
    private TextView text(String s,int sp){
        TextView v=new TextView(this);
        v.setText(s);v.setTextSize(sp);v.setTextColor(0xffe9eeff);
        v.setPadding(0,10,0,10);
        return v;
    }
    private void build(){
        ScrollView scroll=new ScrollView(this);
        scroll.setBackgroundColor(0xff111422);
        LinearLayout body=new LinearLayout(this);
        body.setOrientation(1);body.setPadding(24,24,24,24);
        scroll.addView(body);
        TextView heading=text("AURORA / PRIVATE DOWNLOAD CENTER",21);
        heading.setTypeface(Typeface.DEFAULT,Typeface.BOLD);
        body.addView(heading);
        body.addView(text("Только личное закрытое R2-хранилище. Прямое скачивание " +
            "по HTTPS без публикации Bucket. Никаких игровых APK внутри лаунчера.",13));
        body.addView(text("Создай отдельный токен R2: Object Read ONLY, " +
            "ограниченный Bucket aurora-downloads. Не используй ключ Cyberduck для записи.",12));
        account=field(body,"Account ID",DEFAULT_ACCOUNT,false);
        bucket=field(body,"Bucket",DEFAULT_BUCKET,false);
        access=field(body,"Read-only Access Key ID","",false);
        secret=field(body,"Read-only Secret Access Key","",true);
        Button connect=button(body,"Сохранить приватное подключение и показать файлы",()->{
            if(busy)return;
            try {
                String id=access.getText().toString().trim();
                String key=secret.getText().toString();
                if(id.isEmpty() || key.isEmpty())
                    throw new IllegalArgumentException("Нужен отдельный токен только для чтения.");
                AuroraR2Secrets.save(this,account.getText().toString().trim(),
                    bucket.getText().toString().trim(),id,key);
                access.setText("");secret.setText("");
                refresh();
            }catch(Exception failure){
                showError("Не удалось сохранить подключение. Проверь поля и права токена.");
            }
        });
        button(body,"Обновить список из закрытого Bucket",this::refresh);
        button(body,"Отключить R2 и удалить сохранённые ключи",()->{
            AuroraR2Secrets.clear(this);
            items.removeAllViews();
            status.setText("R2 отключён. Сохранённые ключи удалены.");
        });
        status=text("Подключение ещё не проверялось.",13);
        body.addView(status);
        items=new LinearLayout(this);items.setOrientation(1);body.addView(items);
        body.addView(text("Скачивание сохраняет файл через системный выбор папки (SAF). " +
            "APKS — это архив split APK; установка не производится автоматически. " +
            "Пока идёт загрузка, оставляй Aurora открытой.",12));
        setContentView(scroll);
    }
    private EditText field(LinearLayout box,String label,String defaultValue,boolean hidden){
        box.addView(text(label,12));
        EditText field=new EditText(this);
        field.setTextColor(0xffffffff);
        field.setSingleLine(true);
        if(hidden)field.setInputType(InputType.TYPE_CLASS_TEXT|
            InputType.TYPE_TEXT_VARIATION_PASSWORD);
        else field.setInputType(InputType.TYPE_CLASS_TEXT|
            InputType.TYPE_TEXT_FLAG_NO_SUGGESTIONS);
        field.setText(defaultValue);
        box.addView(field);
        return field;
    }
    private Button button(LinearLayout box,String label,Runnable cb){
        Button button=new Button(this);
        button.setText(label);button.setAllCaps(false);
        button.setOnClickListener(v->cb.run());box.addView(button);
        return button;
    }
    private void showError(String message) {
        new AlertDialog.Builder(this).setTitle("Aurora R2").setMessage(message)
            .setPositiveButton("OK",null).show();
    }
    private static String endpoint(String[] cfg){
        return "https://"+cfg[0]+".r2.cloudflarestorage.com/"+cfg[1]+"/";
    }
    private static HttpURLConnection open(URL url,String[] cfg) throws Exception {
        HttpURLConnection http=(HttpURLConnection)url.openConnection();
        http.setConnectTimeout(12000);
        http.setReadTimeout(30000);
        http.setInstanceFollowRedirects(false);
        http.setRequestMethod("GET");
        http.setRequestProperty("Accept-Encoding","identity");
        for(Map.Entry<String,String> header:AuroraR2Signer.headers(
            url,cfg[2],cfg[3],Instant.now()).entrySet())
            http.setRequestProperty(header.getKey(),header.getValue());
        int code=http.getResponseCode();
        if(code!=200){
            http.disconnect();
            throw new IllegalStateException("R2 HTTP "+code+
                (code==403?": проверь токен Object Read и права на Bucket":""));
        }
        return http;
    }
    private static byte[] readSmall(InputStream in,int max) throws Exception {
        ByteArrayOutputStream b=new ByteArrayOutputStream();
        byte[] block=new byte[8192];int n;
        while((n=in.read(block))!=-1){
            if(b.size()+n>max)throw new IllegalArgumentException("R2 listing too large");
            b.write(block,0,n);
        }
        return b.toByteArray();
    }
    private static String child(Element parent,String name){
        NodeList list=parent.getElementsByTagName(name);
        return list.getLength()==0?"":list.item(0).getTextContent();
    }
    private static ArrayList<ObjectRow> list(String[] cfg) throws Exception {
        URL url=new URL(endpoint(cfg)+"?encoding-type=url&list-type=2&max-keys=100");
        HttpURLConnection http=open(url,cfg);
        byte[] xml;
        try(InputStream in=http.getInputStream()){xml=readSmall(in,1024*1024);}
        finally{http.disconnect();}
        DocumentBuilderFactory factory=DocumentBuilderFactory.newInstance();
        factory.setFeature("http://apache.org/xml/features/disallow-doctype-decl",true);
        factory.setFeature("http://xml.org/sax/features/external-general-entities",false);
        factory.setFeature("http://xml.org/sax/features/external-parameter-entities",false);
        factory.setXIncludeAware(false);factory.setExpandEntityReferences(false);
        Document document=factory.newDocumentBuilder().parse(
            new java.io.ByteArrayInputStream(xml));
        NodeList entries=document.getElementsByTagName("Contents");
        ArrayList<ObjectRow> result=new ArrayList<>();
        for(int i=0;i<entries.getLength() && i<100;i++){
            Element e=(Element)entries.item(i);
            String key=URLDecoder.decode(child(e,"Key"),"UTF-8");
            long size=Long.parseLong(child(e,"Size"));
            if(!key.isEmpty() && size>=0 && size<=MAX_FILE)result.add(new ObjectRow(key,size));
        }
        return result;
    }
    private void refresh(){
        if(busy)return;
        final String[] cfg;
        try {
            cfg=AuroraR2Secrets.load(this);
            if(cfg==null){status.setText("Сначала сохрани read-only ключи R2.");return;}
        }catch(Exception e){
            status.setText("Сохранённые R2-ключи недоступны. Отключи R2 и подключись снова.");
            return;
        }
        busy=true;items.removeAllViews();
        status.setText("Загружаем список из закрытого R2…");
        new Thread(()->{
            try{
                ArrayList<ObjectRow> found=list(cfg);
                MAIN.post(()->{
                    if(isFinishing()||isDestroyed())return;
                    busy=false;
                    status.setText("Файлов: "+found.size()+
                        " (первые 100). Bucket остаётся закрытым.");
                    for(ObjectRow row:found){
                        String filename=row.key;
                        button(items,filename+" · "+String.format(Locale.ROOT,
                            "%.1f МБ",row.size/(1024.0*1024.0)),()->choose(row));
                    }
                });
            }catch(Exception failure){
                MAIN.post(()->{
                    if(isFinishing()||isDestroyed())return;
                    busy=false;status.setText("R2: "+safeError(failure));
                });
            }
        },"AuroraR2List").start();
    }
    private static String safeError(Exception error){
        if(error instanceof java.net.UnknownHostException)return "нет доступа к R2 (DNS).";
        if(error instanceof java.net.SocketTimeoutException)return "тайм-аут сети.";
        if(error instanceof IllegalStateException &&
           error.getMessage()!=null && error.getMessage().startsWith("R2 HTTP "))
            return error.getMessage();
        return "запрос не выполнен. Проверь соединение, имя Bucket и токен.";
    }
    private void choose(ObjectRow row){
        if(busy)return;
        selectedKey=row.key;
        selectedSize=row.size;
        String name=row.key.substring(row.key.lastIndexOf('/')+1);
        selectedName=name.length()>180?name.substring(0,180):name;
        if(selectedName.isEmpty())selectedName="aurora-download";
        Intent intent=new Intent(Intent.ACTION_CREATE_DOCUMENT);
        intent.addCategory(Intent.CATEGORY_OPENABLE);
        intent.setType("application/octet-stream");
        intent.putExtra(Intent.EXTRA_TITLE,selectedName);
        startActivityForResult(intent,CREATE_DOCUMENT);
    }
    @Override protected void onActivityResult(int request,int result,Intent data){
        super.onActivityResult(request,result,data);
        if(request!=CREATE_DOCUMENT||result!=RESULT_OK||data==null ||
            data.getData()==null||selectedKey==null||busy)return;
        final Uri destination=data.getData();
        final String key=selectedKey;
        final long expected=selectedSize;
        selectedKey=null;
        busy=true;
        getWindow().addFlags(WindowManager.LayoutParams.FLAG_KEEP_SCREEN_ON);
        status.setText("Скачивание "+selectedName+"… оставляй Aurora открытой.");
        new Thread(()->{
            long total=0;boolean success=false;String checksum="";
            try {
                String[] cfg=AuroraR2Secrets.load(this);
                if(cfg==null)throw new IllegalStateException("No R2 credentials");
                URL url=new URL(endpoint(cfg)+AuroraR2Signer.escape(key));
                HttpURLConnection http=open(url,cfg);
                try(InputStream in=http.getInputStream();
                    OutputStream out=getContentResolver().openOutputStream(destination,"wt")){
                    if(out==null)throw new IllegalStateException("Could not open selected location");
                    long length=http.getContentLengthLong();
                    if(length>MAX_FILE || (length>=0 && length!=expected))
                        throw new IllegalStateException("R2 file changed; refresh listing");
                    MessageDigest digest=MessageDigest.getInstance("SHA-256");
                    byte[] buffer=new byte[65536];int n;
                    long lastProgress=0;
                    while((n=in.read(buffer))!=-1){
                        out.write(buffer,0,n);digest.update(buffer,0,n);total+=n;
                        if(total>MAX_FILE)throw new IllegalStateException("Oversized download");
                        if(total-lastProgress>=5*1024*1024){
                            lastProgress=total;
                            final long progress=total;
                            MAIN.post(()->{if(!isFinishing()&&!isDestroyed())
                                status.setText("Скачано "+(progress/1048576)+" МБ…");});
                        }
                    }
                    out.flush();
                    if(total!=expected)throw new IllegalStateException("Incomplete R2 download");
                    checksum=toHex(digest.digest());
                    success=true;
                }finally{http.disconnect();}
            }catch(Exception ignored){}
            final boolean ok=success;
            final String sha=checksum;
            if(!ok){
                try{android.provider.DocumentsContract.deleteDocument(
                    getContentResolver(),destination);}catch(Exception ignored){}
            }
            MAIN.post(()->{
                getWindow().clearFlags(WindowManager.LayoutParams.FLAG_KEEP_SCREEN_ON);
                busy=false;
                if(isFinishing()||isDestroyed())return;
                status.setText(ok?"Файл скачан через SAF. SHA-256: "+sha:
                    "Не удалось скачать файл. Проверь доступ/место/соединение. "+
                    "Неполный документ удалён, если хранилище разрешило удаление.");
            });
        },"AuroraR2Download").start();
    }
    private static String toHex(byte[] bytes){
        StringBuilder b=new StringBuilder();
        for(byte n:bytes)b.append(String.format(Locale.ROOT,"%02x",n&255));
        return b.toString();
    }
}

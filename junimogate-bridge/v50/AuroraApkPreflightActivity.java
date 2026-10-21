package org.junimogate.aurora;

import android.app.Activity;
import android.content.Intent;
import android.content.pm.PackageInfo;
import android.content.pm.PackageManager;
import android.content.pm.Signature;
import android.graphics.Typeface;
import android.graphics.drawable.GradientDrawable;
import android.net.Uri;
import android.os.Build;
import android.os.Bundle;
import android.os.Handler;
import android.os.Looper;
import android.widget.Button;
import android.widget.LinearLayout;
import android.widget.ScrollView;
import android.widget.TextView;

import java.io.File;
import java.io.FileOutputStream;
import java.io.InputStream;
import java.security.MessageDigest;
import java.util.Locale;

/** Aurora Safe Installer 4.4: read-only inspection of selected candidate APK.
 * No install/uninstall; no signature bypass or direct save/profile access.
 * Exact signer equality is only one requirement for an in-place upgrade.
 */
public final class AuroraApkPreflightActivity extends Activity {
    private static final int PICK_APK=440;
    private static final long MAX_APK=512L*1024L*1024L;
    private static final Handler UI=new Handler(Looper.getMainLooper());
    private TextView result;
    private Button picker;
    private int fg,muted,panel,bg;
    private boolean busy;
    @Override public void onCreate(Bundle state){
        super.onCreate(state);
        setTitle("Aurora Safe Installer 4.4");
        fg=theme("junimo_on_surface",0xffeceefa);
        muted=theme("junimo_on_surface_variant",0xffbfc5de);
        panel=theme("junimo_surface_container",0xff222b40);
        bg=theme("junimo_surface",0xff111422);
        ScrollView sc=new ScrollView(this);sc.setBackgroundColor(bg);
        LinearLayout page=new LinearLayout(this);page.setOrientation(1);
        page.setPadding(dp(18),dp(20),dp(18),dp(24));sc.addView(page);
        page.addView(label("AURORA / SAFE INSTALLER 4.4",21,true));
        LinearLayout card=card(page);
        card.addView(label("Предварительная проверка APK",17,true));
        card.addView(label("Выбери скачанный APK с помощью Android. Aurora " +
            "проверит ID пакета, сертификат и SHA-256 файла БЕЗ установки " +
            "и без удаления работающего приложения.",13,false));
        picker=button(card,"Выбрать APK для проверки",()->{
            if(busy)return;
            Intent choose=new Intent(Intent.ACTION_OPEN_DOCUMENT);
            choose.setType("application/vnd.android.package-archive");
            choose.addCategory(Intent.CATEGORY_OPENABLE);
            try{startActivityForResult(choose,PICK_APK);}
            catch(Exception err){result.setText("Файловый диалог Android недоступен.");}
        });
        result=label("APK не выбрана.",13,false);result.setTextIsSelectable(true);
        card.addView(result);
        LinearLayout safety=card(page);
        safety.addView(label("Почему это не автоустановка?",17,true));
        safety.addView(label("При разных сертификатах Android отклонит обновление " +
            "поверх существующей Aurora. Ни смена версии, ни резервный ZIP " +
            "не исправляют эту проблему. Сравнение сертификатов не доказывает " +
            "полную совместимость сохранений или успешный запуск нового APK.\n\n" +
            "У QA-версий ключи создавались заново. Не удаляй " +
            "старую Aurora, пока не проверены отдельные копии модов, профилей " +
            "и сохранений и процедура их восстановления. " +
            "Этот экран не изменяет приложение и не обходит подпись.",13,false));
        setContentView(sc);
    }
    @Override protected void onActivityResult(int request,int resultCode,Intent data){
        super.onActivityResult(request,resultCode,data);
        if(request!=PICK_APK||resultCode!=RESULT_OK||data==null||data.getData()==null)return;
        final Uri uri=data.getData();
        busy=true;picker.setEnabled(false);
        result.setText("Читаем APK для проверки, без установки…");
        new Thread(()->{
            String feedback=inspect(uri);
            UI.post(()->{
                if(isFinishing()||isDestroyed())return;
                busy=false;picker.setEnabled(true);result.setText(feedback);
            });
        },"AuroraAPKSignatureInspect").start();
    }
    private String inspect(Uri uri){
        File temp=null;
        try{
            temp=File.createTempFile("aurora-candidate-", ".apk",getCacheDir());
            MessageDigest digest=MessageDigest.getInstance("SHA-256");
            long size=0;
            try(InputStream in=getContentResolver().openInputStream(uri);
                FileOutputStream out=new FileOutputStream(temp)){
                if(in==null)throw new IllegalArgumentException("Документ недоступен");
                byte[] chunk=new byte[65536];
                int len;
                while((len=in.read(chunk))!=-1){
                    size+=len;
                    if(size>MAX_APK)throw new IllegalArgumentException("APK больше 512 МБ");
                    digest.update(chunk,0,len);
                    out.write(chunk,0,len);
                }
            }
            if(size<1024)throw new IllegalArgumentException("Слишком маленький файл");
            int flags=Build.VERSION.SDK_INT>=28?PackageManager.GET_SIGNING_CERTIFICATES:
                PackageManager.GET_SIGNATURES;
            PackageManager mgr=getPackageManager();
            PackageInfo mine=mgr.getPackageInfo(getPackageName(),flags);
            PackageInfo candidate=mgr.getPackageArchiveInfo(temp.getAbsolutePath(),flags);
            if(candidate==null)throw new IllegalArgumentException("Android не распознал APK");
            if(!getPackageName().equals(candidate.packageName))
                return "НЕ ПОДХОДИТ: ID пакета "+candidate.packageName+
                    " отличается от "+getPackageName()+".\nAPK SHA-256: "+hex(digest.digest());
            byte[] installed=certHash(mine);
            byte[] incoming=certHash(candidate);
            if(installed==null||incoming==null)
                return "Подпись прочитать не удалось. Нельзя считать обновление безопасным.";
            boolean match=MessageDigest.isEqual(installed,incoming);
            return (match?"✓ Тот же сертификат подписанта (первичная проверка).":
                "× ДРУГОЙ СЕРТИФИКАТ — не устанавливай поверх текущей Aurora.")+
                "\nТекущая версия: "+mine.versionName+
                "\nНовая заявленная: "+candidate.versionName+
                "\nУстановленный сертификат: "+hex(installed)+
                "\nСертификат APK: "+hex(incoming)+
                "\nSHA-256 APK: "+hex(digest.digest())+
                "\n\nAurora ничего не установила. Совпадение сертификата " +
                "не подтверждает возможность миграции настроек, сохранений " +
                "или совместимость игры. Для обновления всегда используется Android.";
        }catch(Exception error){
            return "Проверка не завершена. APK не установлена. "+
                "Возможная причина: неподдерживаемый/повреждённый файл или " +
                "ограничение файлового провайдера.";
        }finally{
            if(temp!=null && temp.exists())temp.delete();
        }
    }
    private byte[] certHash(PackageInfo info)throws Exception{
        Signature[] signatures;
        if(Build.VERSION.SDK_INT>=28){
            if(info.signingInfo==null)return null;
            signatures=info.signingInfo.hasMultipleSigners()?
                info.signingInfo.getApkContentsSigners():
                info.signingInfo.getSigningCertificateHistory();
        }else{
            signatures=info.signatures;
        }
        if(signatures==null||signatures.length!=1)return null;
        return MessageDigest.getInstance("SHA-256").digest(signatures[0].toByteArray());
    }
    private String hex(byte[] data){
        StringBuilder sb=new StringBuilder();
        for(byte b:data)sb.append(String.format(Locale.ROOT,"%02x",b&255));
        return sb.toString();
    }
    private LinearLayout card(LinearLayout page){
        LinearLayout v=new LinearLayout(this);v.setOrientation(1);
        v.setPadding(dp(15),dp(14),dp(15),dp(15));
        GradientDrawable shape=new GradientDrawable();
        shape.setColor(panel);shape.setCornerRadius(dp(16));v.setBackground(shape);
        LinearLayout.LayoutParams p=new LinearLayout.LayoutParams(-1,-2);
        p.topMargin=dp(14);page.addView(v,p);return v;
    }
    private TextView label(String txt,int size,boolean strong){
        TextView v=new TextView(this);v.setText(txt);v.setTextSize(size);
        v.setTextColor(fg);v.setPadding(0,dp(6),0,dp(8));
        if(strong)v.setTypeface(Typeface.DEFAULT,Typeface.BOLD);return v;
    }
    private Button button(LinearLayout box,String name,Runnable run){
        Button v=new Button(this);v.setText(name);v.setAllCaps(false);
        v.setOnClickListener(w->run.run());box.addView(v);return v;
    }
    private int theme(String key,int fallback){return AuroraWorkshopTabsView.themeColor(this,key,fallback);}
    private int dp(int v){return Math.round(v*getResources().getDisplayMetrics().density);}
}

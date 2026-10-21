package org.junimogate.aurora;

import android.app.Activity;
import android.app.AlertDialog;
import android.content.Intent;
import android.content.pm.PackageInfo;
import android.content.pm.PackageManager;
import android.content.pm.Signature;
import android.graphics.Color;
import android.graphics.Typeface;
import android.graphics.drawable.GradientDrawable;
import android.os.Build;
import android.os.Bundle;
import android.widget.Button;
import android.widget.LinearLayout;
import android.widget.ScrollView;
import android.widget.TextView;
import java.security.MessageDigest;
import java.util.Locale;

/**
 * v2.2 Update Safety. Non-destructive, read-only own certificate fingerprint
 * and explicit backup action. No alternate APK installer, silent reinstall,
 * signature bypass or live Saves write. Fingerprint is information, NOT proof
 * that a future APK has the same signer.
 */
public final class AuroraSafetyActivity extends Activity {
    private int bg,panel,fg,muted;
    @Override public void onCreate(Bundle state) {
        super.onCreate(state);
        setTitle("Aurora Safe Update");
        bg=color("junimo_surface",0xff111422);
        panel=color("junimo_surface_container",0xff222b40);
        fg=color("junimo_on_surface",0xffeceefa);
        muted=color("junimo_on_surface_variant",0xffbfc5de);
        draw();
    }
    private void draw() {
        ScrollView scroll=new ScrollView(this);scroll.setBackgroundColor(bg);
        LinearLayout page=new LinearLayout(this);page.setOrientation(1);
        page.setPadding(dp(20),dp(24),dp(20),dp(24));scroll.addView(page);
        page.addView(label("AURORA / SAFE UPDATE",23,true));
        TextView intro=label("v2.2 · проверка подписи и архива без удаления данных",13,false);
        intro.setTextColor(muted);page.addView(intro);
        LinearLayout cert=card(page);
        cert.addView(label("Подпись установленной Aurora",17,true));
        cert.addView(label(appVersion(),14,false));
        TextView fp=label("SHA-256 сертификата APK:\n"+fingerprint(),12,false);
        fp.setTextIsSelectable(true);cert.addView(fp);
        cert.addView(label("Чтобы Android обновил приложение поверх старого, " +
            "у новой APK должна быть совместимая подпись. У QA-сборок " +
            "сертификаты могли быть разными. Здесь показана подпись " +
            "ТОЛЬКО установленной версии — никакой проверки будущего APK.",12,false));
        LinearLayout backup=card(page);
        backup.addView(label("Внешняя копия модов и сохранений",17,true));
        backup.addView(label("Перед изменением APK закрой игру, экспортируй ZIP, " +
            "дождись повторной проверки SHA-256 и сохрани файл ВНЕ Aurora. " +
            "Восстановление в данной тестовой версии отключено, поэтому " +
            "переустановка со сносом данных сейчас НЕ считается безопасной.",13,false));
        button(backup,"Экспорт / Проверить ZIP",()->
            startActivity(new Intent(this,AuroraBackupActivity.class)));
        LinearLayout next=card(page);
        next.addView(label("Обновление без потери данных",17,true));
        next.addView(label("Aurora не удаляет предыдущее приложение и не " +
            "меняет сертификат. Android проверяет подпись сам. " +
            "Постоянный ключ релизов ещё не подтверждён в CI. " +
            "Никогда не удаляй работающую Aurora ради нового RC без " +
            "независимо проверенного пути восстановления.",13,false));
        button(next,"Официальные релизы",()->{
            try{Intent open=new Intent(Intent.ACTION_VIEW,android.net.Uri.parse(
              "https://github.com/marocto1/SMAPI-Aurora/releases"));
              open.addCategory(Intent.CATEGORY_BROWSABLE);startActivity(open);}
            catch(Exception e){
                new AlertDialog.Builder(this).setMessage("Открой GitHub → marocto1/SMAPI-Aurora → Releases")
                    .setPositiveButton("OK",null).show();
            }
        });
        setContentView(scroll);
    }
    private String appVersion() {
        try {
            PackageInfo p=getPackageManager().getPackageInfo(getPackageName(),0);
            return "Установлено: "+p.versionName+" · "+p.packageName;
        }catch(Exception e){return "Версию не удалось определить.";}
    }
    private String fingerprint() {
        try {
            Signature[] sigs;
            if(Build.VERSION.SDK_INT>=28) {
                PackageInfo p=getPackageManager().getPackageInfo(
                    getPackageName(),PackageManager.GET_SIGNING_CERTIFICATES);
                if(p.signingInfo==null)return "недоступен";
                sigs=p.signingInfo.hasMultipleSigners()?
                    p.signingInfo.getApkContentsSigners():
                    p.signingInfo.getSigningCertificateHistory();
            } else {
                PackageInfo p=getPackageManager().getPackageInfo(
                    getPackageName(),PackageManager.GET_SIGNATURES);
                sigs=p.signatures;
            }
            if(sigs==null||sigs.length==0)return "недоступен";
            MessageDigest digest=MessageDigest.getInstance("SHA-256");
            byte[] hash=digest.digest(sigs[0].toByteArray());
            StringBuilder sb=new StringBuilder();
            for(byte b:hash)sb.append(String.format(Locale.ROOT,"%02X",b&255));
            return sb.toString();
        }catch(Exception ex){return "недоступен"; }
    }
    private LinearLayout card(LinearLayout page){
        LinearLayout c=new LinearLayout(this);c.setOrientation(1);
        c.setPadding(dp(15),dp(14),dp(15),dp(14));
        GradientDrawable shape=new GradientDrawable();
        shape.setColor(panel);shape.setCornerRadius(dp(16));
        c.setBackground(shape);
        LinearLayout.LayoutParams p=new LinearLayout.LayoutParams(-1,-2);
        p.topMargin=dp(16);page.addView(c,p);return c;
    }
    private TextView label(String content,int sp,boolean strong){
        TextView t=new TextView(this);t.setText(content);t.setTextSize(sp);
        t.setTextColor(fg);t.setPadding(0,dp(7),0,dp(8));
        if(strong)t.setTypeface(Typeface.DEFAULT,Typeface.BOLD);
        return t;
    }
    private void button(LinearLayout c,String name,Runnable action){
        Button b=new Button(this);b.setText(name);b.setAllCaps(false);
        b.setOnClickListener(v->action.run());c.addView(b);
    }
    private int color(String id,int fallback){
        return AuroraWorkshopTabsView.themeColor(this,id,fallback);
    }
    private int dp(int x){return Math.round(x*getResources().getDisplayMetrics().density);}
}

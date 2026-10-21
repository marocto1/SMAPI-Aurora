package org.junimogate.aurora;

import android.app.Activity;
import android.content.Intent;
import android.content.pm.PackageInfo;
import android.graphics.Typeface;
import android.graphics.drawable.GradientDrawable;
import android.os.Bundle;
import android.widget.Button;
import android.widget.LinearLayout;
import android.widget.ScrollView;
import android.widget.TextView;

/** Aurora UI 3.0 hub: new native navigation, no replacement of core SMAPI.
 * The stock mod/game operations remain in the original launcher.
 */
public final class AuroraHubActivity extends Activity {
    private int bg,surface,text,muted,accent;
    @Override public void onCreate(Bundle state){
        super.onCreate(state);
        setTitle("Aurora · Next Generation 6.0 RC1");
        bg=color("junimo_surface",0xff111422);
        surface=color("junimo_surface_container",0xff222b40);
        text=color("junimo_on_surface",0xffeceefa);
        muted=color("junimo_on_surface_variant",0xffbfc5de);
        accent=color("junimo_primary",0xffa8dadd);
        render();
    }
    private void render(){
        ScrollView scroll=new ScrollView(this);scroll.setFillViewport(true);
        scroll.setBackgroundColor(bg);
        LinearLayout page=new LinearLayout(this);page.setOrientation(1);
        page.setPadding(dp(18),dp(26),dp(18),dp(28));scroll.addView(page);
        LinearLayout hero=new LinearLayout(this);hero.setOrientation(1);
        hero.setPadding(dp(18),dp(20),dp(18),dp(20));
        GradientDrawable shade=new GradientDrawable(
            GradientDrawable.Orientation.TL_BR,new int[]{getPreferences(MODE_PRIVATE).getBoolean("hub-blue",false)?0xff293a75:0xff1a3760,0xff132c36});
        shade.setCornerRadius(dp(20));hero.setBackground(shade);
        page.addView(hero);
        TextView heading=label("AURORA   /   CONNECTION 6.0",24,true,0xffecf5ff);hero.addView(heading);
        hero.addView(label("Aurora Connection Flow · Android ARM64 · RC1",13,false,0xffb9e5eb));
        hero.addView(label(installedVersion(),13,false,0xffd3e4fc));
        Button accentButton=new Button(this);
        accentButton.setText("Оформление Aurora Hub: сменить акцент");
        accentButton.setAllCaps(false);
        accentButton.setOnClickListener(v->{
            boolean azure=getPreferences(MODE_PRIVATE).getBoolean("hub-blue",false);
            getPreferences(MODE_PRIVATE).edit().putBoolean("hub-blue",!azure).apply();
            render();
        });
        hero.addView(accentButton);
        block(page,"Играть",
            "Запуск установленной Stardew Valley с SMAPI или без него.",
            "Открыть лаунчер",()->openMain());
        block(page,"Моды и Workshop 5.0",
            "Каталог официальных ссылок, активные моды, импорт через штатный менеджер.",
            "Открыть каталог",()->open(AuroraWorkshopCatalogActivity.class));
        block(page,"Aurora Unified 6.0 · Проверить всё",
            "Проверка комнаты ПК, совпадения модов и UDP-маршрута в одном отчёте.",
            "Запустить мастер подключения",()->open(AuroraUnifiedActivity.class));
        block(page,"Aurora Link 6.0",
            "Найденные ранее адреса ПК и быстрое подключение по новому коду.",
            "Aurora Link",()->open(AuroraLinkActivity.class));
        block(page,"Aurora Coop",
            "Комнаты по приглашениям, сравнение модов. Игровой Co-op запускается самой Stardew.",
            "Комнаты",()->open(AuroraRoomActivity.class));
        block(page,"Aurora Network",
            "Текущие сетевые интерфейсы и обнаружение отдельной VPN.",
            "Проверить сеть",()->open(AuroraNetworkActivity.class));
        block(page,"Recovery 2.6 · Безопасность",
            "Проверка резервных ZIP и подписи APK. Android восстановление выключено до QA.",
            "Recovery Preview",()->open(AuroraRecoveryPreviewActivity.class));
        block(page,"Aurora Coop Diagnostics 2.7",
            "Подтверждение UDP-доставки по сети или существующей VPN. " +
            "Игровой порт Stardew не тестируется.",
            "Проверить UDP 24645",()->open(AuroraUdpDiagnosticActivity.class));
        block(page,"Mod Manager Pro 2.8",
            "Метаданные активного профиля, отчёт и сравнение с ПК.",
            "Аудит модов",()->open(AuroraModAuditActivity.class));
        block(page,"Safe Installer 4.4",
            "Проверка скачанного APK, подписанта и SHA-256 без установки.",
            "Проверить APK",()->open(AuroraApkPreflightActivity.class));
        block(page,"Безопасность APK и обновления",
            "SHA-256 подписи установленной Aurora и официальный список релизов.",
            "Safe Update",()->open(AuroraSafetyActivity.class));
        block(page,"Диагностика модов",
            "Проверка активного профиля без изменения модов или сохранений.",
            "Открыть диагностику",()->open(AuroraModOverviewActivity.class));
        page.addView(label(
            "UI 6.0 — отдельный нативный центр управления. Исходный GameHost/SMAPI " +
            "не меняется. Функции VPN-туннеля и автоматического входа в ферму " +
            "пока отсутствуют.",12,false,muted));
        setContentView(scroll);
    }
    private void block(LinearLayout page,String name,String desc,String action,Runnable onClick){
        LinearLayout section=new LinearLayout(this);section.setOrientation(1);
        section.setPadding(dp(16),dp(14),dp(16),dp(12));
        GradientDrawable shape=new GradientDrawable();shape.setColor(surface);
        shape.setCornerRadius(dp(16));section.setBackground(shape);
        LinearLayout.LayoutParams p=new LinearLayout.LayoutParams(-1,-2);
        p.topMargin=dp(12);page.addView(section,p);
        section.addView(label(name,17,true,text));
        section.addView(label(desc,13,false,muted));
        Button button=new Button(this);button.setText(action);
        button.setAllCaps(false);button.setOnClickListener(v->onClick.run());
        section.addView(button);
    }
    private void open(Class<? extends Activity> destination){
        startActivity(new Intent(this,destination));
    }
    private void openMain(){
        try{Intent intent=new Intent();intent.setClassName(
            getPackageName(),"org.junimogate.app.MainActivity");
            intent.addFlags(Intent.FLAG_ACTIVITY_CLEAR_TOP|Intent.FLAG_ACTIVITY_SINGLE_TOP);
            startActivity(intent);finish();
        }catch(Exception exception){finish();}
    }
    private String installedVersion(){
        try{PackageInfo p=getPackageManager().getPackageInfo(getPackageName(),0);
            return "Aurora "+p.versionName+" · статус: тестовая сборка";}
        catch(Exception e){return "Версия приложения неизвестна";}
    }
    private TextView label(String value,int sp,boolean strong,int color){
        TextView t=new TextView(this);t.setText(value);t.setTextSize(sp);
        t.setTextColor(color);t.setPadding(0,dp(5),0,dp(7));
        if(strong)t.setTypeface(Typeface.DEFAULT,Typeface.BOLD);return t;
    }
    private int color(String name,int fallback){
        return AuroraWorkshopTabsView.themeColor(this,name,fallback);
    }
    private int dp(int n){return Math.round(n*getResources().getDisplayMetrics().density);}
}

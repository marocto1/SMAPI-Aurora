package org.junimogate.aurora;

import android.app.Activity;
import android.app.AlertDialog;
import android.content.Intent;
import android.graphics.Typeface;
import android.graphics.drawable.GradientDrawable;
import android.net.Uri;
import android.os.Bundle;
import android.widget.Button;
import android.widget.LinearLayout;
import android.widget.ScrollView;
import android.widget.TextView;
import java.util.Locale;

/** Curated source links + local mod compatibility preflight.
 * Official Nexus pages, not rehosted content or a Nexus API client.
 * The only directly downloadable ZIP is Aurora's own hash-pinned smoke mod.
 */
public final class AuroraWorkshopCatalogActivity extends Activity {
    private int bg, panel,fg,muted;
    private TextView status;
    private static final class Listing {
        final String name,category,id,url,needs;
        Listing(String n,String c,String id,String u,String dep){
            name=n;category=c;this.id=id;url=u;needs=dep;
        }
    }
    private static final Listing[] OPTIONS={
        new Listing("Content Patcher","Фреймворк","Pathoschild.ContentPatcher",
            "https://www.nexusmods.com/stardewvalley/mods/1915","SMAPI"),
        new Listing("Generic Mod Config Menu","Интерфейс",
            "spacechase0.GenericModConfigMenu",
            "https://www.nexusmods.com/stardewvalley/mods/5098","SMAPI"),
        new Listing("Stardew Valley Expanded","Расширение мира","",
            "https://www.nexusmods.com/stardewvalley/mods/3753",
            "Content Patcher и другие зависимости со страницы автора")
    };
    @Override public void onCreate(Bundle state) {
        super.onCreate(state);
        setTitle("Aurora Workshop 3.0");
        bg=color("junimo_surface",0xff111422);
        panel=color("junimo_surface_container",0xff222b40);
        fg=color("junimo_on_surface",0xffeceefa);
        muted=color("junimo_on_surface_variant",0xffbfc5de);
        draw();
    }
    private void draw(){
        ScrollView scroll=new ScrollView(this);scroll.setBackgroundColor(bg);
        LinearLayout page=new LinearLayout(this);page.setOrientation(1);
        page.setPadding(dp(16),dp(20),dp(16),dp(25));
        scroll.addView(page);
        page.addView(label("AURORA / WORKSHOP 3.0",23,true));
        TextView intro=label("Официальные страницы · зависимости · текущая активная группа",13,false);
        intro.setTextColor(muted);page.addView(intro);
        AuroraCoopCompatibility.Snapshot snapshot=AuroraCoopCompatibility.activeMods(this);
        status=label(snapshot.known?
            "Текущие моды: "+snapshot.detail:
            "Статус модов неизвестен. Открой диагностику перед установкой.",13,false);
        status.setTextColor(muted);page.addView(status);
        LinearLayout pinned=card(page);
        pinned.addView(label("Проверенная загрузка · Aurora",17,true));
        pinned.addView(label("Aurora SMAPI Launch Smoke Test · v1.0.0",14,false));
        pinned.addView(label("Тестовый ZIP автора Aurora с фиксированной SHA-256. " +
            "Не является полноценным игровым модом. Проверка работы на Android " +
            "требует журнал SMAPI, даже если скачивание успешно.",12,false));
        button(pinned,"Скачать проверенный тестовый ZIP",this::downloadSmoke);
        for(Listing listing:OPTIONS){
            LinearLayout c=card(page);
            c.addView(label(listing.name+" · "+listing.category,17,true));
            c.addView(label("Нужны: "+listing.needs,13,false));
            String installed=listing.id.isEmpty()?"Состав мод-пакета проверяй отдельно":
                !snapshot.known?"Группа недоступна":
                snapshot.mods.containsKey(listing.id.toLowerCase(Locale.ROOT))?
                    "В активной группе: "+snapshot.mods.get(listing.id.toLowerCase(Locale.ROOT)):
                    "Не найден в активной группе";
            c.addView(label(installed,12,false));
            TextView risk=label("Android: совместимость не подтверждена; " +
                "читай требования автора и журнал SMAPI.",12,false);
            risk.setTextColor(muted);c.addView(risk);
            button(c,"Открыть официальный Nexus",()->openOfficial(listing.url));
        }
        LinearLayout install=card(page);
        install.addView(label("Установка через Aurora",16,true));
        install.addView(label("На официальном Nexus: Files → Manual Download. " +
            "После скачивания вернись в Моды → Импорт ZIP и подтверди " +
            "установку штатным менеджером. Aurora не обходит ограничения Nexus.",13,false));
        button(install,"Открыть штатный импорт ZIP",()->{
            boolean opened=AuroraWorkshopTabsView.requestOriginalZipImport();
            finish();
            if(!opened)android.widget.Toast.makeText(getApplicationContext(),
                "Открой Моды → Импорт ZIP вручную",android.widget.Toast.LENGTH_LONG).show();
        });
        setContentView(scroll);
    }
    private void downloadSmoke(){
        AuroraDirectDownloads.Entry entry=AuroraDirectDownloads.CURATED[0];
        new AlertDialog.Builder(this).setTitle(entry.name)
            .setMessage("Скачать ZIP c GitHub и проверить SHA-256? " +
                "Мод НЕ устанавливается автоматически.")
            .setPositiveButton("Скачать",(d,w)->{
                status.setText("Проверка и загрузка…");
                AuroraDirectDownloads.download(this,entry,new AuroraDirectDownloads.Listener(){
                    @Override public void onProgress(String msg){status.setText(msg);}
                    @Override public void onReady(Uri uri,String name){
                        status.setText("Архив проверен: Downloads/Aurora/"+name);
                        new AlertDialog.Builder(AuroraWorkshopCatalogActivity.this)
                            .setMessage("ZIP скачан. Импортировать его через обычный экран Моды?")
                            .setPositiveButton("Открыть импорт",(a,b)->{
                                boolean ok=AuroraWorkshopTabsView.requestOriginalZipImport();
                                finish();
                                if(!ok)android.widget.Toast.makeText(getApplicationContext(),
                                    "Моды → Импорт ZIP → Загрузки/Aurora",
                                    android.widget.Toast.LENGTH_LONG).show();
                            }).setNegativeButton("Позже",null).show();
                    }
                    @Override public void onFailure(String msg){status.setText("Ошибка: "+msg);}
                });
            }).setNegativeButton("Отмена",null).show();
    }
    private void openOfficial(String url){
        try{
            Intent intent=new Intent(Intent.ACTION_VIEW,Uri.parse(url));
            intent.addCategory(Intent.CATEGORY_BROWSABLE);
            startActivity(intent);
        }catch(Exception error){
            status.setText("Не удалось открыть браузер. Используй вкладку Workshop.");
        }
    }
    private LinearLayout card(LinearLayout p){
        LinearLayout c=new LinearLayout(this);c.setOrientation(1);
        c.setPadding(dp(14),dp(13),dp(14),dp(13));
        GradientDrawable shape=new GradientDrawable();shape.setColor(panel);
        shape.setCornerRadius(dp(14));c.setBackground(shape);
        LinearLayout.LayoutParams lp=new LinearLayout.LayoutParams(-1,-2);
        lp.topMargin=dp(13);p.addView(c,lp);return c;
    }
    private TextView label(String content,int size,boolean bold){
        TextView t=new TextView(this);t.setText(content);t.setTextSize(size);
        t.setTextColor(fg);t.setPadding(0,dp(5),0,dp(6));
        if(bold)t.setTypeface(Typeface.DEFAULT,Typeface.BOLD);return t;
    }
    private Button button(LinearLayout c,String name,Runnable action){
        Button b=new Button(this);b.setText(name);b.setAllCaps(false);
        b.setOnClickListener(v->action.run());c.addView(b);return b;
    }
    private int color(String name,int fallback){
        return AuroraWorkshopTabsView.themeColor(this,name,fallback);
    }
    private int dp(int n){return Math.round(n*getResources().getDisplayMetrics().density);}
}

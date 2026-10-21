package org.junimogate.aurora;

import android.app.Activity;
import android.app.AlertDialog;
import android.content.Intent;
import android.graphics.Typeface;
import android.graphics.drawable.GradientDrawable;
import android.net.Uri;
import android.os.Bundle;
import android.widget.Button;
import android.widget.EditText;
import android.text.TextWatcher;
import android.text.Editable;
import android.widget.Spinner;
import android.widget.ArrayAdapter;
import android.widget.AdapterView;
import android.view.View;
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
    private LinearLayout listings;
    private AuroraCoopCompatibility.Snapshot active;
    private EditText search;
    private Spinner categories;
    private static final class Listing {
        final String name,category,id,url,needs;
        Listing(String n,String c,String id,String u,String dep){
            name=n;category=c;this.id=id;url=u;needs=dep;
        }
    }
    private static final String[] GROUPS={"Все","Включённые моды","Фреймворк","Интерфейс","Расширение мира","Автоматизация","Удобства"};
    private static final Listing[] OPTIONS={
        new Listing("Content Patcher","Фреймворк","Pathoschild.ContentPatcher",
            "https://www.nexusmods.com/stardewvalley/mods/1915","SMAPI"),
        new Listing("Generic Mod Config Menu","Интерфейс",
            "spacechase0.GenericModConfigMenu",
            "https://www.nexusmods.com/stardewvalley/mods/5098","SMAPI"),
        new Listing("Stardew Valley Expanded","Расширение мира","",
            "https://www.nexusmods.com/stardewvalley/mods/3753",
            "Content Patcher и другие зависимости со страницы автора"),
        new Listing("Automate","Автоматизация","Pathoschild.Automate",
            "https://www.nexusmods.com/stardewvalley/mods/1063","SMAPI"),
        new Listing("Lookup Anything","Удобства","Pathoschild.LookupAnything",
            "https://www.nexusmods.com/stardewvalley/mods/541","SMAPI"),
        new Listing("NPC Map Locations","Интерфейс","Bouhm.NPCMapLocations",
            "https://www.nexusmods.com/stardewvalley/mods/239","SMAPI")
    };
    @Override public void onCreate(Bundle state) {
        super.onCreate(state);
        setTitle("Aurora Workshop 5.0");
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
        page.addView(label("AURORA / WORKSHOP 5.0",23,true));
        TextView intro=label("Официальные страницы · фильтры по включённым модам · аудит группы",13,false);
        intro.setTextColor(muted);page.addView(intro);
        active=AuroraCoopCompatibility.activeMods(this);
        status=label(active.known?
            "Текущие моды: "+active.detail:
            "Статус модов неизвестен. Открой диагностику перед установкой.",13,false);
        status.setTextColor(muted);page.addView(status);
        LinearLayout pinned=card(page);
        pinned.addView(label("Проверенная загрузка · Aurora",17,true));
        pinned.addView(label("Aurora SMAPI Launch Smoke Test · v1.0.0",14,false));
        pinned.addView(label("Тестовый ZIP автора Aurora с фиксированной SHA-256. " +
            "Не является полноценным игровым модом. Проверка работы на Android " +
            "требует журнал SMAPI, даже если скачивание успешно.",12,false));
        button(pinned,"Скачать проверенный тестовый ZIP",this::downloadSmoke);
        LinearLayout searchCard=card(page);
        searchCard.addView(label("Найти мод и фильтр категории",16,true));
        search=new EditText(this);
        search.setSingleLine(true);search.setTextColor(fg);
        search.setHintTextColor(muted);search.setHint("Название мода…");
        searchCard.addView(search);
        categories=new Spinner(this);
        categories.setAdapter(new ArrayAdapter<String>(this,
            android.R.layout.simple_spinner_dropdown_item,GROUPS));
        searchCard.addView(categories);
        button(searchCard,"Mod Manager Pro · Отчёт активной группы",()->
            startActivity(new Intent(this,AuroraModAuditActivity.class)));
        listings=new LinearLayout(this);listings.setOrientation(1);
        page.addView(listings);
        search.addTextChangedListener(new TextWatcher(){
            public void beforeTextChanged(CharSequence s,int start,int count,int after){}
            public void onTextChanged(CharSequence s,int start,int before,int count){
                renderListings();
            }
            public void afterTextChanged(Editable s){}
        });
        categories.setOnItemSelectedListener(new AdapterView.OnItemSelectedListener(){
            public void onItemSelected(AdapterView<?> p,View v,int position,long id){
                renderListings();
            }
            public void onNothingSelected(AdapterView<?> p){}
        });
        renderListings();
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
    private void renderListings() {
        if(listings==null)return;
        listings.removeAllViews();
        String match=search==null?"":search.getText().toString().trim()
            .toLowerCase(Locale.ROOT);
        String group=categories==null?"Все":String.valueOf(categories.getSelectedItem());
        int shown=0;
        for(Listing listing:OPTIONS) {
            if("Включённые моды".equals(group)){
                if(!active.known || listing.id.isEmpty() ||
                   !active.mods.containsKey(listing.id.toLowerCase(Locale.ROOT)))continue;
            }else if(!"Все".equals(group)&&!group.equals(listing.category))continue;
            if(!match.isEmpty() && !listing.name.toLowerCase(Locale.ROOT).contains(match) &&
                !listing.category.toLowerCase(Locale.ROOT).contains(match))continue;
            shown++;
            LinearLayout c=card(listings);
            c.addView(label(listing.name+" · "+listing.category,17,true));
            c.addView(label("Нужны: "+listing.needs,13,false));
            String installed=listing.id.isEmpty()?
                "Состав и зависимости пакета проверяй отдельно":
                !active.known?"Активная группа недоступна":
                active.mods.containsKey(listing.id.toLowerCase(Locale.ROOT))?
                    "В активной группе: "+
                    active.mods.get(listing.id.toLowerCase(Locale.ROOT)):
                    "Не найден в активной группе";
            c.addView(label(installed,12,false));
            TextView warning=label("Android SMAPI: работа не подтверждена. " +
                "Следуй требованиям автора и журналу SMAPI.",12,false);
            warning.setTextColor(muted);c.addView(warning);
            boolean favorite=getPreferences(MODE_PRIVATE)
                .getBoolean("favorite:"+listing.url,false);
            button(c,favorite?"★ В избранном":"☆ Добавить в избранное",()->{
                getPreferences(MODE_PRIVATE).edit()
                    .putBoolean("favorite:"+listing.url,!favorite).apply();
                renderListings();
            });
            button(c,"Открыть официальный Nexus",()->openOfficial(listing.url));
        }
        if(shown==0)listings.addView(label("По запросу ничего не найдено.",13,false));
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

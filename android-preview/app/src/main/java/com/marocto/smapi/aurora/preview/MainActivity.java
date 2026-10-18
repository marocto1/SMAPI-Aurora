package com.marocto.smapi.aurora.preview;

import android.app.Activity;
import android.app.AlertDialog;
import android.content.Context;
import android.content.Intent;
import android.content.SharedPreferences;
import android.graphics.Color;
import android.graphics.Typeface;
import android.graphics.drawable.GradientDrawable;
import android.net.Uri;
import android.os.Bundle;
import android.os.Handler;
import android.os.Looper;
import android.provider.Settings;
import android.view.Gravity;
import android.view.View;
import android.view.ViewGroup;
import android.widget.Button;
import android.widget.FrameLayout;
import android.widget.LinearLayout;
import android.widget.ScrollView;
import android.widget.TextView;
import android.widget.Toast;
import android.util.TypedValue;
import java.util.ArrayList;
import java.util.List;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;

public final class MainActivity extends Activity {
    private static final int BG=Color.rgb(11,13,25), SURFACE=Color.rgb(26,29,46);
    private static final int RAISED=Color.rgb(36,40,62), MUTED=Color.rgb(165,172,197);
    private static final int WHITE=Color.rgb(244,246,255), PURPLE=Color.rgb(173,153,255);
    private static final int MINT=Color.rgb(139,239,198), WARN=Color.rgb(255,189,139);
    private static final int REQUEST_TREE=120, REQUEST_ZIP=121;
    private final ExecutorService work=Executors.newSingleThreadExecutor();
    private final Handler main=new Handler(Looper.getMainLooper());
    private SharedPreferences prefs;
    private LinearLayout root, content;
    private String page="home";
    private GameScanner.Report gameReport;
    private List<ModWorkspace.Mod> mods=new ArrayList<>();
    private boolean busyMods=false, busyGame=false;
    private String modError="";
    private boolean reduceMotion=false;

    @Override public void onCreate(Bundle state) {
        super.onCreate(state);
        getWindow().setStatusBarColor(BG);
        getWindow().setNavigationBarColor(BG);
        prefs=getSharedPreferences("aurora_preview",MODE_PRIVATE);
        reduceMotion=prefs.getBoolean("reduce_motion",false);
        page=state==null?"home":state.getString("page","home");
        render();
        refreshGame();
        refreshMods();
    }

    @Override protected void onSaveInstanceState(Bundle out) {
        out.putString("page",page);
        super.onSaveInstanceState(out);
    }
    private int dp(float size) {return (int)(getResources().getDisplayMetrics().density*size+0.5f);}
    private TextView txt(String text,int sp,int color,boolean bold) {
        TextView v=new TextView(this);
        v.setText(text);
        v.setTextColor(color);
        v.setTextSize(TypedValue.COMPLEX_UNIT_SP,sp);
        if(bold) v.setTypeface(Typeface.create("sans-serif",Typeface.BOLD));
        v.setIncludeFontPadding(true);
        return v;
    }
    private GradientDrawable bg(int color,float radius) {
        GradientDrawable g=new GradientDrawable();
        g.setColor(color);
        g.setCornerRadius(dp(radius));
        return g;
    }
    private GradientDrawable gradient(int[] colors,float radius) {
        GradientDrawable g=new GradientDrawable(GradientDrawable.Orientation.TL_BR,colors);
        g.setCornerRadius(dp(radius));
        return g;
    }
    private LinearLayout column() {LinearLayout l=new LinearLayout(this);l.setOrientation(LinearLayout.VERTICAL);return l;}
    private LinearLayout row() {LinearLayout l=new LinearLayout(this);l.setOrientation(LinearLayout.HORIZONTAL);l.setGravity(Gravity.CENTER_VERTICAL);return l;}
    private LinearLayout.LayoutParams lp(int width,int height,int bottom) {
        LinearLayout.LayoutParams p=new LinearLayout.LayoutParams(width<0?width:dp(width),height<0?height:dp(height));
        p.bottomMargin=dp(bottom);
        return p;
    }
    private LinearLayout.LayoutParams fill(int bottom) {return lp(-1,-2,bottom);}
    private void padding(View v,int left,int top,int right,int bottom) {
        v.setPadding(dp(left),dp(top),dp(right),dp(bottom));
    }
    private View card(LinearLayout parent,int bottom) {
        LinearLayout l=column();
        l.setBackground(bg(SURFACE,20));
        padding(l,19,18,19,18);
        parent.addView(l,fill(bottom));
        return l;
    }
    private TextView label(String s) {
        TextView v=txt(s,11,PURPLE,true);
        v.setLetterSpacing(0.1f);
        return v;
    }
    private TextView pill(String s,int color) {
        TextView v=txt(s,11,color,true);
        padding(v,12,8,12,8);
        GradientDrawable gd=bg(RAISED,30);
        gd.setStroke(dp(1),Color.rgb(58,63,91));
        v.setBackground(gd);
        return v;
    }
    private Button button(String text,boolean primary,Runnable listener) {
        Button b=new Button(this);
        b.setAllCaps(false);
        b.setText(text);
        b.setTextSize(TypedValue.COMPLEX_UNIT_SP,14);
        b.setTypeface(Typeface.create("sans-serif-medium",Typeface.BOLD));
        b.setTextColor(primary?BG:WHITE);
        b.setBackground(primary
            ?gradient(new int[]{MINT,Color.rgb(139,211,255)},15)
            :bg(RAISED,15));
        padding(b,10,8,10,8);
        b.setOnClickListener(v->listener.run());
        if(!reduceMotion) b.setStateListAnimator(null);
        return b;
    }
    private void text(LinearLayout parent,String value,int size,int color,boolean bold,int bottom) {
        parent.addView(txt(value,size,color,bold),fill(bottom));
    }
    private void navigate(String tab) {page=tab;render();}
    private void render() {
        root=column();
        root.setBackgroundColor(BG);
        setContentView(root);
        ScrollView scroll=new ScrollView(this);
        scroll.setFillViewport(true);
        scroll.setVerticalScrollBarEnabled(false);
        root.addView(scroll,new LinearLayout.LayoutParams(-1,0,1f));
        content=column();
        padding(content,19,27,19,28);
        scroll.addView(content);
        header();
        if(page.equals("mods")) modsPage();
        else if(page.equals("settings")) settingsPage();
        else homePage();
        navigation();
        if(!reduceMotion) {
            content.setAlpha(0f);
            content.setTranslationY(dp(9));
            content.animate().alpha(1f).translationY(0f).setDuration(225).start();
        }
    }
    private void header() {
        LinearLayout top=row();
        content.addView(top,fill(19));
        LinearLayout branding=column();
        top.addView(branding,new LinearLayout.LayoutParams(0,-2,1f));
        branding.addView(label("✦   S M A P I   /   A U R O R A"),fill(5));
        branding.addView(txt("ANDROID PREVIEW",12,MUTED,false),fill(0));
        top.addView(pill("v0.5.1",MINT));
    }
    private void homePage() {
        text(content,"Твоя долина.\nТвои правила.",30,WHITE,true,7);
        text(content,"Удобное управление игрой и модами на Android.",14,MUTED,false,20);

        LinearLayout hero=column();
        padding(hero,22,22,22,23);
        hero.setBackground(gradient(new int[]{Color.rgb(47,40,97),Color.rgb(34,38,74),Color.rgb(18,53,67)},24));
        content.addView(hero,fill(19));
        hero.addView(label("STARDEW VALLEY  •  ANDROID"),fill(13));
        text(hero,"Игровая библиотека",22,WHITE,true,8);
        text(hero,"Выбери установленную Stardew Valley и проверь совместимость APK.",13,WHITE,false,17);
        Button select=button("⌕  Выбрать игру",true,this::selectGame);
        hero.addView(select,fill(11));
        Button launch=button("▶  Запустить обычную игру",false,this::launchVanillaGame);
        hero.addView(launch,fill(9));
        text(hero,"SMAPI-запуск появится после сборки .NET-ядра Aurora.",12,Color.rgb(210,218,243),false,0);

        content.addView(label("СОСТОЯНИЕ УСТАНОВКИ"),fill(12));
        LinearLayout stat=(LinearLayout)card(content,10);
        LinearLayout r=row();
        stat.addView(r,fill(9));
        TextView tag=txt("Игра",16,WHITE,true);
        r.addView(tag,new LinearLayout.LayoutParams(0,-2,1f));
        String ready=gameReport==null?"ПРОВЕРКА":gameReport.valid()?"ГОТОВО":"ПРОБЛЕМА";
        r.addView(pill(ready,gameReport!=null&&gameReport.valid()?MINT:WARN));
        text(stat,busyGame?"Проверяю APK в фоновом режиме…":
            gameReport==null?"Проверка ещё не выполнена":gameReport.summary(),13,MUTED,false,10);
        String pkg=prefs.getString("selected_game","");
        text(stat,pkg.isEmpty()?"Приложение не выбрано":pkg,12,PURPLE,false,11);
        stat.addView(button("Диагностика APK",false,this::showGameReport),fill(0));

        LinearLayout smapi=(LinearLayout)card(content,16);
        smapi.addView(label("SMAPI RUNTIME"),fill(8));
        text(smapi,"Полная сборка пока недоступна",16,WHITE,true,5);
        text(smapi,"Это настоящий Android APK Aurora Preview, но он НЕ внедряет SMAPI в игру. Для полноценного SMAPI нужны игровые библиотеки сборки и тестирование.",12,MUTED,false,0);
        content.addView(label("БЫСТРЫЕ ДЕЙСТВИЯ"),fill(10));
        content.addView(button("▦  Открыть менеджер модов",false,()->navigate("mods")),fill(10));
    }
    private void modsPage() {
        text(content,"Мои моды",29,WHITE,true,7);
        text(content,"Локальная папка Mods через Android Files",13,MUTED,false,20);
        LinearLayout box=(LinearLayout)card(content,16);
        box.addView(label("ПАПКА МОДОВ"),fill(8));
        String tree=prefs.getString("mods_tree","");
        text(box,tree.isEmpty()?"Папка пока не выбрана":Uri.parse(tree).getLastPathSegment(),14,WHITE,true,7);
        text(box, "Aurora может читать и импортировать моды только в папку, выбранную тобой. Доступ к закрытым папкам других приложений Android не предоставляется.",12,MUTED,false,12);
        box.addView(button("Выбрать папку Mods",true,this::chooseModsFolder),fill(10));
        box.addView(button("＋  Импортировать ZIP модов",false,this::importModZip),fill(0));
        LinearLayout summary=(LinearLayout)card(content,12);
        summary.addView(label("БИБЛИОТЕКА"),fill(8));
        text(summary,busyMods?"Проверка папки…":
            modError.isEmpty()?mods.size()+" мод(ов) найдено":modError,16,WHITE,true,9);
        summary.addView(button("Обновить список",false,this::refreshMods),fill(0));
        for(ModWorkspace.Mod mod:mods) {
            LinearLayout item=(LinearLayout)card(content,9);
            LinearLayout r=row();
            item.addView(r,fill(6));
            TextView icon=txt("✦",24,PURPLE,true);
            r.addView(icon,lp(37,-2,0));
            LinearLayout details=column();
            r.addView(details,new LinearLayout.LayoutParams(0,-2,1f));
            text(details,mod.name,15,WHITE,true,4);
            text(details,"v"+mod.version+" · "+(mod.enabled?"Включён":"Выключен"),12,MUTED,false,0);
            if(!mod.uniqueId.isEmpty()) text(item,mod.uniqueId,11,PURPLE,false,0);
        }
        if(mods.isEmpty() && !busyMods && modError.isEmpty()) {
            LinearLayout empty=(LinearLayout)card(content,7);
            text(empty,"Здесь появятся моды из выбранной папки.",13,MUTED,false,0);
        }
    }
    private void settingsPage() {
        text(content,"Настройки",29,WHITE,true,8);
        text(content,"Персонализация и информация об Aurora",13,MUTED,false,20);
        LinearLayout appearance=(LinearLayout)card(content,16);
        appearance.addView(label("ОФОРМЛЕНИЕ"),fill(12));
        text(appearance,"Плавные переходы",17,WHITE,true,5);
        text(appearance,reduceMotion?"Анимации выключены":"Анимации включены",13,MUTED,false,12);
        appearance.addView(button(reduceMotion?"Включить анимации":"Отключить анимации",false,()->{
            reduceMotion=!reduceMotion;
            prefs.edit().putBoolean("reduce_motion",reduceMotion).apply();
            render();
        }),fill(0));
        LinearLayout about=(LinearLayout)card(content,16);
        about.addView(label("О ПРИЛОЖЕНИИ"),fill(11));
        text(about,"SMAPI Aurora · 0.5.1 Preview",17,WHITE,true,8);
        text(about,"Нативный Android-интерфейс, обнаружение установленных игр и управление папкой модов через системный файловый интерфейс.",13,MUTED,false,12);
        text(about,"Этот APK не является полнофункциональным SMAPI Loader. Он не включает, не модифицирует и не обходит лицензионные проверки Stardew Valley.",12,MUTED,false,0);
        content.addView(button("Открыть исходники на GitHub",false,()->{
            Intent i=new Intent(Intent.ACTION_VIEW,Uri.parse("https://github.com/marocto1/SMAPI-Aurora"));
            startActivity(i);
        }),fill(12));
    }
    private void navigation() {
        LinearLayout nav=row();
        nav.setBackgroundColor(SURFACE);
        padding(nav,9,7,9,7);
        root.addView(nav,new LinearLayout.LayoutParams(-1,dp(70)));
        tab(nav,"⌂","Главная","home");
        tab(nav,"▦","Моды","mods");
        tab(nav,"⚙","Настройки","settings");
    }
    private void tab(LinearLayout parent,String icon,String label,String target) {
        boolean active=page.equals(target);
        LinearLayout cell=column();
        cell.setGravity(Gravity.CENTER);
        if(active)cell.setBackground(bg(RAISED,17));
        TextView first=txt(icon,23,active?MINT:MUTED,true);first.setGravity(Gravity.CENTER);
        cell.addView(first,fill(2));
        TextView second=txt(label,11,active?WHITE:MUTED,active);second.setGravity(Gravity.CENTER);
        cell.addView(second);
        parent.addView(cell,new LinearLayout.LayoutParams(0,-1,1f));
        cell.setOnClickListener(v->navigate(target));
    }
    private void alert(String title,String body) {
        new AlertDialog.Builder(this).setTitle(title).setMessage(body).setPositiveButton("OK",null).show();
    }
    private void toast(String message) { Toast.makeText(this,message,Toast.LENGTH_LONG).show(); }

    private void selectGame() {
        work.execute(()->{
            List<GameScanner.Candidate> found=GameScanner.candidates(this);
            main.post(()->{
                if(isFinishing()) return;
                if(found.isEmpty()){alert("Игры не найдены","Система Android не предоставила список установленных приложений.");return;}
                String[] labels=new String[found.size()];
                for(int i=0;i<found.size();i++) labels[i]=found.get(i).toString();
                new AlertDialog.Builder(this).setTitle("Выбери Stardew Valley")
                    .setItems(labels,(dialog,index)->{
                        prefs.edit().putString("selected_game",found.get(index).packageName).apply();
                        gameReport=null;
                        refreshGame();
                        render();
                    }).setNegativeButton("Отмена",null).show();
            });
        });
    }
    private void refreshGame() {
        final String pkg=prefs.getString("selected_game","");
        busyGame=true;
        work.execute(()->{
            GameScanner.Report r=GameScanner.scan(this,pkg);
            main.post(()->{
                if(isFinishing())return;
                if(!pkg.equals(prefs.getString("selected_game","")))return;
                gameReport=r;
                busyGame=false;
                if(page.equals("home")) render();
            });
        });
    }
    private void showGameReport() {
        if(busyGame){toast("Сканирование ещё выполняется");return;}
        if(gameReport==null){refreshGame();return;}
        alert("Отчёт об APK",gameReport.detail());
    }
    private void launchVanillaGame() {
        String pkg=prefs.getString("selected_game","");
        if(pkg.isEmpty()){alert("Нет игры","Сначала выбери установленную Stardew Valley.");return;}
        new AlertDialog.Builder(this).setTitle("Обычный запуск")
            .setMessage("Будет запущена выбранная игра без SMAPI. Aurora Preview пока не поддерживает загрузку модов в игре.")
            .setNegativeButton("Отмена",null)
            .setPositiveButton("Запустить",(d,w)->{
                try {
                    Intent launch=getPackageManager().getLaunchIntentForPackage(pkg);
                    if(launch==null) throw new IllegalStateException("Android не предоставил активность запуска");
                    startActivity(launch);
                }catch(Exception e){alert("Не удалось запустить игру",e.getMessage());}
            }).show();
    }
    private void chooseModsFolder() {
        try {
            Intent intent=new Intent(Intent.ACTION_OPEN_DOCUMENT_TREE);
            intent.addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION | Intent.FLAG_GRANT_WRITE_URI_PERMISSION
                    | Intent.FLAG_GRANT_PERSISTABLE_URI_PERMISSION);
            startActivityForResult(intent,REQUEST_TREE);
        }catch(Exception e){alert("Выбор папки недоступен",e.getMessage());}
    }
    private void importModZip() {
        if(prefs.getString("mods_tree","").isEmpty()) {
            alert("Сначала выбери папку Mods","Выбери доступную папку Mods через Android Files.");
            return;
        }
        Intent intent=new Intent(Intent.ACTION_OPEN_DOCUMENT);
        intent.addCategory(Intent.CATEGORY_OPENABLE);
        intent.setType("*/*");
        intent.putExtra(Intent.EXTRA_MIME_TYPES,new String[]{"application/zip","application/x-zip-compressed","application/octet-stream"});
        startActivityForResult(intent,REQUEST_ZIP);
    }

    @Override protected void onActivityResult(int request,int result,Intent data) {
        super.onActivityResult(request,result,data);
        if(result!=RESULT_OK||data==null||data.getData()==null)return;
        Uri uri=data.getData();
        if(request==REQUEST_TREE) {
            try{
                int flags=data.getFlags() & (Intent.FLAG_GRANT_READ_URI_PERMISSION|Intent.FLAG_GRANT_WRITE_URI_PERMISSION);
                getContentResolver().takePersistableUriPermission(uri,flags);
                prefs.edit().putString("mods_tree",uri.toString()).apply();
                refreshMods();
                if(page.equals("mods"))render();
            }catch(Exception e){alert("Не удалось открыть папку",e.getMessage());}
        }
        if(request==REQUEST_ZIP) {
            String filename="ImportedMod.zip";
            try(android.database.Cursor c=getContentResolver().query(uri,new String[]{android.provider.OpenableColumns.DISPLAY_NAME},null,null,null)){
                if(c!=null&&c.moveToFirst()) filename=c.getString(0);
            }catch(Exception ignored){}
            if(!filename.toLowerCase(java.util.Locale.ROOT).endsWith(".zip")){
                alert("Неверный файл","Выбери ZIP-архив с manifest.json");
                return;
            }
            final String name=filename;
            busyMods=true;
            if(page.equals("mods")) render();
            work.execute(()->{
                String error=null;int count=0;
                try{
                    Uri folder=Uri.parse(prefs.getString("mods_tree",""));
                    count=new ModWorkspace(this,folder).installZip(uri,name);
                }catch(Exception ex){error=ex.getMessage();}
                final String message=error;
                final int installed=count;
                main.post(()->{
                    if(isFinishing())return;
                    busyMods=false;
                    if(message==null){toast("Импортировано файлов: "+installed);refreshMods();}
                    else {alert("Ошибка установки ZIP",message);refreshMods();}
                });
            });
        }
    }
    private void refreshMods() {
        String selected=prefs.getString("mods_tree","");
        if(selected.isEmpty()) {
            mods=new ArrayList<>();modError="";busyMods=false;
            if(page.equals("mods"))render();
            return;
        }
        busyMods=true;
        work.execute(()->{
            List<ModWorkspace.Mod> list=new ArrayList<>();
            String error="";
            try{list=new ModWorkspace(this,Uri.parse(selected)).scan();}
            catch(Exception e){error="Нет доступа к папке: "+e.getMessage();}
            final List<ModWorkspace.Mod> found=list;final String warning=error;
            main.post(()->{
                if(isFinishing())return;
                mods=found;modError=warning;busyMods=false;
                if(page.equals("mods"))render();
            });
        });
    }
    @Override public void onBackPressed() {
        if(!page.equals("home"))navigate("home");
        else super.onBackPressed();
    }
    @Override protected void onDestroy() {work.shutdownNow();super.onDestroy();}
}

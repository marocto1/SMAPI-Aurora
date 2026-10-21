package org.junimogate.aurora;

import android.app.Activity;
import android.content.Intent;
import android.graphics.Typeface;
import android.graphics.drawable.GradientDrawable;
import android.os.Bundle;
import android.widget.Button;
import android.widget.LinearLayout;
import android.widget.ScrollView;
import android.widget.TextView;

import java.util.ArrayList;
import java.util.Collections;
import java.util.Map;

/** v2.8 offline mod diagnostics; reads Aurora's existing read-only snapshot.
 * No automatic mod updating or rewriting an active mod group.
 */
public final class AuroraModAuditActivity extends Activity {
    private int bg,panel,fg,muted;
    private String report = "";
    @Override public void onCreate(Bundle saved){
        super.onCreate(saved);
        setTitle("Aurora Mod Manager Pro · Audit");
        bg=color("junimo_surface",0xff111422);
        panel=color("junimo_surface_container",0xff222b40);
        fg=color("junimo_on_surface",0xffeceefa);
        muted=color("junimo_on_surface_variant",0xffbfc5de);
        ScrollView scroll=new ScrollView(this);scroll.setBackgroundColor(bg);
        LinearLayout page=new LinearLayout(this);page.setOrientation(1);
        page.setPadding(dp(18),dp(25),dp(18),dp(20));
        scroll.addView(page);
        page.addView(label("AURORA / MOD HEALTH 2.8",22,true));
        LinearLayout card=card(page);
        card.addView(label("Активный профиль Android",17,true));
        AuroraCoopCompatibility.Snapshot snapshot=
            AuroraCoopCompatibility.activeMods(this);
        StringBuilder out=new StringBuilder();
        out.append("Источник: текущая активная группа Aurora.\n");
        out.append(snapshot.detail).append("\n");
        if(!snapshot.known){
            out.append("Достоверная проверка списка модов невозможна. " +
                "Открой штатный менеджер и создай/выбери группу.\n");
        } else {
            ArrayList<String> ids=new ArrayList<>(snapshot.mods.keySet());
            Collections.sort(ids);
            out.append("Включённых модов: ").append(ids.size()).append("\n\n");
            for(String id:ids) {
                out.append("• ").append(id).append("  v")
                    .append(snapshot.mods.get(id)).append("\n");
            }
            if(ids.isEmpty())out.append("Активная группа пуста.\n");
        }
        out.append("\nСписок основан на manifest/profile JSON, " +
            "не является доказательством успешной загрузки DLL.\n");
        out.append("Для сравнения с PC используй Aurora Coop Rooms; " +
            "для обновления модов — оригинальный импорт ZIP/Workshop.\n");
        report=out.toString();
        TextView view=label(report,12,false);
        view.setTextIsSelectable(true);card.addView(view);
        button(card,"Поделиться отчётом (без файлов модов)",()->{
            Intent send=new Intent(Intent.ACTION_SEND);
            send.setType("text/plain");
            send.putExtra(Intent.EXTRA_TEXT,report);
            startActivity(Intent.createChooser(send,"Поделиться диагностикой модов"));
        });
        button(card,"Открыть Aurora Coop для сравнения с ПК",()->
            startActivity(new Intent(this,AuroraRoomActivity.class)));
        button(card,"Открыть штатную диагностику и зависимости",()->
            startActivity(new Intent(this,AuroraModOverviewActivity.class)));
        setContentView(scroll);
    }
    private LinearLayout card(LinearLayout p){
        LinearLayout c=new LinearLayout(this);c.setOrientation(1);
        c.setPadding(dp(16),dp(13),dp(16),dp(13));
        GradientDrawable d=new GradientDrawable();
        d.setColor(panel);d.setCornerRadius(dp(16));c.setBackground(d);
        LinearLayout.LayoutParams lp=new LinearLayout.LayoutParams(-1,-2);
        lp.topMargin=dp(15);p.addView(c,lp);return c;
    }
    private TextView label(String msg,int size,boolean bold){
        TextView t=new TextView(this);t.setText(msg);t.setTextSize(size);
        t.setTextColor(fg);t.setPadding(0,dp(8),0,dp(7));
        if(bold)t.setTypeface(Typeface.DEFAULT,Typeface.BOLD);return t;
    }
    private Button button(LinearLayout box,String msg,Runnable task){
        Button b=new Button(this);b.setText(msg);b.setAllCaps(false);
        b.setOnClickListener(v->task.run());box.addView(b);return b;
    }
    private int color(String id,int def){return AuroraWorkshopTabsView.themeColor(this,id,def);}
    private int dp(int n){return Math.round(n*getResources().getDisplayMetrics().density);}
}

package org.junimogate.aurora;

import android.app.Activity;
import android.app.AlertDialog;
import android.content.Intent;
import android.graphics.Typeface;
import android.graphics.drawable.GradientDrawable;
import android.os.Bundle;
import android.os.Handler;
import android.os.Looper;
import android.widget.Button;
import android.widget.EditText;
import android.widget.LinearLayout;
import android.widget.ScrollView;
import android.widget.TextView;
import android.text.InputType;

import org.json.JSONObject;
import java.io.BufferedReader;
import java.io.InputStreamReader;
import java.net.InetSocketAddress;
import java.net.Socket;
import java.nio.charset.StandardCharsets;

/**
 * LAN pairing preflight ONLY. This is not Stardew's multiplayer protocol.
 * TCP 24643 identifies the user's Aurora PC; game joins via built-in Stardew
 * Co-op screen and UDP 24642. No ADB, elevated permission, game/save edits
 * or virtual-network extension. Manual, private IPv4 address only.
 */
public final class AuroraCoopActivity extends Activity {
    private static final int AURORA_PORT = 24643;
    private static final int TIMEOUT_MS = 2500;
    private static final Handler UI = new Handler(Looper.getMainLooper());
    private EditText ipField;
    private TextView result;
    private Button test;
    private int text, muted, bg, panel, accent;
    private boolean active;

    @Override public void onCreate(Bundle state) {
        super.onCreate(state);
        setTitle("Aurora Coop · LAN");
        text=color("junimo_on_surface",0xffeceefa);
        muted=color("junimo_on_surface_variant",0xffbfc5de);
        bg=color("junimo_surface",0xff111422);
        panel=color("junimo_surface_container",0xff222b40);
        accent=color("junimo_primary",0xffb8c5ff);
        buildUi();
    }
    private void buildUi() {
        ScrollView scroll=new ScrollView(this);
        scroll.setFillViewport(true);scroll.setBackgroundColor(bg);
        LinearLayout page=new LinearLayout(this);
        page.setOrientation(LinearLayout.VERTICAL);
        page.setPadding(dp(18),dp(24),dp(18),dp(18));
        scroll.addView(page);
        page.addView(label("AURORA  /  COOP LAN",22,true));
        TextView intro=label("Android ↔ Windows · соединение по локальному IP",13,false);
        intro.setTextColor(muted);page.addView(intro);
        LinearLayout card=card(page);
        card.addView(label("1. Подготовь ПК",17,true));
        card.addView(label("Запусти Aurora SMAPI PC v1.6.0, выбери установленную Stardew Valley, " +
          "нажми «Включить обнаружение Aurora». ПК и телефон должны быть в одной Wi-Fi-сети.",13,false));
        card.addView(label("2. IP-адрес компьютера",17,true));
        ipField = new EditText(this);
        ipField.setSingleLine(true);ipField.setTextColor(text);
        ipField.setHintTextColor(muted);
        ipField.setHint("192.168.1.100");
        ipField.setInputType(InputType.TYPE_CLASS_PHONE);
        ipField.setText(getPreferences(MODE_PRIVATE).getString("hostIp",""));
        ipField.setSelectAllOnFocus(true);
        card.addView(ipField,new LinearLayout.LayoutParams(-1,dp(52)));
        test=button(card,"Проверить подключение к Aurora PC",this::testLan);
        result=label("Проверка пока не запускалась.",13,false);
        result.setTextColor(muted);card.addView(result);

        LinearLayout guide=card(page);
        guide.addView(label("3. Запусти игру и подключись",17,true));
        guide.addView(label(
          "ПК: в самой Stardew Valley выбери Co-op → Host, открой ферму и подготовь домик для гостя.\n\n" +
          "Телефон: в экспериментальном мобильном мультиплеере выбери Co-op → Join " +
          "и введи тот же IP ПК. Игра использует UDP 24642 — он НЕ проверяется тестом Aurora.\n\n" +
          "Если кнопки Co-op на Android нет: на главном экране нажми листья логотипа " +
          "↑ ↑ ↓ ↓ ← → ← →, затем «?», вернись назад. " +
          "Смотри официальную инструкцию Stardew Valley.",13,false));
        button(guide,"Вернуться к запуску Aurora",this::openLauncher);
        button(guide,"Открыть официальный гайд",this::openGuide);

        LinearLayout warning=card(page);
        warning.addView(label("Что означает успешная проверка",15,true));
        TextView notice=label(
          "Только то, что Aurora Android достигла TCP-сервиса Aurora PC. " +
          "Это НЕ доказывает, что SMAPI/моды совместимы, что ферма открыта, " +
          "или что UDP-мультиплеер уже работает. Не используй единственное сохранение " +
          "в экспериментальном мультиплеере без резервной копии.",12,false);
        notice.setTextColor(muted);warning.addView(notice);
        setContentView(scroll);
    }

    static boolean validPrivateIPv4(String address) {
        if(address==null || !address.matches("[0-9]{1,3}(\\.[0-9]{1,3}){3}")) return false;
        String[] parts=address.split("\\.");
        int[] oct=new int[4];
        for(int i=0;i<4;i++){
            try {oct[i]=Integer.parseInt(parts[i]);} catch(NumberFormatException error){return false;}
            if(oct[i]>255)return false;
        }
        return oct[0]==10 || (oct[0]==172&&oct[1]>=16&&oct[1]<=31) ||
               (oct[0]==192&&oct[1]==168);
    }

    private void testLan() {
        if(active)return;
        String ip=ipField.getText().toString().trim();
        if(!validPrivateIPv4(ip)){
            result.setText("Введите локальный IPv4: 192.168.x.x, 10.x.x.x или 172.16–31.x.x");
            return;
        }
        getPreferences(MODE_PRIVATE).edit().putString("hostIp",ip).apply();
        active=true;test.setEnabled(false);
        result.setText("Подключение к "+ip+":"+AURORA_PORT+" …");
        new Thread(() -> {
            String answer;
            try(Socket connection=new Socket()) {
                connection.connect(new InetSocketAddress(ip,AURORA_PORT),TIMEOUT_MS);
                connection.setSoTimeout(TIMEOUT_MS);
                BufferedReader input=new BufferedReader(
                    new InputStreamReader(connection.getInputStream(),StandardCharsets.UTF_8));
                char[] buf=new char[4096];int n=input.read(buf);
                if(n<=0||n>=buf.length) throw new IllegalArgumentException("Некорректный ответ");
                JSONObject data=new JSONObject(new String(buf,0,n).trim());
                if(!"aurora-coop-status/v1".equals(data.optString("schema")) ||
                    !"windows".equals(data.optString("platform")) ||
                    !"Aurora SMAPI PC".equals(data.optString("launcher")))
                    throw new IllegalArgumentException("Обнаружен не Aurora SMAPI PC");
                answer="Aurora PC обнаружена: "+data.optString("launcher_version")+
                    "\nПрофиль ПК: "+data.optString("profile")+
                    "\nSMAPI: "+("true".equals(data.optString("smapi_installed"))?
                    "найден":"не установлен")+
                    "\nТеперь открой ферму на ПК и введи IP в Stardew Valley на телефоне.";
            } catch(Exception e) {
                answer="Нет ответа от Aurora PC. Проверь IP, одну Wi-Fi-сеть, " +
                   "включён ли сервер обнаружения на ПК и разрешение в Windows Firewall " +
                   "для частной сети. UDP-порт игры этой кнопкой не проверяется.";
            }
            final String message=answer;
            UI.post(() -> {
                if(isFinishing()||isDestroyed())return;
                result.setText(message);active=false;test.setEnabled(true);
            });
        },"AuroraLanCheck").start();
    }

    private void openLauncher() {
        Intent launch = new Intent();
        launch.setClassName(getPackageName(),"org.junimogate.app.MainActivity");
        launch.addFlags(Intent.FLAG_ACTIVITY_CLEAR_TOP|Intent.FLAG_ACTIVITY_SINGLE_TOP);
        try{startActivity(launch);finish();}
        catch(Exception e){
            new AlertDialog.Builder(this).setMessage("Открой Aurora обычным способом.")
                .setPositiveButton("OK",null).show();
        }
    }
    private void openGuide() {
        try {
            Intent intent=new Intent(Intent.ACTION_VIEW,
                android.net.Uri.parse("https://www.stardewvalley.net/mobile-multiplayer-guide/"));
            intent.addCategory(Intent.CATEGORY_BROWSABLE);
            startActivity(intent);
        } catch(Exception e) {
            result.setText("Открой stardewvalley.net/mobile-multiplayer-guide/ в браузере.");
        }
    }
    private LinearLayout card(LinearLayout parent) {
        LinearLayout v=new LinearLayout(this);v.setOrientation(LinearLayout.VERTICAL);
        v.setPadding(dp(15),dp(13),dp(15),dp(13));
        GradientDrawable d=new GradientDrawable();d.setColor(panel);d.setCornerRadius(dp(15));
        v.setBackground(d);
        LinearLayout.LayoutParams p=new LinearLayout.LayoutParams(-1,-2);
        p.topMargin=dp(12);parent.addView(v,p);return v;
    }
    private TextView label(String value,int size,boolean bold) {
        TextView v=new TextView(this);v.setText(value);v.setTextSize(size);v.setTextColor(text);
        v.setPadding(0,dp(8),0,dp(7));
        if(bold)v.setTypeface(Typeface.DEFAULT,Typeface.BOLD);
        return v;
    }
    private Button button(LinearLayout parent,String name,Runnable run) {
        Button b=new Button(this);b.setText(name);b.setAllCaps(false);b.setOnClickListener(v->run.run());
        parent.addView(b,new LinearLayout.LayoutParams(-1,dp(52)));return b;
    }
    private int color(String name,int fallback) {
        return AuroraWorkshopTabsView.themeColor(this,name,fallback);
    }
    private int dp(int n){return Math.round(n*getResources().getDisplayMetrics().density);}
}

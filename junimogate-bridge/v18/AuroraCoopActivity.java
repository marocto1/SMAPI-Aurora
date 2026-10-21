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
import java.net.DatagramPacket;
import java.net.DatagramSocket;
import java.net.InetAddress;
import java.net.SocketTimeoutException;
import java.security.SecureRandom;
import java.util.ArrayList;
import java.util.LinkedHashSet;
import java.util.Locale;
import java.util.Set;
import java.net.Socket;
import java.nio.charset.StandardCharsets;

/**
 * v1.7 LAN auto-discovery via UDP 24644 and v1.8 read-only compatibility.
 * TCP 24643 identifies Aurora PC. Neither service joins a Stardew farm
 * (actual game uses UDP 24642). No ADB, VPN, secrets or save-file edits.
 */
public final class AuroraCoopActivity extends Activity {
    private static final int AURORA_PORT = 24643;
    private static final int DISCOVERY_PORT = 24644;
    private static final int TIMEOUT_MS = 2500;
    private static final Handler UI = new Handler(Looper.getMainLooper());
    private EditText ipField;
    private TextView result;
    private Button test, discover;
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
        page.addView(label("AURORA  /  COOP AUTO + COMPATIBILITY",22,true));
        TextView intro=label("Android ↔ Windows · автопоиск ПК в одной Wi-Fi-сети",13,false);
        intro.setTextColor(muted);page.addView(intro);
        LinearLayout card=card(page);
        card.addView(label("1. Подготовь ПК",17,true));
        card.addView(label("Запусти Aurora SMAPI PC v1.8.0, выбери папку игры и профиль модов, " +
          "нажми «Включить обнаружение Aurora». ПК и телефон должны быть в одной Wi-Fi-сети.",13,false));
        card.addView(label("2. Найди Aurora PC автоматически",17,true));
        discover=button(card,"Найти компьютеры с Aurora",this::discoverLan);
        card.addView(label("Или введи адрес вручную (на случай блокировки UDP 24644)",12,false));
        card.addView(label("IP-адрес компьютера",16,true));
        ipField = new EditText(this);
        ipField.setSingleLine(true);ipField.setTextColor(text);
        ipField.setHintTextColor(muted);
        ipField.setHint("192.168.1.100");
        ipField.setInputType(InputType.TYPE_CLASS_PHONE);
        ipField.setText(getPreferences(MODE_PRIVATE).getString("hostIp",""));
        ipField.setSelectAllOnFocus(true);
        card.addView(ipField,new LinearLayout.LayoutParams(-1,dp(52)));
        test=button(card,"Подключиться и сравнить версии/моды",this::testLan);
        result=label("Автопоиск пока не запускался.",13,false);
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
          "Совпадение номеров модов НЕ доказывает, что DLL-моды работают на Android, что ферма открыта, " +
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

    private void discoverLan() {
        if(active)return;
        active=true;
        discover.setEnabled(false);
        test.setEnabled(false);
        result.setText("Поиск компьютеров в Wi-Fi по UDP 24644…");
        new Thread(() -> {
            Set<String> found=new LinkedHashSet<>();
            try(DatagramSocket udp=new DatagramSocket()) {
                udp.setBroadcast(true);
                udp.setSoTimeout(650);
                byte[] random=new byte[8];
                new SecureRandom().nextBytes(random);
                StringBuilder hex=new StringBuilder();
                for(byte b:random)hex.append(String.format(Locale.ROOT,"%02x",b&255));
                String nonce=hex.toString();
                byte[] request=("AURORA_DISCOVER_V2 "+nonce)
                    .getBytes(StandardCharsets.US_ASCII);
                byte[] reply=new byte[128];
                for(int pass=0;pass<5;pass++){
                    if(pass==0 || pass==2) {
                        udp.send(new DatagramPacket(request,request.length,
                            InetAddress.getByName("255.255.255.255"),DISCOVERY_PORT));
                    }
                    DatagramPacket received=new DatagramPacket(reply,reply.length);
                    try {
                        udp.receive(received);
                        String message=new String(received.getData(),received.getOffset(),
                            received.getLength(),StandardCharsets.US_ASCII);
                        String address=received.getAddress().getHostAddress();
                        if(message.equals("AURORA_HERE_V2 "+nonce+" 24643") &&
                           validPrivateIPv4(address))found.add(address);
                        if(found.size()>=12)break;
                    } catch(SocketTimeoutException ignored){}
                }
            } catch(Exception ignored) {
                // Router/firewall may block broadcast; manual IP remains available.
            }
            final ArrayList<String> hosts=new ArrayList<>(found);
            UI.post(() -> {
                if(isFinishing()||isDestroyed())return;
                active=false;
                discover.setEnabled(true);test.setEnabled(true);
                if(hosts.isEmpty()){
                    result.setText("Aurora PC не найдена автоматически. Проверь " +
                        "Windows Aurora v1.8, разреши UDP 24644 и TCP 24643 " +
                        "только в частной сети. Можешь ввести IP вручную.");
                    return;
                }
                String[] names=new String[hosts.size()];
                for(int i=0;i<hosts.size();i++)names[i]="Aurora PC · "+hosts.get(i);
                new AlertDialog.Builder(this).setTitle("Найдено ПК: "+hosts.size())
                    .setItems(names,(dialog,chosen)->{
                        ipField.setText(hosts.get(chosen));
                        testLan();
                    })
                    .setNegativeButton("Отмена",null).show();
                result.setText("Найдено устройств: "+hosts.size()+". Выбери ПК.");
            });
        },"AuroraDiscoverLAN").start();
    }

    private static String readLineBounded(BufferedReader input) throws Exception {
        StringBuilder result=new StringBuilder();
        for(int i=0;i<32768;i++) {
            int value=input.read();
            if(value<0)break;
            if(value=='\n')return result.toString();
            if(value=='\r')continue;
            result.append((char)value);
        }
        throw new IllegalArgumentException("Aurora PC ответила слишком длинным или незавершённым сообщением");
    }

    private void testLan() {
        if(active)return;
        String ip=ipField.getText().toString().trim();
        if(!validPrivateIPv4(ip)){
            result.setText("Введите локальный IPv4: 192.168.x.x, 10.x.x.x или 172.16–31.x.x");
            return;
        }
        getPreferences(MODE_PRIVATE).edit().putString("hostIp",ip).apply();
        active=true;test.setEnabled(false);discover.setEnabled(false);
        result.setText("Подключение к "+ip+":"+AURORA_PORT+" …");
        new Thread(() -> {
            String answer;
            try(Socket connection=new Socket()) {
                connection.connect(new InetSocketAddress(ip,AURORA_PORT),TIMEOUT_MS);
                connection.setSoTimeout(TIMEOUT_MS);
                BufferedReader input=new BufferedReader(
                    new InputStreamReader(connection.getInputStream(),StandardCharsets.UTF_8));
                JSONObject data=new JSONObject(readLineBounded(input));
                answer=AuroraCoopCompatibility.compare(this,data);
                answer+="\n\nСледующий шаг: открой Co-op → Host на ПК и " +
                    "Co-op → Join на Android. Aurora не открывает ферму автоматически.";
            } catch(Exception e) {
                answer="Не удалось получить совместимость от Aurora PC v1.8. " +
                    "Убедись, что ПК и телефон в одной сети, на ПК включён автопоиск, " +
                    "Windows Firewall пропускает TCP 24643 и UDP 24644. " +
                    "Aurora PC v1.6 использует старый формат и нуждается в обновлении. " +
                    "Статус не доказывает доступность UDP 24642.";
            }
            final String message=answer;
            UI.post(() -> {
                if(isFinishing()||isDestroyed())return;
                result.setText(message);
                active=false;test.setEnabled(true);discover.setEnabled(true);
            });
        },"AuroraLANCompatibility").start();
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

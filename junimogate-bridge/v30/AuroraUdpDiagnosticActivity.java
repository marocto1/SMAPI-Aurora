package org.junimogate.aurora;

import android.app.Activity;
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

import java.net.DatagramPacket;
import java.net.DatagramSocket;
import java.net.InetAddress;
import java.security.SecureRandom;
import java.nio.charset.StandardCharsets;
import java.util.Locale;

/** v2.7 user-initiated UDP preflight for Aurora PC, NEVER Stardew gameplay.
 * Uses ephemeral room token from existing Aurora invite; makes one bounded
 * UDP 24645 echo exchange on the chosen private LAN/overlay IP.
 */
public final class AuroraUdpDiagnosticActivity extends Activity {
    private static final Handler UI = new Handler(Looper.getMainLooper());
    private static final int PORT=24645;
    private int fg,muted,bg,panel;
    private TextView result;
    private EditText code;
    private Button check;
    private boolean running;
    @Override public void onCreate(Bundle saved) {
        super.onCreate(saved);
        setTitle("Aurora Coop · UDP диагностика");
        fg=color("junimo_on_surface",0xffeceefa);
        muted=color("junimo_on_surface_variant",0xffbfc5de);
        bg=color("junimo_surface",0xff111422);
        panel=color("junimo_surface_container",0xff222b40);
        ScrollView sc=new ScrollView(this);sc.setBackgroundColor(bg);
        LinearLayout page=new LinearLayout(this);page.setOrientation(1);
        page.setPadding(dp(18),dp(26),dp(18),dp(18));sc.addView(page);
        page.addView(label("AURORA / COOP DIAGNOSTICS",21,true));
        TextView info=label("Проверка UDP между устройствами через уже существующий " +
            "LAN/VPN-маршрут, без изменения игры.",13,false);
        info.setTextColor(muted);page.addView(info);
        LinearLayout box=card(page);
        box.addView(label("Код приглашения Aurora PC v3.0 RC",17,true));
        code=new EditText(this);code.setTextSize(13);code.setTextColor(fg);
        code.setHintTextColor(muted);code.setSingleLine(false);
        code.setInputType(InputType.TYPE_CLASS_TEXT|InputType.TYPE_TEXT_FLAG_NO_SUGGESTIONS);
        code.setHint("AURORA2|IP|32-символьный токен");box.addView(code);
        check=button(box,"Проверить передачу UDP-пакетов",this::probe);
        result=label("Проверка не запускалась.",13,false);
        result.setTextColor(muted);box.addView(result);
        LinearLayout caution=card(page);
        caution.addView(label("Что именно проверяет тест",16,true));
        caution.addView(label("Aurora отправляет небольшой UDP-пакет на ПОРТ 24645 " +
            "Windows Aurora. Полученный ответ означает только доступность " +
            "диагностического сервиса.\n\n" +
            "Stardew Valley использует игровой UDP 24642: его открытость, " +
            "состояние фермы, совпадение модов и возможность входа " +
            "в игру ЭТОТ тест не подтверждает.\n\n" +
            "Не открывай порты Aurora в публичный интернет. " +
            "Через разные сети нужна заранее подключённая защищённая VPN.",13,false));
        setContentView(sc);
    }
    private void probe(){
        if(running)return;
        AuroraRoomActivity.Invite invite;
        try{invite=AuroraRoomActivity.parse(code.getText().toString());}
        catch(Exception invalid){result.setText("Неверный код приглашения.");return;}
        running=true;check.setEnabled(false);
        result.setText("Проверяю UDP "+invite.ip+":"+PORT+"…");
        new Thread(()->{
            String message;
            try(DatagramSocket udp=new DatagramSocket()) {
                udp.setSoTimeout(2500);
                byte[] bytes=new byte[8];
                new SecureRandom().nextBytes(bytes);
                StringBuilder nonce=new StringBuilder();
                for(byte b:bytes)nonce.append(String.format(Locale.ROOT,"%02x",b&255));
                byte[] request=("AURORA_UDP_V1 "+invite.token+" "+nonce)
                    .getBytes(StandardCharsets.US_ASCII);
                InetAddress address=InetAddress.getByName(invite.ip);
                udp.send(new DatagramPacket(request,request.length,address,PORT));
                byte[] received=new byte[128];
                DatagramPacket reply=new DatagramPacket(received,received.length);
                udp.receive(reply);
                String text=new String(reply.getData(),reply.getOffset(),
                    reply.getLength(),StandardCharsets.US_ASCII);
                if(reply.getAddress().getHostAddress().equals(invite.ip) &&
                    text.equals("AURORA_UDP_OK_V1 "+nonce)) {
                    message="UDP 24645: ответ Aurora PC получен. " +
                        "Это НЕ проверка игрового UDP 24642.";
                } else {
                    message="Получен некорректный ответ UDP. " +
                        "Проверь приглашение и сеть.";
                }
            } catch(Exception err){
                message="Aurora PC не ответила по UDP 24645. " +
                    "Проверь, что комната открыта, Windows Firewall разрешает " +
                    "UDP 24645 только в частной/VPN сети, и VPN соединена. " +
                    "Не перенаправляй публичные порты.";
            }
            String outcome=message;
            UI.post(()->{
                if(isFinishing()||isDestroyed())return;
                running=false;check.setEnabled(true);result.setText(outcome);
            });
        },"AuroraUdpPreflight").start();
    }
    private LinearLayout card(LinearLayout p){
        LinearLayout c=new LinearLayout(this);c.setOrientation(1);
        c.setPadding(dp(15),dp(15),dp(15),dp(15));
        GradientDrawable d=new GradientDrawable();
        d.setColor(panel);d.setCornerRadius(dp(16));c.setBackground(d);
        LinearLayout.LayoutParams lp=new LinearLayout.LayoutParams(-1,-2);
        lp.topMargin=dp(14);p.addView(c,lp);return c;
    }
    private TextView label(String v,int sz,boolean bold){
        TextView t=new TextView(this);t.setText(v);t.setTextSize(sz);
        t.setTextColor(fg);t.setPadding(0,dp(6),0,dp(8));
        if(bold)t.setTypeface(Typeface.DEFAULT,Typeface.BOLD);return t;
    }
    private Button button(LinearLayout parent,String label,Runnable cb){
        Button b=new Button(this);b.setText(label);b.setAllCaps(false);
        b.setOnClickListener(v->cb.run());parent.addView(b);return b;
    }
    private int color(String n,int fallback){
        return AuroraWorkshopTabsView.themeColor(this,n,fallback);
    }
    private int dp(int size){
        return Math.round(size*getResources().getDisplayMetrics().density);
    }
}

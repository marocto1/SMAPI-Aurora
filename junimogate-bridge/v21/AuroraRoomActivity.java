package org.junimogate.aurora;

import android.app.Activity;
import android.app.AlertDialog;
import android.content.ClipData;
import android.content.ClipboardManager;
import android.content.Context;
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
import java.io.OutputStream;
import java.net.InetSocketAddress;
import java.net.Socket;
import java.nio.charset.StandardCharsets;
import java.util.Locale;
import java.util.regex.Pattern;

/** Room invitation preflight over LAN or an ALREADY connected VPN.
 * Not an internet VPN, tunnel, matchmaking server, game UDP proxy, or join.
 * Invite is short-lived and kept only in RAM; no save/mod mutation.
 */
public final class AuroraRoomActivity extends Activity {
    private static final Pattern TOKEN=Pattern.compile("[a-f0-9]{32}");
    private static final Handler MAIN=new Handler(Looper.getMainLooper());
    private static final int PORT=24643;
    private EditText code;
    private TextView details;
    private Button connect;
    private volatile boolean busy;
    private int surface,panel,fg,secondary;
    static final class Invite {
        final String ip,token;
        Invite(String ip,String token){this.ip=ip;this.token=token;}
    }

    static boolean allowedIPv4(String address) {
        if(address==null||!address.matches("[0-9]{1,3}(\\.[0-9]{1,3}){3}"))return false;
        String[] fields=address.split("\\.");int[] oct=new int[4];
        try {for(int i=0;i<4;i++){oct[i]=Integer.parseInt(fields[i]);if(oct[i]>255)return false;}}
        catch(NumberFormatException e){return false;}
        if(oct[0]==10||oct[0]==172&&oct[1]>=16&&oct[1]<=31||
           oct[0]==192&&oct[1]==168)return true;
        return oct[0]==100 && oct[1]>=64 && oct[1]<=127 &&
               !(oct[1]==100&&oct[2]==100);
    }

    static Invite parse(String raw) {
        if(raw==null || raw.length()>120)throw new IllegalArgumentException("Слишком длинный код");
        String[] pieces=raw.trim().split("\\|",-1);
        if(pieces.length!=3||!"AURORA2".equals(pieces[0]) ||
           !allowedIPv4(pieces[1])||!TOKEN.matcher(pieces[2]).matches())
            throw new IllegalArgumentException("Формат: AURORA2|локальный-IP|32-символа");
        return new Invite(pieces[1],pieces[2]);
    }

    @Override public void onCreate(Bundle saved) {
        super.onCreate(saved);
        setTitle("Aurora Coop · Комнаты");
        surface=color("junimo_surface",0xff111422);
        panel=color("junimo_surface_container",0xff222b40);
        fg=color("junimo_on_surface",0xffeceefa);
        secondary=color("junimo_on_surface_variant",0xffbfc5de);
        ScrollView scroll=new ScrollView(this);scroll.setBackgroundColor(surface);
        LinearLayout page=new LinearLayout(this);page.setOrientation(1);
        page.setPadding(dp(18),dp(24),dp(18),dp(20));
        scroll.addView(page);
        page.addView(text("AURORA / COOP ROOMS",22,true));
        TextView intro=text("v1.9 Network bridge + v2.0 комнатные приглашения",13,false);
        intro.setTextColor(secondary);page.addView(intro);
        LinearLayout room=card(page);
        room.addView(text("Присоединиться к комнате ПК",18,true));
        room.addView(text("На Windows открой Aurora SMAPI PC v2.0 и нажми " +
            "«Открыть комнату». Получи код у друга.",14,false));
        code=new EditText(this);
        code.setSingleLine(false);code.setMinLines(2);code.setMaxLines(3);
        code.setTextColor(fg);code.setTextSize(13);
        code.setHint("AURORA2|192.168.1.10|0123456789abcdef0123456789abcdef");
        code.setHintTextColor(secondary);
        code.setInputType(InputType.TYPE_CLASS_TEXT|InputType.TYPE_TEXT_FLAG_NO_SUGGESTIONS);
        room.addView(code);
        button(room,"Вставить приглашение",this::pasteInvite);
        connect=button(room,"Проверить комнату и моды",this::check);
        details=text("Нет проверенного подключения.",13,false);
        details.setTextColor(secondary);room.addView(details);
        LinearLayout network=card(page);
        network.addView(text("Через интернет",18,true));
        network.addView(text("Если вы в разных сетях, сначала подключи оба устройства " +
            "к ОДНОЙ доверенной виртуальной сети (например, Tailscale). " +
            "На Windows в поле IP комнаты введи адрес VPN в диапазоне " +
            "100.64–127.x.x, открой комнату, скопируй приглашение. " +
            "На Android VPN должна быть активна ДО проверки. " +
            "Aurora не создаёт VPN самостоятельно и не обходит авторизацию.",13,false));
        button(network,"Открыть инструкцию по VPN",() -> {
            try{Intent i=new Intent(Intent.ACTION_VIEW,android.net.Uri.parse(
                "https://tailscale.com/kb/1033/ip-and-dns-addresses/"));
                i.addCategory(Intent.CATEGORY_BROWSABLE);startActivity(i);}
            catch(Exception e){details.setText("Открой tailscale.com/kb/1033/ip-and-dns-addresses/");}
        });
        LinearLayout game=card(page);
        game.addView(text("После успешной проверки",17,true));
        game.addView(text("ПК вручную создаёт ферму через Stardew Valley Co-op → Host. " +
            "Android использует внутриигровое Co-op → Join и тот же IP. " +
            "Для игры нужен доступ к UDP 24642 внутри вашей LAN/VPN. " +
            "Успешная проверка Aurora TCP 24643 НЕ проверяет UDP и не означает вход в ферму.",13,false));
        setContentView(scroll);
    }
    private void pasteInvite() {
        ClipboardManager clipboard=(ClipboardManager)getSystemService(Context.CLIPBOARD_SERVICE);
        ClipData clip=clipboard==null?null:clipboard.getPrimaryClip();
        if(clip==null||clip.getItemCount()==0){details.setText("Буфер обмена пуст.");return;}
        CharSequence value=clip.getItemAt(0).coerceToText(this);
        if(value!=null){String raw=value.toString();if(raw.length()<121)code.setText(raw);}
    }
    private void check() {
        if(busy)return;
        final Invite invitation;
        try{invitation=parse(code.getText().toString());}
        catch(Exception ex){details.setText("Некорректный код комнаты.");return;}
        busy=true;connect.setEnabled(false);
        details.setText("Проверяем Aurora PC по TCP 24643…");
        new Thread(() -> {
            String message;
            try(Socket socket=new Socket()) {
                socket.connect(new InetSocketAddress(invitation.ip,PORT),2500);
                socket.setSoTimeout(2800);
                OutputStream out=socket.getOutputStream();
                out.write(("AURORA_ROOM_V1 "+invitation.token+"\n")
                    .getBytes(StandardCharsets.US_ASCII));out.flush();
                BufferedReader reader=new BufferedReader(new InputStreamReader(
                    socket.getInputStream(),StandardCharsets.UTF_8));
                StringBuilder body=new StringBuilder();
                boolean completed=false;
                for(int k=0;k<32768;k++){
                    int c=reader.read();if(c<0)break;
                    if(c=='\n'){completed=true;break;}
                    body.append((char)c);
                }
                if(!completed||body.length()==0)
                    throw new IllegalArgumentException("Неполный ответ");
                JSONObject pc=new JSONObject(body.toString());
                message="Комната Aurora доступна по IP "+invitation.ip+"\n\n"+
                    AuroraCoopCompatibility.compare(this,pc)+
                    "\n\nЭто только проверка лаунчеров. В игру заходи через Co-op.";
            } catch(Exception ex) {
                message="Не удалось проверить комнату. Убедись, что владелец её не закрыл, " +
                    "приглашение новое, а компьютер и телефон в одной LAN/VPN. " +
                    "Разреши TCP 24643 в частной сети. Aurora не настраивает сеть за тебя.";
            }
            final String answer=message;
            MAIN.post(()->{
                if(isFinishing()||isDestroyed())return;
                details.setText(answer);busy=false;connect.setEnabled(true);
            });
        },"AuroraRoomCheck").start();
    }
    private LinearLayout card(LinearLayout page){
        LinearLayout c=new LinearLayout(this);c.setOrientation(1);
        c.setPadding(dp(15),dp(15),dp(15),dp(15));
        GradientDrawable bg=new GradientDrawable();bg.setColor(panel);bg.setCornerRadius(dp(16));
        c.setBackground(bg);
        LinearLayout.LayoutParams lp=new LinearLayout.LayoutParams(-1,-2);lp.topMargin=dp(14);
        page.addView(c,lp);return c;
    }
    private TextView text(String value,int size,boolean bold){
        TextView t=new TextView(this);t.setText(value);t.setTextSize(size);
        t.setTextColor(fg);t.setPadding(0,dp(8),0,dp(7));
        if(bold)t.setTypeface(Typeface.DEFAULT,Typeface.BOLD);
        return t;
    }
    private Button button(LinearLayout c,String title,Runnable action){
        Button b=new Button(this);b.setText(title);b.setAllCaps(false);
        b.setOnClickListener(v->action.run());c.addView(b);return b;
    }
    private int color(String key,int fallback){
        return AuroraWorkshopTabsView.themeColor(this,key,fallback);
    }
    private int dp(int n){return Math.round(n*getResources().getDisplayMetrics().density);}
}

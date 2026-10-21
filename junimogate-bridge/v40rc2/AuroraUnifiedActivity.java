package org.junimogate.aurora;

import android.app.Activity;
import android.content.ClipData;
import android.content.ClipboardManager;
import android.content.Context;
import android.content.Intent;
import android.graphics.Typeface;
import android.graphics.drawable.GradientDrawable;
import android.os.Bundle;
import android.os.Handler;
import android.os.Looper;
import android.text.InputType;
import android.widget.Button;
import android.widget.EditText;
import android.widget.LinearLayout;
import android.widget.ScrollView;
import android.widget.TextView;

import org.json.JSONObject;
import java.io.BufferedReader;
import java.io.InputStreamReader;
import java.io.OutputStream;
import java.net.DatagramPacket;
import java.net.DatagramSocket;
import java.net.InetAddress;
import java.net.InetSocketAddress;
import java.net.Socket;
import java.nio.charset.StandardCharsets;
import java.security.SecureRandom;
import java.util.Locale;

/**
 * Aurora Unified 4.0: one *user-initiated* readiness run for launcher TCP
 * (24643), metadata compatibility, and diagnostic UDP (24645).
 * Does not touch Stardew's UDP 24642 or save files. Does not create VPN.
 * Never sends Android mod list to a PC; it only receives PC metadata.
 */
public final class AuroraUnifiedActivity extends Activity {
    private static final Handler MAIN=new Handler(Looper.getMainLooper());
    private int bg,panel,fg,muted;
    private EditText invitation;
    private TextView output;
    private Button run;
    private boolean checking=false;
    private String latest="Проверка пока не запускалась.";

    @Override public void onCreate(Bundle state){
        super.onCreate(state);
        if(state!=null) {
            String restored=state.getString("aurora-redacted-report","");
            if(!restored.isEmpty() && restored.length()<=40000)latest=restored;
        }
        setTitle("Aurora Unified · v4.0 RC2");
        bg=theme("junimo_surface",0xff111422);
        panel=theme("junimo_surface_container",0xff222b40);
        fg=theme("junimo_on_surface",0xffeceefa);
        muted=theme("junimo_on_surface_variant",0xffbfc5de);
        draw();
    }

    private void draw(){
        ScrollView scroll=new ScrollView(this);
        scroll.setFillViewport(true);scroll.setBackgroundColor(bg);
        LinearLayout page=new LinearLayout(this);
        page.setOrientation(1);page.setPadding(dp(18),dp(24),dp(18),dp(22));
        scroll.addView(page);
        page.addView(label("AURORA / UNIFIED 4.0",22,true));
        TextView desc=label(
          "Android ↔ Windows · одна проверка связи, профиля модов и сетевого маршрута",
          13,false);
        desc.setTextColor(muted);page.addView(desc);
        LinearLayout guide=card(page);
        guide.addView(label("1. Подготовь компьютер",17,true));
        guide.addView(label(
          "Aurora SMAPI PC v4.0: выбери Stardew Valley, создай комнату " +
          "и скопируй приглашение. Для разных сетей заранее подключи оба " +
          "устройства к доверенной VPN. Порты Aurora не публикуй в интернете.",
          13,false));
        LinearLayout conn=card(page);
        conn.addView(label("2. Приглашение Aurora PC",17,true));
        invitation=new EditText(this);
        invitation.setTextSize(13);invitation.setTextColor(fg);
        invitation.setHintTextColor(muted);
        invitation.setSingleLine(false);invitation.setMaxLines(3);
        invitation.setInputType(InputType.TYPE_CLASS_TEXT |
            InputType.TYPE_TEXT_FLAG_NO_SUGGESTIONS);
        invitation.setHint("AURORA2|IP|32-символьный-токен");
        conn.addView(invitation);
        button(conn,"Вставить код из буфера",this::paste);
        run=button(conn,"Проверить всё",this::check);
        LinearLayout result=card(page);
        result.addView(label("Результат проверки",17,true));
        output=label(latest,13,false);
        output.setTextIsSelectable(true);result.addView(output);
        button(result,"Поделиться текстовым отчётом",this::shareReport);
        LinearLayout next=card(page);
        next.addView(label("3. Запусти кооператив внутри игры",17,true));
        next.addView(label(
          "После проверки открой Stardew Valley на ПК → Co-op → Host. " +
          "На Android открой экспериментальный Co-op → Join и введи адрес ПК.\n\n" +
          "TCP 24643 проверяет только сведения Aurora. UDP 24645 проверяет " +
          "только диагностический ответ Aurora PC. Stardew Valley использует " +
          "игровой UDP 24642 — готовность игры этим мастером не доказывается.",
          13,false));
        button(next,"Открыть настройки сети / VPN",()->open(AuroraNetworkActivity.class));
        button(next,"Открыть Mod Manager Pro",()->open(AuroraModAuditActivity.class));
        button(next,"Открыть Recovery Preview",()->open(AuroraRecoveryPreviewActivity.class));
        setContentView(scroll);
    }

    @Override protected void onSaveInstanceState(Bundle saved){
        // Keep only an already-redacted report. Never save the room token.
        saved.putString("aurora-redacted-report",latest);
        super.onSaveInstanceState(saved);
    }

    private void paste(){
        ClipboardManager clipboard=(ClipboardManager)getSystemService(Context.CLIPBOARD_SERVICE);
        ClipData clip=clipboard==null?null:clipboard.getPrimaryClip();
        if(clip==null || clip.getItemCount()==0){
            output.setText("В буфере обмена нет приглашения.");return;
        }
        CharSequence candidate=clip.getItemAt(0).coerceToText(this);
        if(candidate!=null && candidate.length()<=120)
            invitation.setText(candidate);
        else output.setText("В буфере слишком длинный текст.");
    }

    private static String readBounded(BufferedReader input) throws Exception {
        StringBuilder sb=new StringBuilder();
        for(int i=0;i<32768;i++){
            int c=input.read();
            if(c=='\n')return sb.toString();
            if(c<0)break;
            if(c!='\r')sb.append((char)c);
        }
        throw new IllegalArgumentException("Некорректный или слишком большой ответ ПК");
    }

    private void check(){
        if(checking)return;
        final AuroraRoomActivity.Invite code;
        try{code=AuroraRoomActivity.parse(invitation.getText().toString());}
        catch(Exception invalid){output.setText("Неверный код комнаты Aurora.");return;}
        checking=true;run.setEnabled(false);
        output.setText("Проверяем TCP Aurora, моды и затем UDP Aurora…");
        new Thread(()->{
            StringBuilder result=new StringBuilder();
            result.append("AURORA 4.0 · ПАРНАЯ ДИАГНОСТИКА\n");
            result.append("ПК: ").append(code.ip).append("\n");
            result.append("Токен скрыт в отчёте.\n\n");
            boolean tcp=false;
            try(Socket socket=new Socket()){
                socket.connect(new InetSocketAddress(code.ip,24643),2500);
                socket.setSoTimeout(2800);
                OutputStream out=socket.getOutputStream();
                out.write(("AURORA_ROOM_V1 "+code.token+"\n")
                    .getBytes(StandardCharsets.US_ASCII));
                out.flush();
                BufferedReader reader=new BufferedReader(new InputStreamReader(
                    socket.getInputStream(),StandardCharsets.UTF_8));
                JSONObject metadata=new JSONObject(readBounded(reader));
                String comparison=AuroraCoopCompatibility.compare(this,metadata);
                tcp=true;
                result.append("✓ TCP 24643: комната обнаружена.\n");
                result.append(comparison).append("\n");
            }catch(Exception error){
                result.append("× TCP 24643: не удалось проверить комнату. " +
                    "Возможны неверный токен, закрытая комната, Firewall или VPN.\n");
            }
            if(tcp){
                boolean udpOk=false;
                try(DatagramSocket socket=new DatagramSocket()){
                    socket.setSoTimeout(2500);
                    byte[] random=new byte[8];
                    new SecureRandom().nextBytes(random);
                    StringBuilder nonce=new StringBuilder();
                    for(byte b:random)
                        nonce.append(String.format(Locale.ROOT,"%02x",b&255));
                    byte[] request=("AURORA_UDP_V1 "+code.token+" "+nonce)
                        .getBytes(StandardCharsets.US_ASCII);
                    InetAddress host=InetAddress.getByName(code.ip);
                    socket.send(new DatagramPacket(request,request.length,host,24645));
                    byte[] buf=new byte[128];
                    DatagramPacket reply=new DatagramPacket(buf,buf.length);
                    socket.receive(reply);
                    String answer=new String(reply.getData(),reply.getOffset(),
                        reply.getLength(),StandardCharsets.US_ASCII);
                    udpOk=reply.getAddress().getHostAddress().equals(code.ip) &&
                        answer.equals("AURORA_UDP_OK_V1 "+nonce);
                }catch(Exception networkError){
                    udpOk=false;
                }
                result.append(udpOk?
                    "\n✓ UDP 24645: диагностический ответ Aurora PC получен.\n":
                    "\n× UDP 24645: ответа нет. Проверь VPN/частный Firewall.\n");
            } else {
                result.append("– UDP 24645: не запускался после ошибки TCP.\n");
            }
            result.append("\n– Игровой UDP 24642: НЕ проверялся.\n");
            result.append("– Подключение к ферме: НЕ проверялось.\n");
            result.append("– Работа DLL на Android: НЕ гарантирована.\n");
            result.append("– Android восстановление/подпись APK: без изменений.\n");
            final String text=result.toString();
            MAIN.post(()->{
                if(isFinishing()||isDestroyed())return;
                latest=text;output.setText(latest);
                checking=false;run.setEnabled(true);
            });
        },"AuroraUnifiedPreflight").start();
    }

    private void shareReport(){
        Intent intent=new Intent(Intent.ACTION_SEND);
        intent.setType("text/plain");
        intent.putExtra(Intent.EXTRA_TEXT,latest);
        startActivity(Intent.createChooser(intent,"Aurora · Отчёт диагностики"));
    }
    private void open(Class<? extends Activity> activity){
        startActivity(new Intent(this,activity));
    }
    private LinearLayout card(LinearLayout page){
        LinearLayout item=new LinearLayout(this);
        item.setOrientation(1);item.setPadding(dp(15),dp(14),dp(15),dp(14));
        GradientDrawable bgShape=new GradientDrawable();
        bgShape.setColor(panel);bgShape.setCornerRadius(dp(15));
        item.setBackground(bgShape);
        LinearLayout.LayoutParams lp=new LinearLayout.LayoutParams(-1,-2);
        lp.topMargin=dp(13);page.addView(item,lp);return item;
    }
    private TextView label(String msg,int sp,boolean bold){
        TextView view=new TextView(this);view.setText(msg);view.setTextSize(sp);
        view.setTextColor(fg);view.setPadding(0,dp(7),0,dp(7));
        if(bold)view.setTypeface(Typeface.DEFAULT,Typeface.BOLD);
        return view;
    }
    private Button button(LinearLayout parent,String title,Runnable cb){
        Button result=new Button(this);result.setText(title);result.setAllCaps(false);
        result.setOnClickListener(v->cb.run());parent.addView(result);return result;
    }
    private int theme(String name,int fallback){
        return AuroraWorkshopTabsView.themeColor(this,name,fallback);
    }
    private int dp(int size){
        return Math.round(size*getResources().getDisplayMetrics().density);
    }
}

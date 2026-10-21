package org.junimogate.aurora;

import android.app.Activity;
import android.content.ClipData;
import android.content.ClipboardManager;
import android.content.Context;
import android.content.Intent;
import android.graphics.Typeface;
import android.graphics.drawable.GradientDrawable;
import android.os.Bundle;
import android.widget.Button;
import android.widget.EditText;
import android.widget.LinearLayout;
import android.widget.ScrollView;
import android.widget.TextView;

import org.json.JSONArray;
import java.util.ArrayList;

/**
 * Aurora Link 4.1: quick-access previously checked IPs and a transient
 * invite handoff to Aurora Unified. Never persists room tokens, identities,
 * passwords, saves, mods, or a false "trusted device" claim.
 */
public final class AuroraLinkActivity extends Activity {
    private int bg,panel,fg,muted;
    private EditText input;
    private LinearLayout recent;

    public static void rememberCheckedPeer(Context ctx, String ip){
        if(!AuroraRoomActivity.allowedIPv4(ip))return;
        try {
            android.content.SharedPreferences sp=ctx.getSharedPreferences(
                "aurora-link-v1",Context.MODE_PRIVATE);
            JSONArray prev=new JSONArray(sp.getString("checked-hosts","[]"));
            JSONArray next=new JSONArray();next.put(ip);
            for(int i=0;i<prev.length() && next.length()<5;i++){
                String addr=prev.optString(i,"");
                if(AuroraRoomActivity.allowedIPv4(addr)&&!addr.equals(ip))
                    next.put(addr);
            }
            sp.edit().putString("checked-hosts",next.toString()).apply();
        }catch(Exception ignored){}
    }

    @Override public void onCreate(Bundle state){
        super.onCreate(state);setTitle("Aurora Link 4.1");
        bg=theme("junimo_surface",0xff111422);
        panel=theme("junimo_surface_container",0xff222b40);
        fg=theme("junimo_on_surface",0xffeceefa);
        muted=theme("junimo_on_surface_variant",0xffbfc5de);
        draw();
    }
    private void draw(){
        ScrollView view=new ScrollView(this);view.setBackgroundColor(bg);
        LinearLayout page=new LinearLayout(this);page.setOrientation(1);
        page.setPadding(dp(18),dp(20),dp(18),dp(24));view.addView(page);
        page.addView(label("AURORA / LINK 4.1",22,true));
        TextView hint=label("Быстрое подключение по приглашению без сохранения секрета комнаты",13,false);
        hint.setTextColor(muted);page.addView(hint);
        LinearLayout panel=card(page);
        panel.addView(label("Приглашение Aurora PC",17,true));
        input=new EditText(this);input.setTextColor(fg);
        input.setSingleLine(false);input.setMaxLines(3);
        input.setHint("AURORA2|IP|32-символьный-токен");
        input.setHintTextColor(muted);panel.addView(input);
        button(panel,"Вставить из буфера",this::paste);
        button(panel,"Проверить соединение",this::connect);
        LinearLayout history=card(page);
        history.addView(label("Последние проверенные адреса",17,true));
        history.addView(label("Это история IP после успешной проверки Aurora; " +
            "это НЕ проверка личности владельца компьютера. Новый токен " +
            "нужен для каждой открытой комнаты.",12,false));
        recent=new LinearLayout(this);recent.setOrientation(1);history.addView(recent);
        button(history,"Очистить адреса",()->{
            getSharedPreferences("aurora-link-v1",MODE_PRIVATE).edit().clear().apply();
            draw();
        });
        refreshHistory();
        page.addView(label("Для удалённой игры нужна отдельная подключённая VPN. " +
            "Aurora Link не создаёт VPN и не проверяет игровую ферму.",12,false));
        setContentView(view);
    }
    private void refreshHistory(){
        recent.removeAllViews();
        try{
            JSONArray stored=new JSONArray(getSharedPreferences(
                "aurora-link-v1",MODE_PRIVATE).getString("checked-hosts","[]"));
            if(stored.length()==0){recent.addView(label("Адресов пока нет.",13,false));return;}
            for(int i=0;i<Math.min(5,stored.length());i++){
                final String address=stored.optString(i,"");
                if(!AuroraRoomActivity.allowedIPv4(address))continue;
                button(recent,"Компьютер: "+address+" · Требуется новое приглашение",()->{
                    input.setText("AURORA2|"+address+"|");
                    input.setSelection(input.getText().length());
                });
            }
        }catch(Exception ignored){recent.addView(label("История пока недоступна.",12,false));}
    }
    private void paste(){
        ClipboardManager cb=(ClipboardManager)getSystemService(Context.CLIPBOARD_SERVICE);
        ClipData data=cb==null?null:cb.getPrimaryClip();
        if(data==null||data.getItemCount()==0)return;
        CharSequence item=data.getItemAt(0).coerceToText(this);
        if(item!=null && item.length()<=120)input.setText(item);
    }
    private void connect(){
        String value=input.getText().toString().trim();
        try{AuroraRoomActivity.parse(value);}
        catch(Exception invalid){
            new android.app.AlertDialog.Builder(this).setMessage(
                "Нужно полное приглашение от владельца Aurora PC. " +
                "Последний IP без свежего токена недостаточен."
            ).setPositiveButton("OK",null).show();
            return;
        }
        Intent next=new Intent(this,AuroraUnifiedActivity.class);
        next.putExtra("aurora-invite-transient",value);
        startActivity(next);
        // Never save the invitation in SharedPreferences/Android files.
    }
    private LinearLayout card(LinearLayout page){
        LinearLayout box=new LinearLayout(this);box.setOrientation(1);
        box.setPadding(dp(16),dp(14),dp(16),dp(14));
        GradientDrawable shape=new GradientDrawable();shape.setColor(panel);
        shape.setCornerRadius(dp(15));box.setBackground(shape);
        LinearLayout.LayoutParams lp=new LinearLayout.LayoutParams(-1,-2);
        lp.topMargin=dp(14);page.addView(box,lp);return box;
    }
    private TextView label(String s,int size,boolean strong){
        TextView t=new TextView(this);t.setText(s);t.setTextSize(size);t.setTextColor(fg);
        t.setPadding(0,dp(7),0,dp(7));
        if(strong)t.setTypeface(Typeface.DEFAULT,Typeface.BOLD);return t;
    }
    private void button(LinearLayout c,String title,Runnable action){
        Button b=new Button(this);b.setText(title);b.setAllCaps(false);
        b.setOnClickListener(v->action.run());c.addView(b);
    }
    private int theme(String id,int backup){
        return AuroraWorkshopTabsView.themeColor(this,id,backup);
    }
    private int dp(int x){return Math.round(x*getResources().getDisplayMetrics().density);}
}

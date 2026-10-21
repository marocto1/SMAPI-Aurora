package org.junimogate.aurora;

import android.app.Activity;
import android.app.AlertDialog;
import android.content.Intent;
import android.net.ConnectivityManager;
import android.net.Network;
import android.net.NetworkCapabilities;
import android.net.LinkProperties;
import android.os.Build;
import android.os.Bundle;
import android.graphics.Typeface;
import android.graphics.drawable.GradientDrawable;
import android.widget.Button;
import android.widget.LinearLayout;
import android.widget.ScrollView;
import android.widget.TextView;
import java.net.Inet4Address;
import java.net.InetAddress;
import java.util.HashSet;

/**
 * v2.4.0 read-only network diagnostics. Detects Android VPN transport
 * without requesting VPN service or modifying connectivity. No
 * VPN installation, account tokens, network tunnels or third-party API.
 */
public final class AuroraNetworkActivity extends Activity {
    private int bg, panel,fg,muted;
    private TextView report;
    @Override public void onCreate(Bundle b){
        super.onCreate(b);setTitle("Aurora Network 2.0");
        bg=color("junimo_surface",0xff111422);
        panel=color("junimo_surface_container",0xff222b40);
        fg=color("junimo_on_surface",0xffeceefa);
        muted=color("junimo_on_surface_variant",0xffbfc5de);
        ScrollView scroller=new ScrollView(this);scroller.setBackgroundColor(bg);
        LinearLayout page=new LinearLayout(this);page.setOrientation(1);
        page.setPadding(dp(18),dp(25),dp(18),dp(25));
        scroller.addView(page);
        page.addView(label("AURORA / NETWORK 2.0",23,true));
        page.addView(label("Диагностика маршрутов Android и внешней VPN",14,false));
        LinearLayout box=card(page);
        report=label("Загрузка локального статуса…",13,false);
        report.setTextIsSelectable(true);box.addView(report);
        button(box,"Обновить диагностику",this::refresh);
        LinearLayout help=card(page);
        help.addView(label("Как играть через разные сети",17,true));
        help.addView(label("1. Подключи оба устройства к одной доверенной " +
            "виртуальной сети, например Tailscale, через отдельные приложения.\n" +
            "2. Открой Aurora PC → Комната и укажи IPv4 компьютера в VPN.\n" +
            "3. В Aurora Android открой Coop Rooms и введи приглашение.\n" +
            "4. В Stardew Valley на ПК выбери Co-op → Host, а на телефоне " +
            "Co-op → Join с тем же IP. Игра требует UDP 24642.\n\n" +
            "Aurora проверяет наличие VPN-маршрута, но НЕ создаёт и не " +
            "проверяет сам игровой туннель. VPN-приложение должно быть " +
            "установлено и подключено отдельно.",13,false));
        button(help,"Открыть сайт Tailscale",()->openUrl("https://tailscale.com/"));
        button(help,"Открыть Aurora Coop Rooms",()->
            startActivity(new Intent(this,AuroraRoomActivity.class)));
        setContentView(scroller);refresh();
    }
    private void refresh(){
        try{
            ConnectivityManager cm=(ConnectivityManager)getSystemService(CONNECTIVITY_SERVICE);
            if(cm==null){report.setText("Служба сети недоступна.");return;}
            boolean activeVpn=false;
            StringBuilder sb=new StringBuilder();
            Network[] networks=cm.getAllNetworks();
            int count=0;
            HashSet<String> shown=new HashSet<>();
            for(Network network:networks){
                NetworkCapabilities caps=cm.getNetworkCapabilities(network);
                if(caps==null)continue;
                boolean vpn=caps.hasTransport(NetworkCapabilities.TRANSPORT_VPN);
                activeVpn|=vpn;
                if(++count>16)break;
                sb.append(vpn?"VPN":"Сеть");
                if(caps.hasTransport(NetworkCapabilities.TRANSPORT_WIFI))sb.append(" · Wi-Fi");
                if(caps.hasTransport(NetworkCapabilities.TRANSPORT_CELLULAR))sb.append(" · мобильная");
                sb.append("\n");
                LinkProperties link=cm.getLinkProperties(network);
                if(link!=null){
                    for(android.net.LinkAddress address:link.getLinkAddresses()){
                        InetAddress ip=address.getAddress();
                        if(ip instanceof Inet4Address && shown.add(ip.getHostAddress())){
                            sb.append(" IPv4: ").append(ip.getHostAddress()).append("\n");
                        }
                    }
                }
            }
            report.setText((activeVpn?
                "VPN-транспорт обнаружен Android.":"VPN-транспорт не обнаружен.")+
                "\nЭто НЕ проверка связи с удалённым ПК и не подтверждение UDP 24642.\n\n"+
                (sb.length()>0?sb.toString():"Нет доступных сведений о сетях."));
        }catch(SecurityException denied){
            report.setText("Android ограничил доступ к сведениям сети. " +
                "Проверь VPN вручную в системных настройках.");
        }catch(Exception e){
            report.setText("Сетевые сведения временно недоступны.");
        }
    }
    private void openUrl(String url){
        try{Intent i=new Intent(Intent.ACTION_VIEW,android.net.Uri.parse(url));
            i.addCategory(Intent.CATEGORY_BROWSABLE);startActivity(i);}
        catch(Exception e){new AlertDialog.Builder(this)
           .setMessage("Открой "+url+" в браузере").setPositiveButton("OK",null).show();}
    }
    private LinearLayout card(LinearLayout page){
        LinearLayout c=new LinearLayout(this);c.setOrientation(1);
        c.setPadding(dp(15),dp(13),dp(15),dp(13));
        GradientDrawable d=new GradientDrawable();
        d.setColor(panel);d.setCornerRadius(dp(16));c.setBackground(d);
        LinearLayout.LayoutParams p=new LinearLayout.LayoutParams(-1,-2);
        p.topMargin=dp(15);page.addView(c,p);return c;
    }
    private TextView label(String content,int size,boolean strong){
        TextView t=new TextView(this);t.setText(content);
        t.setTextSize(size);t.setTextColor(fg);
        t.setPadding(0,dp(6),0,dp(7));
        if(strong)t.setTypeface(Typeface.DEFAULT,Typeface.BOLD);
        return t;
    }
    private void button(LinearLayout c,String name,Runnable r){
        Button b=new Button(this);b.setText(name);b.setAllCaps(false);
        b.setOnClickListener(v->r.run());c.addView(b);
    }
    private int color(String key,int fallback){
        return AuroraWorkshopTabsView.themeColor(this,key,fallback);
    }
    private int dp(int n){return Math.round(n*getResources().getDisplayMetrics().density);}
}

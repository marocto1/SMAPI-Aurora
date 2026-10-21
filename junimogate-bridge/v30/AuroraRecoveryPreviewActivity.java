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

/** v2.6 Android Recovery: SAFE audit entrypoint, NOT file restoration.
 * The existing v1.4 SAF verifier streams each file and checks SHA256.
 * Android live app-private/profile/Saves restore is deliberately disabled.
 */
public final class AuroraRecoveryPreviewActivity extends Activity {
    private int bg,card,fg,muted;
    @Override public void onCreate(Bundle state) {
        super.onCreate(state);
        setTitle("Aurora Recovery · Safe Preview");
        bg=color("junimo_surface",0xff111422);
        card=color("junimo_surface_container",0xff222b40);
        fg=color("junimo_on_surface",0xffeceefa);
        muted=color("junimo_on_surface_variant",0xffbfc5de);
        ScrollView scroll=new ScrollView(this);scroll.setBackgroundColor(bg);
        LinearLayout page=new LinearLayout(this);page.setOrientation(1);
        page.setPadding(dp(18),dp(24),dp(18),dp(22));scroll.addView(page);
        page.addView(label("AURORA / RECOVERY 2.6",22,true));
        LinearLayout section=panel(page);
        section.addView(label("Безопасное восстановление — только проверка",17,true));
        section.addView(label(
            "Здесь можно выбрать внешний ZIP и проверить содержимое резервной " +
            "копии Aurora по SHA-256 через штатный экран. " +
            "Программа НЕ записывает архив поверх действующих профилей, модов " +
            "или сохранений. Закрой Stardew Valley перед созданием резервной копии.",
            13,false));
        button(section,"Открыть экспорт и проверку ZIP",()->
            startActivity(new Intent(this,AuroraBackupActivity.class)));
        LinearLayout important=panel(page);
        important.addView(label("Почему нельзя включить восстановление автоматически",16,true));
        important.addView(label(
            "Android требует совместимого сертификата, чтобы установить новую " +
            "APK поверх старой. QA-релизы Aurora подписывались временными " +
            "ключами. Удаление работающей Aurora может уничтожить закрытые " +
            "данные приложения.\n\n" +
            "Перед разрешением восстановления нужны устройство для тестирования, " +
            "проверка всех путей Mods/Saves, транзакционный откат и подтверждённая " +
            "совместимость подписи. Это ещё не проверено. " +
            "Не удаляй работающую Aurora ради RC.",
            13,false));
        button(important,"Проверить сертификат установленной Aurora",()->
            startActivity(new Intent(this,AuroraSafetyActivity.class)));
        setContentView(scroll);
    }
    private LinearLayout panel(LinearLayout p){
        LinearLayout c=new LinearLayout(this);c.setOrientation(1);
        c.setPadding(dp(16),dp(15),dp(16),dp(15));
        GradientDrawable d=new GradientDrawable();
        d.setColor(card);d.setCornerRadius(dp(16));c.setBackground(d);
        LinearLayout.LayoutParams lp=new LinearLayout.LayoutParams(-1,-2);
        lp.topMargin=dp(15);p.addView(c,lp);return c;
    }
    private TextView label(String v,int size,boolean bold){
        TextView t=new TextView(this);t.setText(v);t.setTextSize(size);
        t.setTextColor(fg);t.setPadding(0,dp(8),0,dp(8));
        if(bold)t.setTypeface(Typeface.DEFAULT,Typeface.BOLD);return t;
    }
    private void button(LinearLayout parent,String title,Runnable run){
        Button b=new Button(this);b.setText(title);b.setAllCaps(false);
        b.setOnClickListener(v->run.run());parent.addView(b);
    }
    private int color(String key,int fallback){
        return AuroraWorkshopTabsView.themeColor(this,key,fallback);
    }
    private int dp(int n){return Math.round(n*getResources().getDisplayMetrics().density);}
}

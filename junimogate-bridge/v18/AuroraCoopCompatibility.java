package org.junimogate.aurora;

import android.content.Context;
import android.content.pm.PackageInfo;
import android.content.pm.PackageManager;

import org.json.JSONArray;
import org.json.JSONObject;

import java.io.ByteArrayOutputStream;
import java.io.File;
import java.io.FileInputStream;
import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.util.HashMap;
import java.util.HashSet;
import java.util.Locale;
import java.util.Map;

/**
 * Read-only cross-device comparison for Aurora Coop.
 * Reads the exact JunimoGate library/profile schemas used by ModOverview.
 * Never sends Android mod data over the network or edits live game state.
 */
public final class AuroraCoopCompatibility {
    private AuroraCoopCompatibility() {}

    static final class Snapshot {
        final Map<String,String> mods = new HashMap<>();
        boolean known;
        String detail = "профиль модов недоступен";
    }

    static JSONObject loadJson(File path, int max) throws Exception {
        if (!path.isFile() || path.length() < 2 || path.length() > max)
            throw new IOException("Missing or oversized mod metadata");
        try (FileInputStream in = new FileInputStream(path);
             ByteArrayOutputStream data = new ByteArrayOutputStream()) {
            byte[] chunk = new byte[8192];
            int n;
            while ((n = in.read(chunk)) >= 0) {
                if (data.size() + n > max)
                    throw new IOException("Mod metadata exceeds limit");
                data.write(chunk,0,n);
            }
            return new JSONObject(new String(data.toByteArray(),StandardCharsets.UTF_8));
        }
    }

    static Snapshot activeMods(Context context) {
        Snapshot snapshot = new Snapshot();
        try {
            File root = new File(context.getNoBackupFilesDir(),"junimogate/user-data");
            JSONObject index=loadJson(new File(root,"mods/library-index.json"),2*1024*1024);
            if (!"junimogate-mod-library/v1".equals(index.optString("schema")))
                throw new IOException("Unexpected mod library schema");
            JSONArray items=index.getJSONArray("items");
            if (items.length() > 1024) throw new IOException("Library too large");
            File profileDir=new File(root,"profiles");
            String activeId="default";
            File selected=new File(profileDir,"active-profile.json");
            if (selected.isFile()) {
                JSONObject choice=loadJson(selected,16384);
                if (!"junimogate-active-mod-profile/v1".equals(choice.optString("schema")))
                    throw new IOException("Unknown active profile format");
                activeId=choice.getString("activeProfileId");
            }
            if (!activeId.matches("[A-Za-z0-9_-]{1,80}"))
                throw new IOException("Invalid active profile");
            File profilePath=new File(new File(profileDir,activeId),"profile.json");
            if (!profilePath.isFile())
                throw new IOException("No saved active profile");
            JSONObject profile=loadJson(profilePath,1024*1024);
            if (!"junimogate-mod-profile/v2".equals(profile.optString("schema")))
                throw new IOException("Unknown mod profile format");
            JSONArray members=profile.getJSONArray("members");
            if (members.length()>1024)throw new IOException("Too many active profile members");
            HashMap<String,String> enabled=new HashMap<>();
            HashSet<String> ids = new HashSet<>();
            for(int i=0;i<members.length();i++) {
                JSONObject member=members.getJSONObject(i);
                if(member.optBoolean("enabled",false)) {
                    String id=member.getString("uniqueId").toLowerCase(Locale.ROOT);
                    enabled.put(id,member.optString("libraryItemId",""));
                }
            }
            for(int i=0;i<items.length();i++) {
                JSONObject item=items.getJSONObject(i);
                JSONObject manifest=item.getJSONObject("manifest");
                String id=manifest.getString("uniqueId");
                String key=id.toLowerCase(Locale.ROOT);
                if(enabled.containsKey(key) &&
                   item.optString("libraryItemId").equals(enabled.get(key))) {
                    if(!ids.add(key))throw new IOException("Duplicate active mod");
                    snapshot.mods.put(key,manifest.optString("version","?"));
                }
            }
            if(snapshot.mods.size()!=enabled.size())
                throw new IOException("Profile entries missing from library");
            snapshot.known=true;
            snapshot.detail="группа "+activeId+", включено "+snapshot.mods.size();
        } catch(Exception e) {
            snapshot.known=false;
            snapshot.mods.clear();
            snapshot.detail="невозможно прочитать текущую активную группу";
        }
        return snapshot;
    }

    static String androidGameVersion(Context context) {
        try {
            PackageInfo p=context.getPackageManager().getPackageInfo(
                "com.chucklefish.stardewvalley",0);
            if(p.versionName!=null && !p.versionName.isEmpty())return p.versionName;
        } catch(PackageManager.NameNotFoundException ignored) {}
        return "";
    }

    static String compare(Context context,JSONObject pc) throws Exception {
        if(!"aurora-coop-status/v2".equals(pc.optString("schema")) ||
           !"windows".equals(pc.optString("platform")) ||
           !"Aurora SMAPI PC".equals(pc.optString("launcher")))
            throw new IOException("Unexpected Aurora PC v1.8 response");
        StringBuilder out=new StringBuilder();
        out.append("Aurora PC: ").append(pc.optString("launcher_version","?"));
        out.append("\nПрофиль PC: ").append(pc.optString("profile","?"));
        out.append("\nВерсии PC указаны пользователем, а не проверены по работающей игре.");
        String mobile=androidGameVersion(context);
        String desktop=pc.optString("game_version","");
        if(mobile.isEmpty() || desktop.isEmpty()) {
            out.append("\nStardew Valley: сравнение версий невозможно (нет данных).");
        } else if(mobile.equals(desktop)) {
            out.append("\nStardew Valley: совпадают указанные номера (")
               .append(mobile).append(").");
        } else {
            out.append("\nВНИМАНИЕ Stardew Valley: Android ").append(mobile)
               .append(" / PC ").append(desktop).append(" (разные номера).");
        }
        // Android target version is a packaging baseline, not a runtime attestation.
        String androidSmapiBaseline="4.5.2";
        String pcSmapi=pc.optString("smapi_version","");
        if(pcSmapi.isEmpty()) {
            out.append("\nSMAPI: версия PC не указана. Сравнить невозможно.");
        } else if(pcSmapi.equals(androidSmapiBaseline) ||
                  pcSmapi.startsWith(androidSmapiBaseline+"-") ||
                  pcSmapi.startsWith(androidSmapiBaseline+"+")) {
            out.append("\nSMAPI: PC ").append(pcSmapi)
               .append(" соответствует заявленной базе Android 4.5.2. " +
                    "Версию загруженного SMAPI дополнительно проверь в журнале.");
        } else {
            out.append("\nВНИМАНИЕ SMAPI: PC ").append(pcSmapi)
               .append(" / целевая база Android 4.5.2.");
        }
        out.append("\nSMAPI на PC: ")
           .append(pc.optBoolean("smapi_installed",false)?"EXE найден":"не найден");
        JSONArray pcMods=pc.optJSONArray("mods");
        if(pcMods==null || pcMods.length()>180)
            throw new IOException("Bad PC mod manifest payload");
        HashMap<String,String> desktopMods=new HashMap<>();
        for(int i=0;i<pcMods.length();i++) {
            JSONObject row=pcMods.getJSONObject(i);
            String id=row.optString("id","");
            String version=row.optString("version","?");
            if(id.isEmpty()||id.length()>140||version.length()>80)
                throw new IOException("Invalid mod metadata");
            String key=id.toLowerCase(Locale.ROOT);
            if(desktopMods.put(key,version)!=null)
                throw new IOException("Duplicate PC mod identifier");
        }
        Snapshot phone=activeMods(context);
        out.append("\nAndroid: ").append(phone.detail);
        out.append("\nPC: ").append(desktopMods.size()).append(" модов по manifest.json");
        if(!phone.known) {
            out.append("\nСравнение модов недоступно: Aurora не может подтвердить " +
                       "активный профиль Android.");
            return out.toString();
        }
        int different=0,phoneOnly=0,pcOnly=0;
        StringBuilder issues=new StringBuilder();
        for(Map.Entry<String,String> entry:phone.mods.entrySet()) {
            String pv=desktopMods.get(entry.getKey());
            if(pv==null) {phoneOnly++;appendIssue(issues,entry.getKey()+" только Android");}
            else if(!pv.equals(entry.getValue())) {
                different++;appendIssue(issues,entry.getKey()+": Android "+
                    entry.getValue()+" / PC "+pv);
            }
        }
        for(String id:desktopMods.keySet()) {
            if(!phone.mods.containsKey(id)) {pcOnly++;appendIssue(issues,id+" только PC");}
        }
        out.append("\nСравнение модов: разные версии ").append(different)
           .append(", только Android ").append(phoneOnly)
           .append(", только PC ").append(pcOnly).append(".");
        if(issues.length()>0)out.append("\n").append(issues);
        else out.append("\nМанифесты совпадают по ID/версии. " +
            "Это НЕ доказывает, что DLL-моды работают на Android.");
        out.append("\nИтоговую совместимость проверяй в журнале SMAPI и внутри игры.");
        return out.toString();
    }

    private static void appendIssue(StringBuilder result,String issue) {
        if(result.length()<800)result.append("• ").append(issue).append("\n");
    }
}

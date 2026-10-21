package org.junimogate.aurora;

import android.content.Context;
import android.content.SharedPreferences;
import android.security.keystore.KeyGenParameterSpec;
import android.security.keystore.KeyProperties;
import android.util.Base64;
import java.net.URL;
import java.nio.charset.StandardCharsets;
import java.security.KeyStore;
import javax.crypto.Cipher;
import javax.crypto.KeyGenerator;
import javax.crypto.SecretKey;
import javax.crypto.spec.GCMParameterSpec;
import org.json.JSONObject;

/** Owner session is local and encrypted; R2 keys never enter this application. */
public final class AuroraOwnerSession {
    private static final String ALIAS="aurora-versions-session-v1";
    private static final String PREF="aurora-versions-owner-session";
    private AuroraOwnerSession(){}
    static String validateServer(String s) throws Exception {
        URL url=new URL(s);
        String host=url.getHost().toLowerCase(java.util.Locale.ROOT);
        if(!"https".equals(url.getProtocol())||url.getPort()!=-1||
            url.getUserInfo()!=null||url.getQuery()!=null||url.getRef()!=null||
            !"/".equals(url.getPath()) && !url.getPath().isEmpty()||
            !host.endsWith(".up.railway.app") && !host.endsWith(".workers.dev") && !host.endsWith(".onrender.com"))
            throw new IllegalArgumentException("Only secure Aurora backend HTTPS endpoints");
        return url.getProtocol()+"://"+host;
    }
    private static SecretKey key(boolean create) throws Exception {
        KeyStore store=KeyStore.getInstance("AndroidKeyStore");
        store.load(null);
        if(store.containsAlias(ALIAS))return ((KeyStore.SecretKeyEntry)
            store.getEntry(ALIAS,null)).getSecretKey();
        if(!create)throw new IllegalStateException("Owner session needs pairing");
        KeyGenerator generator=KeyGenerator.getInstance("AES","AndroidKeyStore");
        generator.init(new KeyGenParameterSpec.Builder(ALIAS,
          KeyProperties.PURPOSE_ENCRYPT|KeyProperties.PURPOSE_DECRYPT)
          .setBlockModes(KeyProperties.BLOCK_MODE_GCM)
          .setEncryptionPaddings(KeyProperties.ENCRYPTION_PADDING_NONE)
          .setKeySize(256).build());
        return generator.generateKey();
    }
    public static void save(Context ctx,String server,String token) throws Exception {
        server=validateServer(server);
        if(token==null||token.length()>1024||token.length()<20)
            throw new IllegalArgumentException("Invalid paired session");
        JSONObject object=new JSONObject();
        object.put("server",server);object.put("session",token);
        Cipher cipher=Cipher.getInstance("AES/GCM/NoPadding");
        cipher.init(Cipher.ENCRYPT_MODE,key(true));
        String data=Base64.encodeToString(cipher.getIV(),Base64.NO_WRAP)+":"+
          Base64.encodeToString(cipher.doFinal(object.toString().getBytes(StandardCharsets.UTF_8)),
              Base64.NO_WRAP);
        if(!ctx.getSharedPreferences(PREF,Context.MODE_PRIVATE).edit()
            .putString("encrypted",data).commit())
            throw new IllegalStateException("Failed to save Aurora session");
    }
    public static String[] load(Context ctx) throws Exception {
        String data=ctx.getSharedPreferences(PREF,Context.MODE_PRIVATE)
            .getString("encrypted","");
        if(data.isEmpty())return null;
        String[] pieces=data.split(":",-1);
        if(pieces.length!=2)throw new IllegalStateException("Invalid owner session");
        byte[] iv=Base64.decode(pieces[0],Base64.NO_WRAP);
        if(iv.length!=12)throw new IllegalStateException("Invalid owner session IV");
        Cipher cipher=Cipher.getInstance("AES/GCM/NoPadding");
        cipher.init(Cipher.DECRYPT_MODE,key(false),new GCMParameterSpec(128,iv));
        JSONObject parsed=new JSONObject(new String(cipher.doFinal(
          Base64.decode(pieces[1],Base64.NO_WRAP)),StandardCharsets.UTF_8));
        String server=validateServer(parsed.getString("server"));
        String token=parsed.getString("session");
        if(token.length()<20||token.length()>1024)
            throw new IllegalStateException("Invalid owner session token");
        return new String[]{server,token};
    }
    public static void clear(Context ctx) {
        ctx.getSharedPreferences(PREF,Context.MODE_PRIVATE).edit().clear().commit();
    }
}

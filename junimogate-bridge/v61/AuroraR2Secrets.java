package org.junimogate.aurora;

import android.content.Context;
import android.content.SharedPreferences;
import android.security.keystore.KeyGenParameterSpec;
import android.security.keystore.KeyProperties;
import android.util.Base64;

import java.security.KeyStore;
import java.security.SecureRandom;
import javax.crypto.Cipher;
import javax.crypto.KeyGenerator;
import javax.crypto.SecretKey;
import javax.crypto.spec.GCMParameterSpec;
import org.json.JSONObject;

/** Per-install Android Keystore encryption for personal read-only R2 credentials.
 * Never ship a credential in app source, APK resources or remote telemetry.
 */
public final class AuroraR2Secrets {
    private static final String ALIAS="aurora-private-r2-aes-v1";
    private static final String PREF="aurora-private-r2-v1";
    private AuroraR2Secrets() {}

    private static SecretKey key(boolean create) throws Exception {
        KeyStore store=KeyStore.getInstance("AndroidKeyStore");
        store.load(null);
        if(store.containsAlias(ALIAS))return ((KeyStore.SecretKeyEntry)
            store.getEntry(ALIAS,null)).getSecretKey();
        if(!create)throw new IllegalStateException("Private R2 key unavailable; reconnect");
        KeyGenerator generator=KeyGenerator.getInstance("AES","AndroidKeyStore");
        generator.init(new KeyGenParameterSpec.Builder(ALIAS,
            KeyProperties.PURPOSE_ENCRYPT|KeyProperties.PURPOSE_DECRYPT)
            .setBlockModes(KeyProperties.BLOCK_MODE_GCM)
            .setEncryptionPaddings(KeyProperties.ENCRYPTION_PADDING_NONE)
            .setKeySize(256).build());
        return generator.generateKey();
    }
    public static void save(Context context,String account,String bucket,
                            String access,String secret) throws Exception {
        if(!account.matches("[a-fA-F0-9]{32}") ||
           !bucket.matches("[a-z0-9][a-z0-9.-]{1,61}[a-z0-9]") ||
           !access.matches("[A-Za-z0-9]{8,128}") ||
           secret.length()<16||secret.length()>256)
            throw new IllegalArgumentException("Invalid R2 connection parameters");
        JSONObject payload=new JSONObject();
        payload.put("access",access);payload.put("secret",secret);
        Cipher cipher=Cipher.getInstance("AES/GCM/NoPadding");
        cipher.init(Cipher.ENCRYPT_MODE,key(true));
        byte[] encrypted=cipher.doFinal(payload.toString().getBytes("UTF-8"));
        String value=Base64.encodeToString(cipher.getIV(),Base64.NO_WRAP)+":"+
            Base64.encodeToString(encrypted,Base64.NO_WRAP);
        SharedPreferences pref=context.getSharedPreferences(PREF,Context.MODE_PRIVATE);
        if(!pref.edit().putString("account",account.toLowerCase())
              .putString("bucket",bucket).putString("encrypted",value).commit())
            throw new IllegalStateException("Could not save private R2 connection");
    }
    public static String[] load(Context context) throws Exception {
        SharedPreferences pref=context.getSharedPreferences(PREF,Context.MODE_PRIVATE);
        String encrypted=pref.getString("encrypted","");
        String account=pref.getString("account","");
        String bucket=pref.getString("bucket","");
        if(encrypted.isEmpty())return null;
        String[] pieces=encrypted.split(":",-1);
        if(pieces.length!=2||!account.matches("[a-f0-9]{32}") ||
             !bucket.matches("[a-z0-9][a-z0-9.-]{1,61}[a-z0-9]"))
            throw new IllegalStateException("Damaged private R2 settings");
        byte[] iv=Base64.decode(pieces[0],Base64.DEFAULT);
        if(iv.length!=12)throw new IllegalStateException("Invalid R2 encryption IV");
        Cipher cipher=Cipher.getInstance("AES/GCM/NoPadding");
        cipher.init(Cipher.DECRYPT_MODE,key(false),new GCMParameterSpec(128,iv));
        byte[] plain=cipher.doFinal(Base64.decode(pieces[1],Base64.DEFAULT));
        JSONObject data=new JSONObject(new String(plain,"UTF-8"));
        return new String[]{account,bucket,data.getString("access"),data.getString("secret")};
    }
    public static void clear(Context context) {
        context.getSharedPreferences(PREF,Context.MODE_PRIVATE).edit().clear().commit();
        // Keep system-owned key; disconnect destroys ciphertext and credentials.
    }
}

package org.junimogate.aurora;

import java.net.URL;
import java.nio.charset.StandardCharsets;
import java.security.MessageDigest;
import java.time.Instant;
import java.time.ZoneOffset;
import java.time.format.DateTimeFormatter;
import java.util.Locale;
import java.util.LinkedHashMap;
import java.util.Map;
import javax.crypto.Mac;
import javax.crypto.spec.SecretKeySpec;

/**
 * S3 Signature V4 for a READ-ONLY private Cloudflare R2 account.
 * Pure Java: regression-tested without the Android runtime.
 * Never store or log keys in this class.
 */
public final class AuroraR2Signer {
    private static final DateTimeFormatter STAMP =
        DateTimeFormatter.ofPattern("yyyyMMdd'T'HHmmss'Z'", Locale.ROOT)
            .withZone(ZoneOffset.UTC);
    private AuroraR2Signer() {}

    private static byte[] digest(byte[] bytes) throws Exception {
        return MessageDigest.getInstance("SHA-256").digest(bytes);
    }
    private static String hex(byte[] bytes) {
        StringBuilder out=new StringBuilder(bytes.length*2);
        for(byte value:bytes)out.append(String.format(Locale.ROOT,"%02x",value&255));
        return out.toString();
    }
    private static byte[] hmac(byte[] key,String text) throws Exception {
        Mac mac=Mac.getInstance("HmacSHA256");
        mac.init(new SecretKeySpec(key,"HmacSHA256"));
        return mac.doFinal(text.getBytes(StandardCharsets.UTF_8));
    }
    /** RFC 3986 escaping, including slash in object keys to avoid path ambiguity. */
    public static String escape(String value) {
        StringBuilder out=new StringBuilder();
        byte[] bytes=value.getBytes(StandardCharsets.UTF_8);
        for(byte b:bytes) {
            int n=b&255;
            if((n>=65&&n<=90)||(n>=97&&n<=122)||(n>=48&&n<=57)||
                    n==45||n==46||n==95||n==126) out.append((char)n);
            else out.append('%').append(String.format(Locale.ROOT,"%02X",n));
        }
        return out.toString();
    }
    public static Map<String,String> headers(URL url,String access,String secret,Instant when)
            throws Exception {
        if(!"https".equals(url.getProtocol())||
                !url.getHost().matches("[a-fA-F0-9]{32}\\.r2\\.cloudflarestorage\\.com")||
                url.getPort()!=-1)throw new IllegalArgumentException("Only account-specific HTTPS R2 endpoints");
        if(access==null||!access.matches("[A-Za-z0-9]{8,128}")||
                secret==null||secret.length()<16||secret.length()>256)
            throw new IllegalArgumentException("Invalid R2 credentials");
        String stamp=STAMP.format(when);
        String date=stamp.substring(0,8);
        String scope=date+"/auto/s3/aws4_request";
        String path=url.getPath();
        // URL#getPath is already percent-encoded in Java URL; use raw path verbatim.
        if(path==null||path.isEmpty())path="/";
        String query=url.getQuery()==null?"":url.getQuery();
        String payloadHash=hex(digest(new byte[0]));
        String canonicalHeaders="host:"+url.getHost().toLowerCase(Locale.ROOT)+"\n"+
            "x-amz-content-sha256:"+payloadHash+"\n"+
            "x-amz-date:"+stamp+"\n";
        String signedHeaders="host;x-amz-content-sha256;x-amz-date";
        String request="GET\n"+path+"\n"+query+"\n"+canonicalHeaders+
            "\n"+signedHeaders+"\n"+payloadHash;
        String stringToSign="AWS4-HMAC-SHA256\n"+stamp+"\n"+scope+"\n"+
            hex(digest(request.getBytes(StandardCharsets.UTF_8)));
        byte[] key=("AWS4"+secret).getBytes(StandardCharsets.UTF_8);
        key=hmac(key,date);
        key=hmac(key,"auto");
        key=hmac(key,"s3");
        key=hmac(key,"aws4_request");
        String signature=hex(hmac(key,stringToSign));
        Map<String,String> result=new LinkedHashMap<>();
        result.put("x-amz-date",stamp);
        result.put("x-amz-content-sha256",payloadHash);
        result.put("Authorization","AWS4-HMAC-SHA256 Credential="+access+"/"+scope+
            ", SignedHeaders="+signedHeaders+", Signature="+signature);
        return result;
    }
}

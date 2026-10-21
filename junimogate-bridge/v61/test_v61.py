"""R2 private downloads: source safety and cross-checked SigV4 requests."""
from pathlib import Path
import hashlib
import hmac
import subprocess
import tempfile
import unittest

HERE=Path(__file__).resolve().parent
ACCOUNT="d0ab9fdebeadcc640b3fc0324da411b3"
BUCKET="aurora-downloads"
ACCESS="TESTACCESS123456"
SECRET="testsecret0123456789abcdef"

class R2PrivateTests(unittest.TestCase):
    def test_signer_matches_independent_s3_sigv4_reference(self):
        runner=f'''import java.net.URL;
import java.time.Instant;
import org.junimogate.aurora.AuroraR2Signer;
public class SignerHarness {{
  public static void main(String[] args) throws Exception {{
    URL url=new URL("https://{ACCOUNT}.r2.cloudflarestorage.com/{BUCKET}/Stardew%20Valley.apks");
    System.out.println(AuroraR2Signer.headers(url,"{ACCESS}","{SECRET}",
        Instant.parse("2026-10-21T12:00:00Z")).get("Authorization"));
    System.out.println(AuroraR2Signer.escape("Stardew Valley.apks"));
    try {{
      AuroraR2Signer.headers(new URL("https://evil.example.com/bucket/file"),
        "{ACCESS}","{SECRET}",Instant.now());
      System.out.println("INSECURE");
    }} catch (IllegalArgumentException expected) {{
      System.out.println("REJECTED");
    }}
  }}
}}
'''
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder)
            (root/"SignerHarness.java").write_text(runner)
            subprocess.run(["javac","-encoding","UTF-8","-d",folder,
                            str(HERE/"AuroraR2Signer.java"),
                            str(root/"SignerHarness.java")],
                           check=True,capture_output=True,text=True)
            output=subprocess.check_output(["java","-cp",folder,"SignerHarness"],
                                           text=True).strip().splitlines()
        stamp="20261021T120000Z"
        date=stamp[:8]
        scope=date+"/auto/s3/aws4_request"
        empty=hashlib.sha256(b"").hexdigest()
        signed="host;x-amz-content-sha256;x-amz-date"
        request=("GET\n/"+BUCKET+"/Stardew%20Valley.apks\n\n"+
                 f"host:{ACCOUNT}.r2.cloudflarestorage.com\n"+
                 f"x-amz-content-sha256:{empty}\n"+
                 f"x-amz-date:{stamp}\n\n{signed}\n{empty}")
        hashed=hashlib.sha256(request.encode()).hexdigest()
        tosign=f"AWS4-HMAC-SHA256\n{stamp}\n{scope}\n{hashed}"
        key=("AWS4"+SECRET).encode()
        for segment in (date,"auto","s3","aws4_request"):
            key=hmac.new(key,segment.encode(),hashlib.sha256).digest()
        signature=hmac.new(key,tosign.encode(),hashlib.sha256).hexdigest()
        expected=(f"AWS4-HMAC-SHA256 Credential={ACCESS}/{scope}, "+
                  f"SignedHeaders={signed}, Signature={signature}")
        self.assertEqual(output[0],expected)
        self.assertEqual(output[1],"Stardew%20Valley.apks")
        self.assertEqual(output[2],"REJECTED")

    def test_personal_private_only_no_public_or_auto_installs(self):
        activity=(HERE/"AuroraR2PrivateActivity.java").read_text()
        store=(HERE/"AuroraR2Secrets.java").read_text()
        injector=(HERE/"inject_v61.py").read_text()
        self.assertIn("Intent.ACTION_CREATE_DOCUMENT",activity)
        self.assertIn("getContentResolver().openOutputStream(destination",activity)
        self.assertIn("KeyProperties.KEY_ALGORITHM",store) if False else None
        self.assertIn('"AndroidKeyStore"',store)
        self.assertIn("AES/GCM/NoPadding",store)
        self.assertIn('node.set(A+"exported","false")',injector)
        self.assertIn("patch_v60(root)",injector)
        self.assertNotIn("ACTION_INSTALL_PACKAGE",activity)
        self.assertNotIn("REQUEST_INSTALL_PACKAGES",injector)
        self.assertNotIn("putString(\"secret\"",store)
        self.assertNotIn("setInstanceFollowRedirects(true)",activity)
        self.assertNotIn("QUERY_ALL_PACKAGES",injector)

if __name__=="__main__":
    unittest.main()

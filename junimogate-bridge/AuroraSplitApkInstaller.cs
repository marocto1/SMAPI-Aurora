// Source-only Aurora game version installer. No commercial game files are bundled.
// Compilation and on-device PackageInstaller behavior must both be validated.
using System.IO.Compression;
using System.Security.Cryptography;
using Android.App;
using Android.Content;
using Android.Content.PM;
using Android.Net;

namespace JunimoGate.App;

internal static class AuroraSplitApkInstaller
{
    public const string CallbackAction = "org.junimogate.app.AURORA_SPLIT_INSTALL_RESULT";
    private const string GamePackage = "com.chucklefish.stardewvalley";
    private const long MaxCompressedBytes = 330_000_000;
    private static readonly (string Name, long Size, string Sha256)[] KnownBuild245 =
    [
        ("base.apk", 4858693,
            "763c2dc5681ec8f079d0b8be590b77d12c76027769ccef957f3ae4357c120837"),
        ("split_config.arm64_v8a.apk", 53857797,
            "efa488b4ba5d5bead3924276a565eb992f022e11e03c7688b6921a484612eeb3"),
        ("split_content.apk", 361158047,
            "a90797b428249e040ecfc724168ba1310858855990136b5f813da6d456872d25"),
    ];

    public static async Task StageKnownBuild245Async(
        Activity activity,
        global::Android.Net.Uri document,
        CancellationToken cancellationToken)
    {
        ArgumentNullException.ThrowIfNull(activity);
        ArgumentNullException.ThrowIfNull(document);

        var installer = activity.PackageManager?.PackageInstaller
            ?? throw new InvalidOperationException("Android PackageInstaller is not available.");
        var cache = activity.CacheDir?.AbsolutePath
            ?? throw new IOException("Android private cache is unavailable.");
        var temporary = Path.Combine(cache, "aurora-game-" + Guid.NewGuid().ToString("N") + ".apks");
        var sessionId = -1;
        var committed = false;
        try
        {
            // ContentResolver streams supplied by cloud drives can be non-seekable.
            // Use app-private temporary storage, never external game/save folders.
            await using (var destination = new FileStream(
                temporary, FileMode.CreateNew, FileAccess.Write, FileShare.None,
                128 * 1024, useAsync: true))
            await using (var source = activity.ContentResolver?.OpenInputStream(document)
                ?? throw new IOException("Selected document cannot be opened."))
            {
                var buffer = new byte[128 * 1024];
                long length = 0;
                int read;
                while ((read = await source.ReadAsync(buffer, cancellationToken)
                    .ConfigureAwait(false)) != 0)
                {
                    length += read;
                    if (length > MaxCompressedBytes)
                        throw new InvalidDataException("Selected .apks archive is too large.");
                    await destination.WriteAsync(buffer.AsMemory(0, read), cancellationToken)
                        .ConfigureAwait(false);
                }
                if (length < 200_000_000)
                    throw new InvalidDataException("Selected .apks archive is incomplete.");
            }

            using var archive = ZipFile.OpenRead(temporary);
            if (archive.Entries.Count != KnownBuild245.Length)
                throw new InvalidDataException("Expected exactly three Android split packages.");
            var expected = KnownBuild245.ToDictionary(item => item.Name, StringComparer.Ordinal);
            var seen = new HashSet<string>(StringComparer.Ordinal);
            foreach (var entry in archive.Entries)
            {
                if (!expected.TryGetValue(entry.FullName, out var item) ||
                    !seen.Add(entry.FullName) || entry.Length != item.Size ||
                    entry.CompressedLength <= 0)
                    throw new InvalidDataException("Split APK archive contents do not match build 245.");
            }
            if (seen.Count != KnownBuild245.Length)
                throw new InvalidDataException("Split APK archive is missing required files.");

            using var parameters = new PackageInstaller.SessionParams(PackageInstallMode.FullInstall);
            parameters.SetAppPackageName(GamePackage);
            parameters.SetSize(KnownBuild245.Sum(item => item.Size));
            if (OperatingSystem.IsAndroidVersionAtLeast(31))
                parameters.SetRequireUserAction(1);
            sessionId = installer.CreateSession(parameters);
            using var session = installer.OpenSession(sessionId);

            foreach (var item in KnownBuild245)
            {
                cancellationToken.ThrowIfCancellationRequested();
                var entry = archive.GetEntry(item.Name)
                    ?? throw new InvalidDataException("Missing split APK: " + item.Name);
                using var input = entry.Open();
                using var output = session.OpenWrite(item.Name, 0, item.Size);
                using var hash = IncrementalHash.CreateHash(HashAlgorithmName.SHA256);
                var buffer = new byte[128 * 1024];
                long written = 0;
                int read;
                while ((read = await input.ReadAsync(buffer.AsMemory(), cancellationToken)
                    .ConfigureAwait(false)) > 0)
                {
                    written += read;
                    if (written > item.Size)
                        throw new InvalidDataException("Split APK decompression size mismatch.");
                    hash.AppendData(buffer, 0, read);
                    await output.WriteAsync(buffer.AsMemory(0, read), cancellationToken)
                        .ConfigureAwait(false);
                }
                if (written != item.Size ||
                    !hash.GetHashAndReset().AsSpan().SequenceEqual(Convert.FromHexString(item.Sha256)))
                    throw new InvalidDataException("Split APK SHA256 mismatch: " + item.Name);
                await output.FlushAsync(cancellationToken).ConfigureAwait(false);
                session.Fsync(output);
            }

            var callback = new Intent(activity, activity.GetType());
            callback.SetAction(CallbackAction);
            callback.AddFlags(ActivityFlags.NewTask | ActivityFlags.SingleTop | ActivityFlags.ClearTop);
            var pending = PendingIntent.GetActivity(
                activity, sessionId, callback,
                PendingIntentFlags.UpdateCurrent | PendingIntentFlags.Mutable)
                ?? throw new InvalidOperationException("Android installer callback cannot be created.");
            using (pending)
            {
                session.Commit(pending.IntentSender);
                committed = true;
            }
        }
        finally
        {
            if (!committed && sessionId >= 0)
            {
                try { installer.AbandonSession(sessionId); }
                catch (Java.Lang.SecurityException) { }
                catch (Java.Lang.IllegalStateException) { }
            }
            try { File.Delete(temporary); } catch (IOException) { }
        }
    }

    public static bool HandleCallback(Activity activity, Intent? intent)
    {
        if (intent?.Action != CallbackAction)
            return false;

        var status = (PackageInstallStatus)intent.GetIntExtra(
            PackageInstaller.ExtraStatus, (int)PackageInstallStatus.Failure);
        if (status == PackageInstallStatus.PendingUserAction)
        {
#pragma warning disable CS0618
            var approval = intent.GetParcelableExtra(Intent.ExtraIntent) as Intent;
#pragma warning restore CS0618
            if (approval is not null)
                activity.StartActivity(approval);
        }
        else
        {
            var message = status == PackageInstallStatus.Success
                ? "Stardew Valley installed by Android"
                : "Android rejected game installation: " +
                    (intent.GetStringExtra(PackageInstaller.ExtraStatusMessage) ?? status.ToString());
            ToastOnUiThread(activity, message);
        }
        return true;
    }

    private static void ToastOnUiThread(Activity activity, string message) =>
        activity.RunOnUiThread(() =>
            Android.Widget.Toast.MakeText(activity, message, Android.Widget.ToastLength.Long)?.Show());
}

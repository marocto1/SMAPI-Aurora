using Android.Content;
using Android.Graphics;
using Android.Views;
using Android.Widget;
using System;
using System.Threading.Tasks;
using AndroidX.CardView.Widget;

namespace SMAPIGameLoader.Launcher;

public sealed class GameInfoCard : CardView
{
    private readonly TextView _status;
    private readonly TextView _detail;
    private readonly TextView _package;

    public GameInfoCard(Context context) : base(context)
    {
        Radius = AuroraUi.Dp(context, 18);
        CardElevation = AuroraUi.Dp(context, 2);
        SetCardBackgroundColor(AuroraUi.Surface);
        UseCompatPadding = false;

        var body = new LinearLayout(context) { Orientation = Orientation.Vertical };
        body.SetPadding(AuroraUi.Dp(context, 19), AuroraUi.Dp(context, 18),
            AuroraUi.Dp(context, 19), AuroraUi.Dp(context, 18));
        AddView(body);

        var top = new LinearLayout(context) { Orientation = Orientation.Horizontal };
        top.SetGravity(GravityFlags.CenterVertical);
        body.AddView(top, AuroraUi.ItemParams(context, 11));

        var title = AuroraUi.Text(context, "Game source", 17, AuroraUi.White, true);
        top.AddView(title, new LinearLayout.LayoutParams(0, ViewGroup.LayoutParams.WrapContent, 1f));

        _status = AuroraUi.Pill(context, "●  CHECKING", AuroraUi.AccentSoft);
        top.AddView(_status);

        _detail = AuroraUi.Text(context, "Checking installed APKs…", 14, AuroraUi.Muted);
        body.AddView(_detail, AuroraUi.ItemParams(context, 6));
        _package = AuroraUi.Text(context, "Please wait", 12, AuroraUi.Muted);
        body.AddView(_package);
    }

    // APK ZIP inspection is disk I/O; never run it while rendering the UI.
    public void CheckAsync(Action<bool> completed)
    {
        Task.Run(() =>
        {
            bool ready = false;
            string detail;
            string package;
            try
            {
                ready = StardewApkTool.IsGameVersionSupport;
                detail = ready
                    ? "Stardew Valley  ·  " + StardewApkTool.CurrentGameVersion
                    : "No compatible Android game detected";
                package = StardewApkTool.CurrentPackageInfo?.PackageName
                    ?? "Choose an installed game below";
            }
            catch (Exception ex)
            {
                detail = "Unable to inspect installed game";
                package = ex.Message;
            }

            LauncherActivity.Instance.RunOnUiThread(() =>
            {
                _status.Text = ready ? "●  READY" : "●  NOT READY";
                _status.SetTextColor(ready ? AuroraUi.Mint : AuroraUi.Warn);
                _detail.Text = detail;
                _package.Text = package;
                completed(ready);
            });
        });
    }
}
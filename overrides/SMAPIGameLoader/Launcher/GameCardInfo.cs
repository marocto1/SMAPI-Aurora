using Android.Content;
using Android.Graphics;
using Android.Views;
using Android.Widget;
using AndroidX.CardView.Widget;

namespace SMAPIGameLoader.Launcher;

public sealed class GameInfoCard : CardView
{
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

        var isReady = StardewApkTool.IsInstalled && StardewApkTool.IsGameVersionSupport;
        var status = AuroraUi.Text(context, isReady ? "●  READY" : "●  NOT READY", 11,
            isReady ? AuroraUi.Mint : Color.Rgb(255, 173, 143), true);
        status.SetPadding(AuroraUi.Dp(context, 10), AuroraUi.Dp(context, 6),
            AuroraUi.Dp(context, 10), AuroraUi.Dp(context, 6));
        status.Background = AuroraUi.Solid(context, AuroraUi.SurfaceRaised, 13);
        top.AddView(status);

        var info = StardewApkTool.CurrentPackageInfo;
        var version = StardewApkTool.CurrentGameVersion;
        body.AddView(AuroraUi.Text(context,
            isReady ? "Stardew Valley  ·  " + version : "No compatible installed game detected",
            14, AuroraUi.Muted), AuroraUi.ItemParams(context, 6));
        body.AddView(AuroraUi.Text(context,
            info?.PackageName ?? "Choose an installed game below", 12, AuroraUi.Muted));
    }
}

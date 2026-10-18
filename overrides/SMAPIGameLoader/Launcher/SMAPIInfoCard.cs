using Android.Content;
using Android.Graphics;
using Android.Views;
using Android.Widget;
using AndroidX.CardView.Widget;
using System;

namespace SMAPIGameLoader.Launcher;

public sealed class SMAPIInfoCard : CardView
{
    public event Action? StatusChanged;
    private readonly TextView _status;
    private readonly TextView _version;
    private readonly TextView _build;
    private readonly Button _install;
    private readonly Button _remove;

    public SMAPIInfoCard(Context context) : base(context)
    {
        Radius = AuroraUi.Dp(context, 18);
        CardElevation = AuroraUi.Dp(context, 2);
        SetCardBackgroundColor(AuroraUi.Surface);
        UseCompatPadding = false;

        var body = new LinearLayout(context) { Orientation = Orientation.Vertical };
        body.SetPadding(AuroraUi.Dp(context, 19), AuroraUi.Dp(context, 18),
            AuroraUi.Dp(context, 19), AuroraUi.Dp(context, 18));
        AddView(body);

        var header = new LinearLayout(context) { Orientation = Orientation.Horizontal };
        header.SetGravity(GravityFlags.CenterVertical);
        body.AddView(header, AuroraUi.ItemParams(context, 12));

        var name = AuroraUi.Text(context, "SMAPI Runtime", 17, AuroraUi.White, true);
        header.AddView(name, new LinearLayout.LayoutParams(0, ViewGroup.LayoutParams.WrapContent, 1f));
        _status = AuroraUi.Text(context, "CHECKING", 11, AuroraUi.Mint, true);
        _status.SetPadding(AuroraUi.Dp(context, 8), AuroraUi.Dp(context, 5),
            AuroraUi.Dp(context, 8), AuroraUi.Dp(context, 5));
        _status.Background = AuroraUi.Solid(context, AuroraUi.SurfaceRaised, 12);
        header.AddView(_status);

        _version = AuroraUi.Text(context, "Version: —", 14, AuroraUi.Muted);
        body.AddView(_version, AuroraUi.ItemParams(context, 6));
        _build = AuroraUi.Text(context, "Build: —", 13, AuroraUi.Muted);
        body.AddView(_build, AuroraUi.ItemParams(context, 13));

        var actions = new LinearLayout(context) { Orientation = Orientation.Horizontal };
        body.AddView(actions);

        _install = new Button(context) { Text = "Install SMAPI" };
        _install.SetAllCaps(false);
        _install.SetTextColor(AuroraUi.White);
        AuroraUi.Ripple(_install, AuroraUi.Solid(context, AuroraUi.Accent, 13));
        actions.AddView(_install, new LinearLayout.LayoutParams(0, ViewGroup.LayoutParams.WrapContent, 1f));
        _install.Click += (sender, e) =>
        {
            SMAPIInstaller.OnInstalledSMAPI = Refresh;
            SMAPIInstaller.OnClickInstallSMAPIZip(sender, e);
        };
        AuroraUi.AddPressAnimation(_install);

        _remove = new Button(context) { Text = "Remove" };
        _remove.SetAllCaps(false);
        _remove.SetTextColor(AuroraUi.Muted);
        AuroraUi.Ripple(_remove, AuroraUi.Solid(context, AuroraUi.SurfaceRaised, 13));
        actions.AddView(_remove, new LinearLayout.LayoutParams(
            ViewGroup.LayoutParams.WrapContent, ViewGroup.LayoutParams.WrapContent)
        { LeftMargin = AuroraUi.Dp(context, 10) });
        _remove.Click += (_, __) =>
        {
            new AndroidX.AppCompat.App.AlertDialog.Builder(Context)
                .SetTitle("Remove SMAPI?")
                .SetMessage("The game and mods will be kept. SMAPI must be reinstalled before launching with mods.")
                .SetPositiveButton("Remove", (s, e) => { SMAPIInstaller.UninstallSMAPI(); Refresh(); })
                .SetNegativeButton("Cancel", (s, e) => { })
                .Show();
        };
        Refresh();
    }

    public void Refresh()
    {
        var installed = SMAPIInstaller.IsInstalled;
        _status.Text = installed ? "●  INSTALLED" : "●  MISSING";
        _status.SetTextColor(installed ? AuroraUi.Mint : Color.Rgb(255, 173, 143));
        _version.Text = installed ? "Version: " + SMAPIInstaller.GetCurrentVersion() : "SMAPI not installed";
        var build = SMAPIInstaller.GetBuildCode();
        _build.Text = build > 0 ? "Build: " + build : "Install a SMAPI Android ZIP to begin";
        _install.Text = installed ? "Update SMAPI" : "Install SMAPI";
        _remove.Enabled = installed;
        _remove.Alpha = installed ? 1f : 0.4f;
        StatusChanged?.Invoke();
    }
}
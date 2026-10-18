using Android.Content;
using Android.Graphics;
using Android.Views;
using Android.Widget;
using AndroidX.AppCompat.Widget;

namespace SMAPIGameLoader.Launcher.Pages;

/// <summary>Aurora-only preferences; changes do not modify SMAPI or game files.</summary>
internal sealed class SettingsPage : ScrollView
{
    public SettingsPage(Context context) : base(context)
    {
        SetBackgroundColor(AuroraUi.Background);
        FillViewport = true;
        VerticalScrollBarEnabled = false;

        var stack = new LinearLayout(context) { Orientation = Orientation.Vertical };
        stack.SetPadding(AuroraUi.Dp(context, 20), AuroraUi.Dp(context, 31),
            AuroraUi.Dp(context, 20), AuroraUi.Dp(context, 32));
        AddView(stack);

        stack.AddView(AuroraUi.Section(context, "PERSONALIZE"), AuroraUi.ItemParams(context, 9));
        stack.AddView(AuroraUi.Text(context, "Your Aurora", 27, AuroraUi.White, true), AuroraUi.ItemParams(context, 7));
        stack.AddView(AuroraUi.Text(context, "A calmer space for your valley.", 14, AuroraUi.Muted),
            AuroraUi.ItemParams(context, 25));

        var appearance = new LinearLayout(context) { Orientation = Orientation.Vertical };
        appearance.Background = AuroraUi.Solid(context, AuroraUi.Surface, 20, true);
        appearance.SetPadding(AuroraUi.Dp(context, 18), AuroraUi.Dp(context, 20),
            AuroraUi.Dp(context, 18), AuroraUi.Dp(context, 20));
        stack.AddView(appearance, AuroraUi.ItemParams(context, 18));

        var title = AuroraUi.Text(context, "Appearance", 17, AuroraUi.White, true);
        appearance.AddView(title, AuroraUi.ItemParams(context, 16));
        var row = new LinearLayout(context) { Orientation = Orientation.Horizontal };
        row.SetGravity(GravityFlags.CenterVertical);
        appearance.AddView(row);
        var labels = new LinearLayout(context) { Orientation = Orientation.Vertical };
        row.AddView(labels, new LinearLayout.LayoutParams(0, ViewGroup.LayoutParams.WrapContent, 1f));
        labels.AddView(AuroraUi.Text(context, "Smooth animations", 15, AuroraUi.White, true),
            AuroraUi.ItemParams(context, 5));
        labels.AddView(AuroraUi.Text(context,
            "Turn off motion to reduce visual effects and save battery.", 12, AuroraUi.Muted));
        var motion = new SwitchCompat(context) { Checked = AuroraUi.UseMotion(context) };
        motion.ContentDescription = "Enable interface animations";
        motion.ThumbTintList = Android.Content.Res.ColorStateList.ValueOf(AuroraUi.AccentSoft);
        row.AddView(motion);
        motion.CheckedChange += (_, e) => AuroraUi.SetMotion(context, e.IsChecked);

        var about = new LinearLayout(context) { Orientation = Orientation.Vertical };
        about.Background = AuroraUi.Solid(context, AuroraUi.Surface, 20, true);
        about.SetPadding(AuroraUi.Dp(context, 18), AuroraUi.Dp(context, 20),
            AuroraUi.Dp(context, 18), AuroraUi.Dp(context, 20));
        stack.AddView(about, AuroraUi.ItemParams(context, 20));
        about.AddView(AuroraUi.Text(context, "About Aurora", 17, AuroraUi.White, true),
            AuroraUi.ItemParams(context, 12));
        about.AddView(AuroraUi.Pill(context, "v0.4.0  ·  ANDROID PREVIEW", AuroraUi.Mint),
            new LinearLayout.LayoutParams(ViewGroup.LayoutParams.WrapContent, ViewGroup.LayoutParams.WrapContent)
            { BottomMargin = AuroraUi.Dp(context, 15) });
        about.AddView(AuroraUi.Text(context,
            "Community Android SMAPI launcher UI based on NRTnarathip/SMAPILoader. " +
            "Requires a compatible installed game and a separate SMAPI Android runtime.",
            13, AuroraUi.Muted), AuroraUi.ItemParams(context, 12));
        about.AddView(AuroraUi.Text(context,
            "Aurora does not provide the game, bypass purchase checks, or guarantee support for modified APKs.",
            12, AuroraUi.Muted));
    }
}
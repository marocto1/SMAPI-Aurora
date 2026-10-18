using Android.Content;
using Android.Graphics;
using Android.Views;
using Android.Widget;
using AndroidX.AppCompat.Widget;
using AndroidX.CardView.Widget;
using AndroidX.RecyclerView.Widget;
using System;

namespace SMAPIGameLoader.Launcher;

internal sealed class ModViewHolder : RecyclerView.ViewHolder
{
    private readonly TextView _name;
    private readonly TextView _version;
    private readonly SwitchCompat _toggle;
    private readonly Action<ModInfo> _toggled;
    private readonly Action<ModInfo, View> _clicked;
    private ModInfo? _mod;
    private bool _binding;

    private ModViewHolder(View root, TextView name, TextView version, SwitchCompat toggle,
        Action<ModInfo> onToggled, Action<ModInfo, View> onClicked) : base(root)
    {
        _name = name;
        _version = version;
        _toggle = toggle;
        _toggled = onToggled;
        _clicked = onClicked;
        _toggle.CheckedChange += (_, e) =>
        {
            if (_binding || _mod == null || _mod.Enabled == e.IsChecked) return;
            _mod.Enabled = e.IsChecked;
            _toggled(_mod);
            _binding = true;
            _toggle.Checked = _mod.Enabled;
            _binding = false;
        };
        root.Click += (_, __) =>
        {
            if (_mod != null) _clicked(_mod, root);
        };
    }

    public static ModViewHolder Create(Context context, Action<ModInfo> onToggled,
        Action<ModInfo, View> onClicked)
    {
        var card = new CardView(context)
        {
            Radius = AuroraUi.Dp(context, 17),
            CardElevation = AuroraUi.Dp(context, 2),
            UseCompatPadding = false
        };
        card.SetCardBackgroundColor(AuroraUi.Surface);
        card.LayoutParameters = new RecyclerView.LayoutParams(
            ViewGroup.LayoutParams.MatchParent, ViewGroup.LayoutParams.WrapContent)
        { BottomMargin = AuroraUi.Dp(context, 10) };

        var content = new LinearLayout(context) { Orientation = Orientation.Horizontal };
        content.SetGravity(GravityFlags.CenterVertical);
        content.SetPadding(AuroraUi.Dp(context, 18), AuroraUi.Dp(context, 17),
            AuroraUi.Dp(context, 12), AuroraUi.Dp(context, 17));
        card.AddView(content);

        var icon = AuroraUi.Text(context, "✦", 23, AuroraUi.AccentSoft, true);
        icon.Gravity = GravityFlags.Center;
        icon.Background = AuroraUi.Solid(context, AuroraUi.SurfaceRaised, 13);
        content.AddView(icon, new LinearLayout.LayoutParams(
            AuroraUi.Dp(context, 42), AuroraUi.Dp(context, 42))
        { RightMargin = AuroraUi.Dp(context, 14) });

        var info = new LinearLayout(context) { Orientation = Orientation.Vertical };
        content.AddView(info, new LinearLayout.LayoutParams(0, ViewGroup.LayoutParams.WrapContent, 1f));
        var name = AuroraUi.Text(context, "", 15, AuroraUi.White, true);
        name.SetMaxLines(2);
        info.AddView(name, AuroraUi.ItemParams(context, 5));
        var version = AuroraUi.Text(context, "", 12, AuroraUi.Muted);
        info.AddView(version);

        var toggle = new SwitchCompat(context);
        toggle.ThumbTintList = Android.Content.Res.ColorStateList.ValueOf(AuroraUi.AccentSoft);
        content.AddView(toggle);
        return new ModViewHolder(card, name, version, toggle, onToggled, onClicked);
    }

    public void Bind(ModInfo mod)
    {
        _mod = mod;
        _name.Text = mod.modName;
        _version.Text = "v" + mod.modVersion + (mod.Enabled ? "  ·  Enabled" : "  ·  Disabled");
        _binding = true;
        _toggle.Checked = mod.Enabled;
        _binding = false;
    }
}

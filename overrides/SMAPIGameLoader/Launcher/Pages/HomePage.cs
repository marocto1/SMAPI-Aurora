using Android.Content;
using Android.Graphics;
using Android.Views;
using Android.Widget;
using AndroidX.AppCompat.App;
using System;
using System.Linq;
using System.Threading.Tasks;

namespace SMAPIGameLoader.Launcher.Pages;

public sealed class HomePage : LinearLayout
{
    public Button PlayButton { get; }
    public SMAPIInfoCard SmapiCard { get; }
    public GameInfoCard GameInfoCard { get; }
    private bool _gameReady;
    private TextView _launchHint = null!;

    public HomePage(Context context) : base(context)
    {
        Orientation = Orientation.Vertical;
        SetBackgroundColor(AuroraUi.Background);

        var scroll = new ScrollView(context) { FillViewport = true };
        scroll.VerticalScrollBarEnabled = false;
        AddView(scroll, new LayoutParams(LayoutParams.MatchParent, LayoutParams.MatchParent));

        var content = new LinearLayout(context) { Orientation = Orientation.Vertical };
        content.SetPadding(AuroraUi.Dp(context, 19), AuroraUi.Dp(context, 29),
            AuroraUi.Dp(context, 19), AuroraUi.Dp(context, 24));
        scroll.AddView(content);

        var brand = AuroraUi.Text(context, "✦   S M A P I   /   A U R O R A", 13, AuroraUi.AccentSoft, true);
        content.AddView(brand, AuroraUi.ItemParams(context, 10));
        var headline = AuroraUi.Text(context, "Your valley, your way.", 26, AuroraUi.White, true);
        content.AddView(headline, AuroraUi.ItemParams(context, 5));
        var subtitle = AuroraUi.Text(context, "One launcher. All your mods.", 14, AuroraUi.Muted);
        content.AddView(subtitle, AuroraUi.ItemParams(context, 14));
        content.AddView(AuroraUi.Pill(context, "v0.3  ·  ANDROID PREVIEW", AuroraUi.Mint),
            new LayoutParams(LayoutParams.WrapContent, LayoutParams.WrapContent)
            { BottomMargin = AuroraUi.Dp(context, 20) });

        var hero = new LinearLayout(context) { Orientation = Orientation.Vertical };
        hero.SetPadding(AuroraUi.Dp(context, 22), AuroraUi.Dp(context, 25),
            AuroraUi.Dp(context, 22), AuroraUi.Dp(context, 22));
        hero.Background = AuroraUi.Gradient(context);
        content.AddView(hero, AuroraUi.ItemParams(context, 19));

        var eyebrow = AuroraUi.Text(context, "STARDEW VALLEY  •  ANDROID", 11,
            AuroraUi.AccentSoft, true);
        hero.AddView(eyebrow, AuroraUi.ItemParams(context, 14));
        var heroTitle = AuroraUi.Text(context, "A whole new\nway to play.", 30, AuroraUi.White, true);
        hero.AddView(heroTitle, AuroraUi.ItemParams(context, 12));
        var heroDescription = AuroraUi.Text(context,
            "Launch Stardew Valley with SMAPI and your selected mods.",
            14, Color.Rgb(210, 216, 238));
        hero.AddView(heroDescription, AuroraUi.ItemParams(context, 19));

        PlayButton = new Button(context) { Text = "▶   Launch with SMAPI" };
        PlayButton.SetAllCaps(false);
        PlayButton.SetTextColor(AuroraUi.Background);
        PlayButton.SetTextSize(Android.Util.ComplexUnitType.Sp, 16);
        PlayButton.SetTypeface(null, TypefaceStyle.Bold);
        AuroraUi.Ripple(PlayButton, AuroraUi.Solid(context, AuroraUi.Mint, 15));
        PlayButton.SetPadding(AuroraUi.Dp(context, 12), AuroraUi.Dp(context, 12),
            AuroraUi.Dp(context, 12), AuroraUi.Dp(context, 12));
        PlayButton.Enabled = false;
        PlayButton.Alpha = 0.55f;
        PlayButton.Click += (_, __) => LauncherActivity.Instance.OnClickStartGame();
        hero.AddView(PlayButton, AuroraUi.ItemParams(context, 10));
        _launchHint = AuroraUi.Text(context, "Checking game and SMAPI…", 12, AuroraUi.White);
        hero.AddView(_launchHint);
        AuroraUi.AddPressAnimation(PlayButton);

        var sectionTitle = AuroraUi.Text(context, "YOUR SETUP", 12, AuroraUi.Muted, true);
        content.AddView(sectionTitle, AuroraUi.ItemParams(context, 12));

        GameInfoCard = new GameInfoCard(context);
        content.AddView(GameInfoCard, AuroraUi.ItemParams(context, 12));

        var selectButton = new Button(context) { Text = "⌕   Choose installed game" };
        selectButton.SetAllCaps(false);
        selectButton.SetTextSize(Android.Util.ComplexUnitType.Sp, 14);
        selectButton.SetTextColor(AuroraUi.AccentSoft);
        AuroraUi.Ripple(selectButton, AuroraUi.Solid(context, AuroraUi.SurfaceRaised, 15, true));
        selectButton.Click += OnChooseGame;
        content.AddView(selectButton, AuroraUi.ItemParams(context, 18));
        AuroraUi.AddPressAnimation(selectButton);

        SmapiCard = new SMAPIInfoCard(context);
        SmapiCard.StatusChanged += UpdatePlayState;
        content.AddView(SmapiCard, AuroraUi.ItemParams(context, 17));
        var footnote = AuroraUi.Text(context,
            "Uses a compatible installed Android game. Does not bypass purchases or game protection.",
            11, AuroraUi.Muted);
        content.AddView(footnote);
        AuroraUi.AnimateIn(hero);
        GameInfoCard.CheckAsync(ready =>
        {
            _gameReady = ready;
            UpdatePlayState();
        });
    }

    private void UpdatePlayState()
    {
        var ready = _gameReady && SMAPIInstaller.IsInstalled;
        PlayButton.Enabled = ready;
        PlayButton.Alpha = ready ? 1f : 0.55f;
        _launchHint.Text = !_gameReady
            ? "Select a compatible Stardew Valley installation below"
            : !SMAPIInstaller.IsInstalled
                ? "Install SMAPI Android to enable launch"
                : "Everything is ready. Have a good day in the valley!";
    }

    private void OnChooseGame(object? sender, EventArgs args)
    {
        try
        {
            var apps = StardewApkTool.GetSelectableApplications();
            if (apps.Count == 0)
            {
                Toast.MakeText(Context, "No installed apps are visible", ToastLength.Long)?.Show();
                return;
            }
            var labels = apps.Select(app => app.Label + "  (" + app.PackageName + ")").ToArray();
            new AlertDialog.Builder(Context)
                .SetTitle("Select installed Stardew Valley")
                .SetItems(labels, (_, click) =>
                {
                    try
                    {
                        // APK ZIP inspection runs off the UI thread to prevent freezes.
                        var selectedPackage = apps[click.Which].PackageName;
                        Toast.MakeText(Context, "Checking installed game…", ToastLength.Short)?.Show();
                        Task.Run(() =>
                        {
                            try
                            {
                                StardewApkTool.SelectInstalledGame(selectedPackage);
                                LauncherActivity.Instance.RunOnUiThread(() => LauncherActivity.Instance.Recreate());
                            }
                            catch (Exception error)
                            {
                                LauncherActivity.Instance.RunOnUiThread(() =>
                                    Toast.MakeText(Context, error.Message, ToastLength.Long)?.Show());
                            }
                        });
                    }
                    catch (Exception error)
                    {
                        Toast.MakeText(Context, error.Message, ToastLength.Long)?.Show();
                    }
                })
                .SetNegativeButton("Cancel", (_, __) => { })
                .Show();
        }
        catch (Exception error)
        {
            Toast.MakeText(Context, error.Message, ToastLength.Long)?.Show();
        }
    }
}
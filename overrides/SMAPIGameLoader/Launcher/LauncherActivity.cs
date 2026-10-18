using Android.App;
using Android.Content.PM;
using Android.Content.Res;
using Android.OS;
using Android.Views;
using Android.Widget;
using AndroidX.AppCompat.App;
using Google.Android.Material.BottomNavigation;
using SMAPIGameLoader.Launcher.Pages;
using SMAPIGameLoader.Tool;
using System;
using Xamarin.Essentials;

namespace SMAPIGameLoader.Launcher;

[Activity(
    Label = "SMAPI Aurora",
    MainLauncher = true,
    Theme = "@style/Theme.Material3.DayNight.NoActionBar",
    AlwaysRetainTaskState = true,
    LaunchMode = LaunchMode.SingleInstance,
    ScreenOrientation = ScreenOrientation.FullSensor
)]
public sealed class LauncherActivity : AppCompatActivity
{
    public static LauncherActivity Instance { get; private set; } = null!;
    private const int HomeId = 1;
    private const int ModsId = 2;

    private FrameLayout _container = null!;
    private View _homePage = null!;
    private View _modPage = null!;
    private BottomNavigationView _navigation = null!;
    private int _activePage = HomeId;

    private static bool IsDeviceSupported => IntPtr.Size == 8;

    protected override void OnCreate(Bundle? state)
    {
        base.OnCreate(state);
        Instance = this;
        Platform.Init(this, state);
        ActivityTool.Init(this);
        AppCompatDelegate.DefaultNightMode = AppCompatDelegate.ModeNightYes;

        if (!IsDeviceSupported)
        {
            Toast.MakeText(this, "ARM64 / 64-bit Android required", ToastLength.Long)?.Show();
            Finish();
            return;
        }
        BuildUi();
        if (!StardewApkTool.IsInstalled)
            Toast.MakeText(this, "Choose your installed game on the Home screen", ToastLength.Long)?.Show();
        if (AdbExtraTool.IsClickStartGame(this))
            OnClickStartGame();
    }

    private void BuildUi()
    {
        var root = new LinearLayout(this) { Orientation = Orientation.Vertical };
        root.SetBackgroundColor(AuroraUi.Background);
        SetContentView(root);

        _container = new FrameLayout(this);
        root.AddView(_container, new LinearLayout.LayoutParams(
            ViewGroup.LayoutParams.MatchParent, 0, 1f));

        _homePage = new HomePage(this);
        _modPage = new ModManagerPage(this);
        _container.AddView(_homePage);
        _container.AddView(_modPage);
        _modPage.Visibility = ViewStates.Gone;

        _navigation = new BottomNavigationView(this);
        _navigation.SetBackgroundColor(AuroraUi.Surface);
        var states = new[]
        {
            new[] { Android.Resource.Attribute.StateChecked },
            Array.Empty<int>()
        };
        var colors = new[] { AuroraUi.AccentSoft.ToArgb(), AuroraUi.Muted.ToArgb() };
        _navigation.ItemIconTintList = new ColorStateList(states, colors);
        _navigation.ItemTextColor = new ColorStateList(states, colors);
        _navigation.Menu.Add(0, HomeId, 0, "Home").SetIcon(Android.Resource.Drawable.IcMenuMyCalendar);
        _navigation.Menu.Add(0, ModsId, 1, "Mods").SetIcon(Android.Resource.Drawable.IcMenuAgenda);
        _navigation.ItemSelected += (_, eventArgs) =>
        {
            ShowPage(eventArgs.Item!.ItemId);
            eventArgs.Handled = true;
        };
        root.AddView(_navigation, new LinearLayout.LayoutParams(
            ViewGroup.LayoutParams.MatchParent, AuroraUi.Dp(this, 72)));
        _navigation.SelectedItemId = HomeId;
        AuroraUi.AnimateIn(_homePage);
    }

    private void ShowPage(int itemId)
    {
        if (itemId == _activePage) return;
        var incoming = itemId == ModsId ? _modPage : _homePage;
        var outgoing = itemId == ModsId ? _homePage : _modPage;
        outgoing.Animate().Cancel();
        outgoing.Visibility = ViewStates.Gone;
        incoming.Visibility = ViewStates.Visible;
        _activePage = itemId;
        AuroraUi.AnimateIn(incoming);
    }

    public void OnClickStartGame()
    {
        if (!StardewApkTool.IsInstalled)
        {
            Toast.MakeText(this, "Select a compatible installed Stardew Valley first", ToastLength.Long)?.Show();
            return;
        }
        EntryGame.LaunchGameActivity(this);
    }
}

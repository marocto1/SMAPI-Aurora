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
    private const int SettingsId = 3;

    private FrameLayout _container = null!;
    private View _homePage = null!;
    private ModManagerPage _modPage = null!;
    private View _settingsPage = null!;
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
        BuildUi(state?.GetInt("aurora_tab", HomeId) ?? HomeId);
        if (AdbExtraTool.IsClickStartGame(this))
            OnClickStartGame();
    }

    private void BuildUi(int restoreTab)
    {
        var root = new LinearLayout(this) { Orientation = Orientation.Vertical };
        root.SetBackgroundColor(AuroraUi.Background);
        SetContentView(root);

        _container = new FrameLayout(this);
        root.AddView(_container, new LinearLayout.LayoutParams(
            ViewGroup.LayoutParams.MatchParent, 0, 1f));

        _homePage = new HomePage(this);
        _modPage = new ModManagerPage(this);
        _settingsPage = new SettingsPage(this);
        _container.AddView(_homePage);
        _container.AddView(_modPage);
        _container.AddView(_settingsPage);
        _modPage.Visibility = ViewStates.Gone;
        _settingsPage.Visibility = ViewStates.Gone;

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
        _navigation.Menu.Add(0, SettingsId, 2, "Settings").SetIcon(Android.Resource.Drawable.IcMenuPreferences);
        _navigation.ItemSelected += (_, eventArgs) =>
        {
            ShowPage(eventArgs.Item!.ItemId);
            eventArgs.Handled = true;
        };
        root.AddView(_navigation, new LinearLayout.LayoutParams(
            ViewGroup.LayoutParams.MatchParent, AuroraUi.Dp(this, 72)));
        _activePage = HomeId;
        _navigation.SelectedItemId = restoreTab is ModsId or SettingsId ? restoreTab : HomeId;
        AuroraUi.AnimateIn(_activePage == ModsId ? _modPage :
            _activePage == SettingsId ? _settingsPage : _homePage);
    }

    private void ShowPage(int itemId)
    {
        if (itemId == _activePage) return;
        var incoming = PageFor(itemId);
        var outgoing = PageFor(_activePage);
        if (incoming == outgoing) return;
        outgoing.Animate().Cancel();
        outgoing.Visibility = ViewStates.Gone;
        outgoing.Alpha = 1f;
        incoming.Visibility = ViewStates.Visible;
        _activePage = itemId;
        if (itemId == ModsId) _modPage.RefreshMods();
        AuroraUi.AnimateIn(incoming);
    }

    private View PageFor(int id) => id switch
    {
        ModsId => _modPage,
        SettingsId => _settingsPage,
        _ => _homePage
    };

    protected override void OnSaveInstanceState(Bundle outState)
    {
        outState.PutInt("aurora_tab", _activePage);
        base.OnSaveInstanceState(outState);
    }

    public void OnClickStartGame() => EntryGame.LaunchGameActivity(this);
}
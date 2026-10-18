using Android.Content;
using Android.Content.Res;
using Android.Graphics;
using Android.Graphics.Drawables;
using Android.Views;
using Android.Views.Animations;
using Android.Widget;
using System;

namespace SMAPIGameLoader.Launcher;

// Pure Android Views; no WebView, extra services or third-party UI packages.
internal static class AuroraUi
{
    public static readonly Color Background = Color.Rgb(12, 15, 25);
    public static readonly Color Surface = Color.Rgb(23, 28, 42);
    public static readonly Color SurfaceRaised = Color.Rgb(31, 38, 56);
    public static readonly Color Accent = Color.Rgb(140, 123, 255);
    public static readonly Color AccentSoft = Color.Rgb(185, 176, 255);
    public static readonly Color Mint = Color.Rgb(103, 224, 187);
    public static readonly Color White = Color.Rgb(248, 249, 255);
    public static readonly Color Muted = Color.Rgb(153, 161, 186);
    public static readonly Color Outline = Color.Rgb(53, 60, 81);

    public static int Dp(Context context, float value) =>
        (int)(value * context.Resources!.DisplayMetrics!.Density + 0.5f);

    public static GradientDrawable Solid(Context context, Color color, float radius = 18f, bool outline = false)
    {
        var shape = new GradientDrawable();
        shape.SetShape(ShapeType.Rectangle);
        shape.SetColor(color);
        shape.SetCornerRadius(Dp(context, radius));
        if (outline)
            shape.SetStroke(Dp(context, 1), Outline);
        return shape;
    }

    public static GradientDrawable Gradient(Context context, float radius = 24f)
    {
        var gradient = new GradientDrawable(
            GradientDrawable.Orientation.TlBr,
            new[] { Color.Rgb(67, 52, 124).ToArgb(), Color.Rgb(31, 49, 80).ToArgb(), Color.Rgb(18, 65, 65).ToArgb() });
        gradient.SetCornerRadius(Dp(context, radius));
        return gradient;
    }

    public static TextView Text(Context context, string value, float sizeSp, Color color, bool bold = false)
    {
        var text = new TextView(context) { Text = value };
        text.SetTextSize(Android.Util.ComplexUnitType.Sp, sizeSp);
        text.SetTextColor(color);
        text.IncludeFontPadding = false;
        if (bold)
            text.SetTypeface(null, TypefaceStyle.Bold);
        return text;
    }

    public static void Ripple(View view, GradientDrawable background)
    {
        // Native material touch-feedback, with no frame-by-frame allocations.
        var ripple = new RippleDrawable(
            ColorStateList.ValueOf(Color.Argb(35, 255, 255, 255)), background, null);
        view.Background = ripple;
    }

    public static void AnimateIn(View view)
    {
        view.Alpha = 0f;
        view.TranslationY = Dp(view.Context!, 12);
        view.Animate().Cancel();
        view.Animate().Alpha(1f).TranslationY(0f)
            .SetDuration(240)
            .SetInterpolator(new DecelerateInterpolator())
            .Start();
    }

    public static void AddPressAnimation(View view)
    {
        view.Touch += (_, args) =>
        {
            if (args.Event == null) return;
            switch (args.Event.Action)
            {
                case MotionEventActions.Down:
                    view.Animate().ScaleX(0.985f).ScaleY(0.985f).SetDuration(90).Start();
                    break;
                case MotionEventActions.Up:
                case MotionEventActions.Cancel:
                    view.Animate().ScaleX(1f).ScaleY(1f).SetDuration(150).Start();
                    break;
            }
            args.Handled = false; // Preserve native click, accessibility and scrolling.
        };
    }

    public static LinearLayout.LayoutParams ItemParams(Context context, int bottomDp = 0)
    {
        return new LinearLayout.LayoutParams(
            ViewGroup.LayoutParams.MatchParent, ViewGroup.LayoutParams.WrapContent)
        {
            BottomMargin = Dp(context, bottomDp)
        };
    }
}

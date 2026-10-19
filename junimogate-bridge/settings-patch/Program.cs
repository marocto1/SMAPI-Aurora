using Mono.Cecil;
using Mono.Cecil.Cil;

if (args.Length != 2)
{
    Console.Error.WriteLine("Usage: AuroraSettingsPatch <original-app.dll> <patched-app.dll>");
    return 2;
}

var resolver = new DefaultAssemblyResolver();
resolver.AddSearchDirectory(Path.GetDirectoryName(Path.GetFullPath(args[0]))!);
using var assembly = AssemblyDefinition.ReadAssembly(args[0], new ReaderParameters {
    InMemory = true, AssemblyResolver = resolver
});
var module = assembly.MainModule;
var fragment = module.Types.SingleOrDefault(t => t.FullName == "JunimoGate.App.SettingsFragment")
    ?? throw new InvalidOperationException("Bundled SMAPI SettingsFragment missing or renamed");
var onView = fragment.Methods.SingleOrDefault(m => m.Name == "OnViewCreated" && m.Parameters.Count == 2)
    ?? throw new InvalidOperationException("Settings OnViewCreated signature changed");
if (fragment.Methods.Any(m => m.Name == "AuroraOpenVersionSettings"))
    throw new InvalidOperationException("Settings already patched, refusing double-injection");

TypeReference Ref(string fullName)
{
    var known = module.GetTypeReferences().FirstOrDefault(t => t.FullName == fullName);
    if (known is not null) return known;
    var sample = module.GetTypeReferences().FirstOrDefault(t => t.FullName.StartsWith(
        fullName.StartsWith("AndroidX.") ? "AndroidX." :
        fullName.StartsWith("Google.") ? "Google." : "Android.", StringComparison.Ordinal));
    if (sample is null) throw new InvalidOperationException("Cannot resolve framework scope for " + fullName);
    var split = fullName.LastIndexOf('.');
    return new TypeReference(fullName[..split], fullName[(split + 1)..], module, sample.Scope);
}
var viewT = Ref("Android.Views.View");
var viewGroupT = Ref("Android.Views.ViewGroup");
var scrollT = Ref("Android.Widget.ScrollView");
var linearT = Ref("Android.Widget.LinearLayout");
var textViewT = Ref("Android.Widget.TextView");
var buttonT = Ref("Google.Android.Material.Button.MaterialButton");
var contextT = Ref("Android.Content.Context");
var intentT = Ref("Android.Content.Intent");
var eventHandlerT = module.ImportReference(typeof(EventHandler));
var eventArgsT = module.ImportReference(typeof(EventArgs));

MethodReference Meth(TypeReference declaring, string name, TypeReference result, params TypeReference[] parms)
{
    var m = new MethodReference(name, result, declaring) { HasThis = true };
    foreach (var p in parms) m.Parameters.Add(new ParameterDefinition(p));
    return m;
}
var requireContext = Meth(fragment.BaseType, "RequireContext", contextT);
var buttonCtor = Meth(buttonT, ".ctor", module.TypeSystem.Void, contextT);
var textSetter = Meth(textViewT, "set_Text", module.TypeSystem.Void, module.TypeSystem.String);
var onClick = Meth(viewT, "add_Click", module.TypeSystem.Void, eventHandlerT);
var childAt = Meth(viewGroupT, "GetChildAt", viewT, module.TypeSystem.Int32);
var addView = Meth(viewGroupT, "AddView", module.TypeSystem.Void, viewT);
var intentCtor = Meth(intentT, ".ctor", module.TypeSystem.Void);
var setClass = Meth(intentT, "SetClassName", intentT, contextT, module.TypeSystem.String);
var putExtra = Meth(intentT, "PutExtra", intentT, module.TypeSystem.String, module.TypeSystem.Int32);
var startActivity = Meth(fragment.BaseType, "StartActivity", module.TypeSystem.Void, intentT);
var eventCtor = module.ImportReference(typeof(EventHandler).GetConstructor([typeof(object), typeof(IntPtr)])
    ?? throw new InvalidOperationException("EventHandler constructor missing"));

var handler = new MethodDefinition("AuroraOpenVersionSettings",
    MethodAttributes.Private | MethodAttributes.HideBySig, module.TypeSystem.Void);
handler.Parameters.Add(new ParameterDefinition("sender", ParameterAttributes.None, module.TypeSystem.Object));
handler.Parameters.Add(new ParameterDefinition("args", ParameterAttributes.None, eventArgsT));
fragment.Methods.Add(handler);
handler.Body.InitLocals = true;
var intentLocal = new VariableDefinition(intentT);
handler.Body.Variables.Add(intentLocal);
var h = handler.Body.GetILProcessor();
h.Append(h.Create(OpCodes.Newobj, intentCtor));
h.Append(h.Create(OpCodes.Stloc, intentLocal));
h.Append(h.Create(OpCodes.Ldloc, intentLocal));
h.Append(h.Create(OpCodes.Ldarg_0));
h.Append(h.Create(OpCodes.Callvirt, requireContext));
h.Append(h.Create(OpCodes.Ldstr, "org.junimogate.aurora.AuroraVersionActivity"));
h.Append(h.Create(OpCodes.Callvirt, setClass));
h.Append(h.Create(OpCodes.Pop));
h.Append(h.Create(OpCodes.Ldloc, intentLocal));
h.Append(h.Create(OpCodes.Ldstr, "aurora-start-page"));
h.Append(h.Create(OpCodes.Ldc_I4_2));
h.Append(h.Create(OpCodes.Callvirt, putExtra));
h.Append(h.Create(OpCodes.Pop));
h.Append(h.Create(OpCodes.Ldarg_0));
h.Append(h.Create(OpCodes.Ldloc, intentLocal));
h.Append(h.Create(OpCodes.Callvirt, startActivity));
h.Append(h.Create(OpCodes.Ret));

// The existing fragment_settings root is a ScrollView with one LinearLayout.
// Append an actual version-settings button without changing bundled Android resource IDs.
onView.Body.InitLocals = true;
var newButton = new VariableDefinition(buttonT);
onView.Body.Variables.Add(newButton);
var il = onView.Body.GetILProcessor();
var ret = onView.Body.Instructions.LastOrDefault(x => x.OpCode == OpCodes.Ret)
    ?? throw new InvalidOperationException("OnViewCreated has no normal return");
var seq = new List<Instruction>
{
    il.Create(OpCodes.Ldarg_0),
    il.Create(OpCodes.Callvirt, requireContext),
    il.Create(OpCodes.Newobj, buttonCtor),
    il.Create(OpCodes.Stloc, newButton),
    il.Create(OpCodes.Ldloc, newButton),
    il.Create(OpCodes.Ldstr, "Настройки версий"),
    il.Create(OpCodes.Callvirt, textSetter),
    il.Create(OpCodes.Ldloc, newButton),
    il.Create(OpCodes.Ldarg_0),
    il.Create(OpCodes.Ldftn, handler),
    il.Create(OpCodes.Newobj, eventCtor),
    il.Create(OpCodes.Callvirt, onClick),
    il.Create(OpCodes.Ldarg_1),
    il.Create(OpCodes.Castclass, scrollT),
    il.Create(OpCodes.Ldc_I4_0),
    il.Create(OpCodes.Callvirt, childAt),
    il.Create(OpCodes.Castclass, linearT),
    il.Create(OpCodes.Ldloc, newButton),
    il.Create(OpCodes.Callvirt, addView),
};
foreach (var ins in seq) il.InsertBefore(ret, ins);
assembly.Write(args[1]);

using var audited = AssemblyDefinition.ReadAssembly(args[1]);
var auditedSettings = audited.MainModule.Types.Single(t => t.FullName == fragment.FullName);
var patchedHandler = auditedSettings.Methods.Single(m => m.Name == "AuroraOpenVersionSettings");
var viewMethod = auditedSettings.Methods.Single(m => m.Name == "OnViewCreated");
if (!patchedHandler.Body.Instructions.Any(x => x.OpCode == OpCodes.Ldstr && (string?)x.Operand == "aurora-start-page")
    || !viewMethod.Body.Instructions.Any(x => x.OpCode == OpCodes.Ldstr && (string?)x.Operand == "Настройки версий"))
    throw new InvalidOperationException("Patched Settings button did not round-trip");
Console.WriteLine("PASS: native SMAPI SettingsFragment includes wired Aurora Version Settings button and Intent deep link");
return 0;

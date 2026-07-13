# Plug-in Build and Registration

Preferred path for new server-side behavior:

1. Add domain/application logic under `src/Shared`.
2. Add a thin stateless plug-in adapter under `src/Plugins/CCSB.Plugins/Steps`.
3. Add or update step metadata under `src/Plugins/CCSB.PluginRegistration/Definitions`.
4. Build the SDK-style project targeting .NET Framework 4.6.2.
5. Package dependent assemblies from the start when dependencies are required.
6. Register through Power Platform CLI or Plug-in Registration Tool and include the resulting components in the appropriate Dataverse solution.

Avoid ILMerge. Use Dataverse dependent assemblies / plug-in packages when dependencies need to travel with the plug-in.

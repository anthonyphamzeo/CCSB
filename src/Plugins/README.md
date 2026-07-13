# Plug-ins

`CCSB.Plugins` contains Dataverse event entry points, registered-step adapters, and handlers. Steps should validate execution context, create a correlation scope, and delegate to application services.

`CCSB.PluginRegistration` contains repeatable registration/profiling utilities and declarative step metadata. Registration output must be environment-neutral and solution-aware.

Project rules:

- Use SDK-style projects targeting .NET Framework 4.6.2 for Dataverse plug-in compatibility.
- Keep plug-in classes stateless.
- Prefer Dataverse dependent assemblies / plug-in packages when dependencies must be deployed with the plug-in.
- Do not use ILMerge.
- Do not perform unbounded queries, long-running external calls, or duplicate business rules in plug-in classes.

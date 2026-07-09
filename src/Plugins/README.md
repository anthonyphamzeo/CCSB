# Plug-ins

`CCSB.Plugins` contains Dataverse event entry points, registered-step adapters, and handlers. Steps should validate execution context, create a correlation scope, and delegate to application services.

`CCSB.PluginRegistration` contains repeatable registration/profiling utilities and declarative step metadata. Registration output must be environment-neutral and solution-aware.

Do not perform unbounded queries, long-running external calls, or duplicate business rules in plug-in classes.


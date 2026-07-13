# Plug-in Registration

This folder stores environment-neutral registration metadata for Dataverse plug-ins and Custom API handlers.

Preferred registration path:

1. Build the plug-in project.
2. Package dependent assemblies from the start when dependencies are required.
3. Register or update using Power Platform CLI / Plug-in Registration Tool.
4. Keep step definitions in `Definitions/` so solution changes are reproducible.

No secrets or environment-specific connection strings belong here.

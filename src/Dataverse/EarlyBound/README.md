# Dataverse Early-Bound Model

This folder is the controlled home for generated Dataverse early-bound classes.

## Recommended generator

Use Microsoft Power Platform CLI:

```powershell
pac auth create --url https://<environment>.crm.dynamics.com
.\generate-early-bound.ps1
```

The script calls:

```powershell
pac modelbuilder build --outdirectory .\CCSB.Dataverse.EarlyBound\model --settingsTemplateFile .\CCSB.Dataverse.EarlyBound\model\builderSettings.json
```

## Rules

- Keep generated classes in `CCSB.Dataverse.EarlyBound/model`.
- Update `builderSettings.json` when a task introduces or removes Dataverse tables, choices, or Custom APIs.
- Filter generated tables and messages to CCSB-owned components; do not generate the whole environment.
- Review generated diffs as part of the task PR.
- Do not hand-edit generated entity, message, or option-set files.

## About spkl

`spkl` is not the preferred generator for new work in this repository. It can remain a legacy reference if we need to reproduce older CRM build behavior, but new early-bound generation should use `pac modelbuilder build`.

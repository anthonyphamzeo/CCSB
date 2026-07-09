# CCSB Core — Import and Verification Runbook

## Goal

Create an unmanaged **`CCSB_Core`** solution in a Dataverse development environment, then export a Dataverse-generated unmanaged solution archive for controlled import into other environments.

## Before applying

1. Use a dedicated development environment.
2. Confirm that no previously released `ccsb_*` tables must be preserved.
3. Confirm that a publisher prefix of `ccsb` is available.
4. Use a System Administrator identity.
5. Run validation-only mode first.

## Validation-only command

```powershell
.\Build-CCSBCore.ps1 `
  -ConnectionString "AuthType=OAuth;Url=https://YOURORG.crm.dynamics.com;AppId=YOUR-APP-ID;RedirectUri=http://localhost;LoginPrompt=Auto"
```

Expected result: a `CCSB_Core_build_report.json` file with `Success: true` and no Dataverse changes.

## Apply command

```powershell
.\Build-CCSBCore.ps1 `
  -ConnectionString "AuthType=OAuth;Url=https://YOURORG.crm.dynamics.com;AppId=YOUR-APP-ID;RedirectUri=http://localhost;LoginPrompt=Auto" `
  -Apply
```

Expected output:

```text
artifacts\CCSB_Core_1_0_0_0_unmanaged.zip
artifacts\CCSB_Core_build_report.json
```

## Verify the source development environment

In Power Apps:

1. Open **Solutions**.
2. Open **CCSB Core**.
3. Confirm exactly 26 custom tables beginning with `ccsb_`.
4. Open several tables and confirm:
   - the expected display name;
   - the `ccsb_name` primary-name column;
   - the expected ownership model;
   - no unintended business fields, lookup relationships, Choices, forms, or sample records.
5. Review the build report.

## Import to a target development environment

1. Copy `CCSB_Core_1_0_0_0_unmanaged.zip`.
2. Open **Solutions** in the target environment.
3. Select **Import solution**.
4. Select the exported ZIP.
5. Wait for successful import.
6. Validate the same 26 tables and the `CCSB` publisher prefix.

## Promote through ALM

For UAT and Production:

1. Make the approved changes in the Dev **unmanaged** `CCSB_Core` solution.
2. Export the solution from Dev as a **managed** solution for UAT.
3. Test there.
4. Promote the managed artifact to Production.
5. Do not develop directly in the target environment.

## Failure handling

| Symptom | Action |
|---|---|
| `ccsb` publisher prefix already exists | Confirm it belongs to CCSB. The provisioner adopts one compatible publisher but stops when more than one uses the prefix. |
| A table exists with different ownership | Stop. Do not try to change ownership. Rename/replan before creating fields or data. |
| A table has been created before a run fails | Fix the reported issue and rerun. The tool adopts compatible existing tables. |
| Cannot export solution | Confirm solution privileges and that the solution is unmanaged in the development environment. |
| Import fails in target | Use the exact generated ZIP, inspect import logs, and resolve only the reported dependency or publisher issue. |


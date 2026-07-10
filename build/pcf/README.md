# PCF Build

PCF controls should be generated with Power Platform CLI and built with the generated `pcf-scripts` setup.

Common commands from an individual control folder:

```powershell
npm install
npm run build
npm run build -- --buildMode production
```

Packaging belongs in `src/PCF/Solutions/Planora.PCFControls`. Generated `.zip`, `out`, `dist`, and `node_modules` folders remain ignored.

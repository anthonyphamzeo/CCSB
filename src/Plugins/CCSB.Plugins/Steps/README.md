# Plug-in Steps

Add one folder per registered behavior, using this pattern:

```text
Steps/
  <Message><Entity><Stage>/
    <PluginClass>.cs
    README.md
```

Step classes must stay stateless. They should validate the execution context, then delegate to `CCSB.Application` services.

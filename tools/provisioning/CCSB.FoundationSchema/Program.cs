using System.Data.Common;
using System.Text.Json;
using Microsoft.PowerPlatform.Dataverse.Client;
using CrmSdkMessages = Microsoft.Crm.Sdk.Messages;
using Microsoft.Xrm.Sdk;
using Microsoft.Xrm.Sdk.Metadata;
using Microsoft.Xrm.Sdk.Messages;
using Microsoft.Xrm.Sdk.Query;

namespace CCSB.FoundationSchema.Provisioner;

internal static class Program
{
    private static int Main(string[] args)
    {
        try
        {
            var options = CommandLineOptions.Parse(args);
            var schemaPath = options.SchemaPath ?? Path.Combine(AppContext.BaseDirectory, "schema", "ccsb.foundation.schema.json");

            if (!File.Exists(schemaPath))
            {
                throw new FileNotFoundException("The schema file was not found.", schemaPath);
            }

            var schema = JsonSerializer.Deserialize<FoundationSchema>(
                File.ReadAllText(schemaPath),
                JsonOptions)
                ?? throw new InvalidOperationException("The schema file could not be parsed.");

            ValidateSchema(schema);
            var counts = GetCounts(schema);
            Console.WriteLine($"Schema: {schema.Solution.UniqueName} v{schema.Solution.Version}");
            Console.WriteLine($"New tables: {counts.NewTables}; new-table fields: {counts.NewTableFields}; relationships: {counts.Relationships}; existing-table fields: {counts.ExtensionFields}.");

            if (options.WhatIf)
            {
                Console.WriteLine("What-if complete. No Dataverse metadata was changed.");
                return 0;
            }

            var connectionString = ResolveConnectionString(options);

            using var service = new ServiceClient(connectionString);
            if (!service.IsReady)
            {
                throw new InvalidOperationException($"Dataverse connection failed: {service.LastError}");
            }

            var provisioner = new FoundationProvisioner(service, schema, options);
            if (options.ValidateLiveOnly)
            {
                provisioner.ValidateLiveOnly();
                Console.WriteLine("Live metadata compatibility validation completed successfully.");
                return 0;
            }

            provisioner.Run();

            Console.WriteLine("Foundation schema provisioning completed successfully.");
            return 0;
        }
        catch (Exception ex)
        {
            Console.Error.WriteLine(ex.ToString());
            return 1;
        }
    }

    private static string ResolveConnectionString(CommandLineOptions options)
    {
        if (!string.IsNullOrWhiteSpace(options.ConnectionString))
        {
            return options.ConnectionString;
        }

        if (!string.IsNullOrWhiteSpace(options.EnvironmentUrl))
        {
            return BuildInteractiveConnectionString(options);
        }

        var configuredConnection = Environment.GetEnvironmentVariable("DATAVERSE_CONNECTION_STRING");
        if (!string.IsNullOrWhiteSpace(configuredConnection))
        {
            return configuredConnection;
        }

        throw new InvalidOperationException(
            "Supply --connection, set DATAVERSE_CONNECTION_STRING, or use --environment-url for interactive OAuth sign-in.");
    }

    private static string BuildInteractiveConnectionString(CommandLineOptions options)
    {
        if (!Uri.TryCreate(options.EnvironmentUrl, UriKind.Absolute, out var environmentUri) ||
            !string.Equals(environmentUri.Scheme, Uri.UriSchemeHttps, StringComparison.OrdinalIgnoreCase))
        {
            throw new ArgumentException("--environment-url must be an absolute HTTPS Dataverse environment URL.");
        }

        var redirectUri = string.IsNullOrWhiteSpace(options.RedirectUri)
            ? CommandLineOptions.DefaultInteractiveRedirectUri
            : options.RedirectUri;

        if (!Uri.TryCreate(redirectUri, UriKind.Absolute, out var redirect) ||
            !string.Equals(redirect.Host, "localhost", StringComparison.OrdinalIgnoreCase))
        {
            throw new ArgumentException(
                "Interactive OAuth on .NET requires a loopback redirect URI. Use http://localhost.");
        }

        var appId = string.IsNullOrWhiteSpace(options.AppId)
            ? CommandLineOptions.DefaultInteractiveAppId
            : options.AppId;

        if (!Guid.TryParse(appId, out _))
        {
            throw new ArgumentException("--app-id must be a valid Microsoft Entra application (client) ID GUID.");
        }

        var builder = new DbConnectionStringBuilder
        {
            ["AuthType"] = "OAuth",
            ["Url"] = environmentUri.GetLeftPart(UriPartial.Authority),
            ["AppId"] = appId,
            ["RedirectUri"] = redirectUri,
            ["LoginPrompt"] = "Always",
            ["RequireNewInstance"] = "true",
        };

        if (!string.IsNullOrWhiteSpace(options.Username))
        {
            // Login hint only. Do not pass or store a user password in this tool.
            builder["Username"] = options.Username;
        }

        if (!string.IsNullOrWhiteSpace(options.TokenCacheStorePath))
        {
            builder["TokenCacheStorePath"] = options.TokenCacheStorePath;
        }

        Console.WriteLine("Interactive OAuth selected. A browser sign-in window will open.");
        Console.WriteLine($"Dataverse environment: {environmentUri.GetLeftPart(UriPartial.Authority)}");
        if (!string.IsNullOrWhiteSpace(options.Username))
        {
            Console.WriteLine($"Sign-in hint: {options.Username}");
        }

        return builder.ConnectionString;
    }

    private static readonly JsonSerializerOptions JsonOptions = new()
    {
        PropertyNameCaseInsensitive = true,
        ReadCommentHandling = JsonCommentHandling.Skip,
        AllowTrailingCommas = true,
    };

    private static void ValidateSchema(FoundationSchema schema)
    {
        if (string.IsNullOrWhiteSpace(schema.SchemaVersion) ||
            !Version.TryParse(schema.SchemaVersion, out _))
        {
            throw new InvalidOperationException("schemaVersion is required and must be a semantic version.");
        }

        if (string.IsNullOrWhiteSpace(schema.Solution.UniqueName))
        {
            throw new InvalidOperationException("solution.uniqueName is required.");
        }

        if (string.IsNullOrWhiteSpace(schema.Solution.Version) ||
            !Version.TryParse(schema.Solution.Version, out _))
        {
            throw new InvalidOperationException("solution.version is required and must be a semantic version.");
        }

        var tableNames = new HashSet<string>(StringComparer.OrdinalIgnoreCase);
        foreach (var table in schema.Tables)
        {
            if (!tableNames.Add(table.LogicalName))
            {
                throw new InvalidOperationException($"Duplicate table logical name: {table.LogicalName}");
            }

            if (!table.LogicalName.StartsWith("ccsb_", StringComparison.OrdinalIgnoreCase) ||
                !table.SchemaName.StartsWith("ccsb_", StringComparison.OrdinalIgnoreCase))
            {
                throw new InvalidOperationException($"Table '{table.LogicalName}' does not use the ccsb prefix.");
            }

            var fields = new HashSet<string>(StringComparer.OrdinalIgnoreCase)
            {
                table.PrimaryName.LogicalName,
            };

            foreach (var field in table.Fields)
            {
                if (!fields.Add(field.LogicalName))
                {
                    throw new InvalidOperationException($"Duplicate field '{field.LogicalName}' in '{table.LogicalName}'.");
                }

                ValidateField(field, table.LogicalName);
            }
        }

        foreach (var extension in schema.Extensions)
        {
            foreach (var field in extension.Fields)
            {
                ValidateField(field, extension.EntityLogicalName);
            }
        }

        var aliases = new HashSet<string>(StringComparer.OrdinalIgnoreCase);
        foreach (var alias in schema.CoreEntityAliases)
        {
            if (string.IsNullOrWhiteSpace(alias.CanonicalLogicalName) ||
                string.IsNullOrWhiteSpace(alias.DisplayName))
            {
                throw new InvalidOperationException("Each coreEntityAliases entry requires canonicalLogicalName and displayName.");
            }

            if (!aliases.Add(alias.CanonicalLogicalName))
            {
                throw new InvalidOperationException($"Duplicate core entity alias: {alias.CanonicalLogicalName}");
            }
        }

        var relationshipNames = new HashSet<string>(StringComparer.OrdinalIgnoreCase);
        foreach (var relationship in schema.Relationships)
        {
            if (!relationshipNames.Add(relationship.SchemaName))
            {
                throw new InvalidOperationException($"Duplicate relationship schema name: {relationship.SchemaName}");
            }
        }
    }

    private static void ValidateField(FieldSpec field, string entityName)
    {
        if (!field.LogicalName.StartsWith("ccsb_", StringComparison.OrdinalIgnoreCase) ||
            !field.SchemaName.StartsWith("ccsb_", StringComparison.OrdinalIgnoreCase))
        {
            throw new InvalidOperationException($"Field '{entityName}.{field.LogicalName}' does not use the ccsb prefix.");
        }

        if (!SupportedFieldTypes.Contains(field.Type, StringComparer.OrdinalIgnoreCase))
        {
            throw new InvalidOperationException($"Unsupported field type '{field.Type}' on '{entityName}.{field.LogicalName}'.");
        }

        if (field.Type.Equals("Choice", StringComparison.OrdinalIgnoreCase) && field.ChoiceOptions.Count == 0)
        {
            throw new InvalidOperationException($"Choice field '{entityName}.{field.LogicalName}' has no options.");
        }
    }

    private static readonly string[] SupportedFieldTypes =
    [
        "String", "Memo", "Choice", "Boolean", "Integer", "Decimal", "DateOnly", "DateAndTime",
    ];

    private static (int NewTables, int NewTableFields, int Relationships, int ExtensionFields) GetCounts(FoundationSchema schema)
    {
        var newFields = schema.Tables.Sum(t => t.Fields.Count + 1);
        var extensionFields = schema.Extensions.Sum(e => e.Fields.Count);
        return (schema.Tables.Count, newFields, schema.Relationships.Count, extensionFields);
    }
}

internal sealed class FoundationProvisioner
{
    private const int Lcid = 1033;
    private readonly IOrganizationService _service;
    private readonly FoundationSchema _schema;
    private readonly CommandLineOptions _options;
    private readonly HashSet<string> _foundationTableNames;
    private readonly Dictionary<string, string> _resolvedEntityNames = new(StringComparer.OrdinalIgnoreCase);
    private readonly Dictionary<string, CoreEntityAliasSpec> _coreEntityAliases;

    public FoundationProvisioner(IOrganizationService service, FoundationSchema schema, CommandLineOptions options)
    {
        _service = service;
        _schema = schema;
        _options = options;
        _foundationTableNames = new HashSet<string>(
            schema.Tables.Select(table => table.LogicalName),
            StringComparer.OrdinalIgnoreCase);
        _coreEntityAliases = schema.CoreEntityAliases.ToDictionary(
            alias => alias.CanonicalLogicalName,
            StringComparer.OrdinalIgnoreCase);
    }

    public void Run()
    {
        var publisherId = EnsurePublisher();
        EnsureSolution(publisherId);

        // Resolve every non-foundation dependency before changing metadata. This prevents a late
        // failure after creating only part of the foundation schema and avoids assuming that a
        // table's display name is also its logical name.
        ResolveCoreDependenciesOrReport();

        foreach (var table in _schema.Tables)
        {
            EnsureTable(table);
        }

        foreach (var extension in _schema.Extensions)
        {
            var entityLogicalName = ResolveEntityLogicalName(extension.EntityLogicalName);
            foreach (var field in extension.Fields)
            {
                EnsureAttribute(entityLogicalName, field);
            }
        }

        // Relationship creation occurs after all entities and simple attributes exist.
        foreach (var relationship in _schema.Relationships)
        {
            EnsureRelationship(relationship);
        }

        foreach (var table in _schema.Tables)
        {
            foreach (var key in table.AlternateKeys)
            {
                EnsureAlternateKey(table.LogicalName, key);
            }
        }

        ValidateLiveMetadataCompatibility();

        PublishAll();

        if (!_options.SkipExport)
        {
            ExportSolutionPackage();
        }
    }

    public void ValidateLiveOnly()
    {
        ResolveCoreDependenciesOrReport();
        ValidateLiveMetadataCompatibility();
    }

    private void ResolveCoreDependenciesOrReport()
    {
        try
        {
            ResolveCoreDependencies();
        }
        catch (Exception ex)
        {
            if (!string.IsNullOrWhiteSpace(_options.CompatibilityReportPath))
            {
                var diagnostics = new List<SchemaCompatibilityDiagnostic>();
                AddDiagnostic(
                    diagnostics,
                    "CCSB-SCHEMA-CORE-ENTITY-RESOLUTION-FAILED",
                    "Table",
                    ex.Message,
                    expected: "Core dependencies must resolve to logical names outside the foundation table set.",
                    actual: "Core dependency resolution failed.");
                WriteCompatibilityReport(diagnostics);
                PrintCompatibilityDiagnostics(diagnostics);
            }

            throw;
        }
    }

    private void ResolveCoreDependencies()
    {
        var dependencies = new HashSet<string>(StringComparer.OrdinalIgnoreCase);

        foreach (var extension in _schema.Extensions)
        {
            if (!_foundationTableNames.Contains(extension.EntityLogicalName))
            {
                dependencies.Add(extension.EntityLogicalName);
            }
        }

        foreach (var relationship in _schema.Relationships)
        {
            if (!_foundationTableNames.Contains(relationship.ReferencedEntity))
            {
                dependencies.Add(relationship.ReferencedEntity);
            }

            if (!_foundationTableNames.Contains(relationship.ReferencingEntity))
            {
                dependencies.Add(relationship.ReferencingEntity);
            }
        }

        Console.WriteLine("Validating and resolving Core V1 table dependencies.");
        foreach (var dependency in dependencies.OrderBy(name => name, StringComparer.OrdinalIgnoreCase))
        {
            ResolveEntityLogicalName(dependency);
        }
    }

    private Guid EnsurePublisher()
    {
        var existing = RetrieveFirst(
            "publisher",
            new ColumnSet("publisherid", "uniquename", "customizationprefix"),
            new FilterExpression(LogicalOperator.Or)
            {
                Conditions =
                {
                    new ConditionExpression("customizationprefix", ConditionOperator.Equal, _schema.Solution.PublisherPrefix),
                    new ConditionExpression("uniquename", ConditionOperator.Equal, _schema.Solution.PublisherPreferredUniqueName),
                },
            });

        if (existing is not null)
        {
            Console.WriteLine($"Using publisher '{existing.GetAttributeValue<string>("uniquename")}'.");
            return existing.Id;
        }

        var publisher = new Entity("publisher")
        {
            ["friendlyname"] = "Planora",
            ["uniquename"] = _schema.Solution.PublisherPreferredUniqueName,
            ["customizationprefix"] = _schema.Solution.PublisherPrefix,
            ["customizationoptionvalueprefix"] = 83102,
        };

        var publisherId = _service.Create(publisher);
        Console.WriteLine("Created Planora publisher.");
        return publisherId;
    }

    private void EnsureSolution(Guid publisherId)
    {
        var existing = RetrieveFirst(
            "solution",
            new ColumnSet("solutionid", "version", "ismanaged"),
            new FilterExpression(LogicalOperator.And)
            {
                Conditions =
                {
                    new ConditionExpression("uniquename", ConditionOperator.Equal, _schema.Solution.UniqueName),
                },
            });

        if (existing is not null)
        {
            var managed = existing.GetAttributeValue<bool?>("ismanaged") ?? false;
            if (managed)
            {
                throw new InvalidOperationException($"The existing solution '{_schema.Solution.UniqueName}' is managed. Development provisioning requires an unmanaged solution.");
            }

            var update = new Entity("solution", existing.Id)
            {
                ["version"] = _schema.Solution.Version,
            };
            _service.Update(update);
            Console.WriteLine($"Updated unmanaged solution '{_schema.Solution.UniqueName}' to version {_schema.Solution.Version}.");
            return;
        }

        var solution = new Entity("solution")
        {
            ["friendlyname"] = _schema.Solution.DisplayName,
            ["uniquename"] = _schema.Solution.UniqueName,
            ["version"] = _schema.Solution.Version,
            ["description"] = _schema.Solution.Description,
            ["publisherid"] = new EntityReference("publisher", publisherId),
        };
        _service.Create(solution);
        Console.WriteLine($"Created unmanaged solution '{_schema.Solution.UniqueName}'.");
    }

    private void EnsureTable(TableSpec table)
    {
        var existing = TryRetrieveEntity(table.LogicalName, EntityFilters.Entity);
        if (existing is null)
        {
            Console.WriteLine($"Creating table {table.LogicalName}.");
            var ownership = table.Ownership.Equals("OrganizationOwned", StringComparison.OrdinalIgnoreCase)
                ? OwnershipTypes.OrganizationOwned
                : OwnershipTypes.UserOwned;

            var entity = new EntityMetadata
            {
                SchemaName = table.SchemaName,
                DisplayName = Label(table.DisplayName),
                DisplayCollectionName = Label(table.CollectionName),
                Description = Label(table.Description),
                OwnershipType = ownership,
                IsActivity = false,
            };

            var primary = new StringAttributeMetadata
            {
                SchemaName = table.PrimaryName.SchemaName,
                DisplayName = Label(table.PrimaryName.DisplayName),
                Description = Label(table.PrimaryName.Description),
                RequiredLevel = RequiredLevel(true),
                Format = StringFormat.Text,
                MaxLength = table.PrimaryName.MaxLength,
            };

            var request = new CreateEntityRequest
            {
                Entity = entity,
                PrimaryAttribute = primary,
                SolutionUniqueName = _schema.Solution.UniqueName,
            };
            _service.Execute(request);
        }
        else
        {
            Console.WriteLine($"Table {table.LogicalName} already exists; adding missing components only.");
        }

        foreach (var field in table.Fields)
        {
            EnsureAttribute(table.LogicalName, field);
        }
    }

    private string ResolveEntityLogicalName(string declaredLogicalName)
    {
        if (_resolvedEntityNames.TryGetValue(declaredLogicalName, out var resolved))
        {
            return resolved;
        }

        if (_foundationTableNames.Contains(declaredLogicalName))
        {
            _resolvedEntityNames[declaredLogicalName] = declaredLogicalName;
            return declaredLogicalName;
        }

        if (_options.CoreEntityOverrides.TryGetValue(declaredLogicalName, out var overrideLogicalName))
        {
            if (TryRetrieveEntity(overrideLogicalName, EntityFilters.Entity) is null)
            {
                throw new InvalidOperationException(
                    $"Core entity override '{declaredLogicalName}={overrideLogicalName}' was supplied, but table '{overrideLogicalName}' was not found in Dataverse.");
            }

            EnsureCoreResolutionDoesNotUseFoundationName(declaredLogicalName, overrideLogicalName, "explicit override");
            Console.WriteLine($"Resolved Core dependency '{declaredLogicalName}' to '{overrideLogicalName}' using the explicit override.");
            _resolvedEntityNames[declaredLogicalName] = overrideLogicalName;
            return overrideLogicalName;
        }

        if (TryRetrieveEntity(declaredLogicalName, EntityFilters.Entity) is not null)
        {
            _resolvedEntityNames[declaredLogicalName] = declaredLogicalName;
            return declaredLogicalName;
        }

        if (!_coreEntityAliases.TryGetValue(declaredLogicalName, out var alias))
        {
            throw new InvalidOperationException(
                $"Required V1 core table '{declaredLogicalName}' was not found. The provisioner verified the exact logical name and no display-name alias is configured for it.");
        }

        var matches = FindCustomEntitiesByDisplayName(alias.DisplayName);
        if (matches.Count == 1)
        {
            resolved = matches[0].LogicalName!;
            EnsureCoreResolutionDoesNotUseFoundationName(
                declaredLogicalName,
                resolved,
                $"Dataverse display name '{alias.DisplayName}'");
            Console.WriteLine(
                $"Resolved Core dependency '{declaredLogicalName}' to '{resolved}' by Dataverse display name '{alias.DisplayName}'.");
            _resolvedEntityNames[declaredLogicalName] = resolved;
            return resolved;
        }

        if (matches.Count == 0)
        {
            throw new InvalidOperationException(
                $"Required Core V1 table '{declaredLogicalName}' was not found, and no custom table with display name '{alias.DisplayName}' was found. " +
                $"Inspect the table Logical name in Power Apps and rerun with -CoreEntityOverride '{declaredLogicalName}=<actual logical name>'.");
        }

        var matchNames = string.Join(", ", matches.Select(match => match.LogicalName!).OrderBy(name => name, StringComparer.OrdinalIgnoreCase));
        throw new InvalidOperationException(
            $"Multiple custom tables have display name '{alias.DisplayName}': {matchNames}. " +
            $"Rerun with -CoreEntityOverride '{declaredLogicalName}=<actual logical name>'.");
    }

    private void EnsureCoreResolutionDoesNotUseFoundationName(
        string declaredLogicalName,
        string resolvedLogicalName,
        string resolutionSource)
    {
        if (!_foundationTableNames.Contains(resolvedLogicalName))
        {
            return;
        }

        throw new InvalidOperationException(
            $"Core dependency '{declaredLogicalName}' resolved to '{resolvedLogicalName}' using {resolutionSource}, " +
            $"but '{resolvedLogicalName}' is reserved for a foundation table in this schema. " +
            "This is a Core/Foundation logical-name collision; continuing would update an existing Core table as if it were the new foundation table. " +
            $"If the actual Core table has another logical name, rerun with -CoreEntityOverride '{declaredLogicalName}=<actual logical name>'. " +
            "If the Core Schedule Board logical name really is this value, the foundation board table must be renamed in the schema before this package can be safely provisioned.");
    }

    private List<EntityMetadata> FindCustomEntitiesByDisplayName(string displayName)
    {
        var request = new RetrieveAllEntitiesRequest
        {
            EntityFilters = EntityFilters.Entity,
            RetrieveAsIfPublished = true,
        };
        var response = (RetrieveAllEntitiesResponse)_service.Execute(request);

        return response.EntityMetadata
            .Where(entity => entity.IsCustomEntity == true)
            .Where(entity => EntityHasDisplayName(entity, displayName))
            .Where(entity => !string.IsNullOrWhiteSpace(entity.LogicalName))
            .Select(entity => new { Entity = entity, LogicalName = entity.LogicalName! })
            .OrderBy(item => item.LogicalName, StringComparer.OrdinalIgnoreCase)
            .Select(item => item.Entity)
            .ToList();
    }

    private static bool EntityHasDisplayName(EntityMetadata entity, string displayName)
    {
        var labels = entity.DisplayName?.LocalizedLabels ?? [];
        return labels.Any(label => string.Equals(label.Label, displayName, StringComparison.OrdinalIgnoreCase));
    }

    private void EnsureAttribute(string entityLogicalName, FieldSpec field)
    {
        if (TryRetrieveAttribute(entityLogicalName, field.LogicalName) is not null)
        {
            return;
        }

        Console.WriteLine($"  Creating field {entityLogicalName}.{field.LogicalName} ({field.Type}).");
        var request = new CreateAttributeRequest
        {
            EntityName = entityLogicalName,
            Attribute = BuildAttribute(field),
            SolutionUniqueName = _schema.Solution.UniqueName,
        };
        _service.Execute(request);
    }

    private AttributeMetadata BuildAttribute(FieldSpec field)
    {
        var required = RequiredLevel(field.Required);
        var displayName = Label(field.DisplayName);
        var description = Label(field.Description);

        return field.Type.ToLowerInvariant() switch
        {
            "string" => new StringAttributeMetadata
            {
                SchemaName = field.SchemaName,
                DisplayName = displayName,
                Description = description,
                RequiredLevel = required,
                Format = StringFormat.Text,
                MaxLength = field.MaxLength ?? 200,
            },
            "memo" => new MemoAttributeMetadata
            {
                SchemaName = field.SchemaName,
                DisplayName = displayName,
                Description = description,
                RequiredLevel = required,
                Format = StringFormat.TextArea,
                MaxLength = field.MaxLength ?? 100000,
            },
            "choice" => BuildPicklist(field, required, displayName, description),
            "boolean" => new BooleanAttributeMetadata
            {
                SchemaName = field.SchemaName,
                DisplayName = displayName,
                Description = description,
                RequiredLevel = required,
                DefaultValue = field.DefaultValue ?? false,
                OptionSet = new BooleanOptionSetMetadata
                {
                    TrueOption = new OptionMetadata(Label("Yes"), 1),
                    FalseOption = new OptionMetadata(Label("No"), 0),
                },
            },
            "integer" => new IntegerAttributeMetadata
            {
                SchemaName = field.SchemaName,
                DisplayName = displayName,
                Description = description,
                RequiredLevel = required,
                Format = IntegerFormat.None,
                MinValue = field.MinValue is null ? int.MinValue : decimal.ToInt32(field.MinValue.Value),
                MaxValue = field.MaxValue is null ? int.MaxValue : decimal.ToInt32(field.MaxValue.Value),
            },
            "decimal" => new DecimalAttributeMetadata
            {
                SchemaName = field.SchemaName,
                DisplayName = displayName,
                Description = description,
                RequiredLevel = required,
                Precision = field.Precision ?? 2,
                MinValue = field.MinValue ?? decimal.MinValue,
                MaxValue = field.MaxValue ?? decimal.MaxValue,
            },
            "dateonly" => new DateTimeAttributeMetadata
            {
                SchemaName = field.SchemaName,
                DisplayName = displayName,
                Description = description,
                RequiredLevel = required,
                Format = DateTimeFormat.DateOnly,
            },
            "dateandtime" => new DateTimeAttributeMetadata
            {
                SchemaName = field.SchemaName,
                DisplayName = displayName,
                Description = description,
                RequiredLevel = required,
                Format = DateTimeFormat.DateAndTime,
            },
            _ => throw new InvalidOperationException($"Unsupported field type '{field.Type}'."),
        };
    }

    private PicklistAttributeMetadata BuildPicklist(
        FieldSpec field,
        AttributeRequiredLevelManagedProperty required,
        Label displayName,
        Label description)
    {
        var optionSet = new OptionSetMetadata
        {
            IsGlobal = false,
            OptionSetType = OptionSetType.Picklist,
        };

        foreach (var option in field.ChoiceOptions)
        {
            optionSet.Options.Add(new OptionMetadata(Label(option.Label), option.Value));
        }

        return new PicklistAttributeMetadata
        {
            SchemaName = field.SchemaName,
            DisplayName = displayName,
            Description = description,
            RequiredLevel = required,
            OptionSet = optionSet,
        };
    }

    private void EnsureRelationship(RelationshipSpec spec)
    {
        var referencedEntity = ResolveEntityLogicalName(spec.ReferencedEntity);
        var referencingEntity = ResolveEntityLogicalName(spec.ReferencingEntity);

        if (TryRetrieveAttribute(referencingEntity, spec.LookupLogicalName) is not null)
        {
            return;
        }

        Console.WriteLine($"Creating lookup {referencingEntity}.{spec.LookupLogicalName} -> {referencedEntity}.");
        var relationship = new OneToManyRelationshipMetadata
        {
            SchemaName = spec.SchemaName,
            ReferencedEntity = referencedEntity,
            ReferencingEntity = referencingEntity,
            CascadeConfiguration = new CascadeConfiguration
            {
                Assign = CascadeType.NoCascade,
                Delete = CascadeType.Restrict,
                Merge = CascadeType.NoCascade,
                Reparent = CascadeType.NoCascade,
                Share = CascadeType.NoCascade,
                Unshare = CascadeType.NoCascade,
            },
            AssociatedMenuConfiguration = new AssociatedMenuConfiguration
            {
                Behavior = AssociatedMenuBehavior.UseLabel,
                Group = AssociatedMenuGroup.Details,
                Label = Label(spec.CollectionLabel),
                Order = 10000,
            },
        };

        var lookup = new LookupAttributeMetadata
        {
            SchemaName = spec.LookupSchemaName,
            DisplayName = Label(spec.LookupDisplayName),
            Description = Label(spec.Description),
            RequiredLevel = RequiredLevel(false),
            Targets = [referencedEntity],
        };

        var request = new CreateOneToManyRequest
        {
            OneToManyRelationship = relationship,
            Lookup = lookup,
            SolutionUniqueName = _schema.Solution.UniqueName,
        };
        _service.Execute(request);
    }

    private void EnsureAlternateKey(string entityLogicalName, KeySpec key)
    {
        // EntityFilters has no Keys member. Request full metadata because EntityMetadata.Keys
        // is returned only with the complete entity definition.
        var entity = TryRetrieveEntity(entityLogicalName, EntityFilters.All);
        if (entity is null)
        {
            throw new InvalidOperationException($"Cannot create key '{key.SchemaName}' because table '{entityLogicalName}' is missing.");
        }

        var existingKeys = entity.Keys ?? Array.Empty<EntityKeyMetadata>();
        if (existingKeys.Any(k => string.Equals(k.SchemaName, key.SchemaName, StringComparison.OrdinalIgnoreCase)))
        {
            return;
        }

        Console.WriteLine($"Creating alternate key {entityLogicalName}.{key.SchemaName}.");
        var entityKey = new EntityKeyMetadata
        {
            SchemaName = key.SchemaName,
            DisplayName = Label(key.DisplayName),
            KeyAttributes = key.Fields.ToArray(),
        };

        var request = new CreateEntityKeyRequest
        {
            EntityName = entityLogicalName,
            EntityKey = entityKey,
            SolutionUniqueName = _schema.Solution.UniqueName,
        };
        _service.Execute(request);
    }

    private void ValidateLiveMetadataCompatibility()
    {
        Console.WriteLine("Running live Dataverse metadata compatibility validation.");
        var diagnostics = new List<SchemaCompatibilityDiagnostic>();

        ValidateSolutionCompatibility(diagnostics);

        foreach (var table in _schema.Tables)
        {
            var metadata = TryRetrieveEntity(table.LogicalName, EntityFilters.All);
            if (metadata is null)
            {
                AddDiagnostic(
                    diagnostics,
                    "CCSB-SCHEMA-TABLE-MISSING",
                    "Table",
                    $"Expected table '{table.LogicalName}' was not found in Dataverse metadata.",
                    entityLogicalName: table.LogicalName,
                    expected: table.LogicalName,
                    actual: "<missing>");
                continue;
            }

            ValidateTableCompatibility(table, metadata, diagnostics);
        }

        foreach (var extension in _schema.Extensions)
        {
            var entityLogicalName = ResolveEntityLogicalNameForValidation(extension.EntityLogicalName, diagnostics);
            if (entityLogicalName is null)
            {
                continue;
            }

            var metadata = TryRetrieveEntity(entityLogicalName, EntityFilters.All);
            if (metadata is null)
            {
                AddDiagnostic(
                    diagnostics,
                    "CCSB-SCHEMA-EXTENSION-TABLE-MISSING",
                    "Table",
                    $"Expected extension target table '{entityLogicalName}' was not found in Dataverse metadata.",
                    entityLogicalName: entityLogicalName,
                    expected: entityLogicalName,
                    actual: "<missing>");
                continue;
            }

            var attributes = AttributeMap(metadata);
            foreach (var field in extension.Fields)
            {
                ValidateAttributeCompatibility(entityLogicalName, field, attributes, diagnostics);
            }
        }

        foreach (var relationship in _schema.Relationships)
        {
            ValidateRelationshipCompatibility(relationship, diagnostics);
        }

        WriteCompatibilityReport(diagnostics);

        if (diagnostics.Count > 0)
        {
            PrintCompatibilityDiagnostics(diagnostics);
            throw new InvalidOperationException(
                $"Live Dataverse metadata compatibility validation failed with {diagnostics.Count} issue(s). See diagnostics above before publishing or activating this schema.");
        }

        Console.WriteLine("Live Dataverse metadata compatibility validation passed.");
    }

    private void ValidateSolutionCompatibility(List<SchemaCompatibilityDiagnostic> diagnostics)
    {
        var solution = RetrieveFirst(
            "solution",
            new ColumnSet("solutionid", "version", "ismanaged"),
            new FilterExpression(LogicalOperator.And)
            {
                Conditions =
                {
                    new ConditionExpression("uniquename", ConditionOperator.Equal, _schema.Solution.UniqueName),
                },
            });

        if (solution is null)
        {
            AddDiagnostic(
                diagnostics,
                "CCSB-SCHEMA-SOLUTION-MISSING",
                "Solution",
                $"Expected solution '{_schema.Solution.UniqueName}' was not found.",
                expected: _schema.Solution.UniqueName,
                actual: "<missing>");
            return;
        }

        var actualVersion = solution.GetAttributeValue<string>("version") ?? string.Empty;
        if (!string.Equals(actualVersion, _schema.Solution.Version, StringComparison.OrdinalIgnoreCase))
        {
            AddDiagnostic(
                diagnostics,
                "CCSB-SCHEMA-SOLUTION-VERSION-MISMATCH",
                "Solution",
                $"Solution '{_schema.Solution.UniqueName}' version must match the schema package version before export or activation.",
                expected: _schema.Solution.Version,
                actual: string.IsNullOrWhiteSpace(actualVersion) ? "<empty>" : actualVersion);
        }

        if (solution.GetAttributeValue<bool?>("ismanaged") ?? false)
        {
            AddDiagnostic(
                diagnostics,
                "CCSB-SCHEMA-SOLUTION-MANAGED",
                "Solution",
                $"Solution '{_schema.Solution.UniqueName}' is managed. Foundation provisioning and validation must run against the unmanaged DEV layer.",
                expected: "Unmanaged",
                actual: "Managed");
        }
    }

    private void ValidateTableCompatibility(TableSpec table, EntityMetadata metadata, List<SchemaCompatibilityDiagnostic> diagnostics)
    {
        var expectedOwnership = table.Ownership.Equals("OrganizationOwned", StringComparison.OrdinalIgnoreCase)
            ? OwnershipTypes.OrganizationOwned
            : OwnershipTypes.UserOwned;

        if (metadata.OwnershipType != expectedOwnership)
        {
            AddDiagnostic(
                diagnostics,
                "CCSB-SCHEMA-TABLE-OWNERSHIP-MISMATCH",
                "Table",
                $"Table '{table.LogicalName}' ownership is incompatible with the schema contract.",
                entityLogicalName: table.LogicalName,
                expected: expectedOwnership.ToString(),
                actual: metadata.OwnershipType?.ToString() ?? "<null>");
        }

        if (!string.Equals(metadata.PrimaryNameAttribute, table.PrimaryName.LogicalName, StringComparison.OrdinalIgnoreCase))
        {
            AddDiagnostic(
                diagnostics,
                "CCSB-SCHEMA-PRIMARY-NAME-MISMATCH",
                "Field",
                $"Table '{table.LogicalName}' primary name field does not match the schema contract.",
                entityLogicalName: table.LogicalName,
                fieldLogicalName: table.PrimaryName.LogicalName,
                expected: table.PrimaryName.LogicalName,
                actual: string.IsNullOrWhiteSpace(metadata.PrimaryNameAttribute) ? "<missing>" : metadata.PrimaryNameAttribute);
        }

        var attributes = AttributeMap(metadata);
        var primaryField = new FieldSpec
        {
            SchemaName = table.PrimaryName.SchemaName,
            LogicalName = table.PrimaryName.LogicalName,
            DisplayName = table.PrimaryName.DisplayName,
            Type = "String",
            Description = table.PrimaryName.Description,
            Required = true,
            MaxLength = table.PrimaryName.MaxLength,
        };
        ValidateAttributeCompatibility(table.LogicalName, primaryField, attributes, diagnostics);

        foreach (var field in table.Fields)
        {
            ValidateAttributeCompatibility(table.LogicalName, field, attributes, diagnostics);
        }
    }

    private void ValidateAttributeCompatibility(
        string entityLogicalName,
        FieldSpec field,
        IReadOnlyDictionary<string, AttributeMetadata> attributes,
        List<SchemaCompatibilityDiagnostic> diagnostics)
    {
        if (!attributes.TryGetValue(field.LogicalName, out var attribute))
        {
            AddDiagnostic(
                diagnostics,
                "CCSB-SCHEMA-FIELD-MISSING",
                "Field",
                $"Expected field '{entityLogicalName}.{field.LogicalName}' was not found in Dataverse metadata.",
                entityLogicalName: entityLogicalName,
                fieldLogicalName: field.LogicalName,
                expected: field.Type,
                actual: "<missing>");
            return;
        }

        var actualType = DescribeAttributeType(attribute);
        if (!AttributeMatchesType(attribute, field.Type))
        {
            AddDiagnostic(
                diagnostics,
                "CCSB-SCHEMA-FIELD-TYPE-MISMATCH",
                "Field",
                $"Field '{entityLogicalName}.{field.LogicalName}' has an incompatible Dataverse metadata type.",
                entityLogicalName: entityLogicalName,
                fieldLogicalName: field.LogicalName,
                expected: field.Type,
                actual: actualType);
        }

        var actualRequired = IsRequired(attribute);
        if (actualRequired != field.Required)
        {
            AddDiagnostic(
                diagnostics,
                "CCSB-SCHEMA-FIELD-REQUIRED-MISMATCH",
                "Field",
                $"Field '{entityLogicalName}.{field.LogicalName}' required level is incompatible with the schema contract.",
                entityLogicalName: entityLogicalName,
                fieldLogicalName: field.LogicalName,
                expected: field.Required ? "ApplicationRequired" : "None",
                actual: attribute.RequiredLevel?.Value.ToString() ?? "<null>");
        }

        ValidateAttributeConstraints(entityLogicalName, field, attribute, diagnostics);
    }

    private static void ValidateAttributeConstraints(
        string entityLogicalName,
        FieldSpec field,
        AttributeMetadata attribute,
        List<SchemaCompatibilityDiagnostic> diagnostics)
    {
        switch (attribute)
        {
            case StringAttributeMetadata text when field.MaxLength is int expectedMaxLength && text.MaxLength < expectedMaxLength:
                AddFieldConstraintDiagnostic(diagnostics, entityLogicalName, field, "max length", expectedMaxLength.ToString(), text.MaxLength?.ToString() ?? "<null>");
                break;
            case MemoAttributeMetadata memo when field.MaxLength is int expectedMaxLength && memo.MaxLength < expectedMaxLength:
                AddFieldConstraintDiagnostic(diagnostics, entityLogicalName, field, "max length", expectedMaxLength.ToString(), memo.MaxLength?.ToString() ?? "<null>");
                break;
            case DecimalAttributeMetadata number:
                if (field.Precision is int expectedPrecision && number.Precision < expectedPrecision)
                {
                    AddFieldConstraintDiagnostic(diagnostics, entityLogicalName, field, "precision", expectedPrecision.ToString(), number.Precision?.ToString() ?? "<null>");
                }

                ValidateNumericRange(entityLogicalName, field, number.MinValue, number.MaxValue, diagnostics);
                break;
            case IntegerAttributeMetadata number:
                ValidateNumericRange(entityLogicalName, field, number.MinValue, number.MaxValue, diagnostics);
                break;
            case PicklistAttributeMetadata choice:
                ValidateChoiceOptions(entityLogicalName, field, choice, diagnostics);
                break;
            case BooleanAttributeMetadata boolean when field.DefaultValue is bool expectedDefault && boolean.DefaultValue != expectedDefault:
                AddDiagnostic(
                    diagnostics,
                    "CCSB-SCHEMA-FIELD-DEFAULT-MISMATCH",
                    "Field",
                    $"Field '{entityLogicalName}.{field.LogicalName}' default value is incompatible with the schema contract.",
                    entityLogicalName: entityLogicalName,
                    fieldLogicalName: field.LogicalName,
                    expected: expectedDefault.ToString(),
                    actual: boolean.DefaultValue?.ToString() ?? "<null>");
                break;
        }
    }

    private static void ValidateNumericRange(
        string entityLogicalName,
        FieldSpec field,
        decimal? actualMin,
        decimal? actualMax,
        List<SchemaCompatibilityDiagnostic> diagnostics)
    {
        if (field.MinValue is decimal expectedMin && actualMin is decimal min && min > expectedMin)
        {
            AddFieldConstraintDiagnostic(diagnostics, entityLogicalName, field, "minimum value", expectedMin.ToString(), min.ToString());
        }

        if (field.MaxValue is decimal expectedMax && actualMax is decimal max && max < expectedMax)
        {
            AddFieldConstraintDiagnostic(diagnostics, entityLogicalName, field, "maximum value", expectedMax.ToString(), max.ToString());
        }
    }

    private static void ValidateChoiceOptions(
        string entityLogicalName,
        FieldSpec field,
        PicklistAttributeMetadata choice,
        List<SchemaCompatibilityDiagnostic> diagnostics)
    {
        var actualValues = (choice.OptionSet?.Options ?? [])
            .Where(option => option.Value.HasValue)
            .Select(option => option.Value!.Value)
            .ToHashSet();

        foreach (var expectedOption in field.ChoiceOptions)
        {
            if (!actualValues.Contains(expectedOption.Value))
            {
                AddDiagnostic(
                    diagnostics,
                    "CCSB-SCHEMA-CHOICE-OPTION-MISSING",
                    "Field",
                    $"Choice field '{entityLogicalName}.{field.LogicalName}' is missing option value {expectedOption.Value} ({expectedOption.Label}).",
                    entityLogicalName: entityLogicalName,
                    fieldLogicalName: field.LogicalName,
                    expected: $"{expectedOption.Value}={expectedOption.Label}",
                    actual: string.Join(", ", actualValues.OrderBy(value => value)));
            }
        }
    }

    private void ValidateRelationshipCompatibility(RelationshipSpec spec, List<SchemaCompatibilityDiagnostic> diagnostics)
    {
        var referencedEntity = ResolveEntityLogicalNameForValidation(spec.ReferencedEntity, diagnostics);
        var referencingEntity = ResolveEntityLogicalNameForValidation(spec.ReferencingEntity, diagnostics);
        if (referencedEntity is null || referencingEntity is null)
        {
            return;
        }

        var lookup = TryRetrieveAttribute(referencingEntity, spec.LookupLogicalName);
        if (lookup is null)
        {
            AddDiagnostic(
                diagnostics,
                "CCSB-SCHEMA-LOOKUP-FIELD-MISSING",
                "Relationship",
                $"Relationship '{spec.SchemaName}' requires lookup field '{referencingEntity}.{spec.LookupLogicalName}'.",
                entityLogicalName: referencingEntity,
                fieldLogicalName: spec.LookupLogicalName,
                relationshipSchemaName: spec.SchemaName,
                expected: $"Lookup -> {referencedEntity}",
                actual: "<missing>");
        }
        else if (lookup is not LookupAttributeMetadata lookupMetadata)
        {
            AddDiagnostic(
                diagnostics,
                "CCSB-SCHEMA-LOOKUP-FIELD-TYPE-MISMATCH",
                "Relationship",
                $"Relationship '{spec.SchemaName}' lookup field '{referencingEntity}.{spec.LookupLogicalName}' is not a Dataverse lookup.",
                entityLogicalName: referencingEntity,
                fieldLogicalName: spec.LookupLogicalName,
                relationshipSchemaName: spec.SchemaName,
                expected: "Lookup",
                actual: DescribeAttributeType(lookup));
        }
        else if (!lookupMetadata.Targets.Contains(referencedEntity, StringComparer.OrdinalIgnoreCase))
        {
            AddDiagnostic(
                diagnostics,
                "CCSB-SCHEMA-LOOKUP-TARGET-MISMATCH",
                "Relationship",
                $"Relationship '{spec.SchemaName}' lookup field '{referencingEntity}.{spec.LookupLogicalName}' does not target '{referencedEntity}'.",
                entityLogicalName: referencingEntity,
                fieldLogicalName: spec.LookupLogicalName,
                relationshipSchemaName: spec.SchemaName,
                expected: referencedEntity,
                actual: string.Join(", ", lookupMetadata.Targets));
        }

        var relationship = TryRetrieveRelationship(spec.SchemaName);
        if (relationship is null)
        {
            AddDiagnostic(
                diagnostics,
                "CCSB-SCHEMA-RELATIONSHIP-MISSING",
                "Relationship",
                $"Expected Dataverse relationship '{spec.SchemaName}' was not found.",
                relationshipSchemaName: spec.SchemaName,
                expected: $"{referencingEntity} many-to-one {referencedEntity}",
                actual: "<missing>");
            return;
        }

        if (relationship is not OneToManyRelationshipMetadata oneToMany)
        {
            AddDiagnostic(
                diagnostics,
                "CCSB-SCHEMA-RELATIONSHIP-CARDINALITY-MISMATCH",
                "Relationship",
                $"Relationship '{spec.SchemaName}' has incompatible cardinality for the CCSB lookup contract.",
                relationshipSchemaName: spec.SchemaName,
                expected: "OneToMany/ManyToOne lookup relationship",
                actual: relationship.GetType().Name);
            return;
        }

        if (!string.Equals(oneToMany.ReferencedEntity, referencedEntity, StringComparison.OrdinalIgnoreCase) ||
            !string.Equals(oneToMany.ReferencingEntity, referencingEntity, StringComparison.OrdinalIgnoreCase))
        {
            AddDiagnostic(
                diagnostics,
                "CCSB-SCHEMA-RELATIONSHIP-ENDPOINT-MISMATCH",
                "Relationship",
                $"Relationship '{spec.SchemaName}' endpoints are incompatible with the schema contract.",
                relationshipSchemaName: spec.SchemaName,
                expected: $"{referencingEntity} -> {referencedEntity}",
                actual: $"{oneToMany.ReferencingEntity} -> {oneToMany.ReferencedEntity}");
        }

        var deleteCascade = oneToMany.CascadeConfiguration?.Delete;
        if (deleteCascade != CascadeType.Restrict)
        {
            AddDiagnostic(
                diagnostics,
                "CCSB-SCHEMA-RELATIONSHIP-DELETE-BEHAVIOR-MISMATCH",
                "Relationship",
                $"Relationship '{spec.SchemaName}' must use Restrict delete behavior for upgrade-safe CCSB graph metadata.",
                relationshipSchemaName: spec.SchemaName,
                expected: CascadeType.Restrict.ToString(),
                actual: deleteCascade?.ToString() ?? "<null>");
        }
    }

    private string? ResolveEntityLogicalNameForValidation(string declaredLogicalName, List<SchemaCompatibilityDiagnostic> diagnostics)
    {
        try
        {
            return ResolveEntityLogicalName(declaredLogicalName);
        }
        catch (Exception ex)
        {
            AddDiagnostic(
                diagnostics,
                "CCSB-SCHEMA-ENTITY-RESOLUTION-FAILED",
                "Table",
                ex.Message,
                entityLogicalName: declaredLogicalName,
                expected: declaredLogicalName,
                actual: "<unresolved>");
            return null;
        }
    }

    private void WriteCompatibilityReport(IReadOnlyCollection<SchemaCompatibilityDiagnostic> diagnostics)
    {
        var reportPath = _options.CompatibilityReportPath;
        if (string.IsNullOrWhiteSpace(reportPath))
        {
            return;
        }

        var fullPath = Path.GetFullPath(reportPath);
        var directory = Path.GetDirectoryName(fullPath);
        if (!string.IsNullOrWhiteSpace(directory))
        {
            Directory.CreateDirectory(directory);
        }

        var payload = new
        {
            generatedOnUtc = DateTimeOffset.UtcNow,
            status = diagnostics.Count == 0 ? "Passed" : "Failed",
            schemaVersion = _schema.SchemaVersion,
            solution = new
            {
                _schema.Solution.UniqueName,
                _schema.Solution.Version,
            },
            diagnostics = OrderedDiagnostics(diagnostics).ToList(),
        };

        File.WriteAllText(
            fullPath,
            JsonSerializer.Serialize(payload, new JsonSerializerOptions { WriteIndented = true }));
        Console.WriteLine($"Compatibility report written to '{fullPath}'.");
    }

    private static void PrintCompatibilityDiagnostics(IReadOnlyCollection<SchemaCompatibilityDiagnostic> diagnostics)
    {
        Console.Error.WriteLine($"Live Dataverse metadata compatibility validation failed with {diagnostics.Count} issue(s):");
        foreach (var diagnostic in OrderedDiagnostics(diagnostics))
        {
            Console.Error.WriteLine($"  [{diagnostic.Severity}] {diagnostic.Code} {diagnostic.Target}: {diagnostic.Message}");
            if (!string.IsNullOrWhiteSpace(diagnostic.Expected) || !string.IsNullOrWhiteSpace(diagnostic.Actual))
            {
                Console.Error.WriteLine($"      expected: {diagnostic.Expected ?? "<unspecified>"}; actual: {diagnostic.Actual ?? "<unspecified>"}");
            }
        }
    }

    private static IEnumerable<SchemaCompatibilityDiagnostic> OrderedDiagnostics(IEnumerable<SchemaCompatibilityDiagnostic> diagnostics) =>
        diagnostics
            .OrderBy(diagnostic => diagnostic.TargetType, StringComparer.OrdinalIgnoreCase)
            .ThenBy(diagnostic => diagnostic.Target, StringComparer.OrdinalIgnoreCase)
            .ThenBy(diagnostic => diagnostic.Code, StringComparer.OrdinalIgnoreCase);

    private static IReadOnlyDictionary<string, AttributeMetadata> AttributeMap(EntityMetadata metadata) =>
        (metadata.Attributes ?? Array.Empty<AttributeMetadata>())
            .Where(attribute => !string.IsNullOrWhiteSpace(attribute.LogicalName))
            .ToDictionary(attribute => attribute.LogicalName!, StringComparer.OrdinalIgnoreCase);

    private static bool AttributeMatchesType(AttributeMetadata attribute, string expectedType) =>
        expectedType.ToLowerInvariant() switch
        {
            "string" => attribute is StringAttributeMetadata,
            "memo" => attribute is MemoAttributeMetadata,
            "choice" => attribute is PicklistAttributeMetadata,
            "boolean" => attribute is BooleanAttributeMetadata,
            "integer" => attribute is IntegerAttributeMetadata,
            "decimal" => attribute is DecimalAttributeMetadata,
            "dateonly" => attribute is DateTimeAttributeMetadata dateOnly && dateOnly.Format == DateTimeFormat.DateOnly,
            "dateandtime" => attribute is DateTimeAttributeMetadata dateAndTime && dateAndTime.Format == DateTimeFormat.DateAndTime,
            _ => false,
        };

    private static string DescribeAttributeType(AttributeMetadata attribute) =>
        attribute switch
        {
            StringAttributeMetadata => "String",
            MemoAttributeMetadata => "Memo",
            PicklistAttributeMetadata => "Choice",
            BooleanAttributeMetadata => "Boolean",
            IntegerAttributeMetadata => "Integer",
            DecimalAttributeMetadata => "Decimal",
            DateTimeAttributeMetadata dateTime => dateTime.Format == DateTimeFormat.DateOnly ? "DateOnly" : "DateAndTime",
            LookupAttributeMetadata => "Lookup",
            _ => attribute.AttributeType?.ToString() ?? attribute.GetType().Name,
        };

    private static bool IsRequired(AttributeMetadata attribute)
    {
        var requiredLevel = attribute.RequiredLevel?.Value;
        return requiredLevel is AttributeRequiredLevel.ApplicationRequired or AttributeRequiredLevel.SystemRequired;
    }

    private static void AddFieldConstraintDiagnostic(
        List<SchemaCompatibilityDiagnostic> diagnostics,
        string entityLogicalName,
        FieldSpec field,
        string constraint,
        string expected,
        string actual)
    {
        AddDiagnostic(
            diagnostics,
            "CCSB-SCHEMA-FIELD-CONSTRAINT-MISMATCH",
            "Field",
            $"Field '{entityLogicalName}.{field.LogicalName}' {constraint} is incompatible with the schema contract.",
            entityLogicalName: entityLogicalName,
            fieldLogicalName: field.LogicalName,
            expected: expected,
            actual: actual);
    }

    private static void AddDiagnostic(
        List<SchemaCompatibilityDiagnostic> diagnostics,
        string code,
        string targetType,
        string message,
        string? entityLogicalName = null,
        string? fieldLogicalName = null,
        string? relationshipSchemaName = null,
        string? expected = null,
        string? actual = null)
    {
        diagnostics.Add(new SchemaCompatibilityDiagnostic
        {
            Code = code,
            Severity = "Error",
            TargetType = targetType,
            EntityLogicalName = entityLogicalName,
            FieldLogicalName = fieldLogicalName,
            RelationshipSchemaName = relationshipSchemaName,
            Expected = expected,
            Actual = actual,
            Message = message,
        });
    }

    private void PublishAll()
    {
        Console.WriteLine("Publishing customizations.");
        _service.Execute(new CrmSdkMessages.PublishAllXmlRequest());
    }

    private void ExportSolutionPackage()
    {
        var exportPath = _options.ExportPath
            ?? Path.Combine(
                Environment.CurrentDirectory,
                "out",
                _options.ExportManaged
                    ? "CCSB_FoundationSchema_1_0_0_1_managed.zip"
                    : "CCSB_FoundationSchema_1_0_0_1_unmanaged.zip");
        Directory.CreateDirectory(Path.GetDirectoryName(Path.GetFullPath(exportPath))!);

        var packageType = _options.ExportManaged ? "managed" : "unmanaged";
        Console.WriteLine($"Exporting {packageType} solution to '{exportPath}'.");
        var request = new CrmSdkMessages.ExportSolutionRequest
        {
            SolutionName = _schema.Solution.UniqueName,
            Managed = _options.ExportManaged,
        };
        var response = (CrmSdkMessages.ExportSolutionResponse)_service.Execute(request);
        var content = response.ExportSolutionFile;
        if (content is null || content.Length == 0)
        {
            throw new InvalidOperationException("Dataverse did not return ExportSolutionFile.");
        }

        File.WriteAllBytes(exportPath, content);
        Console.WriteLine($"Export complete: {new FileInfo(exportPath).Length:N0} bytes.");
    }

    private Entity? RetrieveFirst(string entityName, ColumnSet columns, FilterExpression criteria)
    {
        var query = new QueryExpression(entityName)
        {
            ColumnSet = columns,
            Criteria = criteria,
            TopCount = 1,
        };
        return _service.RetrieveMultiple(query).Entities.FirstOrDefault();
    }

    private EntityMetadata? TryRetrieveEntity(string logicalName, EntityFilters filters)
    {
        try
        {
            var request = new RetrieveEntityRequest
            {
                LogicalName = logicalName,
                EntityFilters = filters,
                RetrieveAsIfPublished = true,
            };
            var response = (RetrieveEntityResponse)_service.Execute(request);
            return response.EntityMetadata;
        }
        catch (Exception ex) when (IsNotFound(ex))
        {
            return null;
        }
    }

    private AttributeMetadata? TryRetrieveAttribute(string entityLogicalName, string attributeLogicalName)
    {
        try
        {
            var request = new RetrieveAttributeRequest
            {
                EntityLogicalName = entityLogicalName,
                LogicalName = attributeLogicalName,
                RetrieveAsIfPublished = true,
            };
            var response = (RetrieveAttributeResponse)_service.Execute(request);
            return response.AttributeMetadata;
        }
        catch (Exception ex) when (IsNotFound(ex))
        {
            return null;
        }
    }

    private RelationshipMetadataBase? TryRetrieveRelationship(string schemaName)
    {
        try
        {
            var request = new RetrieveRelationshipRequest
            {
                Name = schemaName,
                RetrieveAsIfPublished = true,
            };
            var response = (RetrieveRelationshipResponse)_service.Execute(request);
            return response.RelationshipMetadata;
        }
        catch (Exception ex) when (IsNotFound(ex))
        {
            return null;
        }
    }

    private static bool IsNotFound(Exception ex)
    {
        var message = ex.ToString();
        return message.Contains("does not exist", StringComparison.OrdinalIgnoreCase)
            || message.Contains("not found", StringComparison.OrdinalIgnoreCase)
            || message.Contains("Could not find", StringComparison.OrdinalIgnoreCase);
    }

    private static Label Label(string text) => new(text, Lcid);

    private static AttributeRequiredLevelManagedProperty RequiredLevel(bool required) =>
        new(required ? AttributeRequiredLevel.ApplicationRequired : AttributeRequiredLevel.None);
}

internal sealed class CommandLineOptions
{
    public const string DefaultInteractiveAppId = "51f81489-12ee-4a9e-aaae-a2591f45987d";
    public const string DefaultInteractiveRedirectUri = "http://localhost";

    public string? ConnectionString { get; init; }
    public string? EnvironmentUrl { get; init; }
    public string? Username { get; init; }
    public string? AppId { get; init; }
    public string? RedirectUri { get; init; }
    public string? TokenCacheStorePath { get; init; }
    public string? SchemaPath { get; init; }
    public string? ExportPath { get; init; }
    public string? CompatibilityReportPath { get; init; }
    public bool ExportManaged { get; init; }
    public bool SkipExport { get; init; }
    public bool WhatIf { get; init; }
    public bool ValidateLiveOnly { get; init; }
    public required Dictionary<string, string> CoreEntityOverrides { get; init; }

    public static CommandLineOptions Parse(string[] args)
    {
        string? connection = null;
        string? environmentUrl = null;
        string? username = null;
        string? appId = null;
        string? redirectUri = null;
        string? tokenCacheStorePath = null;
        string? schema = null;
        string? export = null;
        string? compatibilityReport = null;
        var exportManaged = false;
        var skipExport = false;
        var whatIf = false;
        var validateLiveOnly = false;
        var coreEntityOverrides = new Dictionary<string, string>(StringComparer.OrdinalIgnoreCase);

        for (var index = 0; index < args.Length; index++)
        {
            switch (args[index])
            {
                case "--connection":
                    connection = RequireValue(args, ref index, "--connection");
                    break;
                case "--environment-url":
                    environmentUrl = RequireValue(args, ref index, "--environment-url");
                    break;
                case "--username":
                    username = RequireValue(args, ref index, "--username");
                    break;
                case "--app-id":
                    appId = RequireValue(args, ref index, "--app-id");
                    break;
                case "--redirect-uri":
                    redirectUri = RequireValue(args, ref index, "--redirect-uri");
                    break;
                case "--token-cache-store-path":
                    tokenCacheStorePath = RequireValue(args, ref index, "--token-cache-store-path");
                    break;
                case "--schema":
                    schema = RequireValue(args, ref index, "--schema");
                    break;
                case "--export":
                    export = RequireValue(args, ref index, "--export");
                    break;
                case "--compatibility-report":
                    compatibilityReport = RequireValue(args, ref index, "--compatibility-report");
                    break;
                case "--export-managed":
                    exportManaged = true;
                    break;
                case "--core-entity-override":
                    AddCoreEntityOverride(coreEntityOverrides, RequireValue(args, ref index, "--core-entity-override"));
                    break;
                case "--skip-export":
                    skipExport = true;
                    break;
                case "--validate-live-only":
                    validateLiveOnly = true;
                    break;
                case "--what-if":
                    whatIf = true;
                    break;
                case "--help":
                case "-h":
                    PrintHelpAndExit();
                    break;
                default:
                    throw new ArgumentException($"Unknown argument '{args[index]}'. Use --help for supported options.");
            }
        }

        if (!string.IsNullOrWhiteSpace(connection) && !string.IsNullOrWhiteSpace(environmentUrl))
        {
            throw new ArgumentException("Use either --connection or --environment-url, not both.");
        }

        if (whatIf && validateLiveOnly)
        {
            throw new ArgumentException("Use either --what-if for static schema validation or --validate-live-only for connected metadata validation, not both.");
        }

        return new CommandLineOptions
        {
            ConnectionString = connection,
            EnvironmentUrl = environmentUrl,
            Username = username,
            AppId = appId,
            RedirectUri = redirectUri,
            TokenCacheStorePath = tokenCacheStorePath,
            SchemaPath = schema,
            ExportPath = export,
            CompatibilityReportPath = compatibilityReport,
            ExportManaged = exportManaged,
            SkipExport = skipExport,
            WhatIf = whatIf,
            ValidateLiveOnly = validateLiveOnly,
            CoreEntityOverrides = coreEntityOverrides,
        };
    }

    private static void AddCoreEntityOverride(Dictionary<string, string> target, string value)
    {
        var separatorIndex = value.IndexOf('=');
        if (separatorIndex <= 0 || separatorIndex == value.Length - 1)
        {
            throw new ArgumentException(
                "--core-entity-override must use the format <expected logical name>=<actual logical name>.");
        }

        var expected = value[..separatorIndex].Trim();
        var actual = value[(separatorIndex + 1)..].Trim();
        if (expected.Length == 0 || actual.Length == 0)
        {
            throw new ArgumentException(
                "--core-entity-override must use the format <expected logical name>=<actual logical name>.");
        }

        if (!target.TryAdd(expected, actual))
        {
            throw new ArgumentException($"Duplicate --core-entity-override supplied for '{expected}'.");
        }
    }

    private static string RequireValue(string[] args, ref int index, string argument)
    {
        if (index + 1 >= args.Length || args[index + 1].StartsWith("--", StringComparison.Ordinal))
        {
            throw new ArgumentException($"{argument} requires a value.");
        }
        index++;
        return args[index];
    }

    private static void PrintHelpAndExit()
    {
        Console.WriteLine($"""
CCSB Foundation Schema Provisioner

Usage:
  dotnet run --project CCSB.FoundationSchema.Provisioner.csproj -- [options]

Connection options (choose one):
  --connection <Dataverse connection string>  Use an existing supported Dataverse connection string.
  DATAVERSE_CONNECTION_STRING                 Environment-variable alternative to --connection.
  --environment-url <https://org.crm.dynamics.com>
      [--username <user@tenant.onmicrosoft.com>]
      [--app-id <Entra application client ID>]
      [--redirect-uri http://localhost]
      [--token-cache-store-path <path>]
                                            Interactive OAuth sign-in. A browser window opens.

Core table resolution:
  --core-entity-override <expected>=<actual>
      Explicitly maps an expected Core logical name to the actual target logical name.
      The default schema automatically resolves ccsb_scheduleboard by the display name
      'Schedule Board' if that exact logical name is absent.

Other options:
  --schema <path>                           Override schema JSON path.
  --export <path>                           Solution ZIP output path.
  --export-managed                          Export a managed solution ZIP for TEST/PROD import.
  --compatibility-report <path>             Write live metadata validation diagnostics as JSON.
  --skip-export                             Create/update metadata but do not export a ZIP.
  --validate-live-only                      Validate connected Dataverse metadata without changing it.
  --what-if                                 Validate the schema only; no Dataverse changes.
  --help                                    Show this help.

Interactive example:
  dotnet run -- --environment-url https://org.crm.dynamics.com --username user@tenant.onmicrosoft.com

Notes:
  Interactive .NET OAuth requires a loopback redirect URI. The default is http://localhost.
  The default sample client ID is for development/prototyping. Use your tenant-owned app registration for production.
""");
        Environment.Exit(0);
    }
}

internal sealed class FoundationSchema
{
    public required string SchemaVersion { get; init; }
    public required SolutionSpec Solution { get; init; }
    public required List<TableSpec> Tables { get; init; }
    public required List<RelationshipSpec> Relationships { get; init; }
    public required List<EntityExtensionSpec> Extensions { get; init; }
    public required List<CoreEntityAliasSpec> CoreEntityAliases { get; init; }
}

internal sealed class SolutionSpec
{
    public required string UniqueName { get; init; }
    public required string DisplayName { get; init; }
    public required string Version { get; init; }
    public required string PublisherPrefix { get; init; }
    public required string PublisherPreferredUniqueName { get; init; }
    public required string Description { get; init; }
}

internal sealed class TableSpec
{
    public required string SchemaName { get; init; }
    public required string LogicalName { get; init; }
    public required string DisplayName { get; init; }
    public required string CollectionName { get; init; }
    public required string Ownership { get; init; }
    public required string Description { get; init; }
    public required PrimaryNameSpec PrimaryName { get; init; }
    public required List<FieldSpec> Fields { get; init; }
    public required List<KeySpec> AlternateKeys { get; init; }
}

internal sealed class PrimaryNameSpec
{
    public required string SchemaName { get; init; }
    public required string LogicalName { get; init; }
    public required string DisplayName { get; init; }
    public required string Description { get; init; }
    public int MaxLength { get; init; } = 200;
}

internal sealed class FieldSpec
{
    public required string SchemaName { get; init; }
    public required string LogicalName { get; init; }
    public required string DisplayName { get; init; }
    public required string Type { get; init; }
    public required string Description { get; init; }
    public bool Required { get; init; }
    public int? MaxLength { get; init; }
    public int? Precision { get; init; }
    public decimal? MinValue { get; init; }
    public decimal? MaxValue { get; init; }
    public bool? DefaultValue { get; init; }
    public List<ChoiceOptionSpec> ChoiceOptions { get; init; } = [];
}

internal sealed class ChoiceOptionSpec
{
    public int Value { get; init; }
    public required string Label { get; init; }
}

internal sealed class KeySpec
{
    public required string SchemaName { get; init; }
    public required string DisplayName { get; init; }
    public required List<string> Fields { get; init; }
}

internal sealed class RelationshipSpec
{
    public required string SchemaName { get; init; }
    public required string ReferencedEntity { get; init; }
    public required string ReferencingEntity { get; init; }
    public required string LookupSchemaName { get; init; }
    public required string LookupLogicalName { get; init; }
    public required string LookupDisplayName { get; init; }
    public required string Description { get; init; }
    public required string CollectionLabel { get; init; }
}

internal sealed class EntityExtensionSpec
{
    public required string EntityLogicalName { get; init; }
    public required List<FieldSpec> Fields { get; init; }
}

internal sealed class CoreEntityAliasSpec
{
    public required string CanonicalLogicalName { get; init; }
    public required string DisplayName { get; init; }
    public string? Description { get; init; }
}

internal sealed class SchemaCompatibilityDiagnostic
{
    public required string Code { get; init; }
    public required string Severity { get; init; }
    public required string TargetType { get; init; }
    public string? EntityLogicalName { get; init; }
    public string? FieldLogicalName { get; init; }
    public string? RelationshipSchemaName { get; init; }
    public string? Expected { get; init; }
    public string? Actual { get; init; }
    public required string Message { get; init; }

    public string Target
    {
        get
        {
            if (!string.IsNullOrWhiteSpace(RelationshipSchemaName))
            {
                return RelationshipSchemaName;
            }

            if (!string.IsNullOrWhiteSpace(EntityLogicalName) && !string.IsNullOrWhiteSpace(FieldLogicalName))
            {
                return $"{EntityLogicalName}.{FieldLogicalName}";
            }

            return EntityLogicalName ?? TargetType;
        }
    }
}

using System.Security.Cryptography;
using System.Text;
using System.Text.Json;
using System.Xml.Linq;
using Microsoft.Identity.Client;
using Microsoft.PowerPlatform.Dataverse.Client;
using Microsoft.Xrm.Sdk;
using Microsoft.Xrm.Sdk.Messages;
using Microsoft.Xrm.Sdk.Metadata;
using Microsoft.Xrm.Sdk.Query;
using CrmSdkMessages = Microsoft.Crm.Sdk.Messages;

namespace CSB.AuditEntities.Provisioner;

internal static class Program
{
    internal const int EntityComponentType = 1;
    internal const int SavedQueryComponentType = 26;
    internal const int MainFormComponentType = 60;
    internal const int MainFormType = 2;

    private static readonly JsonSerializerOptions JsonOptions = new()
    {
        PropertyNameCaseInsensitive = true,
        ReadCommentHandling = JsonCommentHandling.Skip,
        AllowTrailingCommas = true,
    };

    public static int Main(string[] args)
    {
        try
        {
            var options = ProvisionerOptions.Parse(args);
            var schemaPath = options.SchemaPath ?? Path.Combine(AppContext.BaseDirectory, "schema", "csb.auditentities.schema.json");

            if (!File.Exists(schemaPath))
            {
                throw new FileNotFoundException("The audit-entities schema manifest was not found.", schemaPath);
            }

            var schema = JsonSerializer.Deserialize<AuditEntitiesSchema>(File.ReadAllText(schemaPath), JsonOptions)
                ?? throw new InvalidOperationException("Unable to deserialize the audit-entities schema manifest.");

            ValidateSchema(schema);
            var simpleFields = schema.Tables.Sum(table => table.Fields.Count);
            var lookupFields = schema.Relationships.Count;
            var totalColumns = simpleFields + lookupFields + schema.Tables.Count * 2;
            var views = schema.Tables.Sum(table => table.Views.Count);

            Console.WriteLine($"Solution: {schema.Solution.DisplayName} ({schema.Solution.UniqueName}) v{schema.Solution.Version}");
            Console.WriteLine($"Tables: {schema.Tables.Count}; simple fields: {simpleFields}; lookup relationships: {lookupFields}; expected total columns including primary id/name: {totalColumns}; forms: {schema.Tables.Count}; views: {views}.");

            if (options.WhatIf)
            {
                Console.WriteLine("What-if complete. Manifest validation passed; no Dataverse metadata was changed.");
                return 0;
            }

            using var service = options.CreateServiceClient();
            if (!service.IsReady)
            {
                throw new InvalidOperationException($"Dataverse connection failed: {service.LastError}");
            }

            new AuditEntitiesProvisioner(service, schema, options).Run();
            Console.WriteLine("CSB Audit Entities provisioning completed successfully.");
            return 0;
        }
        catch (Exception exception)
        {
            Console.Error.WriteLine(exception);
            return 1;
        }
    }

    private static void ValidateSchema(AuditEntitiesSchema schema)
    {
        if (string.IsNullOrWhiteSpace(schema.Solution.UniqueName) ||
            !schema.Solution.UniqueName.StartsWith("CSB", StringComparison.Ordinal))
        {
            throw new InvalidOperationException("The solution unique name must be present and start with CSB.");
        }

        if (string.IsNullOrWhiteSpace(schema.Solution.DisplayName) ||
            !schema.Solution.DisplayName.StartsWith("CSB", StringComparison.Ordinal))
        {
            throw new InvalidOperationException("The solution display name must be present and start with CSB.");
        }

        if (schema.Solution.PublisherPrefix != "ccsb")
        {
            throw new InvalidOperationException("The publisher prefix must remain ccsb to match the CCSB canonical logical names.");
        }

        var tableNames = new HashSet<string>(StringComparer.OrdinalIgnoreCase);
        foreach (var table in schema.Tables)
        {
            if (!tableNames.Add(table.LogicalName))
            {
                throw new InvalidOperationException($"Duplicate table logical name '{table.LogicalName}'.");
            }

            if (!table.LogicalName.StartsWith("ccsb_", StringComparison.Ordinal) ||
                table.LogicalName != table.LogicalName.ToLowerInvariant())
            {
                throw new InvalidOperationException($"Table '{table.LogicalName}' must be lowercase and start with ccsb_.");
            }

            if (table.Ownership is not ("UserOwned" or "OrganizationOwned"))
            {
                throw new InvalidOperationException($"Table '{table.LogicalName}' has unsupported ownership '{table.Ownership}'.");
            }

            var fieldNames = new HashSet<string>(StringComparer.OrdinalIgnoreCase)
            {
                table.PrimaryName.LogicalName,
            };

            foreach (var field in table.Fields)
            {
                if (!field.LogicalName.StartsWith("ccsb_", StringComparison.Ordinal) ||
                    field.LogicalName != field.LogicalName.ToLowerInvariant())
                {
                    throw new InvalidOperationException($"Field '{table.LogicalName}.{field.LogicalName}' must be lowercase and start with ccsb_.");
                }

                if (!fieldNames.Add(field.LogicalName))
                {
                    throw new InvalidOperationException($"Duplicate field '{table.LogicalName}.{field.LogicalName}'.");
                }

                if (field.Type.Equals("Choice", StringComparison.OrdinalIgnoreCase) && field.ChoiceOptions.Count == 0)
                {
                    throw new InvalidOperationException($"Choice field '{table.LogicalName}.{field.LogicalName}' has no options.");
                }
            }

            foreach (var key in table.AlternateKeys)
            {
                if (key.Fields.Count == 0)
                {
                    throw new InvalidOperationException($"Alternate key '{key.SchemaName}' on '{table.LogicalName}' has no fields.");
                }
            }
        }

        var relationships = new HashSet<string>(StringComparer.OrdinalIgnoreCase);
        foreach (var relationship in schema.Relationships)
        {
            if (!relationships.Add(relationship.SchemaName))
            {
                throw new InvalidOperationException($"Duplicate relationship schema name '{relationship.SchemaName}'.");
            }

            if (!relationship.SchemaName.StartsWith("ccsb_", StringComparison.Ordinal))
            {
                throw new InvalidOperationException($"Relationship '{relationship.SchemaName}' must start with ccsb_.");
            }

            if (!tableNames.Contains(relationship.ReferencingEntity))
            {
                throw new InvalidOperationException($"Relationship '{relationship.SchemaName}' references unknown source table '{relationship.ReferencingEntity}'.");
            }
        }
    }
}

internal sealed class AuditEntitiesProvisioner
{
    private const int Lcid = 1033;
    private const string TextControl = "{4273EDBD-AC1D-40D3-9FB2-095C621B552D}";
    private const string MultilineTextControl = "{E0DECE4B-6FC8-4A8F-A065-082708572369}";
    private const string LookupControl = "{270BD3DB-D9AF-4782-9025-509E298DEC0A}";
    private const string ChoiceControl = "{3EF39988-22BB-4F0B-BBBE-64B5A3748AEE}";
    private const string StatusControl = "{5D68B988-0661-4DB2-BC3E-17598AD3BE6C}";
    private const string DateTimeControl = "{5B773807-9FB2-42DB-97C3-7A91EFF8ADFF}";
    private const string WholeNumberControl = "{C6D124CA-7EDA-4A60-AEA9-7FB8D318B68F}";
    private const string DecimalControl = "{C3EFE0C3-0EC6-42BE-8349-CBD9079C5A6F}";
    private const string BooleanControl = "{67FAC785-CD58-4F9F-ABB3-4B7DDC6ED5ED}";

    private readonly IOrganizationService _service;
    private readonly AuditEntitiesSchema _schema;
    private readonly ProvisionerOptions _options;
    private readonly Dictionary<string, EntityMetadata> _metadataCache = new(StringComparer.OrdinalIgnoreCase);
    private Guid _solutionId;

    public AuditEntitiesProvisioner(IOrganizationService service, AuditEntitiesSchema schema, ProvisionerOptions options)
    {
        _service = service;
        _schema = schema;
        _options = options;
    }

    public void Run()
    {
        var publisherId = EnsurePublisher();
        _solutionId = EnsureSolution(publisherId);

        foreach (var table in _schema.Tables)
        {
            EnsureTable(table);
        }

        foreach (var table in _schema.Tables)
        {
            foreach (var field in table.Fields)
            {
                EnsureAttribute(table.LogicalName, field);
            }
        }

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

        PublishAll();
        _metadataCache.Clear();

        foreach (var table in _schema.Tables)
        {
            var metadata = RequireEntity(table.LogicalName, EntityFilters.All);
            EnsureTableInSolution(metadata);
            EnsureMainForm(table, metadata);
            foreach (var view in table.Views)
            {
                EnsureView(table, metadata, view);
            }
        }

        PublishChangedEntities(_schema.Tables.Select(table => table.LogicalName));

        if (!_options.SkipExport)
        {
            ExportUnmanagedSolution();
        }
    }

    private Guid EnsurePublisher()
    {
        var query = new QueryExpression("publisher")
        {
            ColumnSet = new ColumnSet("publisherid", "uniquename", "friendlyname", "customizationprefix"),
            Criteria = new FilterExpression(LogicalOperator.Or),
            TopCount = 1,
        };
        query.Criteria.AddCondition("customizationprefix", ConditionOperator.Equal, _schema.Solution.PublisherPrefix);
        query.Criteria.AddCondition("uniquename", ConditionOperator.Equal, _schema.Solution.PublisherPreferredUniqueName);

        var existing = _service.RetrieveMultiple(query).Entities.FirstOrDefault();
        if (existing is not null)
        {
            Console.WriteLine($"Using publisher '{existing.GetAttributeValue<string>("uniquename")}' with prefix '{existing.GetAttributeValue<string>("customizationprefix")}'.");
            return existing.Id;
        }

        Console.WriteLine($"Creating publisher '{_schema.Solution.PublisherPreferredUniqueName}' with prefix '{_schema.Solution.PublisherPrefix}'.");
        var publisher = new Entity("publisher")
        {
            ["uniquename"] = _schema.Solution.PublisherPreferredUniqueName,
            ["friendlyname"] = _schema.Solution.PublisherFriendlyName,
            ["customizationprefix"] = _schema.Solution.PublisherPrefix,
            ["customizationoptionvalueprefix"] = 83103,
            ["description"] = "Publisher for CSB/CCSB audit and schedule-control schema components.",
        };

        return _service.Create(publisher);
    }

    private Guid EnsureSolution(Guid publisherId)
    {
        var query = new QueryExpression("solution")
        {
            ColumnSet = new ColumnSet("solutionid", "uniquename", "friendlyname", "version", "ismanaged"),
            Criteria = new FilterExpression(LogicalOperator.And),
            TopCount = 1,
        };
        query.Criteria.AddCondition("uniquename", ConditionOperator.Equal, _schema.Solution.UniqueName);

        var existing = _service.RetrieveMultiple(query).Entities.FirstOrDefault();
        if (existing is not null)
        {
            if (existing.GetAttributeValue<bool>("ismanaged"))
            {
                throw new InvalidOperationException($"Solution '{_schema.Solution.UniqueName}' already exists as managed. Use an unmanaged solution for this provisioner.");
            }

            Console.WriteLine($"Updating unmanaged solution '{_schema.Solution.UniqueName}'.");
            _service.Update(new Entity("solution", existing.Id)
            {
                ["friendlyname"] = _schema.Solution.DisplayName,
                ["version"] = _schema.Solution.Version,
                ["description"] = _schema.Solution.Description,
            });
            return existing.Id;
        }

        Console.WriteLine($"Creating unmanaged solution '{_schema.Solution.DisplayName}'.");
        return _service.Create(new Entity("solution")
        {
            ["uniquename"] = _schema.Solution.UniqueName,
            ["friendlyname"] = _schema.Solution.DisplayName,
            ["version"] = _schema.Solution.Version,
            ["description"] = _schema.Solution.Description,
            ["publisherid"] = new EntityReference("publisher", publisherId),
        });
    }

    private void EnsureTable(TableSpec table)
    {
        var expectedOwnership = table.Ownership.Equals("OrganizationOwned", StringComparison.OrdinalIgnoreCase)
            ? OwnershipTypes.OrganizationOwned
            : OwnershipTypes.UserOwned;

        var existing = TryRetrieveEntity(table.LogicalName, EntityFilters.Entity);
        if (existing is not null)
        {
            if (existing.OwnershipType != expectedOwnership)
            {
                throw new InvalidOperationException(
                    $"Table '{table.LogicalName}' already exists with ownership '{existing.OwnershipType}', but the optimized CSB design requires '{expectedOwnership}'. " +
                    "Dataverse table ownership cannot be changed after creation; recreate the table before provisioning production metadata.");
            }

            Console.WriteLine($"Table {table.LogicalName} already exists; adding missing components only.");
            EnsureTableInSolution(existing);
            return;
        }

        Console.WriteLine($"Creating table {table.LogicalName} ({table.Ownership}).");
        var entity = new EntityMetadata
        {
            SchemaName = table.SchemaName,
            DisplayName = Label(table.DisplayName),
            DisplayCollectionName = Label(table.CollectionName),
            Description = Label(table.Description),
            OwnershipType = expectedOwnership,
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

        _service.Execute(new CreateEntityRequest
        {
            Entity = entity,
            PrimaryAttribute = primary,
            SolutionUniqueName = _schema.Solution.UniqueName,
        });
    }

    private void EnsureAttribute(string entityLogicalName, FieldSpec field)
    {
        if (TryRetrieveAttribute(entityLogicalName, field.LogicalName) is not null)
        {
            return;
        }

        Console.WriteLine($"  Creating field {entityLogicalName}.{field.LogicalName} ({field.Type}).");
        _service.Execute(new CreateAttributeRequest
        {
            EntityName = entityLogicalName,
            Attribute = BuildAttribute(field),
            SolutionUniqueName = _schema.Solution.UniqueName,
        });
    }

    private AttributeMetadata BuildAttribute(FieldSpec field)
    {
        var required = RequiredLevel(field.Required);
        var displayName = Label(field.DisplayName);
        var description = Label(field.Description);

        AttributeMetadata attribute = field.Type.ToLowerInvariant() switch
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
                MinValue = field.MinValue is null ? 0 : decimal.ToInt32(field.MinValue.Value),
                MaxValue = field.MaxValue is null ? int.MaxValue : decimal.ToInt32(field.MaxValue.Value),
            },
            "decimal" => new DecimalAttributeMetadata
            {
                SchemaName = field.SchemaName,
                DisplayName = displayName,
                Description = description,
                RequiredLevel = required,
                Precision = field.Precision ?? 2,
                MinValue = field.MinValue ?? -100000000,
                MaxValue = field.MaxValue ?? 100000000,
            },
            "datetime" => new DateTimeAttributeMetadata
            {
                SchemaName = field.SchemaName,
                DisplayName = displayName,
                Description = description,
                RequiredLevel = required,
                Format = DateTimeFormat.DateAndTime,
            },
            _ => throw new InvalidOperationException($"Unsupported field type '{field.Type}' for '{field.LogicalName}'."),
        };

        attribute.IsSecured = field.IsSecured;
        return attribute;
    }

    private static PicklistAttributeMetadata BuildPicklist(
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

    private void EnsureRelationship(RelationshipSpec relationship)
    {
        var source = RequireEntity(relationship.ReferencingEntity, EntityFilters.Entity);
        var target = TryRetrieveEntity(relationship.ReferencedEntity, EntityFilters.Entity);
        if (target is null)
        {
            var message = $"Relationship '{relationship.SchemaName}' requires target table '{relationship.ReferencedEntity}', which was not found.";
            if (_options.SkipMissingRelationshipTargets || !relationship.FailIfTargetMissing)
            {
                Console.WriteLine($"Skipping: {message}");
                return;
            }

            throw new InvalidOperationException(message + " Import or create the dependency first, or rerun with --skip-missing-relationship-targets for a partial schema pass.");
        }

        if (TryRetrieveAttribute(source.LogicalName!, relationship.LookupLogicalName) is not null)
        {
            return;
        }

        Console.WriteLine($"Creating relationship {relationship.LookupLogicalName}: {relationship.ReferencingEntity} -> {relationship.ReferencedEntity}.");
        var metadata = new OneToManyRelationshipMetadata
        {
            SchemaName = relationship.SchemaName,
            ReferencedEntity = target.LogicalName,
            ReferencingEntity = source.LogicalName,
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
                Label = Label(relationship.CollectionLabel),
                Order = 10000,
            },
        };

        var lookup = new LookupAttributeMetadata
        {
            SchemaName = relationship.LookupSchemaName,
            DisplayName = Label(relationship.LookupDisplayName),
            Description = Label(relationship.Description),
            RequiredLevel = RequiredLevel(relationship.Required),
            Targets = new[] { target.LogicalName! },
        };

        _service.Execute(new CreateOneToManyRequest
        {
            OneToManyRelationship = metadata,
            Lookup = lookup,
            SolutionUniqueName = _schema.Solution.UniqueName,
        });
    }

    private void EnsureAlternateKey(string entityLogicalName, AlternateKeySpec key)
    {
        var entity = RequireEntity(entityLogicalName, EntityFilters.All);
        if ((entity.Keys ?? Array.Empty<EntityKeyMetadata>())
            .Any(existing => string.Equals(existing.SchemaName, key.SchemaName, StringComparison.OrdinalIgnoreCase)))
        {
            return;
        }

        Console.WriteLine($"Creating alternate key {entityLogicalName}.{key.SchemaName}.");
        _service.Execute(new CreateEntityKeyRequest
        {
            EntityName = entityLogicalName,
            EntityKey = new EntityKeyMetadata
            {
                SchemaName = key.SchemaName,
                DisplayName = Label(key.DisplayName),
                KeyAttributes = key.Fields.ToArray(),
            },
            SolutionUniqueName = _schema.Solution.UniqueName,
        });
    }

    private void EnsureMainForm(TableSpec table, EntityMetadata metadata)
    {
        var formXml = BuildFormXml(table, metadata);
        var formId = EnsureSystemForm(metadata.LogicalName!, table.MainForm.Name, Program.MainFormType, formXml);
        EnsureSolutionComponent(formId, Program.MainFormComponentType);
        Console.WriteLine($"  Main form: {table.MainForm.Name}");
    }

    private Guid EnsureSystemForm(string entityLogicalName, string formName, int formType, string formXml)
    {
        var query = new QueryExpression("systemform")
        {
            ColumnSet = new ColumnSet("formid", "formxml"),
            Criteria = new FilterExpression(LogicalOperator.And),
            TopCount = 2,
        };
        query.Criteria.AddCondition("objecttypecode", ConditionOperator.Equal, entityLogicalName);
        query.Criteria.AddCondition("type", ConditionOperator.Equal, formType);
        query.Criteria.AddCondition("name", ConditionOperator.Equal, formName);

        var matches = _service.RetrieveMultiple(query).Entities;
        if (matches.Count > 1)
        {
            throw new InvalidOperationException($"More than one main form exists for '{entityLogicalName}' named '{formName}'. Resolve the duplicate and rerun.");
        }

        if (matches.Count == 1)
        {
            _service.Update(new Entity("systemform", matches[0].Id)
            {
                ["formxml"] = formXml,
                ["description"] = "Provisioned by CSB Audit Entities.",
                ["isdesktopenabled"] = true,
                ["istabletenabled"] = true,
            });
            return matches[0].Id;
        }

        return _service.Create(new Entity("systemform")
        {
            ["name"] = formName,
            ["objecttypecode"] = entityLogicalName,
            ["type"] = new OptionSetValue(formType),
            ["formxml"] = formXml,
            ["description"] = "Provisioned by CSB Audit Entities.",
            ["isdesktopenabled"] = true,
            ["istabletenabled"] = true,
        });
    }

    private void EnsureView(TableSpec table, EntityMetadata metadata, ViewSpec view)
    {
        var available = AttributeMap(metadata);
        var columns = view.Columns
            .Where(column => available.ContainsKey(column))
            .Distinct(StringComparer.OrdinalIgnoreCase)
            .ToList();

        if (columns.Count == 0)
        {
            columns.Add(metadata.PrimaryNameAttribute!);
        }

        var sortField = available.ContainsKey(view.Sort.Field) ? view.Sort.Field : "modifiedon";
        if (!available.ContainsKey(sortField))
        {
            sortField = metadata.PrimaryNameAttribute!;
        }

        var filter = view.Filter is not null && available.ContainsKey(view.Filter.Field)
            ? view.Filter
            : null;

        var effectiveView = view with
        {
            Columns = columns,
            Sort = view.Sort with { Field = sortField },
            Filter = filter,
        };

        var fetchXml = BuildFetchXml(metadata, effectiveView);
        var layoutXml = BuildLayoutXml(metadata, effectiveView, available);
        var viewId = EnsureSavedQuery(metadata.LogicalName!, effectiveView, fetchXml, layoutXml);
        EnsureSolutionComponent(viewId, Program.SavedQueryComponentType);
        Console.WriteLine($"  View: {view.Name}");
    }

    private Guid EnsureSavedQuery(string entityLogicalName, ViewSpec view, string fetchXml, string layoutXml)
    {
        var query = new QueryExpression("savedquery")
        {
            ColumnSet = new ColumnSet("savedqueryid"),
            Criteria = new FilterExpression(LogicalOperator.And),
            TopCount = 2,
        };
        query.Criteria.AddCondition("returnedtypecode", ConditionOperator.Equal, entityLogicalName);
        query.Criteria.AddCondition("name", ConditionOperator.Equal, view.Name);

        var matches = _service.RetrieveMultiple(query).Entities;
        if (matches.Count > 1)
        {
            throw new InvalidOperationException($"More than one saved query exists for '{entityLogicalName}' named '{view.Name}'. Resolve the duplicate and rerun.");
        }

        if (matches.Count == 1)
        {
            _service.Update(new Entity("savedquery", matches[0].Id)
            {
                ["fetchxml"] = fetchXml,
                ["layoutxml"] = layoutXml,
                ["description"] = view.Purpose,
            });
            return matches[0].Id;
        }

        return _service.Create(new Entity("savedquery")
        {
            ["name"] = view.Name,
            ["returnedtypecode"] = entityLogicalName,
            ["fetchxml"] = fetchXml,
            ["layoutxml"] = layoutXml,
            ["description"] = view.Purpose,
            ["querytype"] = 0,
        });
    }

    private void EnsureTableInSolution(EntityMetadata metadata)
    {
        if (metadata.MetadataId is not Guid metadataId)
        {
            return;
        }

        EnsureSolutionComponent(metadataId, Program.EntityComponentType);
    }

    private void EnsureSolutionComponent(Guid componentId, int componentType)
    {
        var check = new QueryExpression("solutioncomponent")
        {
            ColumnSet = new ColumnSet("solutioncomponentid"),
            Criteria = new FilterExpression(LogicalOperator.And),
            TopCount = 1,
        };
        check.Criteria.AddCondition("solutionid", ConditionOperator.Equal, _solutionId);
        check.Criteria.AddCondition("objectid", ConditionOperator.Equal, componentId);
        check.Criteria.AddCondition("componenttype", ConditionOperator.Equal, componentType);

        if (_service.RetrieveMultiple(check).Entities.Count > 0)
        {
            return;
        }

        _service.Execute(new CrmSdkMessages.AddSolutionComponentRequest
        {
            ComponentType = componentType,
            ComponentId = componentId,
            SolutionUniqueName = _schema.Solution.UniqueName,
            AddRequiredComponents = false,
            DoNotIncludeSubcomponents = true,
        });
    }

    private string BuildFormXml(TableSpec table, EntityMetadata metadata)
    {
        var attributes = AttributeMap(metadata);
        var tabs = new List<XElement>();
        foreach (var tabGroup in table.MainForm.Sections.GroupBy(section => section.Tab, StringComparer.OrdinalIgnoreCase))
        {
            var sections = tabGroup
                .Select(section => BuildSection(metadata, table.MainForm.Name, section, attributes))
                .Where(section => section is not null)
                .Cast<XElement>()
                .ToList();

            if (sections.Count == 0)
            {
                continue;
            }

            tabs.Add(
                new XElement(
                    "tab",
                    new XAttribute("verticallayout", "true"),
                    new XAttribute("id", BracedGuid($"{metadata.LogicalName}|tab|{tabGroup.Key}")),
                    new XAttribute("name", SafeName(tabGroup.Key)),
                    new XAttribute("IsUserDefined", "0"),
                    new XAttribute("locklevel", "0"),
                    new XAttribute("showlabel", "true"),
                    new XAttribute("expanded", "true"),
                    Labels(tabGroup.Key),
                    new XElement(
                        "columns",
                        new XElement(
                            "column",
                            new XAttribute("width", "100%"),
                            new XElement("sections", sections)))));
        }

        var form = new XElement(
            "form",
            new XElement(
                "tabs",
                tabs));

        return form.ToString(SaveOptions.DisableFormatting);
    }

    private static XElement? BuildSection(
        EntityMetadata metadata,
        string formName,
        FormSectionSpec section,
        IReadOnlyDictionary<string, AttributeMetadata> attributes)
    {
        var fields = section.Fields
            .Where(attributes.ContainsKey)
            .Distinct(StringComparer.OrdinalIgnoreCase)
            .ToList();

        if (fields.Count == 0)
        {
            return null;
        }

        var rows = fields.Select(field =>
        {
            var attribute = attributes[field];
            return new XElement(
                "row",
                new XElement(
                    "cell",
                    new XAttribute("id", BracedGuid($"{metadata.LogicalName}|{formName}|cell|{section.Section}|{field}")),
                    new XAttribute("showlabel", "true"),
                    new XAttribute("locklevel", "0"),
                    Labels(DisplayName(attribute, field)),
                    new XElement(
                        "control",
                        new XAttribute("id", field),
                        new XAttribute("classid", ControlClassId(attribute)),
                        new XAttribute("datafieldname", field),
                        new XAttribute("disabled", "false"))));
        });

        return new XElement(
            "section",
            new XAttribute("id", BracedGuid($"{metadata.LogicalName}|{formName}|section|{section.Section}")),
            new XAttribute("name", SafeName(section.Section)),
            new XAttribute("showlabel", "true"),
            new XAttribute("showbar", "false"),
            new XAttribute("columns", "1"),
            new XAttribute("labelwidth", "115"),
            new XAttribute("celllabelalignment", "Left"),
            new XAttribute("celllabelposition", "Left"),
            Labels(section.Section),
            new XElement("rows", rows));
    }

    private static string BuildFetchXml(EntityMetadata metadata, ViewSpec view)
    {
        var entity = new XElement(
            "entity",
            new XAttribute("name", metadata.LogicalName!),
            view.Columns.Select(column => new XElement("attribute", new XAttribute("name", column))),
            new XElement(
                "order",
                new XAttribute("attribute", view.Sort.Field),
                new XAttribute("descending", view.Sort.Descending ? "true" : "false")));

        if (view.Filter is not null)
        {
            entity.Add(
                new XElement(
                    "filter",
                    new XAttribute("type", "and"),
                    new XElement(
                        "condition",
                        new XAttribute("attribute", view.Filter.Field),
                        new XAttribute("operator", view.Filter.Operator),
                        new XAttribute("value", view.Filter.Value))));
        }

        return new XElement(
            "fetch",
            new XAttribute("version", "1.0"),
            new XAttribute("output-format", "xml-platform"),
            new XAttribute("mapping", "logical"),
            new XAttribute("distinct", "false"),
            entity).ToString(SaveOptions.DisableFormatting);
    }

    private static string BuildLayoutXml(
        EntityMetadata metadata,
        ViewSpec view,
        IReadOnlyDictionary<string, AttributeMetadata> attributes)
    {
        if (metadata.ObjectTypeCode is not int objectTypeCode || objectTypeCode <= 0)
        {
            throw new InvalidOperationException($"Table '{metadata.LogicalName}' does not have a valid ObjectTypeCode required for LayoutXML.");
        }

        var width = Math.Max(120, 1000 / Math.Max(1, view.Columns.Count));
        var cells = view.Columns.Select(column =>
        {
            var cellWidth = attributes[column] is MemoAttributeMetadata ? Math.Max(240, width) : width;
            return new XElement("cell", new XAttribute("name", column), new XAttribute("width", cellWidth));
        });

        return new XElement(
            "grid",
            new XAttribute("name", "resultset"),
            new XAttribute("object", objectTypeCode.ToString(System.Globalization.CultureInfo.InvariantCulture)),
            new XAttribute("jump", metadata.PrimaryNameAttribute!),
            new XAttribute("select", "1"),
            new XAttribute("icon", "1"),
            new XAttribute("preview", "1"),
            new XElement(
                "row",
                new XAttribute("name", "result"),
                new XAttribute("id", metadata.PrimaryIdAttribute!),
                cells)).ToString(SaveOptions.DisableFormatting);
    }

    private static IReadOnlyDictionary<string, AttributeMetadata> AttributeMap(EntityMetadata metadata) =>
        (metadata.Attributes ?? Array.Empty<AttributeMetadata>())
        .Where(attribute => !string.IsNullOrWhiteSpace(attribute.LogicalName))
        .ToDictionary(attribute => attribute.LogicalName!, StringComparer.OrdinalIgnoreCase);

    private EntityMetadata RequireEntity(string logicalName, EntityFilters filters) =>
        TryRetrieveEntity(logicalName, filters)
        ?? throw new InvalidOperationException($"Required Dataverse table '{logicalName}' was not found.");

    private EntityMetadata? TryRetrieveEntity(string logicalName, EntityFilters filters)
    {
        if (_metadataCache.TryGetValue($"{logicalName}|{filters}", out var cached))
        {
            return cached;
        }

        try
        {
            var response = (RetrieveEntityResponse)_service.Execute(new RetrieveEntityRequest
            {
                LogicalName = logicalName,
                EntityFilters = filters,
                RetrieveAsIfPublished = true,
            });
            _metadataCache[$"{logicalName}|{filters}"] = response.EntityMetadata;
            return response.EntityMetadata;
        }
        catch (Exception exception) when (IsNotFound(exception))
        {
            return null;
        }
    }

    private AttributeMetadata? TryRetrieveAttribute(string entityLogicalName, string attributeLogicalName)
    {
        try
        {
            var response = (RetrieveAttributeResponse)_service.Execute(new RetrieveAttributeRequest
            {
                EntityLogicalName = entityLogicalName,
                LogicalName = attributeLogicalName,
                RetrieveAsIfPublished = true,
            });
            return response.AttributeMetadata;
        }
        catch (Exception exception) when (IsNotFound(exception))
        {
            return null;
        }
    }

    private void PublishAll()
    {
        Console.WriteLine("Publishing table metadata.");
        _service.Execute(new CrmSdkMessages.PublishAllXmlRequest());
    }

    private void PublishChangedEntities(IEnumerable<string> entityNames)
    {
        var parameterXml = new XElement(
            "importexportxml",
            new XElement(
                "entities",
                entityNames
                    .Distinct(StringComparer.OrdinalIgnoreCase)
                    .OrderBy(name => name, StringComparer.OrdinalIgnoreCase)
                    .Select(name => new XElement("entity", name))));

        Console.WriteLine("Publishing CSB Audit Entities forms and views.");
        _service.Execute(new CrmSdkMessages.PublishXmlRequest
        {
            ParameterXml = parameterXml.ToString(SaveOptions.DisableFormatting),
        });
    }

    private void ExportUnmanagedSolution()
    {
        var fullPath = Path.GetFullPath(_options.ExportPath);
        Directory.CreateDirectory(Path.GetDirectoryName(fullPath)!);
        Console.WriteLine($"Exporting unmanaged solution to '{fullPath}'.");

        var response = (CrmSdkMessages.ExportSolutionResponse)_service.Execute(new CrmSdkMessages.ExportSolutionRequest
        {
            SolutionName = _schema.Solution.UniqueName,
            Managed = false,
        });
        File.WriteAllBytes(fullPath, response.ExportSolutionFile);
    }

    private static bool IsNotFound(Exception exception)
    {
        var message = exception.ToString();
        return message.Contains("does not exist", StringComparison.OrdinalIgnoreCase) ||
               message.Contains("not found", StringComparison.OrdinalIgnoreCase) ||
               message.Contains("Could not find", StringComparison.OrdinalIgnoreCase);
    }

    private static Label Label(string text) => new(text, Lcid);

    private static AttributeRequiredLevelManagedProperty RequiredLevel(bool required) =>
        new(required ? AttributeRequiredLevel.ApplicationRequired : AttributeRequiredLevel.None);

    private static XElement Labels(string label) =>
        new("labels", new XElement("label", new XAttribute("description", label), new XAttribute("languagecode", Lcid)));

    private static string DisplayName(AttributeMetadata attribute, string fallback) =>
        attribute.DisplayName?.UserLocalizedLabel?.Label ??
        attribute.DisplayName?.LocalizedLabels?.FirstOrDefault()?.Label ??
        fallback;

    private static string ControlClassId(AttributeMetadata attribute) => attribute switch
    {
        LookupAttributeMetadata => LookupControl,
        PicklistAttributeMetadata => ChoiceControl,
        StatusAttributeMetadata => StatusControl,
        StateAttributeMetadata => StatusControl,
        DateTimeAttributeMetadata => DateTimeControl,
        IntegerAttributeMetadata => WholeNumberControl,
        DecimalAttributeMetadata => DecimalControl,
        BooleanAttributeMetadata => BooleanControl,
        MemoAttributeMetadata => MultilineTextControl,
        _ => TextControl,
    };

    private static string BracedGuid(string seed)
    {
        var hash = SHA256.HashData(Encoding.UTF8.GetBytes(seed));
        var bytes = hash.Take(16).ToArray();
        bytes[7] = (byte)((bytes[7] & 0x0F) | 0x40);
        bytes[8] = (byte)((bytes[8] & 0x3F) | 0x80);
        return "{" + new Guid(bytes).ToString().ToUpperInvariant() + "}";
    }

    private static string SafeName(string value)
    {
        var builder = new StringBuilder();
        foreach (var character in value)
        {
            builder.Append(char.IsLetterOrDigit(character) ? character : '_');
        }
        return builder.ToString().Trim('_').ToLowerInvariant();
    }
}

internal sealed class ProvisionerOptions
{
    public const string DefaultInteractiveAppId = "51f81489-12ee-4a9e-aaae-a2591f45987d";
    public const string DefaultInteractiveRedirectUri = "http://localhost";
    public const string DefaultAuthority = "https://login.microsoftonline.com/common";

    public string? ConnectionString { get; init; }
    public string? EnvironmentUrl { get; init; }
    public string? Username { get; init; }
    public string AppId { get; init; } = DefaultInteractiveAppId;
    public string RedirectUri { get; init; } = DefaultInteractiveRedirectUri;
    public string Authority { get; init; } = DefaultAuthority;
    public string? SchemaPath { get; init; }
    public string ExportPath { get; init; } = Path.Combine(Environment.CurrentDirectory, "out", "CSB_AuditEntities_1_0_0_0_unmanaged.zip");
    public bool WhatIf { get; init; }
    public bool SkipExport { get; init; }
    public bool SkipMissingRelationshipTargets { get; init; }

    public static ProvisionerOptions Parse(string[] args)
    {
        var values = new Dictionary<string, List<string>>(StringComparer.OrdinalIgnoreCase);
        var switches = new HashSet<string>(StringComparer.OrdinalIgnoreCase);

        for (var index = 0; index < args.Length; index++)
        {
            var argument = args[index];
            if (!argument.StartsWith("--", StringComparison.Ordinal))
            {
                throw new ArgumentException($"Unexpected argument '{argument}'.");
            }

            if (argument is "--what-if" or "--skip-export" or "--skip-missing-relationship-targets")
            {
                switches.Add(argument);
                continue;
            }

            if (index + 1 >= args.Length || args[index + 1].StartsWith("--", StringComparison.Ordinal))
            {
                throw new ArgumentException($"Argument '{argument}' requires a value.");
            }

            if (!values.TryGetValue(argument, out var list))
            {
                list = new List<string>();
                values[argument] = list;
            }

            list.Add(args[++index]);
        }

        string? Value(string key) => values.TryGetValue(key, out var list) ? list.LastOrDefault() : null;

        var connection = Value("--connection") ?? Environment.GetEnvironmentVariable("DATAVERSE_CONNECTION_STRING");
        var environmentUrl = Value("--environment-url");
        if (!string.IsNullOrWhiteSpace(connection) && !string.IsNullOrWhiteSpace(environmentUrl))
        {
            throw new ArgumentException("Use either --connection or --environment-url, not both.");
        }

        return new ProvisionerOptions
        {
            ConnectionString = connection,
            EnvironmentUrl = environmentUrl,
            Username = Value("--username"),
            AppId = Value("--app-id") ?? DefaultInteractiveAppId,
            RedirectUri = Value("--redirect-uri") ?? DefaultInteractiveRedirectUri,
            Authority = Value("--authority") ?? DefaultAuthority,
            SchemaPath = Value("--schema"),
            ExportPath = Value("--export") ?? Path.Combine(Environment.CurrentDirectory, "out", "CSB_AuditEntities_1_0_0_0_unmanaged.zip"),
            WhatIf = switches.Contains("--what-if"),
            SkipExport = switches.Contains("--skip-export"),
            SkipMissingRelationshipTargets = switches.Contains("--skip-missing-relationship-targets"),
        };
    }

    public ServiceClient CreateServiceClient()
    {
        if (!string.IsNullOrWhiteSpace(ConnectionString))
        {
            return new ServiceClient(ConnectionString);
        }

        if (string.IsNullOrWhiteSpace(EnvironmentUrl))
        {
            throw new InvalidOperationException(
                "A Dataverse connection is required. Use --environment-url 'https://org314f8ab8.crm.dynamics.com' or provide --connection / DATAVERSE_CONNECTION_STRING.");
        }

        if (!Uri.TryCreate(EnvironmentUrl, UriKind.Absolute, out var environmentUri) ||
            !string.Equals(environmentUri.Scheme, Uri.UriSchemeHttps, StringComparison.OrdinalIgnoreCase))
        {
            throw new ArgumentException("--environment-url must be an absolute HTTPS Dataverse environment URL.");
        }

        if (!Uri.TryCreate(RedirectUri, UriKind.Absolute, out var redirectUri) ||
            !string.Equals(redirectUri.Scheme, Uri.UriSchemeHttp, StringComparison.OrdinalIgnoreCase) ||
            !string.Equals(redirectUri.Host, "localhost", StringComparison.OrdinalIgnoreCase))
        {
            throw new ArgumentException("--redirect-uri must use a loopback URI such as http://localhost for interactive OAuth.");
        }

        if (!Guid.TryParse(AppId, out _))
        {
            throw new ArgumentException("--app-id must be a valid Microsoft Entra application client ID GUID.");
        }

        if (!Uri.TryCreate(Authority, UriKind.Absolute, out var authorityUri) ||
            !string.Equals(authorityUri.Scheme, Uri.UriSchemeHttps, StringComparison.OrdinalIgnoreCase))
        {
            throw new ArgumentException("--authority must be an absolute HTTPS Microsoft Entra authority URI.");
        }

        var normalizedEnvironmentUrl = environmentUri.GetLeftPart(UriPartial.Authority);
        var normalizedAuthority = authorityUri.GetLeftPart(UriPartial.Authority) + authorityUri.AbsolutePath.TrimEnd('/');
        var application = PublicClientApplicationBuilder
            .Create(AppId)
            .WithAuthority(normalizedAuthority)
            .WithRedirectUri(redirectUri.ToString())
            .Build();

        var scope = $"{normalizedEnvironmentUrl}/.default";
        var tokenProvider = new InteractiveDataverseTokenProvider(application, scope, Username);

        Console.WriteLine("Interactive OAuth selected. A browser sign-in window will open when Dataverse requests an access token.");
        Console.WriteLine($"Dataverse environment: {normalizedEnvironmentUrl}");
        Console.WriteLine($"Microsoft Entra authority: {normalizedAuthority}");
        if (!string.IsNullOrWhiteSpace(Username))
        {
            Console.WriteLine($"Sign-in hint: {Username}");
        }

        return new ServiceClient(environmentUri, tokenProvider.GetAccessTokenAsync, useUniqueInstance: true);
    }
}

internal sealed class InteractiveDataverseTokenProvider
{
    private readonly IPublicClientApplication _application;
    private readonly string[] _scopes;
    private readonly string? _username;
    private readonly SemaphoreSlim _gate = new(1, 1);
    private AuthenticationResult? _currentToken;

    public InteractiveDataverseTokenProvider(IPublicClientApplication application, string scope, string? username)
    {
        _application = application;
        _scopes = new[] { scope };
        _username = username;
    }

    public async Task<string> GetAccessTokenAsync(string _)
    {
        await _gate.WaitAsync().ConfigureAwait(false);
        try
        {
            if (_currentToken is not null && _currentToken.ExpiresOn > DateTimeOffset.UtcNow.AddMinutes(5))
            {
                return _currentToken.AccessToken;
            }

            var account = (await _application.GetAccountsAsync().ConfigureAwait(false)).FirstOrDefault();
            if (account is not null)
            {
                try
                {
                    _currentToken = await _application
                        .AcquireTokenSilent(_scopes, account)
                        .ExecuteAsync()
                        .ConfigureAwait(false);
                }
                catch (MsalUiRequiredException)
                {
                    _currentToken = null;
                }
            }

            if (_currentToken is null || _currentToken.ExpiresOn <= DateTimeOffset.UtcNow.AddMinutes(5))
            {
                var interactiveRequest = _application.AcquireTokenInteractive(_scopes).WithPrompt(Prompt.SelectAccount);
                if (!string.IsNullOrWhiteSpace(_username))
                {
                    interactiveRequest = interactiveRequest.WithLoginHint(_username);
                }

                _currentToken = await interactiveRequest.ExecuteAsync().ConfigureAwait(false);
            }

            return _currentToken.AccessToken;
        }
        finally
        {
            _gate.Release();
        }
    }
}

internal sealed class AuditEntitiesSchema
{
    public string SchemaVersion { get; init; } = "";
    public SolutionSpec Solution { get; init; } = new();
    public List<TableSpec> Tables { get; init; } = new();
    public List<RelationshipSpec> Relationships { get; init; } = new();
}

internal sealed class SolutionSpec
{
    public string UniqueName { get; init; } = "";
    public string DisplayName { get; init; } = "";
    public string Version { get; init; } = "";
    public string PublisherPrefix { get; init; } = "";
    public string PublisherPreferredUniqueName { get; init; } = "";
    public string PublisherFriendlyName { get; init; } = "";
    public string Description { get; init; } = "";
}

internal sealed class TableSpec
{
    public string SchemaName { get; init; } = "";
    public string LogicalName { get; init; } = "";
    public string DisplayName { get; init; } = "";
    public string CollectionName { get; init; } = "";
    public string Ownership { get; init; } = "";
    public string Description { get; init; } = "";
    public PrimaryNameSpec PrimaryName { get; init; } = new();
    public List<FieldSpec> Fields { get; init; } = new();
    public List<AlternateKeySpec> AlternateKeys { get; init; } = new();
    public MainFormSpec MainForm { get; init; } = new();
    public List<ViewSpec> Views { get; init; } = new();
}

internal sealed class PrimaryNameSpec
{
    public string SchemaName { get; init; } = "";
    public string LogicalName { get; init; } = "";
    public string DisplayName { get; init; } = "";
    public string Description { get; init; } = "";
    public int MaxLength { get; init; } = 300;
}

internal sealed class FieldSpec
{
    public string SchemaName { get; init; } = "";
    public string LogicalName { get; init; } = "";
    public string DisplayName { get; init; } = "";
    public string Type { get; init; } = "";
    public string Description { get; init; } = "";
    public bool Required { get; init; }
    public bool IsSecured { get; init; }
    public int? MaxLength { get; init; }
    public List<ChoiceOptionSpec> ChoiceOptions { get; init; } = new();
    public bool? DefaultValue { get; init; }
    public decimal? MinValue { get; init; }
    public decimal? MaxValue { get; init; }
    public int? Precision { get; init; }
}

internal sealed class ChoiceOptionSpec
{
    public int Value { get; init; }
    public string Label { get; init; } = "";
}

internal sealed class AlternateKeySpec
{
    public string SchemaName { get; init; } = "";
    public string DisplayName { get; init; } = "";
    public List<string> Fields { get; init; } = new();
}

internal sealed class RelationshipSpec
{
    public string SchemaName { get; init; } = "";
    public string ReferencedEntity { get; init; } = "";
    public string ReferencingEntity { get; init; } = "";
    public string LookupSchemaName { get; init; } = "";
    public string LookupLogicalName { get; init; } = "";
    public string LookupDisplayName { get; init; } = "";
    public string CollectionLabel { get; init; } = "";
    public string Description { get; init; } = "";
    public bool Required { get; init; }
    public bool FailIfTargetMissing { get; init; } = true;
}

internal sealed class MainFormSpec
{
    public string Name { get; init; } = "";
    public List<FormSectionSpec> Sections { get; init; } = new();
}

internal sealed class FormSectionSpec
{
    public string Tab { get; init; } = "";
    public string Section { get; init; } = "";
    public List<string> Fields { get; init; } = new();
}

internal sealed record ViewSpec
{
    public string Name { get; init; } = "";
    public string Purpose { get; init; } = "";
    public ViewFilterSpec? Filter { get; init; }
    public ViewSortSpec Sort { get; init; } = new();
    public List<string> Columns { get; init; } = new();
}

internal sealed record ViewFilterSpec
{
    public string Field { get; init; } = "";
    public string Operator { get; init; } = "";
    public string Value { get; init; } = "";
}

internal sealed record ViewSortSpec
{
    public string Field { get; init; } = "";
    public bool Descending { get; init; }
}

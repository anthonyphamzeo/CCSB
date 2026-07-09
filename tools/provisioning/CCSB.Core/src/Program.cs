using CrmMessages = Microsoft.Crm.Sdk.Messages;
using Microsoft.PowerPlatform.Dataverse.Client;
using Microsoft.Xrm.Sdk;
using Microsoft.Xrm.Sdk.Messages;
using Microsoft.Xrm.Sdk.Metadata;
using Microsoft.Xrm.Sdk.Query;
using System.Text.Json;
using System.Text.Json.Serialization;

namespace Ccsb.Core.Provisioner;

internal static class Program
{
    public static int Main(string[] args)
    {
        BuildReport? report = null;

        try
        {
            var options = CommandLineOptions.Parse(args);
            var manifestPath = Path.GetFullPath(options.ManifestPath ??
                Path.Combine(global::System.AppContext.BaseDirectory, "table-manifest.json"));

            if (!File.Exists(manifestPath))
            {
                throw new InvalidOperationException($"Table manifest was not found: {manifestPath}");
            }

            var manifest = JsonSerializer.Deserialize<CoreManifest>(
                File.ReadAllText(manifestPath),
                JsonSerialization.Options)
                ?? throw new InvalidOperationException("The table manifest could not be read.");

            ManifestValidator.Validate(manifest);

            report = new BuildReport
            {
                StartedUtc = DateTime.UtcNow,
                Mode = options.Apply ? "Apply" : "ValidateOnly",
                ManifestPath = manifestPath,
                SolutionUniqueName = manifest.Solution.UniqueName,
                SolutionVersion = manifest.Solution.Version
            };

            OAuthConnectionStringValidator.Validate(options.ConnectionString);

            var client = new ServiceClient(options.ConnectionString);
            if (!client.IsReady)
            {
                throw new InvalidOperationException($"Dataverse connection failed: {client.LastError}");
            }

            var provisioner = new CoreSolutionProvisioner(client, manifest, options, report);
            provisioner.Run();

            report.CompletedUtc = DateTime.UtcNow;
            report.Success = report.Errors.Count == 0;

            var reportPath = Path.GetFullPath(options.ReportPath ??
                Path.Combine(
                    Path.GetDirectoryName(Path.GetFullPath(options.OutputPath)) ?? ".",
                    "CCSB_Core_build_report.json"));

            Directory.CreateDirectory(Path.GetDirectoryName(reportPath)!);
            File.WriteAllText(
                reportPath,
                JsonSerializer.Serialize(report, JsonSerialization.Options));

            Console.WriteLine();
            Console.WriteLine(report.Success
                ? $"Completed successfully. Report: {reportPath}"
                : $"Completed with errors. Report: {reportPath}");

            return report.Success ? 0 : 2;
        }
        catch (Exception ex)
        {
            Console.Error.WriteLine($"CCSB Core provisioning failed: {ex.Message}");

            if (report is not null)
            {
                report.Errors.Add(new ReportItem
                {
                    Stage = "Unhandled",
                    Action = "Error",
                    Subject = ex.GetType().Name,
                    Detail = ex.ToString()
                });
                report.CompletedUtc = DateTime.UtcNow;
                report.Success = false;

                try
                {
                    var fallbackPath = Path.Combine(Environment.CurrentDirectory, "CCSB_Core_failed_build_report.json");
                    File.WriteAllText(
                        fallbackPath,
                        JsonSerializer.Serialize(report, JsonSerialization.Options));
                    Console.Error.WriteLine($"Failure report: {fallbackPath}");
                }
                catch
                {
                    // Preserve the original failure even when reporting is not possible.
                }
            }

            return 1;
        }
    }
}


internal static class OAuthConnectionStringValidator
{
    /// <summary>
    /// This .NET 8 console application uses MSAL's system-browser interactive flow.
    /// That flow requires an HTTP loopback redirect URI. Fail before ServiceClient
    /// creates an MSAL client so the user gets a specific remediation message.
    /// </summary>
    public static void Validate(string connectionString)
    {
        var settings = Parse(connectionString);

        if (!settings.TryGetValue("AuthType", out var authType) ||
            !authType.Equals("OAuth", StringComparison.OrdinalIgnoreCase))
        {
            return;
        }

        var redirectUri = Get(settings, "RedirectUri") ?? Get(settings, "ReplyUrl");

        if (string.IsNullOrWhiteSpace(redirectUri))
        {
            throw new InvalidOperationException(
                "OAuth connection strings for this .NET 8 provisioner require RedirectUri=http://localhost.");
        }

        if (!Uri.TryCreate(redirectUri, UriKind.Absolute, out var uri))
        {
            throw new InvalidOperationException(
                $"OAuth RedirectUri '{redirectUri}' is not a valid absolute URI. " +
                "Use RedirectUri=http://localhost.");
        }

        // Uri.IsLoopback is true for localhost, 127.0.0.1 and ::1.
        // It is the supported Uri API; Uri does not expose an IPAddress property.
        var isLoopbackHttp = uri.Scheme.Equals(Uri.UriSchemeHttp, StringComparison.OrdinalIgnoreCase) &&
                             uri.IsLoopback;

        if (!isLoopbackHttp)
        {
            throw new InvalidOperationException(
                $"OAuth RedirectUri '{redirectUri}' is incompatible with this .NET 8/MSAL system-browser flow. " +
                "Use RedirectUri=http://localhost (or http://localhost:<port>) in both the connection string " +
                "and the Microsoft Entra app registration. Do not use app://... for this provisioner.");
        }
    }

    private static string? Get(IReadOnlyDictionary<string, string> settings, string key) =>
        settings.TryGetValue(key, out var value) ? value : null;

    private static Dictionary<string, string> Parse(string connectionString)
    {
        var result = new Dictionary<string, string>(StringComparer.OrdinalIgnoreCase);

        foreach (var segment in connectionString.Split(';', StringSplitOptions.RemoveEmptyEntries | StringSplitOptions.TrimEntries))
        {
            var separatorIndex = segment.IndexOf('=');
            if (separatorIndex <= 0)
            {
                continue;
            }

            var key = segment[..separatorIndex].Trim();
            var value = segment[(separatorIndex + 1)..].Trim();

            if (!string.IsNullOrWhiteSpace(key))
            {
                result[key] = value;
            }
        }

        return result;
    }
}

internal sealed class CoreSolutionProvisioner
{
    private readonly IOrganizationService _service;
    private readonly CoreManifest _manifest;
    private readonly CommandLineOptions _options;
    private readonly BuildReport _report;

    // Dataverse solution component type 1 = Entity/Table.
    // Keep this in the provisioner scope because it is used while adding existing tables to the solution.
    private const int EntitySolutionComponentType = 1;

    private Entity? _publisher;
    private Guid _solutionId;

    public CoreSolutionProvisioner(
        IOrganizationService service,
        CoreManifest manifest,
        CommandLineOptions options,
        BuildReport report)
    {
        _service = service;
        _manifest = manifest;
        _options = options;
        _report = report;
    }

    public void Run()
    {
        if (!_options.Apply)
        {
            ValidateOnly();
            return;
        }

        _publisher = EnsurePublisher();
        EnsureSolution();
        EnsureTables();
        PublishAll();

        if (!_options.NoExport)
        {
            ExportUnmanagedSolution();
        }
    }

    private void ValidateOnly()
    {
        _report.AddInfo("Validation", "Manifest", $"Validated {_manifest.Tables.Count} requested CCSB tables.");
        _report.AddInfo("Validation", "Solution", $"Will create or reuse unmanaged solution '{_manifest.Solution.UniqueName}'.");

        var publishers = FindPublishersByPrefix();
        if (publishers.Count == 0)
        {
            _report.AddInfo(
                "Validation",
                "Publisher",
                $"No publisher currently uses prefix '{_manifest.Publisher.CustomizationPrefix}'. " +
                $"Apply mode will create publisher '{_manifest.Publisher.UniqueName}'.");
        }
        else if (publishers.Count == 1)
        {
            _report.AddInfo(
                "Validation",
                "Publisher",
                $"Publisher '{publishers[0].GetAttributeValue<string>("uniquename")}' already owns prefix '{_manifest.Publisher.CustomizationPrefix}'.");
        }
        else
        {
            throw new InvalidOperationException(
                $"More than one Dataverse publisher uses prefix '{_manifest.Publisher.CustomizationPrefix}'. " +
                "Resolve the duplicate publisher configuration before applying the solution.");
        }

        var solution = FindSolution();
        if (solution is null)
        {
            _report.AddInfo("Validation", "Solution", $"Solution '{_manifest.Solution.UniqueName}' does not yet exist and will be created.");
        }
        else
        {
            _report.AddInfo(
                "Validation",
                "Solution",
                $"Solution '{_manifest.Solution.UniqueName}' already exists at version '{solution.GetAttributeValue<string>("version")}'.");
        }

        foreach (var table in _manifest.Tables.OrderBy(t => t.LogicalName, StringComparer.OrdinalIgnoreCase))
        {
            var existing = TryRetrieveEntity(table.LogicalName);
            if (existing is null)
            {
                _report.AddInfo(
                    "Validation",
                    "Table",
                    $"{table.LogicalName}: will create {table.OwnershipType} table with primary name '{_manifest.PrimaryName.LogicalName}'.");
                continue;
            }

            if (existing.OwnershipType != ToOwnershipType(table.OwnershipType))
            {
                throw new InvalidOperationException(
                    $"Existing table '{table.LogicalName}' has ownership '{existing.OwnershipType}', " +
                    $"but the manifest requires '{table.OwnershipType}'. Dataverse ownership cannot be changed after creation.");
            }

            _report.AddInfo(
                "Validation",
                "Table",
                $"{table.LogicalName}: exists and is compatible; it will be added to the unmanaged solution if necessary.");
        }

        _report.AddInfo("Validation", "Result", "No changes were made. Run with --apply to create tables and export the Dataverse-generated unmanaged solution ZIP.");
    }

    private Entity EnsurePublisher()
    {
        var publishers = FindPublishersByPrefix();

        if (publishers.Count > 1)
        {
            throw new InvalidOperationException(
                $"More than one Dataverse publisher uses prefix '{_manifest.Publisher.CustomizationPrefix}'. " +
                "Resolve the duplicate publisher configuration before applying the solution.");
        }

        if (publishers.Count == 1)
        {
            var existing = publishers[0];
            _report.AddInfo(
                "Publisher",
                "Adopted",
                $"Using existing publisher '{existing.GetAttributeValue<string>("uniquename")}' with prefix '{_manifest.Publisher.CustomizationPrefix}'.");
            return existing;
        }

        // Check for a publisher with the requested unique name but a different prefix.
        var byUniqueName = new QueryExpression("publisher")
        {
            ColumnSet = new ColumnSet("publisherid", "uniquename", "customizationprefix")
        };
        byUniqueName.Criteria.AddCondition("uniquename", ConditionOperator.Equal, _manifest.Publisher.UniqueName);
        var sameName = _service.RetrieveMultiple(byUniqueName).Entities.SingleOrDefault();

        if (sameName is not null)
        {
            throw new InvalidOperationException(
                $"Publisher unique name '{_manifest.Publisher.UniqueName}' already exists with prefix " +
                $"'{sameName.GetAttributeValue<string>("customizationprefix")}', not '{_manifest.Publisher.CustomizationPrefix}'.");
        }

        var publisher = new Entity("publisher");
        publisher["uniquename"] = _manifest.Publisher.UniqueName;
        publisher["friendlyname"] = _manifest.Publisher.FriendlyName;
        publisher["customizationprefix"] = _manifest.Publisher.CustomizationPrefix;
        publisher["customizationoptionvalueprefix"] = _manifest.Publisher.OptionValuePrefix;
        publisher["description"] = _manifest.Publisher.Description;

        var publisherId = _service.Create(publisher);
        publisher.Id = publisherId;

        _report.AddCreated(
            "Publisher",
            _manifest.Publisher.UniqueName,
            $"Created publisher with prefix '{_manifest.Publisher.CustomizationPrefix}' and option value prefix '{_manifest.Publisher.OptionValuePrefix}'.");

        return publisher;
    }

    private List<Entity> FindPublishersByPrefix()
    {
        var query = new QueryExpression("publisher")
        {
            ColumnSet = new ColumnSet(
                "publisherid",
                "uniquename",
                "friendlyname",
                "customizationprefix",
                "customizationoptionvalueprefix")
        };
        query.Criteria.AddCondition("customizationprefix", ConditionOperator.Equal, _manifest.Publisher.CustomizationPrefix);
        return _service.RetrieveMultiple(query).Entities.ToList();
    }

    private void EnsureSolution()
    {
        var existing = FindSolution();
        if (existing is not null)
        {
            var existingPublisher = existing.GetAttributeValue<EntityReference>("publisherid");
            if (existingPublisher is null || existingPublisher.Id != _publisher!.Id)
            {
                throw new InvalidOperationException(
                    $"Existing solution '{_manifest.Solution.UniqueName}' belongs to a different publisher. " +
                    "Use a new solution unique name or correct the publisher before continuing.");
            }

            _solutionId = existing.Id;
            _report.AddInfo(
                "Solution",
                "Adopted",
                $"Using existing unmanaged solution '{_manifest.Solution.UniqueName}' at version '{existing.GetAttributeValue<string>("version")}'.");
            return;
        }

        // Microsoft.PowerPlatform.Dataverse.Client 1.2.10 does not expose CreateSolutionRequest.
        // The Dataverse solution table supports create operations, so create the unmanaged
        // solution record through the standard Organization Service API instead.
        var solution = new Entity("solution");
        solution["uniquename"] = _manifest.Solution.UniqueName;
        solution["friendlyname"] = _manifest.Solution.FriendlyName;
        solution["version"] = _manifest.Solution.Version;
        solution["description"] = _manifest.Solution.Description;
        solution["publisherid"] = new EntityReference("publisher", _publisher!.Id);

        _solutionId = _service.Create(solution);

        var created = FindSolution()
            ?? throw new InvalidOperationException($"Solution '{_manifest.Solution.UniqueName}' could not be retrieved after creation.");

        _solutionId = created.Id;
        _report.AddCreated(
            "Solution",
            _manifest.Solution.UniqueName,
            $"Created unmanaged solution version '{_manifest.Solution.Version}'.");
    }

    private Entity? FindSolution()
    {
        var query = new QueryExpression("solution")
        {
            ColumnSet = new ColumnSet("solutionid", "uniquename", "friendlyname", "version", "publisherid", "ismanaged")
        };
        query.Criteria.AddCondition("uniquename", ConditionOperator.Equal, _manifest.Solution.UniqueName);

        var result = _service.RetrieveMultiple(query).Entities.SingleOrDefault();
        if (result is not null && result.GetAttributeValue<bool>("ismanaged"))
        {
            throw new InvalidOperationException(
                $"A managed solution named '{_manifest.Solution.UniqueName}' already exists. " +
                "The base solution must be built in an unmanaged development environment.");
        }

        return result;
    }

    private void EnsureTables()
    {
        foreach (var table in _manifest.Tables.OrderBy(t => t.LogicalName, StringComparer.OrdinalIgnoreCase))
        {
            var existing = TryRetrieveEntity(table.LogicalName);
            if (existing is null)
            {
                CreateTable(table);
                continue;
            }

            if (existing.OwnershipType != ToOwnershipType(table.OwnershipType))
            {
                throw new InvalidOperationException(
                    $"Existing table '{table.LogicalName}' has ownership '{existing.OwnershipType}', " +
                    $"but the manifest requires '{table.OwnershipType}'. Dataverse ownership cannot be changed after creation.");
            }

            if (existing.MetadataId is not Guid metadataId)
            {
                throw new InvalidOperationException($"Existing table '{table.LogicalName}' has no metadata identifier.");
            }

            if (!IsComponentInSolution(EntitySolutionComponentType, metadataId))
            {
                _service.Execute(new CrmMessages.AddSolutionComponentRequest
                {
                    ComponentType = EntitySolutionComponentType,
                    ComponentId = metadataId,
                    SolutionUniqueName = _manifest.Solution.UniqueName,
                    AddRequiredComponents = true,
                    DoNotIncludeSubcomponents = false
                });

                _report.AddInfo(
                    "Table",
                    "Adopted",
                    $"Added existing compatible table '{table.LogicalName}' to solution '{_manifest.Solution.UniqueName}'.");
            }
            else
            {
                _report.AddSkipped("Table", table.LogicalName, "Already exists in the solution.");
            }
        }
    }

    private void CreateTable(TableDefinition table)
    {
        var entity = new EntityMetadata
        {
            SchemaName = table.SchemaName,
            DisplayName = new Label(table.DisplayName, _manifest.Lcid),
            DisplayCollectionName = new Label(table.DisplayCollectionName, _manifest.Lcid),
            Description = new Label(table.Description, _manifest.Lcid),
            OwnershipType = ToOwnershipType(table.OwnershipType),
            IsActivity = false
        };

        var primaryAttribute = new StringAttributeMetadata
        {
            SchemaName = _manifest.PrimaryName.SchemaName,
            DisplayName = new Label(table.PrimaryNameDisplayName, _manifest.Lcid),
            Description = new Label(
                $"Primary display name for {table.DisplayName} records. This is the only custom column included in the CCSB Core table foundation.",
                _manifest.Lcid),
            RequiredLevel = new AttributeRequiredLevelManagedProperty(AttributeRequiredLevel.None),
            MaxLength = _manifest.PrimaryName.MaxLength,
            FormatName = StringFormatName.Text
        };

        _service.Execute(new CreateEntityRequest
        {
            Entity = entity,
            PrimaryAttribute = primaryAttribute,
            HasActivities = false,
            HasNotes = false,
            SolutionUniqueName = _manifest.Solution.UniqueName
        });

        _report.AddCreated(
            "Table",
            table.LogicalName,
            $"Created {table.OwnershipType} table '{table.DisplayName}' with primary name '{_manifest.PrimaryName.LogicalName}'.");
    }

    private EntityMetadata? TryRetrieveEntity(string logicalName)
    {
        try
        {
            var response = (RetrieveEntityResponse)_service.Execute(new RetrieveEntityRequest
            {
                LogicalName = logicalName,
                EntityFilters = EntityFilters.Entity | EntityFilters.Attributes,
                RetrieveAsIfPublished = true
            });
            return response.EntityMetadata;
        }
        catch
        {
            return null;
        }
    }

    private bool IsComponentInSolution(int componentType, Guid objectId)
    {
        var query = new QueryExpression("solutioncomponent")
        {
            ColumnSet = new ColumnSet("solutioncomponentid")
        };
        query.Criteria.AddCondition("solutionid", ConditionOperator.Equal, _solutionId);
        query.Criteria.AddCondition("componenttype", ConditionOperator.Equal, componentType);
        query.Criteria.AddCondition("objectid", ConditionOperator.Equal, objectId);

        return _service.RetrieveMultiple(query).Entities.Count > 0;
    }

    private void PublishAll()
    {
        _service.Execute(new CrmMessages.PublishAllXmlRequest());
        _report.AddInfo("Publish", "Completed", "Published all customizations in the development environment.");
    }

    private void ExportUnmanagedSolution()
    {
        var outputPath = Path.GetFullPath(_options.OutputPath);
        Directory.CreateDirectory(Path.GetDirectoryName(outputPath)!);

        var response = (CrmMessages.ExportSolutionResponse)_service.Execute(new CrmMessages.ExportSolutionRequest
        {
            SolutionName = _manifest.Solution.UniqueName,
            Managed = false
        });

        File.WriteAllBytes(outputPath, response.ExportSolutionFile);

        _report.AddCreated(
            "Export",
            Path.GetFileName(outputPath),
            $"Dataverse-generated unmanaged solution ZIP written to '{outputPath}'.");
    }

    private static OwnershipTypes ToOwnershipType(string ownershipType)
    {
        return ownershipType.Equals("OrganizationOwned", StringComparison.OrdinalIgnoreCase)
            ? OwnershipTypes.OrganizationOwned
            : OwnershipTypes.UserOwned;
    }
}

internal sealed class CommandLineOptions
{
    public string ConnectionString { get; private init; } = string.Empty;
    public bool Apply { get; private init; }
    public bool NoExport { get; private init; }
    public string OutputPath { get; private init; } =
        Path.Combine("artifacts", "CCSB_Core_1_0_0_0_unmanaged.zip");
    public string? ManifestPath { get; private init; }
    public string? ReportPath { get; private init; }

    public static CommandLineOptions Parse(string[] args)
    {
        string? connectionString = null;
        string? outputPath = null;
        string? manifestPath = null;
        string? reportPath = null;
        bool apply = false;
        bool noExport = false;

        for (var index = 0; index < args.Length; index++)
        {
            var argument = args[index];

            switch (argument.ToLowerInvariant())
            {
                case "--connection-string":
                case "-c":
                    connectionString = ReadValue(args, ref index, argument);
                    break;

                case "--output":
                case "-o":
                    outputPath = ReadValue(args, ref index, argument);
                    break;

                case "--manifest":
                    manifestPath = ReadValue(args, ref index, argument);
                    break;

                case "--report":
                    reportPath = ReadValue(args, ref index, argument);
                    break;

                case "--apply":
                    apply = true;
                    break;

                case "--validate-only":
                    apply = false;
                    break;

                case "--no-export":
                    noExport = true;
                    break;

                case "--help":
                case "-h":
                    PrintUsage();
                    Environment.Exit(0);
                    break;

                default:
                    throw new InvalidOperationException($"Unknown argument '{argument}'. Use --help for usage.");
            }
        }

        if (string.IsNullOrWhiteSpace(connectionString))
        {
            throw new InvalidOperationException("--connection-string is required.");
        }

        return new CommandLineOptions
        {
            ConnectionString = connectionString,
            Apply = apply,
            NoExport = noExport,
            OutputPath = outputPath ?? Path.Combine("artifacts", "CCSB_Core_1_0_0_0_unmanaged.zip"),
            ManifestPath = manifestPath,
            ReportPath = reportPath
        };
    }

    private static string ReadValue(string[] args, ref int index, string argument)
    {
        if (index + 1 >= args.Length)
        {
            throw new InvalidOperationException($"Argument '{argument}' requires a value.");
        }

        index++;
        return args[index];
    }

    private static void PrintUsage()
    {
        Console.WriteLine("""
Usage:
  dotnet run --project src/CCSB.Core.Provisioner.csproj -- \
    --connection-string "<Dataverse connection string>" \
    [--validate-only | --apply] \
    [--output "artifacts/CCSB_Core_1_0_0_0_unmanaged.zip"] \
    [--no-export] \
    [--manifest "table-manifest.json"] \
    [--report "artifacts/CCSB_Core_build_report.json"]

Modes:
  --validate-only  Default. Connects and reports the planned actions without changing Dataverse.
  --apply          Creates/reuses the publisher and solution, creates/reuses the 26 tables, publishes, and exports an unmanaged solution ZIP.
""");
    }
}

internal static class ManifestValidator
{
    public static void Validate(CoreManifest manifest)
    {
        if (!string.Equals(manifest.Publisher.CustomizationPrefix, "ccsb", StringComparison.OrdinalIgnoreCase))
        {
            throw new InvalidOperationException("This package is locked to the 'ccsb' publisher prefix.");
        }

        if (manifest.Tables.Count != 26)
        {
            throw new InvalidOperationException($"The manifest must contain exactly 26 tables; found {manifest.Tables.Count}.");
        }

        var expectedTables = new HashSet<string>(StringComparer.OrdinalIgnoreCase)
        {
            "ccsb_board",
            "ccsb_boardconfiguration",
            "ccsb_viewdefinition",
            "ccsb_resourcedefinition",
            "ccsb_eventtypedefinition",
            "ccsb_groupdefinition",
            "ccsb_statusdefinition",
            "ccsb_statustransition",
            "ccsb_ruledefinition",
            "ccsb_resource",
            "ccsb_service",
            "ccsb_calendar",
            "ccsb_calendarrule",
            "ccsb_calendarexception",
            "ccsb_publicholiday",
            "ccsb_shift",
            "ccsb_availabilitywindow",
            "ccsb_leave",
            "ccsb_groupnode",
            "ccsb_groupmembership",
            "ccsb_scheduleversion",
            "ccsb_scheduleitem",
            "ccsb_schedulerequirement",
            "ccsb_scheduleassignment",
            "ccsb_conflict",
            "ccsb_publishsnapshot"
        };

        var actualTables = manifest.Tables
            .Select(table => table.LogicalName)
            .ToHashSet(StringComparer.OrdinalIgnoreCase);

        if (!expectedTables.SetEquals(actualTables))
        {
            var missing = expectedTables.Except(actualTables).OrderBy(name => name);
            var unexpected = actualTables.Except(expectedTables).OrderBy(name => name);
            throw new InvalidOperationException(
                $"The manifest table set is not the approved CCSB Core baseline. " +
                $"Missing: {string.Join(", ", missing)}. Unexpected: {string.Join(", ", unexpected)}.");
        }

        if (manifest.Publisher.OptionValuePrefix < 10000 || manifest.Publisher.OptionValuePrefix > 99999)
        {
            throw new InvalidOperationException("Publisher option value prefix must be between 10000 and 99999.");
        }

        var duplicateTables = manifest.Tables
            .GroupBy(t => t.LogicalName, StringComparer.OrdinalIgnoreCase)
            .Where(group => group.Count() > 1)
            .Select(group => group.Key)
            .ToArray();

        if (duplicateTables.Length > 0)
        {
            throw new InvalidOperationException($"Duplicate table logical name(s): {string.Join(", ", duplicateTables)}.");
        }

        foreach (var table in manifest.Tables)
        {
            if (!table.LogicalName.StartsWith("ccsb_", StringComparison.OrdinalIgnoreCase))
            {
                throw new InvalidOperationException($"Table '{table.LogicalName}' does not use the 'ccsb_' prefix.");
            }

            if (string.IsNullOrWhiteSpace(table.SchemaName) ||
                string.IsNullOrWhiteSpace(table.DisplayName) ||
                string.IsNullOrWhiteSpace(table.DisplayCollectionName) ||
                string.IsNullOrWhiteSpace(table.PrimaryNameDisplayName))
            {
                throw new InvalidOperationException($"Table '{table.LogicalName}' has incomplete metadata.");
            }

            if (!table.OwnershipType.Equals("OrganizationOwned", StringComparison.OrdinalIgnoreCase) &&
                !table.OwnershipType.Equals("UserOwned", StringComparison.OrdinalIgnoreCase))
            {
                throw new InvalidOperationException(
                    $"Table '{table.LogicalName}' must be OrganizationOwned or UserOwned.");
            }
        }
    }
}

internal static class JsonSerialization
{
    public static readonly JsonSerializerOptions Options = new()
    {
        PropertyNameCaseInsensitive = true,
        WriteIndented = true,
        DefaultIgnoreCondition = JsonIgnoreCondition.WhenWritingNull
    };
}

internal sealed class CoreManifest
{
    public string PackageName { get; init; } = string.Empty;
    public string PackageVersion { get; init; } = string.Empty;
    public string Purpose { get; init; } = string.Empty;
    public SolutionDefinition Solution { get; init; } = new();
    public PublisherDefinition Publisher { get; init; } = new();
    public int Lcid { get; init; } = 1033;
    public PrimaryNameDefinition PrimaryName { get; init; } = new();
    public List<TableDefinition> Tables { get; init; } = new();
}

internal sealed class SolutionDefinition
{
    public string UniqueName { get; init; } = string.Empty;
    public string FriendlyName { get; init; } = string.Empty;
    public string Version { get; init; } = string.Empty;
    public string Description { get; init; } = string.Empty;
}

internal sealed class PublisherDefinition
{
    public string UniqueName { get; init; } = string.Empty;
    public string FriendlyName { get; init; } = string.Empty;
    public string CustomizationPrefix { get; init; } = string.Empty;
    public int OptionValuePrefix { get; init; }
    public string Description { get; init; } = string.Empty;
}

internal sealed class PrimaryNameDefinition
{
    public string LogicalName { get; init; } = string.Empty;
    public string SchemaName { get; init; } = string.Empty;
    public int MaxLength { get; init; }
    public string RequiredLevel { get; init; } = string.Empty;
    public string Format { get; init; } = string.Empty;
}

internal sealed class TableDefinition
{
    public string LogicalName { get; init; } = string.Empty;
    public string SchemaName { get; init; } = string.Empty;
    public string DisplayName { get; init; } = string.Empty;
    public string DisplayCollectionName { get; init; } = string.Empty;
    public string PrimaryNameDisplayName { get; init; } = string.Empty;
    public string Description { get; init; } = string.Empty;
    public string OwnershipType { get; init; } = string.Empty;
    public string Category { get; init; } = string.Empty;
}

internal sealed class BuildReport
{
    public DateTime StartedUtc { get; set; }
    public DateTime? CompletedUtc { get; set; }
    public string Mode { get; set; } = string.Empty;
    public string ManifestPath { get; set; } = string.Empty;
    public string SolutionUniqueName { get; set; } = string.Empty;
    public string SolutionVersion { get; set; } = string.Empty;
    public bool Success { get; set; }
    public List<ReportItem> Events { get; } = new();
    public List<ReportItem> Errors { get; } = new();

    public void AddCreated(string stage, string subject, string detail)
    {
        Events.Add(new ReportItem { Stage = stage, Action = "Created", Subject = subject, Detail = detail });
    }

    public void AddSkipped(string stage, string subject, string detail)
    {
        Events.Add(new ReportItem { Stage = stage, Action = "Skipped", Subject = subject, Detail = detail });
    }

    public void AddInfo(string stage, string action, string detail)
    {
        Events.Add(new ReportItem { Stage = stage, Action = action, Subject = string.Empty, Detail = detail });
    }
}

internal sealed class ReportItem
{
    public string Stage { get; set; } = string.Empty;
    public string Action { get; set; } = string.Empty;
    public string Subject { get; set; } = string.Empty;
    public string Detail { get; set; } = string.Empty;
}

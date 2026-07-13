using System;
using Microsoft.Xrm.Sdk;

namespace CCSB.Plugins.Infrastructure
{
    public sealed class PluginExecutionServices
    {
        private PluginExecutionServices(
            IPluginExecutionContext context,
            IOrganizationServiceFactory serviceFactory,
            IOrganizationService organizationService,
            ITracingService tracingService)
        {
            Context = context;
            ServiceFactory = serviceFactory;
            OrganizationService = organizationService;
            TracingService = tracingService;
        }

        public IPluginExecutionContext Context { get; }

        public IOrganizationServiceFactory ServiceFactory { get; }

        public IOrganizationService OrganizationService { get; }

        public ITracingService TracingService { get; }

        public static PluginExecutionServices Create(IServiceProvider serviceProvider)
        {
            ITracingService tracingService = (ITracingService)serviceProvider.GetService(typeof(ITracingService));
            IPluginExecutionContext context = (IPluginExecutionContext)serviceProvider.GetService(typeof(IPluginExecutionContext));
            IOrganizationServiceFactory serviceFactory = (IOrganizationServiceFactory)serviceProvider.GetService(typeof(IOrganizationServiceFactory));
            IOrganizationService organizationService = serviceFactory.CreateOrganizationService(context.UserId);

            return new PluginExecutionServices(context, serviceFactory, organizationService, tracingService);
        }
    }
}

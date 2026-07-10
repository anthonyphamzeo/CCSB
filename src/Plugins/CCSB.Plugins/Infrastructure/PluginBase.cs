using System;
using System.ServiceModel;
using Microsoft.Xrm.Sdk;

namespace CCSB.Plugins.Infrastructure
{
    public abstract class PluginBase : IPlugin
    {
        public void Execute(IServiceProvider serviceProvider)
        {
            if (serviceProvider == null)
            {
                throw new InvalidPluginExecutionException("The plug-in service provider was not supplied.");
            }

            PluginExecutionServices services = PluginExecutionServices.Create(serviceProvider);

            try
            {
                ExecuteDataversePlugin(services);
            }
            catch (FaultException<OrganizationServiceFault> ex)
            {
                services.TracingService.Trace("{0}: Organization service fault: {1}", GetType().FullName, ex);
                throw new InvalidPluginExecutionException("A Dataverse operation failed during plug-in execution.", ex);
            }
            catch (InvalidPluginExecutionException)
            {
                throw;
            }
            catch (Exception ex)
            {
                services.TracingService.Trace("{0}: Unhandled exception: {1}", GetType().FullName, ex);
                throw new InvalidPluginExecutionException("An unexpected error occurred during plug-in execution.", ex);
            }
        }

        protected abstract void ExecuteDataversePlugin(PluginExecutionServices services);
    }
}

# Back-Pressure and MaxConcurrency

Under heavy load, Mule runtime engine (Mule) might not immediately have the
resources available to process a specific event. This issue might occur
because all threads are busy and the current flow’s concurrency is exceeded.
When this occurs, Mule logs the following message: `Flow 'flowName' is unable
to accept new events at this time`  
This message is known as back-pressure. Mule back-pressure actions are
specific to each connector’s source.

When a producer component outputs information at a higher rate than a consumer
component can process it, you can use the `maxConcurrency` parameter to set
the maximum number of concurrent messages that a flow can process at any given
time, whether the components are internal or external, flows or sources, and
so on.

Although Mule applies back-pressure on its own, the `maxConcurrency` parameter
helps to control the flow performance, especially when a backend server may
affect when having high concurrency. See how to set the parameter in the
following example:

    
    
    <flow name="perf-test-flow" maxConcurrency="${flow.max.concurrency}">

Similarly, you can limit the number of records that can be processed in a
batch job by setting the `maxConcurrency` parameter as in the following
example:

    
    
    <batch:job jobName="test-batch" maxConcurrency="${batch.max.concurrency}">

By default, the Flow and Async scopes do not set a `maxConcurrency` limit, but
the Batch Job component limits concurrency to twice the number of available
cores. The capacity of your system also limits concurrency.

## Components with Max Concurrency Settings

The following [components](about-components) provide a max concurrency
setting:

  * Flow scope

  * Scatter-Gather router

  * Async scope

  * Batch Job scope

  * Parallel For Each scope

## Recommendation

Unless a lower concurrency is required to artificially trigger a back-pressure
event, use the default settings, and do not change the max concurrency value.

## See also

  * [Execution Engine Threads and Concurrency](intro-engine)


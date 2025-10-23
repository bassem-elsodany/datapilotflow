# Tuning Recommendations

Mule 4 provides self-tuning execution, which adjusts itself for optimal
performance according to the underlying operating conditions of the
environment where you deploy Mule runtime engine (Mule).  
Self-tuning allows you to focus on the specifics of your application rather
than Mule internals, which eases the optimization process. Additionally, Mule
comes to you already tuned for optimal performance for most common use cases,
and changing any parameter is advised against unless you fully understand the
implications of doing so.

There are tuning recommendations that you can apply at the application level
and benefit your specific use case.

## Repeatable vs Non-repeatable Streaming

Understand which streaming strategy results in the best flow performance for
your use case:  

  * A repeatable stream (read payload more than once)

  * A non-repeatable stream (read payload only once)

See [Repeatable vs Non-repeatable Streaming](tuning-repeatable-nonrepeatable)
for details.

## Back-Pressure and MaxConcurrency

Understand back-pressure and learn how to use the `maxConcurrency` parameter
to tune the number of concurrent messages sent to your flow.

See [Back-Pressure and MaxConcurrency](tuning-backpressure-maxconcurrency) for
details.

## Backend Server Response Time

Understand if the average latency and throughput of backend servers is
limiting the scalability or performance of your application.

See [Backend Server Response Time](tuning-backend-server) for details.

## Caching

Understand when to use cache and which cache-strategy to follow, based on key
aspects of your data. Mule offers some customizable mechanisms, such as Cache
Scope and the HTTP Caching API Gateway policy, to enable cache according to
your needs.

See [Caching](tuning-caching) for details.

## Pooling Profiles

Pooling components helps process simultaneous incoming requests. Understand
how to add `pooling-profile` to connectors when performance tests show that it
is necessary.

See [Pooling Profiles](tuning-pooling-profiles) for details.

## Domains

Using domains provides a central repository for all the shared resources,
facilitating the class-loading process. Domains enhance performance when you
deploy multiple services on the same on-premises instance of Mule runtime
engine.

See [Domains](shared-resources) for details.

## Logging

Understand why asynchronous logging performs better than synchronous logging.

See [Logging](tuning-logging) for details.

## Batch Processing

Mule can process messages in batches, but batch processing requires having
enough available memory to process the threads in parallel, which means moving
the records from persistent storage into RAM in a fixed-size block. Understand
how to configure the batch block size property for your application.

See [Batch Processing](tuning-batch-processing) for details.

## Application Design Best Practices

Following certain practices at the design phase helps you to achieve better
performance for your Mule apps.

See [Application Design](tuning-app-design) for details.

## See Also

  * [Performance Tuning Guide](tuning-guide)


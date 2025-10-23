# Core Components

Like the operations in connectors and modules, Core components are important
building blocks of flows in a Mule app. Core components provide the logic for
processing a Mule event as it travels in a series of linked steps through the
app. Examples include the Scheduler, For Each, and Logger components.

In Studio, Mule components are accessible by clicking **Core** from the Mule
palette.

![Core components in Anypoint Studio](_images/components-core-studio.png)

Notice that the components are subdivided into types, including Batch, Error
Handling, and Flow Control.

## Batch

To process Mule messages in batches, instead of processing them all together,
you can use Batch components, which include:

  * Batch Aggregator

  * Batch Job

  * Batch Step

See [Batch Processors](batch-processing-concept).

## Components

These Core components perform a variety of tasks:

  * [Custom Business Events](business-events-custom): For collecting information about flows and message processors that handle your business transactions. See also [Business Events](business-events).

  * [Dynamic Evaluate](dynamic-evaluate-component-reference): For dynamically selecting a script, instead of forcing you to hardcode it through the Transform Message Component.

  * [Flow Reference](flowref-about): For routing the Mule event to another flow or subflow (and back) within a Mule app.

  * [Logger](logger-component-reference): For logging important information about your Mule app, such as error messages and status notifications.

  * [Parse Template](parse-template-reference): For processing a template and obtaining a result.

  * [Transform Message](transform-component-about): For converting input data to a new output structure or format.

## Endpoints

Endpoints (sometimes called Sources in Studio) include components that
initiate (or trigger) processing in a Mule flow. The [Scheduler](scheduler-
concept) is an endpoint. It triggers a flow to start at a configurable
interval.

Note that some connectors provide listeners that serve as endpoints. Listeners
can trigger a flow when they receive an external request. For example, an HTTP
Listener that is configured for a given URL can trigger a flow when someone or
some process goes to that URL.

## Error Handling

Error handling components route and process Mule errors that occur in a Mule
app:

  * Error Handler

  * On Error Continue

  * On Error Propagate

See [Error Handlers](error-handling)

## Flow Control (Routers)

A Flow Control component (or Router) takes the input Mule event and routes it
to one or more separate sequences of components. Flow Control components
include:

  * Choice

  * First Successful

  * Round Robin

  * Scatter-Gather

For example, a [Choice router](choice-router-concept) applies DataWeave logic
to pick one of two or more routes, where each route is a separate sequence of
event processors.

A [Scatter-Gather router](scatter-gather-concept) router sends the input event
to every route, and each route independently processes the event. After every
route has processed the event, the results from all the routes are combined
together into one output event.

## Scopes

A Scope is a type of component that groups together a sequence of event
processors (such as other Core components and operations from both modules and
connectors) to apply some programming behavior to that isolated sequence of
event processors.

Scopes include these components:

  * Async

  * Cache

  * Flow

  * For Each

  * Try

  * Until Successful

For example, a Try scope lets you isolate and handle any errors that occur in
a particular sequence of flows. So, you might wrap an outbound HTTP Request
connector (and perhaps some other surrounding components before and after the
HTTP Request connector, such as a Transform Message component or a Logging
component) in a Try scope, so if an error results, you can apply logging or
compensation logic specific to that grouping of components. See [Try
Scope](try-scope-concept).

Another example is the For Each (or Foreach) scope, which takes a collection
of data, usually extracted from the current input event, and applies the same
sequence of event processors to every item in the collection. For example, a
For Each scope might be used to process each individual row returned from a
database query or each individual line from a CSV file. See [For Each
Scope](for-each-scope-concept).

## Transformers

Transformers are components you can use to set or remove a part of the Mule
event. Transformers include:

  * [Remove Variable](remove-variable)

  * [Set Payload](set-payload-transformer-reference)

  * [Set Variable](variable-transformer-reference)

## See Also

  * [Connectors and Modules](../../connectors/)


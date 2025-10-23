# Migrating Exception Strategies to Mule Error Handlers

The following examples will guide you through the migration of the different
exception strategies of Mule 3 considering the new error handling components
in Mule 4.

__ |  The examples do not cover the migration of expressions used within the `when` attribute. See [Migrating MEL to DataWeave](migration-mel) for guidance with migrating expressions, and see [Working With Throwables](../../java-module/latest/java-throwable) to use the Java module to analyze exceptions.   
---|---  
  
## Catch Exception Strategy

A Catch Exception Strategy is equivalent to an Error Handler with a single
`on-error-continue` component that accepts all errors, which is the default
configuration:

Mule 3 Example

    
    
    <flow name="catch">
      <!-- flow logic -->
      <catch-exception-strategy>
        <!-- error handling logic -->
      </catch-exception-strategy>
    </flow>

Mule 4 Example

    
    
    <flow name="catch">
      <!-- flow logic -->
      <error-handler>
        <on-error-continue>
          <!-- error handling logic -->
        </on-error-continue>
      </error-handler>
    </flow>

## Rollback Exception Strategy

A simple (no redelivery) rollback exception strategy is equivalent to an error
handler with a single `on-error-propagate` component that accepts all errors,
which is the default configuration:

Mule 3 Example

    
    
    <flow name="rollback">
      <!-- flow logic -->
      <rollback-exception-strategy>
        <!-- error handling logic -->
      </rollback-exception-strategy>
    </flow>

Mule 4 Example

    
    
    <flow name="rollback">
      <!-- flow logic -->
      <error-handler>
        <on-error-propagate>
          <!-- error handling logic -->
        </on-error-propagate>
      </error-handler>
    </flow>

## With Redelivery

  * `idempotent-redelivery-policy` gets renamed to `redelivery-policy`

  * `org.mule.runtime.core.api.exception.MessageRedeliveredException` has been replaced by the `REDELIVERY_EXHAUSTED` error type.

  * `dead-letter-queue` is removed. Any outbound operation performed to publish to a DLQ must be done as part of the handling of the `REDELIVERY_EXHAUSTED` error, for example:

Mule 3 Example

        
        <idempotent-redelivery-policy maxRedeliveryCount="${maxRedeliveryAttempts}">
            <dead-letter-queue>
                <http:request ... />
            </dead-letter-queue>
        </idempotent-redelivery-policy>

Mule 4 Example

        
        <redelivery-policy maxRedeliveryCount="${maxRedeliveryAttempts}"/>
        
        ...
        
        <error-handler>
            <on-error-propagate type="REDELIVERY_EXHAUSTED">
                <http:request ... />
            </on-error-propagate>
        </error-handler>

  * `maxRedelivery` in `rollback-exception-strategy` is not supported anymore. A `<redelivery-policy>` element with `maxRedelivery` must be created inside the `message-source`.

## Choice Exception Strategy

A Choice exception strategy with inner catch/rollback exception strategies is
equivalent to an error handler with on-error components continue/propagate
according to the exception strategy kind, as explained above:

Mule 3 Example

    
    
    <flow name="choice">
      <!-- flow logic -->
      <choice-exception-strategy>
          <rollback-exception-strategy when="#[some_expression_here]">
              <!-- error handling logic -->
          </rollback-exception-strategy>
          <catch-exception-strategy/>
        </choice-exception-strategy>
    </flow>

Mule 4 Example

    
    
    <flow name="choice">
      <!-- flow logic -->
      <error-handler>
        <on-error-propagate when="#[some_expression_here]">
          <!-- error handling logic -->
        </on-error-propagate>
        <on-error-continue/>
      </error-handler>
    </flow>

## Reference Exception Strategy

Considering that the referenced exception strategy has already been migrated
according to the above guidelines, migrating the actual reference is just
adding a reference `error-handler`.

Mule 3 Example

    
    
    <flow name="reference">
      <!-- flow logic -->
      <exception-strategy ref="referencedHandler"/>
    </flow>

Mule 4 Example

    
    
    <flow name="reference">
      <!-- flow logic -->
      <error-handler ref="referencedHandler"/>
    </flow>

## See Also

[Error Handlers](error-handling)

[Blog: A Look into Error Handling in Mule 4
Beta](https://blogs.mulesoft.com/dev/mule-dev/how-to-error-handling-
mule-4-beta/)


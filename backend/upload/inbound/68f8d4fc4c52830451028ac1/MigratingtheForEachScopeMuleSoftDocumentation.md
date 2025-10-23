# Migrating the For Each Scope

Little changed between For Each scope for Mule 3 and Mule 4 except for the use
of DataWeave 2 as the expression language. This little change however has a
huge impact in terms of usability of the component.

In Mule 3, foreach required the input collection to be a Java Iterable, Java
Iterator or Java array. You were always forced to make sure that the input was
in Java format (and therefore, you were forced to know java).

In Mule 4, we support iterating over any array-like structure, regardless of
the format. For example, suppose the following JSON is posted through an HTTP
request:

    
    
    {
      persons: [
        {
          name: 'John Doe',
          age: 34
        },
        {
          name: 'Jane Doe',
          age: 32
        }
      ]
    }

Mule 3 requires the json being transformed to Java first:

Mule 3 example

    
    
    <flow name="persons">
      <http:listener path="person" method="POST" config-ref="http">
      <json:json-to-object-transformer />
      <foreach batchSize="10" collection="#[payload.persons]">
        <flow-ref name="processPerson" />
      </foreach>
    </flow>

In Mule 4, you can just access the persons array in Json format directly:

Mule 4 example

    
    
    <flow name="persons">
      <http:listener path="person" method="POST" config-ref="http">
      <foreach batchSize="10" collection="#[payload.persons]">
        <flow-ref name="processPerson" />
      </foreach>
    </flow>

## See Also

  * [Migrating Exception Strategies](migration-core-exception-strategies)

  * [Migrating from DataWeave 1.0 to 2.x](migration-dataweave)


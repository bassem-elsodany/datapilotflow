# Migrating the Choice Router

Little changed between Choice router for Mule 3 and Mule 4 except for:

  * DataWeave is now the expression language so the when statements are actually going to use it instead of MEL

  * The `<otherwise>` block is now optional

## Expression Language for the When Block

The when expressions need to be changed from MEL to DataWeave. This also mean
that you can leverage DataWeave’s ability to interpret any format to avoid
unnecessary convertions. For example, suppose a flow in which a JSON document
representing a user is posted through HTTP and you want to check if the person
is underage:

Mule 3 Example: MEL

    
    
    <flow name="checkAge">
      <http:listener path="person" method="POST" config-ref="http" />
      <json:json-to-object-transformer />
      <choice>
        <when expression="#[payload.age > 21]">
          <logger message="adult" />
        </when>
        <otherwise>
          <logger message="underage" />
        </otherwise>
      </choice>
    </flow>

With Mule 4, you don’t need to worry about JSON or Java formats and just do:

Mule 4 Example: DataWeave 2

    
    
    <flow name="checkAge">
      <http:listener path="person" method="POST" config-ref="http" />
      <choice>
        <when expression="#[payload.age > 21]">
          <logger message="adult" />
        </when>
        <otherwise>
          <logger message="underage" />
        </otherwise>
      </choice>
    </flow>

## Optional Otherwise

In Mule 3, the `<otherwise>` block was required. Many times in which fallback
logic was not necessary, you ended up with an `<otherwise>` block which just
had an insignificant logger. In Mule 4, the `<otherwise>` block is optional
and you don’t need to specify it if not necessary.

## See Also

[Introduction to Mule 4: Error Handlers](intro-error-handlers)

[Migrating from MEL to DataWeave](migration-mel)

[Migrating from DataWeave 1.0 to 2.x](migration-dataweave)


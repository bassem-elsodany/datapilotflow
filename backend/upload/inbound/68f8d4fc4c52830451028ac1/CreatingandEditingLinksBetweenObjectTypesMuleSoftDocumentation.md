# Creating and Editing Links Between Object Types

The following tasks explain how to create and undo links between object types.

## Link Related Object Types

Linking enables you to join fields from two related object types to create
more useful query results from the unified schema.

  * Before linking object types, be sure to [set the fields to visible](manage-elements-visibility).

  * You can link only to object types that have [Enable collaboration](collaboration#enable-collaboration-on-an-object-type)for any object types you want to link to.

To link object types:

  1. In the API schema navigation, select the object type you want to link from (source).

  2. Scroll to the **Link to another type** pane, and in **Select the type you want to link to (Target menu)** , select the target object.

Anypoint DataGraph detects and displays the primary key or the composite keys
of the target type.

  3. Use the drop-down menu to select the field that will be the foreign key in the source.

The foreign key maps to the primary key on the target type and has the exact
same data type.

If the target type uses composite keys, you must select two fields.

  4. In **New field configurations** , review and edit, if necessary, the name for the linked field.

Anypoint DataGraph creates this field in your current type and links it to the
target type.

  5. (Optional) Hide the foreign key field from the unified schema.

The new field returns the type you’re linking to, so it’s safe to hide the
foreign key unless it has outstanding queries.

![Link configurations detailing linked target type results](_images/link-
object-type.png)

  6. Click **Save changes**.

If you scroll up to the fields pane, an icon shows the fields are now linked:

![Linked object indicated by link icon](_images/linked-type-icon.png)

## Remove a Link Between Object Types

A field can be linked to only one other object type at a time. So if you no
longer need the link, or want to link the field to another object type, you
can remove the original link.

To remove a linked between object types:

  1. From the unified schema, click **List of APIs added** and select the API that contains the object type with the linked field.

  2. In the API schema navigation, select the object type with the linked field, and scroll to the **Link to another type** pane.

  3. Find the link you want to remove and click **>** to open the link details.

  4. Click **Remove Link**.

  5. Click **Save** , and then click **Apply Changes**.

## Additional Resources

  * [How Links Between Object Types Work in Anypoint DataGraph](linking)


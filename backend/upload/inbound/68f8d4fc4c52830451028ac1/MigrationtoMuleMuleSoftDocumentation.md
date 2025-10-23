# Migration to Mule 4

For your Mule 3 apps to take advantage of Mule 4, migrate them to Mule 4
through one of the following processes:

  * A fully manual migration of connectors, modules, transports, expressions, and API gateways to their Mule 4 counterparts.

For guidance with a fully manual migration, see [Prepare to
Migrate](migration-prep) and review [Manual Migration Process](migration-
process).

  * A partially automated migration with the Mule Migration Assistant (MMA), which is available as an open source project on GitHub.

For guidance using MMA to assist in a migration, see the [user documentation
(on GitHub)](https://github.com/mulesoft/mule-migration-
assistant/blob/master/docs/migration-intro.adoc#understand-the-mma-migration-
process). MuleSoft suggests that you try MMA to determine whether you prefer
it to a fully manual migration. Note that you can run MMA on a sample
application by following steps in the [Migration Tutorial (on
GitHub)](https://github.com/mulesoft/mule-migration-
assistant/blob/master/docs/user-docs/migration-tutorial.adoc).

Important

    

**Mule Migration Assistant (MMA) is subject to the terms and conditions
described for[Community](https://www.mulesoft.com/legal/versioning-back-
support-policy#community) connectors. Additionally, Mule Migration Assistant
is distributed under the terms of the [3-Clause BSD
License](https://github.com/mulesoft/mule-migration-
assistant/blob/master/LICENSE.txt).**

A benefit of using MMA is that it automates part of the migration of Mule 3
apps to Mule 4. Though the MMA does not migrate the app entirely, it provides
significant help with the following tasks:

  * Migrating the project structure.

  * Automatically creating descriptor files, such as `pom.xml` or `mule-artifact.json`.

  * Automatically performing many adaptations of the app’s code.

  * Providing guidance on how to manually migrate components and patterns that cannot be migrated automatically.

MMA helps with such tasks, but it does not deliver a fully functional app.
Some additional steps are required. Those steps include testing and can also
include:

  * Manual migration of unsupported components.

  * Manual migration of complex MEL expressions to DataWeave that cannot be automatically converted by MMA.

  * Manual migration of complex DataWeave transformations that cannot be automatically converted by MMA.

  * Prior migration of the DataMapper with the DataWeave Migration tool, before running the MMA.

It is also important to note that the MMA does not support incremental
migrations.


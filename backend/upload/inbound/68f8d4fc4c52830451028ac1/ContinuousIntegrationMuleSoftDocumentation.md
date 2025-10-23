# Continuous Integration

The need for continuous integration (CI) for a project is very important. By
using Maven as your build tool, you can create a build that gets triggered on
every project change, and run all of its unit and functional tests
automatically.

The advantages of CI are:

  * Provides early notification of issues in the software development lifecycle.

  * Ensures code gets fully tested before release.

  * Successfully tested branches ensure better success when merging to the main branch.

## Continuous Integration Objectives

A CI system does all of the following:

  1. Listens for new commits to a project’s source code management system. The CI system watches many branches for new commits. You can either use polling to find new commits, or the management system can trigger events that inform your program of commits.

  2. Pulls the newest branch into a centralized server.

  3. Creates build jobs on a centralized server.

  4. Runs configurable unit and integration tests on the code base that compile, test, package, and deploy the project in a sandbox to ensure the project works correctly.

  5. Stores artifacts in a repository.

  6. Displays the results of each build.

  7. Deploys passing builds to production.

For information about these tools, see their websites.

## MuleSoft CI Tools

You can deploy Mule applications using:

  * [The API Manager](../../api-manager/latest/getting-started-proxy)

  * [The Runtime Manager Agent](../../runtime-manager/runtime-manager-agent)

You can create functional tests with [MUnit Unit Testing](../../munit/2.1/).

The mule-maven-plugin supports deployments to:

  * CloudHub

  * Runtime Fabric

  * On-premises Mule instances

    * Standalone deployment

    * Using Anypoint Runtime Manager REST API

    * Using Runtime Manager agent

For a complete CI example that uses Jenkins and Maven, see the Anypoint
Platform Development: Advanced class on the [MuleSoft training
site](https://training.mulesoft.com/course-catalog). The training site also
includes related classes and certification exams.

## External CI Tools

Popular CI tools are:

  * Jenkins

  * Hudson

  * TeamCity

  * Bamboo

For information about these tools, see their websites.

## Integration Notes

If you’ve chosen to use connectors in your functional test cases, watch out
for potential port conflicts that can occur in a continuous build server.

If your target deployable is a web application and not a Mule application,
consider using Junit Integration Test Runner for running your functional tests
and avoiding port conflicts.

## See Also

  * [Maven Support in Mule](using-maven-with-mule)

  * [MUnit Unit Testing](../../munit/2.1/)


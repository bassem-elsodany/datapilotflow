# Anypoint Platform CLI 4.x Overview

Anypoint Platform CLI is a scripting and command-line tool for Anypoint
Platform and Anypoint Platform Private Cloud Edition (Anypoint Platform PCE).

Use Anypoint Platform CLI commands to automate a subset of product actions
through scripts. Anypoint Platform CLI 4.0 and later can be run only in batch
mode. Interactive mode is no longer supported.

With Anypoint CLI 4.x you can:

  * Enhance your workflow efficiency:  
Streamline your API management and development processes with command-line
tools.

  * Ensure consistency across environments and organizations:  
Apply consistent configurations and policies across different organizations
and environments, ensuring stability and reliability in your operations.

  * Manage your applications effectively:  
Perform a wide range of operations on your APIs and applications, from
deployment to monitoring, all from the command line.

__ |  Anypoint Platform CLI 4.x is not backward compatible. If you are using a version of Anypoint CLI earlier than Anypoint CLI 4.x, [read this first to find out about the differences.](diff-earlier-ver)  
---|---  
  
## Before you begin

Because the Anypoint CLI is built with Node.js, you must:

  1. Install the Node package manager (npm)

  2. Install the Anypoint CLI using npm

After the Anypoint CLI installation, you can run the commands.

For more information, refer to [Install Anypoint CLI](install).

## Syntax

The Anypoint Platform CLI command set has the following syntax:

    
    
    $ anypoint-cli-v4 [command]  [parameters] [flags]

If you run a command and there is an error, the application exits and returns
a description of the issue.

When using multi-option flags in a command, either put the parameter before
the flags:

    
    
    anypoint-cli-v4 governance:api:validate param1 param2 --rulesets value1 --rulesets value2 --rulesets value3

Or use a `--` (two dashes followed by a space) before the parameter:

    
    
    anypoint-cli-v4 governance:api:validate --rulesets value1 --rulesets value2 --rulesets value3 -- param1 param2

__ |  You can write all commands separated by spaces or colons. For example: `runtime-mgr:application:list` can also be `runtime-mgr application list`.   
---|---  
  
## Default Flags

Anypoint Platform CLI commands have the following default flags:

Flag | Description  
---|---  
`--help` |  Displays command usage information  
`--organization` |  Your organization within Anypoint Platform You can also pass this value using the environment variable `export ANYPOINT_ORG=<name>`.  
`--environment` |  Your Anypoint Platform environment You can also pass this value using the environment variable `export ANYPOINT_ENV=<name>`.  
`--host` |  The host of your Anypoint Platform Installation  
This value defaults to `anypoint.mulesoft.com`.  

  * If you are using Anypoint Platform PCE, pass the address where you are hosting the platform.
  * If you are using Anypoint Platform EU Cloud, pass your EU control plane URL.

You can also pass this value using a dedicated environment variable
`ANYPOINT_HOST=<name>`. For example, `ANYPOINT_HOST=my.anypoint.mulesoft.com`.  
  
## Override Order

You can use environment variables to define values in Anypoint CLI. Following
is the override order if you mix environment variable settings with explicit
command line values:

  * Environment variables override credentials file parameters.

  * Command-line parameters override environment variables.

  * If you do not pass a command-line flag, the default profile properties are used.

  * If you do not specify an environment, the default is production.

## Session Timeout

Your Anypoint Platform session expires based on the **Default session
timeout** configured in your Organization settings.

For information about Root Organization settings, see [Manage Root
Organization Settings](../../access-management/managing-business-
groups#manage-root-organization-settings).

## Anonymized Usage Data

To improve the Anypoint CLI experience, MuleSoft gathers anonymized usage
data. You can opt out by setting `collectMetrics` to false in the
`credentials` file.

## See also

  1. [Install](install) Anypoint CLI.

  2. [Authenticate to Anypoint Platform](auth).

  3. [View the list of commands](anypoint-platform-cli-commands) available for the Anypoint Platform actions you can execute using Anypoint CLI.

  4. [Use a Proxy Server](proxy).


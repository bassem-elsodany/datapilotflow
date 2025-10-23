# Mule Upgrade Tool

The Mule upgrade tool is a command line utility for updating and upgrading
standalone on-premise instances of Mule 4. Download the tool and integrate it
with your existing automated processes and workflows by using scripts and cron
jobs.

If the Runtime Manager agent is installed in your current Mule instance, the
upgrade tool also updates the agent version as part of the upgrade process.

Upgrading the Anypoint Monitoring agent isn’t supported. To proceed with an
upgrade, you must first uninstall the agent, and reinstall it after the Mule
instance upgrade is complete. See [Update the Anypoint Monitoring
Agent](../../monitoring/am-installing#update-the-anypoint-monitoring-agent).

The Mule upgrade tool supports upgrading clustered Mule instances by manually
upgrading each node using the tool. For additional information on how to
proceed with the upgrade, see Upgrading Clustered Mule Instances. Though
highly recommended, using the tool is not strictly necessary to upgrade your
current Mule instance. For a completely manual upgrade, see [Upgrading an On-
Premises Mule Instance Managed Through Runtime Manager](../../release-
notes/mule-runtime/updating-mule-4-versions#mulerunvers).

## Before You Begin

Before starting your upgrade, ensure that you have:

  * [The latest available version of Mule upgrade tool](../../release-notes/mule-upgrade-tool/mule-upgrade-tool) so that the tool runs with the latest fixes and security enhancements.

Download the Mule upgrade tool from the [Help
Center](https://help.mulesoft.com/s/).

  * A currently operational Mule 4 instance in _stopped_ status to prepare for the upgrade.

For upgrades of Mule versions between 4.1.1 and 4.1.4 with the Mule upgrade
tool, you must upgrade from any patch update released after January 20, 2022.
Releases of versions 4.1.1 through 4.1.4 _before_ January 20, 2022 are not
supported by the tool, and attempts to upgrade them produce an error message
stating that the Mule version cannot be upgraded without first upgrading to a
supported version (see [Mule Upgrades and Patch Updates](../../release-
notes/mule-runtime/upgrade-update-mule)).

  * The latest Mule runtime engine distribution, downloaded and unpacked in your system.

The Mule upgrade tool requires the full distribution of the Mule runtime.
Ensure you download a full Mule runtime distribution, identified by including
the term `distribution` (and not the term `patch`) in the file name, for
example, for the full distribution of the 20220221 patch for Mule 4.4.0:
`mule-ee-distribution-standalone-4.4.0-20220221.zip`.

Download Mule runtime distributions from the [Help
Center](https://help.mulesoft.com/s/).

  * At least 2 GB of available disk space on the file system and access privileges to install the new Mule distribution.

  * (For Windows environments) The execution policy for Powershell scripts set to **Unrestricted**.

  * If Anypoint Monitoring agent is installed, uninstall it prior to the upgrade.

## Upgrade or Update Mule

__ |  The parameter `<newMuleDistributionAbsolutePath>` refers to the temporary location where the new Mule runtime distribution is unpacked for the upgrade process. After the upgrade is successfully completed, this location is no longer required by the Upgrade Tool and can be safely deleted.   
---|---  
  
To upgrade or update your clustered Mule instances to the latest version:

  1. Navigate to the `$MULE_HOME/tools` directory, where you downloaded the Mule upgrade tool.

  2. Run the `upgrade -n` subcommand, specifying as an argument the absolute path of the directory where the latest Mule runtime distribution is downloaded and unpacked, for example:
         
         $MULE_HOME/tools/upgrade-tool upgrade -n <newMuleDistributionAbsolutePath>

The script outputs the following:

         
         ➜  tools ./upgrade-tool upgrade -n /Users/me/mule-download/upgrade/mule-enterprise-standalone-4.5.0/
         Mule Runtime Upgrade Tool
         ─────────────────────────
         INFO: Initiating upgrade process...
         
         INFO: Upgrading distribution at path [/opt/mule/mule-enterprise-standalone-4.4.0-20221212]
               with version: [4.4.0-20221212] to distribution at path
               [/opt/mule/mule-enterprise-standalone-4.4.0-20230217] with version [4.4.0-20230217] ...
         
         Do you want to proceed with the upgrade?
         To confirm please, enter [yes, no] (default: no): yes
         
         WARN: Unknown file tools/mule-runtime-upgrade-tool-logs/mule-runtime-upgrade-tool-logs.log
         was found in the runtime installation, and will be kept.
         
         WARN: A version in your MULE_HOME directory name was detected:
         /opt/mule/mule-enterprise-standalone-4.4.0-20221212, beware it may not match the current
         installed version inside the directory.
         
         INFO: Upgrade process finished successfully.
         
         Verifying Mule Agent
         ────────────────────
         INFO: Mule Agent not installed, skipping setup

Now that your existing Mule instance is upgraded, you can delete the recently
downloaded version (referenced in the example as
`<newMuleDistributionAbsolutePath>`) as the upgrade tool does not need it
anymore.

## Roll Back an Upgrade or Update

Before starting an upgrade or update process, the Mule upgrade tool generates
a backup of the clustered Mule instance you are upgrading or updating, which
enables you to restore the upgraded or updated clustered Mule instance to its
previous state. The backup is stored in the `$MULE_HOME/.upgrade-tool-backup`
folder.

To perform a rollback:

  1. Navigate to the `$MULE_HOME/tools` directory, where you downloaded the Mule upgrade tool.

  2. Run the `rollback` subcommand, for example:
         
         $MULE_HOME/tools/upgrade-tool rollback

## Solving File Conflicts

The Mule upgrade tool compares configuration files from the _current_ Mule
distribution and the _new_ distribution to detect changes and prevent losing
them. When the Mule upgrade tool detects changes in the _new_ Mule
distribution configuration files, it tries to resolve conflicts automatically
and continue with the upgrade. If conflicts cannot be resolved automatically,
the tool performs the following actions:

  * Fails the execution of the `upgrade` subcommand, showing an error message.

  * Logs the names of the Mule configuration files with conflicts into the log output.

  * Copies the configuration files with conflicts from the `${MULE_HOME}/conf` directory of the current Mule distribution to `${MULE_HOME}/upgrade-tool/mule-config-conflicts/to_review`.

  * Copies the original content of the configuration files from the _new_ Mule distribution to the `${MULE_HOME}/upgrade-tool/mule-configs-conflicts/new-${MULE_HOME_NEW_FOLDER_NAME}` folder.

If the upgrade process fails due to conflicts with the configuration files,
follow the next steps to resolve the conflicts and continue the upgrade
process.

### Steps to Solve Conflicts with Mule Configuration Files

Follow these steps to resolve conflicts during an upgrade:

  1. Inside the `${MULE_HOME}/upgrade-tool/mule-config-conflicts/to_review/` folder of the current Mule distribution that you are upgrading, locate one of the files that has a conflict.

  2. Use any file comparison or `diff` tool to compare the contents of the files in the following paths:

     * `${MULE_HOME}/upgrade-tool/mule-config-conflicts/to_review/fileWithConflicts.conf`

     * `${MULE_HOME}/upgrade-tool/mule-configs-files/new-${MULE_HOME_NEW_FOLDER_NAME}/fileWithConflicts.conf`

  3. After reviewing the differences, merge or discard the changes:

     * If you decide to merge the changes, modify the previous configuration file `${MULE_HOME}/upgrade-tool/mule-config-conflicts/to_review/fileWithConflicts.conf` adding the desired changes from the new configuration file `${MULE_HOME}/upgrade-tool/mule-config-conflicts/new-${MULE_HOME_NEW_FOLDER_NAME}/fileWithConflicts.conf`. Then, copy the merged file to the `${MULE_HOME}/upgrade-tool/mule-config-conflicts/ready` folder.

     * If you decide to discard the changes maintaining your previous configuration, move the previous configuration file `${MULE_HOME}/upgrade-tool/mule-config-conflicts/to_review/fileWithConflicts.conf` to the `${MULE_HOME}/upgrade-tool/mule-config-conflicts/ready` folder.

Note that discarding the changes sometimes lead to using deprecated settings
in the updated Mule distribution.

  4. Repeat steps 1 to 3 for each configuration file in the `${MULE_HOME}/upgrade-tool/mule-config-conflicts/to_review` folder.

  5. Retry running the `upgrade` subcommand.

When the upgrade finishes successfully, the tool deletes the
`${MULE_HOME}/upgrade-tool/mule-config-conflicts` folder to have a clean
environment for future upgrades.

### Unattended Upgrades or Updates

You can perform an unattended upgrade or update by resolving the conflicts in
a different environment before running the upgrade in the target environment.
This procedure works only if the _current_ and _new_ Mule distributions that
you configure in the secondary environment match the versions of the _current_
and _new_ Mule distributions, respectively, that you have in the main
environment:

  1. In an environment where user interaction is possible, review and resolve all the conflicts as explained in Steps to Solve Conflicts with Mule Configuration Files.

  2. In the target environment, copy the files from `${MULE_HOME_WITH_USER_INTERACTION}/upgrade-tool/mule-config-conflicts/ready/` to `${MULE_HOME_WITHOUT_USER_INTERACTION}/upgrade-tool/mule-config-conflicts/ready/`.

  3. Run the `upgrade` subcommand in the target environment.

## Configure Logging for the Mule Upgrade Tool

You can enable debug logging to add detailed information about each operation,
change the folder where the tool stores the logs, and also use a customized
log configuration file for the Mule upgrade tool.

### Specify a Custom Log4j File

By default, the Mule upgrade tool uses the `log4j2-upgrade-tool.xml` file that
is located in the `$MULE_HOME/tools/upgrade-tool` folder.

To use a custom Log4j file, use the `-l` parameter and specify the file name
of the custom Log4j configuration file to use, for example:

    
    
    $MULE_HOME/tools/upgrade-tool -l myLog4j2File.xml upgrade

### Enable DEBUG Level Logs

To enable debug logging:

  1. Open the Log4j file you are using with the tool.

  2. Replace the `level` property value `INFO` with `DEBUG`, in the following line of the Log4j file:
         
         <Logger level="INFO" name="com.mulesoft.runtime.upgrade.tool.service" additivity="false">

### Customize the Logs Output

By default, the Mule upgrade tool stores logs in the `./mule-runtime-upgrade-
tool-logs directory`.

To change the file name, output path, and log pattern:

  1. Open the Log4j file you are using with the tool.

  2. Specify the desired values for the `fileName` and `filePattern` properties:
         
         <RollingFile name="RollingFile"
           fileName="./mule-runtime-upgrade-tool-logs/mule-runtime-upgrade-tool-logs.log"
           filePattern="./mule-runtime-upgrade-tool-logs/$${date:yyyy-MM}/mule-runtime-upgrade-tool-logs-%d{-dd-MMMM-yyyy}-%i.log.gz" >

## Mule Upgrade Tool Subcommands and Options

The following table describes the subcommands and options you can use when
running the Mule upgrade tool:

Subcommand | Description  
---|---  
`upgrade` |  Upgrades the local Mule instance to the latest available version.  
The following are the supported options for this subcommand. | Options | Description  
---|---  
`-n <newMuleDistributionPath>` |  Upgrades the local Mule instance to the distribution that is downloaded and unpacked in your file system. Parameter `<newMuleDistribution>` specifies the path to the new Mule distribution, for example:   
`$ ./upgrade-tool upgrade -n /<newMuleDistributionPath>`  
`-o <localMuleInstancePath>` |  Upgrades the local Mule instance located in path `<localMuleInstancePath>`. This option enables you to upgrade a different Mule instance than the one located in the same `$MULE_HOME` path as the upgrade tool, for example:   
`$ ./upgrade-tool upgrade -o /<localMuleInstancePath>`  
`-d` |  Simulates the upgrade process without performing any permanent changes to the current Mule instance.  
`-f` |  Performs the upgrade without requesting user confirmation for destructive operations like overwriting a backup or removing applied patches.  
`-h` |  Displays the help message for this subcommand.  
  
`rollback` |  Restores the Mule instance to its previous state. This subcommand works only after performing a successful upgrade with the tool.  
The following are the supported options for this subcommand. | Options | Description  
---|---  
`-o <localMuleInstancePath>` |  Restores the local Mule instance located in path `<localMuleInstancePath>`. This option enables you to restore a different Mule instance than the one located in the same `$MULE_HOME` path as the upgrade tool, for example:   
`$ ./upgrade-tool rollback -o /<localMuleInstancePath>`  
`-d` |  Simulates the rollback process without performing any permanent changes to the current Mule instance.  
`-f` |  Restores the Mule instance without requesting user confirmation.  
`-h` |  Displays the help message for this subcommand.  
  
`status` |  Provides information about the current Mule instance, including:

  * The Mule runtime engine version
  * A message confirming that the current Mule instance meets conditions to upgrade or roll back
  * Any existing backup and its location
  * The integrity of the backup, if it exists

  
  
## Troubleshooting Common Errors

The following are some of the most common error messages from the upgrade tool
and include the error description and a proposed solution.

### Missing required subcommand

    
    
    ./upgrade-tool
    
    Mule Runtime Upgrade Tool
    ─────────────────────────
    
    Missing required subcommand
    Usage: upgrade-tool [-hV] [COMMAND]
    Try 'upgrade-tool --help' for more information.

#### Cause

This error indicates that the specified subcommand is either unknown or
missing. The only supported subcommands are `upgrade`, `rollback`, or
`status`.

#### Solution

Ensure you are running the `upgrade-tool` command and specifying any of the
supported subcommands: `upgrade`, `rollback`, or `status`.

The `-h` or `--help` options enable you to get additional details for a
certain subcommand, for example:

    
    
    $ ./upgrade-tool rollback --help

### Missing required option

    
    
    ./upgrade-tool upgrade
    
    Mule Runtime Upgrade Tool
    ─────────────────────────
    
    Missing required option: '--new-mule-distro=<newMuleDistro>'
    Usage: upgrade-tool upgrade [-dfh] -n=<newMuleDistro> [-o=<oldMuleDistro>]
    Try 'upgrade-tool upgrade --help' for more information.

#### Cause

This error indicates that the chosen subcommand needs more arguments, for
example, when upgrading, the argument `--new-mule-distro` is required.

#### Solution

Run the following command to get information about which arguments are
required for a specific subcommand:

    
    
    ./upgrade-tool upgrade --help

After running the command, the tool outputs additional information:

    
    
    Mule Runtime Upgrade Tool
    ─────────────────────────
    
    Usage: upgrade-tool upgrade [-dfh] -n=<newMuleDistro> [-o=<oldMuleDistro>]
    Upgrades a Mule Runtime to a newer version
      -d, --dry-run   Simulate upgrade process without performing any permanent
                        changes to the current Mule Runtime Distribution.
      -f, --force     Perform all the destructive operations like overwriting the
                        backup or removing the applied patches without user
                        confirmation
      -h, --help      Display this help message
      -n, --new-mule-distro=<newMuleDistro>
                      File path of the newer Mule Runtime distribution used for the
                        upgrade
      -o, --old-mule-distro=<oldMuleDistro>
                      File path of Mule Runtime distribution to upgrade

The `Usage:` line specifies which options and arguments are optional by
enclosing them in square brackets (`[`,`]`). Options and arguments without
square brackets are mandatory.

### No space left on device

    
    
    $ ./upgrade-tool upgrade -n /tmp/mule-enterprise-standalone-4.4.0-20211104
    
    Mule Runtime Upgrade Tool
    ─────────────────────────
    
    INFO: Initiating upgrade process...
    INFO: Upgrading distribution at path [/opt/mule-enterprise-standalone-4.4.0-20211026] with version: [4.4.0-20211104] to distribution at path [/tmp/mule-enterprise-standalone-4.4.0-20211104] with version [4.4.0-20211104] ...
    ERROR: Version of new Mule distribution 4.4.0-20211104 should be newer than old Mule distribution: 4.4.0-20211104
    ERROR: There's not enough disk space for performing the upgrade.
    ERROR: No space left on device
    No space left on device

#### Cause

This error indicates that there is no available disk space to run the upgrade.

#### Solution

The tool requires at least 2 GB of space available in the file system in which
the Mule instance is running. Ensure that your system has enough disk space
available and that any other requirements are met.

On Linux environments, use the `df` command to check available disk space:

    
    
    $ df -h /opt
    Filesystem              Size  Used Avail Use% Mounted on
    /dev/mapper/vg-opt      419G  205G  193G  52% /opt

### Version should be newer

    
    
    ./upgrade-tool upgrade -n /tmp/mule-enterprise-standalone-4.4.0-20211104
    
    Mule Runtime Upgrade Tool
    ─────────────────────────
    
    INFO: Initiating upgrade process...
    INFO: Upgrading distribution at path [/opt/mule-enterprise-standalone-4.4.0-20211026] with version: [4.4.0-20211104] to distribution at path [/tmp/mule-enterprise-standalone-4.4.0-20211104] with version [4.4.0-20211104] ...
    ERROR: Version of new Mule distribution 4.4.0-20211104 should be newer than old Mule distribution: 4.4.0-20211104

#### Cause

This error occurs when the upgrade command specifies a new Mule distribution
that is in the same version as the current Mule instance.

#### Solution

Verify that the downloaded Mule distribution is in a later version than your
current Mule instance. If you continue to receive this error message during
the upgrade, it means that the current Mule instance is already updated or
running the latest available version.

### Missing reading permissions

    
    
    ./upgrade-tool upgrade -n /tmp/mule-enterprise-standalone-4.4.0-20211104
    
    Mule Runtime Upgrade Tool
    ─────────────────────────
    
    INFO: Initiating upgrade process...
    INFO: Upgrading distribution at path [/opt/mule-enterprise-standalone-4.4.0-20211026] with version: [4.4.0-20211026] to distribution at path [/tmp/mule-enterprise-standalone-4.4.0-20211104] with version [4.4.0-20211104] ...
    ERROR: Error validating required reading permissions under Mule distribution [/tmp/mule-enterprise-standalone-4.4.0-20211104]
    java.nio.file.AccessDeniedException: /tmp/mule-enterprise-standalone-4.4.0-20211104/lib/mule/mule-module-cache-ee-4.4.0-20211104.jar
    [...]

#### Cause

Read permissions in the new Mule distribution are required but not set for the
user who is performing the upgrade, so that user cannot read the file
referenced in the stack trace.

#### Solution

Obtain read permission for files that the upgrade identifies as unreadable.
Contact your system administrator for assistance, if necessary.

### Missing writing permissions

    
    
    ./upgrade-tool upgrade -n /tmp/mule-enterprise-standalone-4.4.0-20211104
    
    Mule Runtime Upgrade Tool
    ─────────────────────────
    
    INFO: Initiating upgrade process...
    INFO: Upgrading distribution at path [/opt/mule-enterprise-standalone-4.4.0-20211026] with version: [4.4.0-20211026] to distribution at path [/tmp/mule-enterprise-standalone-4.4.0-20211104] with version [4.4.0-20211104] ...
    ERROR: Error validating required writing permissions under Mule distribution [/opt/mule-enterprise-standalone-4.4.0-20211026]
    java.nio.file.AccessDeniedException: /opt/mule-enterprise-standalone-4.4.0-20211026/lib/boot/libwrapper-linux-ppcle-64.so
    [...]

#### Cause

Write permissions in the old Mule distribution are required but not set for
the user who is performing the upgrade, so that user cannot write to the file
referenced in the stack trace.

#### Solution

Obtain write permission to files that the upgrade tool identifies. Contact
your system administrator for assistance, if necessary.

### Mule Runtime should be stopped

    
    
    ./upgrade-tool upgrade -n /tmp/mule-enterprise-standalone-4.4.0-20211104
    
    Mule Runtime Upgrade Tool
    ─────────────────────────
    
    INFO: Initiating upgrade process...
    INFO: Upgrading distribution at path [/opt/mule-enterprise-standalone-4.4.0-20211026] with version: [4.4.0-20211026] to distribution at path [/tmp/mule-enterprise-standalone-4.4.0-20211104] with version [4.4.0-20211104] ...
    ERROR: Mule Runtime should be stopped.
    ERROR: Not all preconditions are met to perform the upgrade. Review the log for details.
    Not all preconditions are met to perform the upgrade. Review the log for details.

#### Cause

The upgrade tool detected that Mule is running.

#### Solution

Stop Mule before starting the upgrade process. To check the current status,
use the command `${MULE_HOME}/bin/mule status`.

### Mule version is not supported for an upgrade

    
    
    ./upgrade-tool upgrade -n /tmp/mule-enterprise-standalone-4.4.0-20211104
    
    Mule Runtime Upgrade Tool
    ─────────────────────────
    
    INFO: Initiating upgrade process...
    INFO: Upgrading distribution at path [/tmp/mule-enterprise-standalone-4.1.1-20211222] with version: [4.1.1] to distribution at path [/tmp/mule-enterprise-standalone-4.4.0-20211026] with version [4.4.0-20211026] ...
    ERROR: Your Mule version cannot be upgraded to the new one, you need to upgrade to a version greater than 4.1.5, or for versions between 4.1.1 to 4.1.4, then packages released after January 20, 2022.
    ERROR: Not all preconditions are met to perform the upgrade. Review the log for details.
    Not all preconditions are met to perform the upgrade. Review the log for details.

#### Cause

The Mule upgrade tool requires both the current Mule instance and the new Mule
instance (`/new-${MULE_HOME_NEW_FOLDER_NAME}`) to be running version 4.1.5 or
later.

#### Solution

Perform a manual upgrade to ensure that the current and new Mule instances are
in version 4.1.5 or later before attempting to upgrade using the Mule upgrade
tool.

## Upgrading Clustered Mule Instances

To upgrade clustered Mule instances, use the Mule upgrade tool to automate the
upgrade process of your local Mule instances by manually upgrading each node.

### Before You Begin

Before starting your upgrade, ensure that you have:

  * The new Mule runtime distribution (target version) and the Mule upgrade tool copied to each node that you are upgrading, to reduce downtime.

  * [The latest available version of Mule upgrade tool](../../release-notes/mule-upgrade-tool/mule-upgrade-tool) so that the tool runs with the latest fixes and security enhancements.

Download the Mule upgrade tool from the [Help
Center](https://help.mulesoft.com/s/).

  * A currently operational Mule 4 instance in _stopped_ status to prepare for the upgrade.

For upgrades of Mule versions between 4.1.1 and 4.1.4 with the Mule upgrade
tool, you must upgrade from any patch update released after January 20, 2022.
Releases of versions 4.1.1 through 4.1.4 _before_ January 20, 2022 are not
supported by the tool, and attempts to upgrade them produce an error message
stating that the Mule version cannot be upgraded without first upgrading to a
supported version (see [Mule Upgrades and Patch Updates](../../release-
notes/mule-runtime/upgrade-update-mule)).

  * The latest Mule runtime engine distribution, downloaded and unpacked in your system.

The Mule upgrade tool requires the full distribution of the Mule runtime.
Ensure you download a full Mule runtime distribution, identified by including
the term `distribution` (and not the term `patch`) in the file name, for
example, for the full distribution of the 20220221 patch for Mule 4.4.0:
`mule-ee-distribution-standalone-4.4.0-20220221.zip`.

Download Mule runtime distributions from the [Help
Center](https://help.mulesoft.com/s/).

  * At least 2 GB of available disk space on the file system and access privileges to install the new Mule distribution.

  * (For Windows environments) The execution policy for Powershell scripts set to **Unrestricted**.

  * If Anypoint Monitoring agent is installed, uninstall it prior to the upgrade.

### Upgrade or Update Mule

__ |  The parameter `<newMuleDistributionAbsolutePath>` refers to the temporary location where the new Mule runtime distribution is unpacked for the upgrade process. After the upgrade is successfully completed, this location is no longer required by the Upgrade Tool and can be safely deleted.   
---|---  
  
To upgrade or update your clustered Mule instances to the latest version:

  1. Navigate to the `$MULE_HOME/tools` directory, where you downloaded the Mule upgrade tool.

  2. Run the `upgrade -n` subcommand, specifying as an argument the absolute path of the directory where the latest Mule runtime distribution is downloaded and unpacked, for example:
         
         $MULE_HOME/tools/upgrade-tool upgrade -n <newMuleDistributionAbsolutePath>

The script outputs the following:

         
         ➜  tools ./upgrade-tool upgrade -n /Users/me/mule-download/upgrade/mule-enterprise-standalone-4.5.0/
         Mule Runtime Upgrade Tool
         ─────────────────────────
         INFO: Initiating upgrade process...
         
         INFO: Upgrading distribution at path [/opt/mule/mule-enterprise-standalone-4.4.0-20221212]
               with version: [4.4.0-20221212] to distribution at path
               [/opt/mule/mule-enterprise-standalone-4.4.0-20230217] with version [4.4.0-20230217] ...
         
         Do you want to proceed with the upgrade?
         To confirm please, enter [yes, no] (default: no): yes
         
         WARN: Unknown file tools/mule-runtime-upgrade-tool-logs/mule-runtime-upgrade-tool-logs.log
         was found in the runtime installation, and will be kept.
         
         WARN: A version in your MULE_HOME directory name was detected:
         /opt/mule/mule-enterprise-standalone-4.4.0-20221212, beware it may not match the current
         installed version inside the directory.
         
         INFO: Upgrade process finished successfully.
         
         Verifying Mule Agent
         ────────────────────
         INFO: Mule Agent not installed, skipping setup

Now that your existing Mule instance is upgraded, you can delete the recently
downloaded version (referenced in the example as
`<newMuleDistributionAbsolutePath>`) as the upgrade tool does not need it
anymore.

Note that every node must be upgraded or updated to the same Mule runtime
version to work.

### Roll Back an Upgrade or Update

Before starting an upgrade or update process, the Mule upgrade tool generates
a backup of the clustered Mule instance you are upgrading or updating, which
enables you to restore the upgraded or updated clustered Mule instance to its
previous state. The backup is stored in the `$MULE_HOME/.upgrade-tool-backup`
folder.

To perform a rollback:

  1. Navigate to the `$MULE_HOME/tools` directory, where you downloaded the Mule upgrade tool.

  2. Run the `rollback` subcommand, for example:
         
         $MULE_HOME/tools/upgrade-tool rollback

Note that every node must be rolled back to the same Mule runtime version to
work.

## See Also

  * [Mule Upgrades and Patch Updates](../../release-notes/mule-runtime/upgrade-update-mule)


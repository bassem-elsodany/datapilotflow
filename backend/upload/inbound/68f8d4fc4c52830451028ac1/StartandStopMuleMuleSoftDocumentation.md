# Start and Stop Mule

Learn how to start and stop Mule runtime engine to deploy Mule applications.
To take full advantage of managing and monitoring features, you can deploy to
the same Mule instance via the Anypoint Runtime Manager.

Mule uses the Java Service Wrapper to control the Java Virtual Machine (JVM)
from your native OS. The wrapper provides many options and features, including
the ability to run Mule as a Unix daemon or install or remove Mule as a
Windows Service. The wrapper can handle system signals and start parameters,
and overall provides much better interaction between the JVM and the
underlying OS.

## Startup and Shutdown Script

The wrapper is called by a script in `$MULE_HOME/bin`.

The following table lists all the parameters that the script accepts:

Parameter | Description  
---|---  
`start` |  Starts Mule in the terminal background.  
`stop` |  Stops Mule. Inbound endpoints process in-flight messages before Mule shuts down. However, after the timeout period, inflight messages that haven’t completed are abandoned and Mule shuts down.  
`restart` |  Restarts Mule.  
`status` |  **(Linux/Unix only.)** Displays the status of the Mule server (`running` or `not running`) and the process PID if running.  
`dump` |  **(Linux/Unix only.)** Dumps the Mule wrapper’s core to `$MULE_HOME/log/mule_ee.log`.  
`console` |  Start Mule in the terminal foreground (console mode). Same as running `mule` with no parameters.  
`install` |  Install Mule as a Windows Service or Linux/Unix Daemon.  
`remove` |  Remove Mule from your Windows Services or Linux/Unix Daemons.  
  
## Start Mule

Start Mule from a command line by changing the directory to where you unzipped
the Mule software distribution and then changing to the bin directory. Run the
following commands:

  * On Windows environments:
        
        $ $MULE_HOME\bin\mule.bat

  * On Linux/Unix environments:
        
        $ $MULE_HOME/bin/mule

These commands run Mule in foreground mode, and the startup script displays
information on the terminal’s standard output. You can’t issue further
commands on the terminal as long as Mule is running.

To stop Mule, press `CTRL-C` in the terminal in which the script is running.

## Start Mule as a Windows Service

To run Mule as a Windows service, you need to install it first by running:

    
    
    $ $MULE_HOME\bin\mule.bat install

Once installed, you can run Mule as a service:

    
    
    $ $MULE_HOME\bin\mule.bat start

__ |  When Windows restarts, the Mule service stops the same way as using the `mule stop` command. The only situation where this could be different is if Windows kills the process due to a timeout.  
---|---  
  
## Start Mule as a Linux/Unix Daemon

To run Mule as a Linux-Unix Daemon, you need to install it first by running:

    
    
    $ $MULE_HOME/bin/mule install

Once installed, you can run Mule as a daemon:

    
    
    $ $MULE_HOME/bin/mule start

__ |  You can also start Mule without executing the installation step, which starts Mule in the background of the current user session.  
---|---  
  
The following example starts Mule from a Unix console:

    
    
    $ $MULE_HOME/bin/mule start
    MULE_HOME is set to ~/Downloads/mule-enterprise-standalone-4.3.0
    MULE_BASE is set to ~/Downloads/mule-enterprise-standalone-4.3.0
    Starting Mule Enterprise Edition...
    Waiting for Mule Enterprise Edition.................
    running: PID:87318

## Start Mule from a Script

To start Mule from a script or from your IDE without using the Java Service
Wrapper, you can use the `org.mule.MuleServer` class. This class accepts a
couple of parameters.

    
    
    org.mule.MuleServer -config mule-config.xml

or

    
    
    org.mule.MuleServer -builder <fully qualified classname> -config appContext.xml

  * **-config** specifies one or more configuration files to use. If this argument is omitted, it will look for and use `mule-config.xml` if it exists.

  * **-builder** is a fully qualified classname of the configuration builder to use. If this is not set, the default `org.mule.config.builders.AutoConfigurationBuilder` is used, which will try to auto-detect configuration files based on available builders. In the most common scenario, this will resolve to `org.mule.config.spring.SpringXmlConfigurationBuilder`.

The easiest way to set the classpath is to include all JARs in the
`./lib/mule` and `./lib/opt` directories of the distribution. You can look at
the dependency report for the server and each of the modules to see exactly
which JARs are required for a particular module.

## Stop Mule

Run the `stop` command to stop Mule.

The following example stops Mule from a Unix console:

    
    
    $ $MULE_HOME/bin/mule stop
    MULE_HOME is set to /Applications/mule-enterprise-standalone-4.3.0
    MULE_BASE is set to /Applications/mule-enterprise-standalone-4.3.0
    Stopping Mule Enterprise Edition...
    Stopped Mule Enterprise Edition.

## See Also

  * [Download, Install, Configure, and Upgrade Mule](runtime-installation-task)

  * [Deploy Mule Applications](deploying)

  * [Anypoint Monitoring](../../monitoring/am-installing)

  * [Runtime Manager](../../runtime-manager/)

  * [Deployment Strategies](../../runtime-manager/deployment-strategies)

  * [Set System Properties when Starting Mule](mule-app-properties-system#set-properties)


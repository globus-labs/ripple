Usage
=====

Once the Ripple agent has been deployed on a device it will report itself to the cloud service. It can then be selected from the management website as an agent to register triggers and perform actions. 

Management Website
==================

https://ripple.globuscs.info/

The management website provides a user-friendly method of defining and managing rules and monitoring events. To use the website you must login with a Globus account. This will determine which agents would will have access to.

Create Rule
-----------

When creating a rule you define must provide a name, trigger, and action. The name of the rule is used in the Manage Rules tabs to identify your rule.  

Triggers
~~~~~~~~

A trigger defines the condition on which to invoke the associated action. The trigger must specify::

    - An agent to operate on - such as your laptop.
    - A service to use to monitor for events - e.g., the local file system.
    - The type of event - file create, delete, modify, etc.
    - And event specific parameters. These may be a directory and regex file pattern matching in the case of file system events, or endpoints in the case of Globus transfer events.

Actions
~~~~~~~

An action specifies how and what will be performed in response to an event that matches the trigger conditions. To define an action you must specify::

    - An agent to perform the action.
    - A service to execute the actions - e.g. the local file system, the cloud, or a batch system.
    - The type of action to perform - such as a transfer or an email
    - Action specific parameters - such as email parameters
    - Target match & replace - regex to modify the trigger event condition.

The target match and replace fields allow your actions to be performed on a different target than the target that raised the event. For example, this could be used to perform an action on the directory containing a new file, rather than the file itself.

Manage Rules
------------

The manage rules tab lets you enable and disable rules.

View Events
-----------

As events are detected they are reported to the cloud service and will be displayed in the events tab. Status updates (such as dispatching jobs and action completion) will also be displayed in the list of events.

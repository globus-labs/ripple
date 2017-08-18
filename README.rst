Ripple - Responsive Storage
==================================
|licence| |build-status| |docs|

.. |licence| image:: https://img.shields.io/badge/License-Apache%202.0-blue.svg
   :target: https://github.com/globus-labs/ripple/blob/lustre/LICENSE
   :alt: Apache Licence V2.0
.. |build-status| image:: https://travis-ci.org/globus-labs/ripple.svg?branch=master
   :target: https://travis-ci.org/globus-labs/ripple
   :alt: Build status
.. |docs| image:: https://readthedocs.org/projects/ripple/badge/?version=latest
  :target: http://ripple.readthedocs.io/en/latest/?badge=latest
  :alt: Documentation Status

Ripple is a prototype responsive storage implementation that allows you to program data-driven events across distributed devices.

Disclaimer
==========

Ripple is an active research project and is not maintained by Globus. Currently, Ripple is developed and supported by just one person. Feel free to contact me at rchard@anl.gov if you have any questions or would like to discuss potential use cases.

Overview
========

Deploying the Ripple agent on a device integrates it into a distributed data management fabric. Once installed, the agent is capable of monitoring the underlying file system for data events (e.g., file being created and modified). Using the management console (https://ripple.globuscs.info/) you can create custom rules comprised of triggers and actions.

You need a Globus (https://www.globus.org/) account in order to register an agent and log into the management console.

QuickStart
==========

1. Download Ripple::

    $ git clone https://github.com/globus-labs/ripple.git

2. Install requirements::

    $ pip3 install -r requirements.txt

3. Install Ripple::

    $ python3 setup install

4. Run it::

    $ ripple

5. Go to https://ripple.globuscs.info/ and create rules

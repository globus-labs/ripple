import configparser
import uuid
import os
import sys
import requests
import json
from queue import Queue
from ripple import Singleton, logger

from globus_sdk import (NativeAppAuthClient, TransferClient,
                        RefreshTokenAuthorizer)

class RippleConfig(object, metaclass=Singleton):
    """
    Stateful storage of loaded configuration values in an object. A
    RippleConfig instantiated with its initializer loads config from
    disk and the DB.
    Because this class is a Singleton, multiple attempts to construct it will
    only return one instance of the class
    """

    def __init__(self, *args, **kwargs):
        """
        Load configuration and get the initial set of rules
        """
        # This is the address for Ripple's REST service. It may be updated
        # from time to time.
        self.api = 'https://m0vc2icw3m.execute-api.us-east-1.amazonaws.com'
        self.client_id = '054b488d-c88f-43b4-9c15-a7399631b4dd'

        config_file = 'ripple/ripple.ini'
        if 'config_file' in kwargs:
            config_file = kwargs['config_file']

        self.load_config_file(config_file)

        ripple_config = os.path.expanduser('~') + '/.ripple/config'
        self.load_ripple_config(ripple_config)

        # Check if it is the first time running (if the
        # config just got made)

        if self.first_time:
            print ("This looks to be the first time running "
                   "an agent on this machine. To register "
                   "the agent with Ripple's service "
                   "please log in with Globus:")
            self.register_agent()

        self.rules = json.loads("{}")
        self.new_rules = False

        self.load_rules()

    def register_agent(self):
        """
        Manage the login with Globus and register
        this agent with the cloud service under this
        user's name. If it is a new user they will have
        account created for them by the service.
        """
        scopes = ("urn:globus:auth:scope:transfer.api.globus.org:all " 
                   "urn:globus:auth:scope:auth.globus.org:view_identities "
                   "openid email profile")

        redirect_uri = 'https://auth.globus.org/v2/web/auth-code'

        client = NativeAppAuthClient(client_id=self.client_id)
        client.oauth2_start_flow(requested_scopes=scopes,
                                 redirect_uri=redirect_uri,
                                 refresh_tokens=True)

        url = client.oauth2_get_authorize_url()

        print('Globus Authorization URL: \n{}'.format(url))

        auth_code = input('Enter the auth code: ').strip()

        token_response = client.oauth2_exchange_code_for_tokens(auth_code)
        id_data = token_response.decode_id_token(client)
        user_email = id_data.get('preferred_username', '')
        transfer_tokens = token_response.by_resource_server['transfer.api.globus.org']

        print('Authenticated as: %s' % user_email)

        # Get a user friendly name for this agent
        agent_name = input('Enter a name for this agent (e.g. laptop): ').strip()
        

        payload = {"access_token": transfer_tokens['access_token'], 
                   "username": user_email, "agent_id": self.endpoint_id,
                   "refresh_token": transfer_tokens['refresh_token'],
                   "expires_at_seconds": transfer_tokens['expires_at_seconds'],
                   "agent_name": agent_name}

        # register this data with the service
        r = requests.post(self.agent_path, json=payload)
        logger.info("Response: %s %s" % (r.status_code, r.reason))

        # Check it was successfully registered, otherwise try again
        # Note: this returns 500 at the moment as I haven't configured
        # a response integration with SNS.
        if r.status_code == requests.codes.ok or r.status_code == 500:
            logger.info("Successfully registered agent.")

    def load_rules(self):
        """
        Use the cloud API to get the rules associated with this endpoint.
        """
        # Note: this payload isn't doing anything yet. the lambda
        # only works with query params.
        payload = {'Endpoint': self.endpoint_id}

        r = requests.post(self.get_rules_path, data=payload)
        data = json.loads(r.text)
        json_rules = []
        for rule in data:
            rule = json.loads(rule)
            new_rule = {}
            new_rule['action'] = {'parameters': rule['action'],
                                  'type': rule['action_value'],
                                  'service': rule['service'],
                                  'target_pathname': '',
                                  'target_match': rule['action']['target_match'],
                                  'target_replace': rule['action']['target_replace']}
            new_rule['trigger'] = {'monitor': rule['monitor'],
                                   'event': rule['trigger_type'],
                                   'parameters': rule['trigger'],
                                   'username': rule['username'],
                                   'globus_name': rule['globus_name'],
                                   'rule_name': rule['rule_name'],
                                   'rule_uuid': rule['rule_uuid'],
                                   'user_uuid': rule['user_uuid'],
                                   'endpoint_uuid': self.endpoint_id,
                                   'access_token': rule['transfer_token']}
            json_rules.append(new_rule)

        # check if there is a new rule
        new = False
        if len(self.rules) != len(json_rules):
            new = True
        else:
            # check if all of the new rules match the old rules
            match = 0
            for r in json_rules:
                for s in self.rules:
                    if r['trigger']['rule_uuid'] == s['trigger']['rule_uuid']:
                        match += 1

            if match != len(self.rules):
                new = True

        if new:
            self.rules = json_rules

            self.new_rules = True
            logger.debug("Loaded new rules!")
            logger.debug(self.rules)

    def load_ripple_config(self, config_file):
        """
        Get or set the unique identifier for this agent.
        """
        self.monitor = 'inotify'
        self.first_time = False
        if not os.path.isdir(os.path.expanduser('~') + '/.ripple'):
            os.mkdir(os.path.expanduser('~') + "/.ripple")
        if not os.path.isfile(config_file):
            # create the config file
            self.endpoint_id = str(uuid.uuid4())
            conf_file = os.path.expanduser('~') + "/.ripple/config"
            with open(conf_file, "w") as text_file:
                text_file.write("[Ripple]\nagent_id: %s\n" % self.endpoint_id)
                text_file.write("api: %s\n" % self.api)
                text_file.write("monitor: inotify\n")
                self.first_time = True

        elif os.path.isfile(config_file):
            config = configparser.ConfigParser()
            config.read(config_file)
            self.endpoint_id = config.get('Ripple', 'agent_id')
            self.api = config.get('Ripple', 'api')
            self.monitor = config.get('Ripple', 'monitor')

        if self.monitor == '':
            self.monitor = 'inotify'

        self.get_rules_path = "%s/LATEST/rule" % self.api
        self.report_event_path = "%s/LATEST/event" % (self.api)
        self.get_jobs_path = "%s/LATEST/job" % (self.api)
        self.update_status_path = "%s/LATEST/job_status" % (self.api)
        self.agent_path = "%s/LATEST/agents" % (self.api)

    def load_config_file(self, config_file):
        # read config from a file
        config = configparser.ConfigParser()
        config.read(config_file)

        self.runner_poll_rate = config.get('Runner', 'poll_rate')

        # Sort out test config
        self.test = config.get('Testing', 'test')
        if self.test == 'True':
            self.test = True
        else:
            self.test = False
        self.test_dir = config.get('Testing', 'test_dir')

        # Set up the queue
        self.queue = Queue(maxsize=0)

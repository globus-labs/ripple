import json
import logging
import os
import datetime
import psycopg2
import psycopg2.extras
import re
import requests
import hashlib
import uuid
from globus_sdk import (AuthClient, TransferClient, ConfidentialAppAuthClient,
                            RefreshTokenAuthorizer, AccessTokenAuthorizer)

logger = logging.getLogger()
logger.setLevel(logging.DEBUG)



def lambda_handler(event, context):
    logger.info('Checking for Globus events.')
    
    
    host = "ripple.cuphw2yd59tr.us-east-1.rds.amazonaws.com"
    dbname = "ripple"
    user = "ripple"
    pw = 'ripplepassword'
    cs = 'dbname=%s user=%s password=%s host=%s' % (dbname, user, pw, host)
    conn = None
    cursor = None
    try:
        conn = psycopg2.connect(cs)
        cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    except Exception as e:
        logger.error("I am unable to connect to the database")
        return
        print (e)
    rules = load_globus_rules(cursor)
    print ('ok, i have some rules.')
    print (rules)
    for rule in rules:
        print (rule)
    tokens = get_tokens(rules)
    for token in tokens:
        # now check for new events.
        events = get_globus_events(token)
        print ("\n\n\nEvents:")
        for event in events:
            print (event)
            process_event(event, rules, cursor)


def load_globus_rules(cursor):
    # host = os.environ['host']
    # dbname = os.environ['dbname']
    # user = os.environ['user']
    # pw = os.environ['password']
    try:
        # find any users with active globus rules
        query = ("select * from users, rules, " + 
                 "triggers, trigger_events, actions, action_types where " +
                 "action_types.id = actions.action_type and actions.id = " + 
                 "rules.action and trigger_events.monitor = " +
                 "'globus' and trigger_events.id = triggers.event and " + 
                 "triggers.id = rules.trigger and rules.enabled = True and " + 
                 "rules.user_id = users.id;")
        print (query)
        cursor.execute(query)
        rules = cursor.fetchall()
        
        json_rules = []
        if len(rules) > 0:
            print ('found some rules.')
            print (rules)
            for rule in rules:
                new_rule = {}
                # ['username', 'endpoint', 'user_id', 'transfer_token', 
                # 'source', 'rule_uuid', 'auth_token', 'trigger_type', 'enabled', 
                # 'monitor', 'event', 'rule_name', 'trigger', 'directory', 'action', 
                # 'schema', 'user_uuid', 'id', 'match', 'globus_name']
                
                new_rule['action'] = {'parameters' : rule['action'],
                                      'type' : rule['action_value'], 
                                      'service' : rule['service'], 
                                      'target_name' : '',
                                      'target_path' : '',
                                      'target_pathname' : '',
                                      'target_match' : '',
                                      'target_replace' : '',
                                      'endpoint_uuid' : rule['action']['endpoint']
                }
                new_rule['trigger'] = {'monitor' : rule['monitor'],
                                      'event' : rule['trigger_type'],
                                      'parameters' : rule['trigger'],
                                      'username' : rule['username'],
                                      'globus_name' : rule['globus_name'],
                                      'rule_name' : rule['rule_name'],
                                      'rule_uuid' : rule['rule_uuid'],
                                      'user_uuid' : rule['user_uuid'],
                                      'access_token' : rule['transfer_token'],
                                      'endpoint_uuid' : "12ac80e8-3b13-11e7-a919-92ebcb67fe33"}
                print ("Adding rule: %s" % new_rule)
                json_rules.append(new_rule)
        return json_rules
    except Exception as e:
        logger.error("I am unable to use the database")
        print (e)

def get_globus_events(token):
    # check for events with this token
    transfer_client = TransferClient(
                    authorizer=AccessTokenAuthorizer(token))

    end_time = datetime.datetime.utcnow()
    start_time = end_time - datetime.timedelta(minutes=5)

    data = transfer_client.task_list(filter="type:TRANSFER,DELETE/request_time:%s,%s" % 
                                     (start_time, end_time), limit=20)
    res_events = []
    for d in data.data:
        new_event = {}
        new_event['username'] = d['username']
        new_event['destination_endpoint_id'] = d['destination_endpoint_id']
        new_event['source_endpoint'] = d['source_endpoint']
        new_event['type'] = d['type']
        new_event['source_endpoint_display_name'] = d['source_endpoint_display_name']
        new_event['destination_endpoint_display_name'] = d['destination_endpoint_display_name']
        new_event['request_time'] = d['request_time']
        new_event['source_endpoint_id'] = d['source_endpoint_id']
        new_event['destination_endpoint'] = d['destination_endpoint']
        new_event['bytes_transferred'] = d['bytes_transferred']
        new_event['status'] = d['status']
        new_event['completion_time'] = d['completion_time']
        new_event['label'] = d['label']
        new_event['filename'] = fix_label(d['label'])
        res_events.append(new_event)
    return res_events

def repeat_event(event, cursor):

    print ("Checking event duplicates")
    hash_object = hashlib.md5(json.dumps(event))
    print(hash_object.hexdigest())

    # check if it is in the database
    try:
        # find any users with active globus rules
        query = ("select * from events where hash = '%s'" % hash_object.hexdigest())
        print (query)
        cursor.execute(query)
        rules = cursor.fetchall()
        if len(rules) > 0:
            return None
    except Exception as e:
        logger.error("I am unable to connect to the database")
        print (e)
    return hash_object.hexdigest()

def process_event(event, rules, cursor):
    event_hash = repeat_event(event, cursor)
    if event_hash == None:
        print ("Event hash already exists")
        #return
    
    print ("processing event")
    event_path = ''
    file_name = ''

    if '/' in event['filename']:
        idx = 1
        if event['filename'][-1] == '/':
            idx = 2
        event_path = event['filename'].rsplit("/", idx)[0]
        file_name = event['filename'].rsplit("/", idx)[1]
    # else:
        # event_path = rule['trigger']['directory']
        # file_name = event['filename']
        # event['filename'] = "%s%s" % (event_path, file_name)
    event['name'] = file_name
    event['path'] = event_path
    event['pathname'] = "%s%s" % (event_path, file_name)

    # Iterate through rules and try to apply them
    for rule in rules[:]:
        print(rule)
        print(rule['trigger']['globus_name'])
        print (event['username'])
        if event['username'] not in rule['trigger']['globus_name']:
            print("Ignoring rule because this is a different user.")
            continue

        if event['type'].lower() in rule['trigger']['event'].lower():
            # if re.match(rule['trigger']['directory'].replace('\\', '/'), 
                        # event_path.replace('\\', '/')) or re.match(rule['trigger']['source_ep'], event['source_endpoint']):
            if 'source' in rule['trigger']['parameters']:
                if not re.match(rule['trigger']['parameters']['source'], event['source_endpoint_id']):
                    print("Failed to match source.")
                    continue
            if 'destination' in rule['trigger']['parameters']:
                if not re.match(rule['trigger']['parameters']['destination'], event['destination_endpoint_id']):
                    print("Failed to match destination.")
                    continue
            print("Matched source/dest")
            if 'match' in rule['trigger']['parameters']:
                if not re.match(rule['trigger']['parameters']['match'], file_name):
                    print("Failed to match filename")
                    print(rule['trigger']['parameters']['match'] + "    " +  file_name)
                    continue
            print("Matched filename")
            event['uuid'] = str(uuid.uuid4())
            event['hash'] = event_hash
            send_event = {'event' : event}
                         # {
                         # 'type' : type(event).__name__,
                         # 'pathname' : event['filename'],
                         # 'path' : event_path,
                         # 'name' : file_name
                         # }
                    # }

            # send the request...
            send_event.update(rule)
            # send_event = set_targets(send_event)
            print (send_event)
            
            # url = "%s/LATEST/event" % (os.environ['cloudapi'])
            url = "https://m0vc2icw3m.execute-api.us-east-1.amazonaws.com/LATEST/event"
            r = requests.post(url, json=send_event)

            
            # send_event = set_target(send_event)
            print("Sent data to queue")

    return None

def fix_label(data):
    # add a /~/ to the event and swap dots and slashes
    if data == None:
        return ""
    if len(data) > 0:
        src_path = str(data.replace("-dot-", "."))
        src_path = str(src_path.replace("-slash-", "/"))
        src_path = str(src_path.replace("-tilda-", "~"))

        if "/~/" not in src_path:
            src_path = "/~/%s" % src_path
        src_path = str(src_path.replace("//", "/"))
        return src_path
    return "/~/Unknown"
        
def get_tokens(rules):
    # do the refresh if needed
    ret_tokens = []
    for rule in rules:
        if rule['trigger']['access_token'] in ret_tokens:
            continue
        else:
            ret_tokens.append(rule['trigger']['access_token'])
    return ret_tokens

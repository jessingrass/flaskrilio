#!/usr/bin/env python
import twilio
from twilio.rest import TwilioRestClient
import ConfigParser
import logging
from sys import exit
import os


class Caller:
    """A simple class to make a call from a twilio number"""

    def __init__(self):
        self.cfg = {}

    def load_config(self, twilio_config):
        with open(twilio_config, 'rb') as cfg:
            cp = ConfigParser.RawConfigParser(allow_no_value=True)
            cp.read(twilio_config)
            self.twilio_config = twilio_config
            self.cfg['twilio_api_ver'] = cp.get('twilio_api', 'twilio_api_ver')
            self.cfg['account_sid'] = cp.get('twilio_api', 'account_sid')
            self.cfg['auth_token'] = cp.get('twilio_api', 'auth_token')
            self.cfg['callback_ip_address'] = cp.get('twilio_api',
                                                     'callback_ip_address')

    def connect_to_twilio(self):
        try:
            self.client = twilio.rest.TwilioRestClient(self.cfg['account_sid'],
                                                  self.cfg['auth_token'])
        except twilio.TwilioRestException as e:
            print "Something went wrong when trying to connect to Twilio..."
            print e


    def make_a_call(self, from_no, to_no):
        try:
            call = self.client.calls.create(to = to_no,
                                           from_= from_no,
                                           url = "http://ec2-54-220-44-187.eu-west-1.compute.amazonaws.com/test.twiml"
                                           #url = "http://twimlets.com/holdmusic?Bucket=com.twilio.music.ambient"
                                            )
            print call.sid
        except twilio.TwilioRestException as e:
            print "Something went wrong when trying to establish a call..."
            print e

    def print_config(self):
        for key,val in self.cfg.items():
            print ("%s=%s" % (key, val))


if '__main__' == __name__:
    import optparse

    # Populate our options, -h/--help is already there for you.
    optp = optparse.OptionParser()
    optp.add_option('-v', '--verbose', dest='verbose', action='count',
                    help="Increase verbosity (specify multiple times for more)")
    optp.add_option('-c', '--config-file', dest='config',
                    help="Config file")
    # Parse the arguments (defaults to parsing sys.argv).
    opts, args = optp.parse_args()

    # Here would be a good place to check what came in on the command line and
    # call optp.error("Useful message") to exit if all it not well.


    # create logger with '__name__'
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.INFO)
    # create console handler with a higher log level
    ch = logging.StreamHandler()
    ch.setLevel(logging.INFO)
    # create formatter and add it to the handlers
    formatter=logging.Formatter('[%(asctime)s] [%(levelname)s]: %(message)s', "%a %Y-%m-%d %H:%M:%S %z")
    ch.setFormatter(formatter)
    logger.addHandler(ch)


    log_level = logging.INFO # default
    if opts.verbose >= 1:
        log_level = logging.DEBUG

    if not opts.config:
        logger.error("No config file specified!")
        exit(1)
    else:
        if os.path.exists(opts.config):
            config=opts.config
        else:
            logger.error("Input file '%s' doesn't exist!" %  opts.config)
            exit(66)

    caller = Caller()
    caller.load_config(twilio_config=opts.config)
    caller.connect_to_twilio()
    caller.print_config()
    caller.make_a_call(from_no="+441353210177", to_no="+447402028595")

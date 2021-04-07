import gettext
import json
import logging
import os
import sys

from bot import commands, connectors, modules, logger, player, services, sound_devices, TeamTalk, vars


class Bot:
    def __init__(self, config_file):
        if os.path.isfile(config_file):
            config_path = config_file
        elif os.path.isfile(os.path.join(vars.directory, config_file)):
            config_path = os.path.join(vars.directory, config_file)
        else:
            sys.exit('Incorrect config file path')
        with open(config_path, 'r', encoding='utf-8') as f:
            self.config = json.load(f)
        self.translation = gettext.translation('TTMediaBot', os.path.join(vars.directory, 'locale'), languages=[self.config['general']['language']])
        self.translation.install()
        self.player = player.Player(self.config['player'])
        self.ttclient = TeamTalk.TeamTalk(self.config['teamtalk'])
        self.tt_player_connector = connectors.TTPlayerConnector(self.player, self.ttclient)
        self.sound_device_manager = sound_devices.SoundDeviceManager(self.config['sound_devices'], self. player, self.ttclient)
        self.service_manager = services.ServiceManager(self.config['services'])
        self.module_manager = modules.ModuleManager(self.player, self.ttclient, self.service_manager)
        self.command_processor = commands.CommandProcessor(self.player, self.ttclient, self.module_manager, self.service_manager)

    def initialize(self):
        if self.config['logger']['log']:
            logger.initialize_logger(self.config['logger'])
        logging.debug('Initializing')
        self.ttclient.initialize()
        self.sound_device_manager.initialize()
        self.service_manager.initialize()
        logging.debug('Initialized')

    def run(self):
        logging.debug('Starting')
        self.ttclient.run()
        self.player.run()
        self.tt_player_connector.start()
        logging.info('Started')
        while True:
            message = self.ttclient.message_queue.get()
            logging.info("New message {text} from {username}".format(text=message.text, username=message.user.username))
            reply_text = self.command_processor(message)
            logging.info('replied {text}'.format(text=reply_text))
            if reply_text:
                self.ttclient.send_message(reply_text, message.user)

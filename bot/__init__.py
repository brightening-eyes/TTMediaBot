import logging
import sys

from bot import cache, commands, config, connectors, logger, modules, player, services, sound_devices, TeamTalk, translator

class Bot:
    def __init__(self, config_file_name, cache_file_name, log_file_name):
        try:
            self.config = config.Config(config_file_name)
        except PermissionError:
            print('The config file is already used by another instance of the bot.')
            sys.exit(1)
        translator.install_locale(self.config['general']['language'])
        try:
            if cache_file_name:
                self.cache = cache.Cache(cache_file_name)
            else:
                self.cache = cache.Cache(self.config["general"]["cache_file_name"])
        except PermissionError:
            print(_('The cache file is already used by another instance of the bot.'))
            sys.exit(1)
        self.log_file_name = log_file_name
        self.player = player.Player(self.config['player'], self.cache)
        self.ttclient = TeamTalk.TeamTalk(self, self.config)
        self.tt_player_connector = connectors.TTPlayerConnector(self.player, self.ttclient)
        self.sound_device_manager = sound_devices.SoundDeviceManager(self.config['sound_devices'], self. player, self.ttclient)
        self.service_manager = services.ServiceManager(self.config['services'])
        self.module_manager = modules.ModuleManager(self.config, self.player, self.ttclient, self.service_manager)
        self.command_processor = commands.CommandProcessor(self, self.config, self.player, self.ttclient, self.module_manager, self.service_manager, self.cache)

    def initialize(self):
        if self.config['logger']['log']:
            logger.initialize_logger(self.config['logger'], self.log_file_name)
        logging.debug('Initializing')
        self.player.initialize()
        self.ttclient.initialize()
        self.sound_device_manager.initialize()
        self.service_manager.initialize()
        logging.debug('Initialized')

    def run(self):
        logging.debug('Starting')
        self.ttclient.run(self.command_processor)
        self.player.run()
        self.tt_player_connector.start()
        logging.info('Started')
        self._close = False
        while not self._close:
            message = self.ttclient.message_queue.get()
            logging.info("New message {text} from {username}".format(text=message.text, username=message.user.username))
            reply_text = self.command_processor(message)
            logging.info('replied {text}'.format(text=reply_text))
            if reply_text:
                self.ttclient.send_message(reply_text, message.user)

    def close(self):
        logging.debug('Closing bot')
        self.player.close()
        self.ttclient.close()
        self.tt_player_connector.close()
        self.config.close()
        self.cache.close()
        self._close = True
        logging.debug('Bot closed')

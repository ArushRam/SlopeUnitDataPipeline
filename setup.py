import os
import sys
import logging
import configparser

class ConfigManager:
    def __init__(self, config_file = '/Users/arushramteke/Projects/Landslide/slopeunits_old/config/slopeunits.ini'):
        config = configparser.ConfigParser()
        config.read(config_file)
        self.config = config['DEFAULT']
        self._setup_grass()
        self._setup_logging()
    
    def _setup_grass(self):
        GISBASE = self.config['GISBASE']
        GISDB = self.config['GISDB']
        LOCATION = self.config['LOCATION']
        MAPSET = self.config['MAPSET']

        # Set GRASS environment variables
        os.environ['GISBASE'] = GISBASE
        os.environ['GISDBASE'] = GISDB
        os.environ['PATH'] += os.pathsep + os.path.join(GISBASE, 'bin')
        os.environ['PATH'] += os.pathsep + os.path.join(GISBASE, 'scripts')
        os.environ['LD_LIBRARY_PATH'] = os.path.join(GISBASE, 'lib')
        os.environ['PYTHONPATH'] = os.path.join(GISBASE, 'etc', 'python')

        sys.path.append('/Applications/GRASS-7.8.app/Contents/Resources/etc/python')

        import grass.script.setup as gsetup
        gsetup.init(GISBASE, GISDB, LOCATION, MAPSET)

    def _setup_logging(self):
        log_filename = os.path.join('/Users/arushramteke/Projects/Landslide/logs', self.config['LOGFILE'])
        logger = logging.getLogger()
        logger.setLevel(logging.DEBUG)

        # Create a file handler for file output
        file_handler = logging.FileHandler(log_filename)
        file_handler.setLevel(logging.DEBUG)

        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.DEBUG)
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)

    def get(self, key):
        return self.config[key]

def setup_dir(dirname):
    if not os.path.exists(dirname):
        os.makedirs(dirname)
        print(f"Directory '{dirname}' created.")
    else:
        print(f"Directory '{dirname}' already exists.")

def get_region_files(region_dir):
    unique_files = set()
    for filename in os.listdir(region_dir):
        if os.path.isfile(os.path.join(region_dir, filename)):
            base_name = os.path.splitext(filename)[0]  # Get the file name without extension
            unique_files.add(base_name)
    return [file for file in unique_files if file[0] != '.']

config_manager = ConfigManager()
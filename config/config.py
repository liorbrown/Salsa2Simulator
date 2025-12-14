"""Configuration management for Salsa2 Simulator."""

class MyConfig:
    """Manages configuration values from the salsa2.config file."""
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(MyConfig, cls).__new__(cls)
            cls._instance.config_mapping = None
        return cls._instance
    
    def _load_config(self):
        """Load all configuration values from file once."""
        if self.config_mapping:
            return
        
        try:
            config_file = '/home/lior/Salsa2Simulator/salsa2.config'
            self.config_mapping = {}
            
            with open(config_file, 'r') as file:
                for line in file:
                    if '=' in line:
                        k, v = line.split('=', 1)
                        k = k.strip()
                        v = v.strip().strip("'")                        
                        
                        self.config_mapping[k] = v
            
        except Exception as e:
            print(f"Error reading configuration file: {e}")
    
    def get_key(self, key):
        """Get a configuration value by key."""
        self._load_config()
        return self.config_mapping.get(key)
    
    def set_key(self, key, value):
        """Set a configuration value by key."""
        self._load_config()
        self.config_mapping[key] = value
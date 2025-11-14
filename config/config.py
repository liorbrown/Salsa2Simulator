"""Configuration management for Salsa2 Simulator."""

class MyConfig:
    """Manages configuration values from the salsa2.config file."""
    
    @staticmethod
    def get_config_value(key):
        """
        Retrieve the value associated with a key from a configuration file.

        Args:
            key (str): The key to search for.

        Returns:
            str: The value associated with the key, or None if the key is not found.
        """
        try:
            config_file = '/home/lior/Salsa2Simulator/salsa2.config'
            with open(config_file, 'r') as file:
                for line in file:
                    # Split the line into key and value
                    if '=' in line:
                        k, v = line.split('=', 1)
                        k = k.strip()  # Remove any extra whitespace
                        v = v.strip().strip("'")  # Remove quotes and whitespace
                        if k == key:
                            return v
            return None  # Return None if the key is not found
        except Exception as e:
            print(f"Error reading configuration file: {e}")
            return None
    
    # Load configuration values
    db_file = get_config_value('db_file')
    conf_file = get_config_value('conf_file')
    log_file = get_config_value('log_file')
    http_proxy = get_config_value('http_proxy')
    https_proxy = get_config_value('https_proxy')
    user = get_config_value('user')
    cache_dir = get_config_value('cache_dir')
    squid_port = get_config_value('squid_port')
    ca_bundle = get_config_value('ca_bundle')


def get_ca_bundle() -> str:
    """Return the CA bundle path from config or a sensible system default."""
    return MyConfig.ca_bundle if getattr(MyConfig, 'ca_bundle', None) else '/etc/ssl/certs/ca-certificates.crt'

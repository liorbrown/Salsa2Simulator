class MyConfig:
    @staticmethod
    def get_config_value(key):
        """
        Retrieve the value associated with a key from a configuration file.

        Args:
            config_file (str): Path to the configuration file.
            key (str): The key to search for.

        Returns:
            str: The value associated with the key, or None if the key is not found.
        """
        try:
            config_file = 'salsa2.config'
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
        
    db_file = get_config_value('db_file')
    log_file = get_config_value('log_file')
    http_proxy = get_config_value('http_proxy')
    https_proxy = get_config_value('https_proxy')
    user=get_config_value('user')
    cache_dir=get_config_value('cache_dir')
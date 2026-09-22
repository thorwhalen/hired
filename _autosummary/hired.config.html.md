# hired.config

Configuration management using Mapping interfaces.

Implement:

- ConfigStore: MutableMapping for configuration management
- Default configurations
- Configuration merging utilities

### Functions

| `get_default_config`()   |    |
|--------------------------|----|
| `load_config`(path)      |    |

### Classes

| [`ConfigStore`](#hired.config.ConfigStore)([base_config])   | Configuration store with cascading defaults.   |
|-------------------------------------------------------------------------------|------------------------------------------------|

### *class* hired.config.ConfigStore(base_config=None)

Bases: [`MutableMapping`](https://docs.python.org/3/library/collections.abc.html#collections.abc.MutableMapping)

Configuration store with cascading defaults.

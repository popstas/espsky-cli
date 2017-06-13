Command-line interface for espsky.com

## Features:
- Reset
- Upload file


## Installation
```
pip install -r requirements.txt
```

## Configuration
Copy `config.default` to `config` and fill your MQTT server credentials.


## Commands

### Reset
```
espsky.py --token token_from_espsky.com reset
```

### Upload file:
```
espsky.py download http://hostname/file.lua
espsky.py download /path/to/file.lua
```

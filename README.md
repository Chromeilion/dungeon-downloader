# Dungeon Downloader

Download, update, and verify your dungeon game files, all with one 
command!

## Install

### Release
Simply download the latest release for your platform from the repo and 
run it like any binary. For example, you can run ```./dungeondownloader```
in a bash terminal.

This method is preferred because you don't need to have python 3.12 
installed.

### Through Pip
Make sure you're using python 3.12, and then simply run: 
```bash
pip install git+https://github.com/Chromeilion/dungeon-downloader.git@main
```

### For Development

For development, you may want to install the package in-place. For this 
make sure to be using python 3.12 and then run:

```bash
git clone https://github.com/Chromeilion/dungeon-downloader.git
```
And then from the project root directory:
```bash
pip install -e .
```

## Usage

When running for the first time, there are two flags that you need to 
provide.

```-r``` or ```--root-domain``` is the root domain from which everything 
is downloaded. For example:

```bash
-r https://cdn.dungeongame.com/Dungeon%20Game
```

```-o``` or ```--output-dir``` is the directory to which to save 
outputs. For example:

```bash
-o "/home/user/games/game_dev/Dungeon Game"
```

Keep in mind, the outputs folder should lead to the root folder 
containing the game files, not the folder above it.

You can also just run the script, and it will prompt you for input if 
the config is missing. The script saves all configuration to a config.json 
file, so you don't need to supply the command line arguments every time.

If you supply command line arguments, they will always overwrite the 
current config.json.

When rerunning the script, only files whose hashes have changed online 
will be updated. To force a full recalculation of all local hashes 
(stored in config.json), you can supply the ```-v``` flag.

For more info just run Dungeon Downloader with the ```-h``` flag.

## Contributions

Contributions are very welcome, just fork and pull request. Make sure to 
be following [PEP 8](https://peps.python.org/pep-0008/) and use 
[NumPy](https://numpydoc.readthedocs.io/en/latest/format.html) style 
docstrings.

Log level is controllable via the DUNGEONDOWNLOADER_LOGLEVEL env 
variable. You can use a .env file if its more convenient.

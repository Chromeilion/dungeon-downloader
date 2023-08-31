# Dungeon Downloader

Download, update, and verify your dungeon game files, all with one 
command!

## Disclaimer

This is a fan made program that relies on an undocumented API and may have 
errors. Use at your own risk.

## Install
### Release
Simply download the latest release for your platform from
[here](https://github.com/Chromeilion/dungeon-downloader/releases) and 
run it like any binary. For example, you can run ```./dungeondownloader```
in a bash terminal. You may need to make the file executible as well 
with something such as ```chmod +x dungeondownloader```.

This method is preferred because you don't need to have python 3.12 
installed.

### Through Pip
Make sure you're using python 3.12, and then simply run: 
```bash
pip install git+https://github.com/Chromeilion/dungeon-downloader.git@main
```
Then to run the module you can just type ```dungeondownloader``` in 
your terminal.
### For Development

For development, you will want to install the package in-place. For this 
make sure to be using python 3.12 and then run:

```bash
git clone https://github.com/Chromeilion/dungeon-downloader.git
```
And then from the project root directory:
```bash
pip install -e .
```
For development, you'll want to run ```python -m dungeondownloader``` 
so that you get Python debug utils as well.

## Usage

When running for the first time, there are two flags that you need to 
provide:

```-r``` or ```--root-domain``` is the root domain from which everything 
is downloaded. For example:

```bash
dungeondownloader -r "put_the_correct_link_here"
```

This link is not provided with this package, you need to 
find it yourself.

```-o``` or ```--output-dir``` is the directory to which to save 
outputs. For example:

```bash
dungeondownloader -o "/home/user/games/game_dev/Dungeon Game"
```

Keep in mind, the outputs folder should lead to the root folder 
containing the game files, not the folder above it.

You can also just run the script without arguments, and it will prompt 
you for input. The script saves all configuration to a config.json 
file, so you don't need to supply the command line arguments every time 
you run it. 

By default, the config file is located in the standard program data 
directory for your OS. For linux that would be 
```$XDG_DATA_DIRS/dungeon-downloader/config.json```.

If you supply command line arguments, they will always overwrite the 
current config file.

### Optional Arguments
These arguments don't get saved, so they need to be present every time the 
script is run if you want to use them.

```-d``` or ```--delete-files``` will delete all files that were 
previously downloaded but are no longer present in the online patch list.

```-v``` or ```--validate``` forces a full recalculation of all local 
hashes (stored in config.json).

For more info just run Dungeon Downloader with the ```-h``` flag.

## Contributions

Contributions are very welcome, just fork and pull request. Make sure to 
be following [PEP 8](https://peps.python.org/pep-0008/) and use 
[NumPy](https://numpydoc.readthedocs.io/en/latest/format.html) style 
docstrings along with [sphinx-autodoc-typehints](https://github.com/tox-dev/sphinx-autodoc-typehints)
to avoid duplicate type hints.

Log level is controllable via the DUNGEONDOWNLOADER_LOGLEVEL env 
variable. You can use a .env file if its more convenient.

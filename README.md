# MITOMI Analysis Package

This Python package condenses the MITOMI initial analysis scripts into a simple suite of command line tools. The package is dependent on Python3, which you can grab with [Homebrew](http://brew.sh):

```
$ brew install python3
```

## Installation

Installation is as simple as cloning this repository and running the setup.py file as below:

```
$ git clone https://github.com/FordyceLab/mitomi_analysis.git
$ cd mitomi_analysis
$ python3 setup.py install
```

If installation is successful, you should now have the `mitomi` command line tool. You can check if this is that case by using the which command:

```
$ which mitomi
```

This command should return `/usr/local/bin/mitomi`. If nothing is returned, your installation was unsuccessful.

After installation, you can optionally remove the repository, as it is no longer needed:

```
$ cd ..
$ rm mitomi_analysis
```

## Usage
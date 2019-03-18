# cogmindmod

This is a tool for patching [Cogmind](https://www.gridsagegames.com/cogmind/)
game files with mod content. Currently it only supports modifying the graphical
tiles.

# Dependencies

You need Python 3 and the following libraries, which can be installed with
`pip`:

* bidict
* imageio
* numpy

# Usage

You can use the tool with:

```
python -m cogmindmod [options] /path/to/cogmind
```

For example, to build the [ASCII + Graphical walls
mod](https://ape3000.com/cogmindmod/) run:

```
python -m cogmindmod \
	--keep "#" \
	--keep-code 318 \
	--custom custom \
	/path/to/cogmind
```

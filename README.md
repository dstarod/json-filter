# JAM - JSON-filter Mongo-like

## Command line JSON filter inspired mongo-shell commands syntax

### How to install

    python3 -m pip install git+https://github.com/dstarod/jam

### How to use

#### Write your filter inline

    wget -qO - "http://rest.best.com/data" | jam -f '{"success": false, "percent": {"$lt": 100}}'

#### Read filters from file

    cat examples/data.json  | jam -ff examples/filter.json

#### Or combine both

    wget -qO - "http://rest.best.com/data" | jam -ff /path/to/filters.json -f "{"errors": {"$size": 2}}"

### What are you can now
    
- $gt
- $gte
- $eq
- $lt
- $lte
- $ne
- $in
- $nin
- $exists
- $regex
- $size

### Colorize output (optional)

    python3 -m pip install Pygments
    cat examples/data.json  | jam -ff examples/filter.json  | pygmentize -l json

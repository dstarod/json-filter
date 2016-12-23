# JSON-filter with MongoDB shell syntax

## Command line JSON filter inspired mongo shell commands syntax

### How to install

    python3 -m pip install git+https://github.com/dstarod/json-filter

### How to use

#### Write your filter inline

    wget -qO - "http://rest.best.com/data" | jf -f '{"jf.tool": true}'

#### Read filters from file

    cat examples/data.json  | jf -ff examples/filter.json

#### Or combine both

    wget -qO - "http://rest.best.com/data" | jf -ff /path/to/filters.json -f "{"errors": {"$size": 2}}"

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
- $and
- $or
- $nor
- $not

### Colorize output (optional)

    python3 -m pip install Pygments
    cat examples/data.json  | jf -ff examples/filter.json -c

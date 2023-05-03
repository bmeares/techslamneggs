# Tech Slam 'N Eggs

This repository contains the code for my May 3, 2023 workshop at Greenville's Tech Slam 'N Eggs. If you enjoyed the talk, [please consider starring Meerschaum on GitHub](https://github.com/bmeares/Meerschaum)!

***Disclaimer***
> This project demonstrates how to build a Meerschaum Compose project in a Docker container, which is up to personal / company preference.  
>
> You can follow all of these steps without Docker, just omit `root_dir` from `mrsm-compose.yaml` (and add `root/` to your `.gitignore`).

## FRED Egg Prices Project

For today's project we want to retrieve and aggregate these data sources from [FRED](https://fred.stlouisfed.org/):

- [Average Price: Eggs, Grade A, Large (Cost per Dozen) in U.S. City Average](https://fred.stlouisfed.org/series/APU0000708111)
- [Average Price: Chicken, Fresh, Whole (Cost per Pound/453.6 Grams) in U.S. City Average](https://fred.stlouisfed.org/series/APU0000706111)


### **Step 0:** Setup

Set the secret URI for `MRSM_SQL_ETL` in `.env` at the root of this project. I'm using the default value for the database that comes with `mrsm stack up -d db`:

```bash
# .env

### Set to a URI
export MRSM_SQL_ETL='postgresql://mrsm:mrsm@localhost:5432/meerschaum'

### or set to JSON
export MRSM_SQL_ETL='{
    "flavor": "timescaledb",
    "username": "mrsm",
    "password": "mrsm",
    "host": "localhost",
    "port": 5432,
    "database": "meerschaum"
}'
```

Build and start the development container:

```bash
docker compose up -d --build
```

Once it's up, hop into the container (we've named the service `mrsm-compose` and the container `techslamneggs`):

```bash
docker compose exec mrsm-compose bash
```
or
```bash
docker exec -it techslamneggs bash
```

> **NOTE:** If you aren't using Docker, remove `root_dir` from `mrsm-compose.yaml` and run these commands:
> 
> ```bash
> pip install meerschaum
> mrsm install plugin compose
> mrsm compose show plugins
> ```

If all went well, you should be able to now use `mrsm` and `mrsm compose`. Some quick clarification:

- `mrsm`  
  Uses the default environment, is not bound to any specific project.

- `mrsm compose`  
  Assumes the environment defined in `mrsm-compose.yaml` to isolate pipes to a single project.

From the name you might see how `mrsm compose` is modeled after `docker compose`. This philosophy makes collaboration simpler by defining the expected environment and pipes in one single manifest (akin to `docker-compose.yaml`).

### **Step 1:** Define the pipes

Under `mrsm-compose.yaml`, define a list of pipes under the keys `sync:pipes`. Let's take a look at the first one:

```yaml
sync:
  pipes:
    - connector: "plugin:fred"
      metric: "price"
      location: "eggs"
      target: "price_eggs"
      columns:
        datetime: "DATE"
      dtypes:
        "PRICE": "float64"
      parameters:
        fred:
          series_id: "APU0000708111"
```

Here's a breakdown of these keys:

- `connector: "plugin:fred"`  
  Fetch new data from the `fred` plugin (`plugins/fred.py`).
- `metric: "price"`  
  What kind of data this pipe holds.
- `location: "eggs"`  
  Qualifying tag to the label `price`.
- `instance` (omitted)  
  We can choose to explicitly state which database on which to host this pipe. The default is this project's default instance (`sql:etl`, more info below).
- `target: "price_eggs"`  
  The target table's name (default would be `plugin_fred_price_eggs`).
- `columns`  
  Immutable indices for the table.
  - `datetime: "DATE"`  
    Range axis for query bounding. May be omitted but is strongly encouraged.
- `dtypes`  
  Optional, explictly state desired data types. The `datetime` index is parsed as `datetime64[ns]` unless set as `Int64` here.
- `parameters`  
  All other pipe parameters may be specified here (e.g. `fetch:backtrack_minutes` is often used in `sql` pipes).

  - `fred`  
    Custom parameters for this project! In this case, `series_id` is used to tell the `fred` plugin which dataset to fetch.

That's a lot of keys! Don't worry if you don't know what to include ― the only required keys are `connector` and `metric`. Start with those and work your way up (like most things, it's an interative process).

**NOTE:** The keys you defined above are the keyword arguments for `mrsm.Pipe()`. If you want to try something out, just run the command

```bash
$ mrsm python
```

and pass them into a `Pipe` object:

```python
>>> import meerschaum as mrsm
>>> pipe = mrsm.Pipe(
...     connector='foo',
...     metric='bar',
...     columns={'datetime': 'date'}
... )
>>> 
```

### **Step 2:** The `fred` Plugin

Now it's time to do the fun part: writing the code to fetch the data. Create `plugins/fred.py` and define a function `fetch()` with this signature:

```python
from typing import Any
import meerschaum as mrsm

def fetch(
    pipe: mrsm.Pipe,
    **kwargs: Any
) -> 'pd.DataFrame':
    ...
```

Whatever is returned from this function will be passed into `Pipe.sync()`, so feel safe to return duplicate data.

**NOTE:** It's not used in this project, but the best way to improve the performance of your plugins is to implement the `--begin` and `--end` flags. To do so, your function would look like this:

```python
from typing import Any, Optional
from datetime import datetime
import meerschaum as mrsm

def fetch(
    pipe: mrsm.Pipe,
    begin: Optional[datetime] = None,
    end: Optional[datetime] = None,
    **kwargs: Any
) -> 'pd.DataFrame':
    ...
```

#### **What about `register()`?**

You may have noticed a function `register()` within `fred.py`. This too is optional but is a good reference to other developers as to what parameters you expect to be present. This function is called when you run the command `register pipe -c plugin:fred -m foo` but is overriden by your compose file.

### **Step 3:** Syncing and Managing the Pipes

Now we're ready to begin syncing. To begin, run this command:

```bash
mrsm compose run
```

The `run` command updates the pipes' registrations and performs a sync one-by-one. You can manually refresh the registration with `up --dry`:

```bash
mrsm compose up --dry
```

Conversely, you can delete the pipes from your project with `down -v`:


```bash
mrsm compose down -v
```

A useful command for comparing the state of your compose file against the registered pipes is `explain`:

```bash
mrsm compose explain
```

Apart from the compose-specific commands (i.e. `run`, `up`, `down`, `explain`, `logs`, `ps`), all other commands are executed as standard Meerschaum actions but with the flag `--tags {project_name}` appended.

> You can investigate `**kwargs` with the command `show arguments`:
> 
> ```python
> mrsm compose show arguments --begin 2023-01-01
> ```

A command you'll likely be running often is `sync pipes`: this will [select the pipes](https://meerschaum.io/reference/pipes/#selecting-your-pipes) from your flags and sync them in parallel. For example, to sync all pipes with the connector `plugin:fred`, we would run this command:

```bash
mrsm compose sync pipes -c plugin:fred
```

Consider this command to sync our SQL pipes within a certain date range:

```bash
mrsm compose sync pipes -c sql:etl --begin 2010-01-01 --end 2015-01-01
```

## Conclusion

There's a *lot* more I could have included, but this should be enough to get you started! If you'd like to see what else Meerschaum can do, you can always play around in a Python REPL by running the command `mrsm compose python`.

## License

The code in this project is released under the Apache License 2.0. In a nutshell, feel free to use this code how you wish, just give the proper credits and don't claim my branding. Have fun!
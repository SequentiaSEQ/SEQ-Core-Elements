# The Rates Server

## Dependencies

You can run `nix-shell` from the top directory for SEQ-Core-Elements
and it will start a shell with the right versions of the right dependencies installed.

See the [README-nix.md](../README-nix.md) in the parent directory for details.

Or if your have the correct `<nixpkgs>` configured, you can install the dependencies with:
```bash
nix-env -iA gerbil-unstable gerbilPackages-unstable.gerbil-utils
```

## Building

You don't actually build: see below the section [Running](#Running)
for running the rates server as a script.

But you can also compile the server so it will run oh so slightly faster.
Once you have installed the dependencies, you can build from this directory with:
```bash
./build.ss
```

Building will create a binary in `./.gerbil/bin/rates`
that you can copy where you need.

## Configuring

Copy the sample `rates-assets-config.json` and `rates-services-config.json`
to your directory `~/.config/sequentia/` (or `${XDG_CONFIG_HOME}/sequentia`)
and edit `rates-services-config.json` to use your keys, as gotten from:

- https://www.coinapi.io/get-free-api-key?email=xxx@yyy (use your email)
- https://coinlayer.com/product (choose the free plan, still need a credit card)
- https://coinmarketcap.com/api/pricing/ (choose the free plan)
- https://site.financialmodelingprep.com/developer/docs/pricing (choose the basic plan)
- https://polygon.io/dashboard/stocks

## Running

Assuming you used have installed the suitable dependencies,
you can run the rates server with:
```bash
./rates.ss
```

If you compiled it, you can instead invoke the binary with:
```bash
./.gerbil/bin/rates
```

Either way, the default behavior is to run the `server` command,
which launches a webserver on `http://localhost:29256`,
only replying to the loopback interface (i.e. from the same host, not other hosts).

You can get a list of commands with:
```bash
./rates.ss help
```

And you can get help for a given command (in this case, `server`) with:
```bash
./rates.ss help server
```

## Available commands

- `./rates.ss server` is the default, starting a webserver on the address specified
  with option `-a $address` or `--address $address` and defaulting to `127.0.0.1:29256`
  if no address is specified.

- `./rates.ss getfeeexchangerates` pretty-prints a JSON data structure suitable to be passed
  to the sequentia `setfeeexchangerates` RPC, e.g. as in:
  `elements-cli setfeeexchangerates $(./rates.ss getfeeexchangerates)`
  This is similar to querying http://localhost:29256/getfeeexchangerates
  except that the latter will print the JSON compactly rather than pretty-printing it.

- `./rates.ss getrates` pretty-print the raw rates for each configured asset,
  as extracted as the median response from configured oracles, in RFU (typically USD),
  without fudge factor of normalization to the decimals available on-chain.
  This is similar to querying http://localhost:29256/getrates
  except that the latter will print the JSON compactly rather than pretty-printing it.

- `./rates.ss help` prints help.

- `meta`, `selfcheck`, `version` are commands that are for internal use only
  and not generally useful to end-users
  (meta can be used for autodetection of completions by zsh;
  selfcheck is for debugging only;
  version currently only print the version of the underlying Gerbil implementation).

TODO: add support for starting the server with SSL support,
and configuring its SSL certificate, etc.
Alternatively, document how to install the rates server behind a SSL reverse proxy.

## Using

The current exchange rates can be queried with
```bash
curl -L http://localhost:29256/getfeeexchangerates
```
and fed into a Sequentia node with:
```bash
elements-cli setfeeexchangerates $(curl -L http://localhost:29256/getfeeexchangerates)
```

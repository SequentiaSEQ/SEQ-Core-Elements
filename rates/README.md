# Rates Server

## Setup

### Installing Nix

If you aren't using Nix yet, install it from the
[Nix download page](https://nixos.org/download/).

On Linux (or Windows using WSL), this is typically as follows
(on macOS, omit the `--daemon`):
```
sh <(curl -L https://nixos.org/nix/install) --daemon
```

Another option is the
[Determinate Nix Installer](https://determinate.systems/posts/determinate-nix-installer/).

### Configuring Nix

Once you installed Nix, you can configure it to use our pre-compiled packages
instead of recompiling everything from source,
by creating or editing your `~/.config/nix/nix.conf` and adding these lines:
```
substituters = https://cache.nixos.org https://cache.nixos.org/ https://mukn.cachix.org
trusted-public-keys = cache.nixos.org-1:6NCHdD59X431o0gWypbMrAURkbJ16ZPMQFGspcDShjY= mukn.cachix.org-1:ujoZLZMpGNQMeZbLBxmOcO7aj+7E5XSnZxwFpuhhsqs=
```

### Using a Nix shell

You may now enter a nix shell, which will provide all the build tools and dependencies
for building the rates server written in [Gerbil Scheme](https://cons.io/):
```shell
nix-shell
```

## Configuration

Copy the sample rates-assets-config.json and rates-services-config.json to `~/.config/sequentia/` and edit rates-services-config.json to use your keys, as gotten from:
* https://www.coinapi.io/get-free-api-key?email=xxx
* https://coinlayer.com/product (choose the free plan, still need a credit card)
* https://coinmarketcap.com/api/pricing/ (choose the free plan)
* https://site.financialmodelingprep.com/developer/docs/pricing (choose the basic plan)
* https://polygon.io/dashboard/stocks

## Running

Build with:
```bash
./build.ss
```
Run the server with
```bash
./rates.ss
```
or the compiled version with
```bash
${GERBIL_PATH}/bin/rates
```
Be sure to hide behind a firewall, with a SSL reverse proxy... or configure the httpd as SSL (to be documented)

## Using

The current exchange rates can be queried with
```bash
curl -L http://localhost:29256/getfeeexchangerates
```
and fed into a Sequentia node with:
```bash
elements-cli setfeeexchangerates $(curl -L http://localhost:29256/getfeeexchangerates)
```
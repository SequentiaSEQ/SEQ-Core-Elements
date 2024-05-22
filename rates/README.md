# Rates Server

## Setup

To enter a development shell with all the dependencies necessary to build and run the project:
```bash
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
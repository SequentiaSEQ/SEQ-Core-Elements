# Building and Running with Nix

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

## Building and Running the Software with Nix

### Building the Software

You can build the whole software package with:
```
nix-build
```

This will create a package under your `/nix/store/` and a symlink to it as `./result`.

### Running the Software as Built

After building the software as above, you can invoke the binaries directly with commands such as:
```
./result/bin/elements-cli
```

You can also install the package in your nix profile with either
`nix-env -i result` (if you use `nix-env`) or
`nix profile install result` (if you use `nix profile`).

TODO: In the future, we will also make it work with `nix flake`, and
when the project is stable and launched maybe submit it upstream onto Nixpkgs.

### Using a Nix shell for Development

To modify the source code and interactively build with all the dependencies
that would be used by Nix, you may enter a nix shell as follows:
```shell
nix-shell
```

You may then configure with the following command:
```bash
configurePhase
```

And build with this one:
```bash
buildPhase
```

Finally, you can run the tests with:
```bash
checkPhase
```

The `./src/` directory will have been added to your `PATH`
so you can run commands simply with:
```bash
elements-cli -?
```

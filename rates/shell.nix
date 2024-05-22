let pkgs = import ./pkgs.nix;
    gerbilPackages = [
        pkgs.gerbilPackages-unstable.gerbil-utils
    ];
in pkgs.mkShell {
    buildInputs = gerbilPackages ++ [
        pkgs.gerbil-unstable
    ];

    # Until gerbil-support includes static compilation objects,
    # let's not use gerbilLoadPath and instead copy the sources into the writable GERBIL_PATH.
    shellHook = ''
        export GERBIL_PATH=$PWD/.gerbil
        mkdir -p $GERBIL_PATH
        chmod -R u+w .gerbil
        #export GERBIL_LOADPATH=${pkgs.gerbil-support.gerbilLoadPath (["$out"] ++ gerbilPackages)}
        for i in ${pkgs.lib.concatStringsSep " " gerbilPackages} ; do
          cp -af $i/gerbil/lib $GERBIL_PATH/
          chmod -R u+w .gerbil
        done
        export GERBIL_BUILD_CORES=$NIX_BUILD_CORES
    '';
}
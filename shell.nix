let
  pkgs = import ./pkgs.nix;
  gerbilDeps = pkgs.gerbilDeps;
in pkgs.mkShell {
  inputsFrom = with pkgs; [
    sequentia
  ];
  buildInputs = (with pkgs; [
    python3
    clang-tools
    gerbil-unstable
  ]);

  # Until gerbil-support includes static compilation objects,
  # let's not use gerbilLoadPath and instead copy the sources into the writable GERBIL_PATH.
  shellHook = ''
    export PATH=$PWD/src:$PATH
    export GERBIL_PATH=$PWD/.gerbil
    mkdir -p $GERBIL_PATH
    chmod -R u+w .gerbil
    #export GERBIL_LOADPATH=${pkgs.gerbil-support.gerbilLoadPath (["$out"] ++ gerbilDeps)}
    for i in ${pkgs.lib.concatStringsSep " " gerbilDeps} ; do
      cp -af $i/gerbil/lib $GERBIL_PATH/
      chmod -R u+w .gerbil
    done
    export GERBIL_BUILD_CORES=$NIX_BUILD_CORES
  '';
}

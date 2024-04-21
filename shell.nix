let
  pkgs = import ./pkgs.nix;
  sequentia = pkgs.sequentia;
in pkgs.mkShell {
  inputsFrom = [
    sequentia
  ];
  buildInputs = [
    pkgs.python3
    pkgs.clang-tools
  ];
}

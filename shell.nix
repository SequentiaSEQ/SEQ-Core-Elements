let
  pkgs = import ./pkgs.nix;
  sequentia = pkgs.sequentia;
in pkgs.mkShell {
  inputsFrom = [
    sequentia
  ];
}

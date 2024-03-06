let 
  pkgs = import ./pkgs.nix;
  sequentia = pkgs.callPackage ./default.nix {};
in pkgs.mkShell {
  inputsFrom = [
    sequentia
  ];
} 

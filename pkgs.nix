let
  systemPkgs = import <nixpkgs> {};
  nixpkgs-repo = systemPkgs.fetchFromGitHub {
    owner = "NixOS";
    repo = "nixpkgs";
    rev = "0deaf4d5d224fac3cb2ae9c92a4e349c277be982";
    sha256 = "sha256-uERpVxRrCUB7ySkGb3NtDmzEkPDn23VfkCtT2hJZty8=";
  };
  pkgs = import nixpkgs-repo {};
in pkgs

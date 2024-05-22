let
  systemPkgs = import <nixpkgs> {};
  nixpkgs-source = systemPkgs.fetchFromGitHub {
    owner = "MuKnIO";
    repo = "nixpkgs";
    rev = "8b9c37af42da9e1c3a48d3befbc87bc83ff939a6";
    sha256 = "sha256-WfiWW430xmb6mhaaDqB93e7gGuIXMV4oWqRXALeNvi8=";
  };
  pkgs = import nixpkgs-source { };
in pkgs

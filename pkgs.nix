let
  systemPkgs = import <nixpkgs> {};
  nixpkgs-repo = systemPkgs.fetchFromGitHub {
    owner = "NixOS";
    repo = "nixpkgs";
    rev = "0deaf4d5d224fac3cb2ae9c92a4e349c277be982";
    sha256 = "sha256-uERpVxRrCUB7ySkGb3NtDmzEkPDn23VfkCtT2hJZty8=";
  };
  nixpkgs-gerbil = systemPkgs.fetchFromGitHub {
    owner = "MuKnIO";
    repo = "nixpkgs";
    rev = "b34dfaf64b324157ee3bed43b319f947ca4e93f1";
    sha256 = "sha256-sY1OtbCe4bYA8/izsR+wMCP+25QvGeeHe6H9eJ3FF0U=";
  };
  pg = import nixpkgs-gerbil {};
  pkgs = import nixpkgs-repo {
    config = {
      packageOverrides = superPkgs: {
        inherit sequentia;
        gerbil-support = pg.gerbil-support;
        gerbil-unstable = pg.gerbil-unstable;
        gerbilPackages-unstable = pg.gerbilPackages-unstable;
      } // superPkgs;
    };
  };
  sequentia = pkgs.callPackage pkg {};
  pkg = { lib
, stdenv
, fetchFromGitHub
, autoreconfHook
, pkg-config
, util-linux
, hexdump
, autoSignDarwinBinariesHook ? null
, wrapQtAppsHook ? null
, boost
, libevent
, miniupnpc
, zeromq
, zlib
, db48
, sqlite
, qrencode
, qtbase ? null
, qttools ? null
, python3
, withGui ? false
, withWallet ? true
}:
stdenv.mkDerivation rec {
  pname = if withGui then "sequentia" else "sequentiad";
  version = "23.2.1";

  src = ./.;

  nativeBuildInputs =
    [ autoreconfHook pkg-config ]
    ++ lib.optionals stdenv.isLinux [ util-linux ]
    ++ lib.optionals stdenv.isDarwin [ hexdump ]
    ++ lib.optionals (stdenv.isDarwin && stdenv.isAarch64) [ autoSignDarwinBinariesHook ]
    ++ lib.optionals withGui [ wrapQtAppsHook ];

  buildInputs = [ boost libevent miniupnpc zeromq zlib ]
    ++ lib.optionals withWallet [ db48 sqlite ]
    ++ lib.optionals withGui [ qrencode qtbase qttools ];

  configureFlags = [
    "--with-boost-libdir=${boost.out}/lib"
    "--disable-bench"
  ] ++ lib.optionals (!doCheck) [
    "--disable-tests"
    "--disable-gui-tests"
  ] ++ lib.optionals (!withWallet) [
    "--disable-wallet"
  ] ++ lib.optionals withGui [
    "--with-gui=qt5"
    "--with-qt-bindir=${qtbase.dev}/bin:${qttools.dev}/bin"
  ];

  # fix "Killed: 9  test/test_bitcoin"
  # https://github.com/NixOS/nixpkgs/issues/179474
  hardeningDisable = lib.optionals (stdenv.isAarch64 && stdenv.isDarwin) [ "fortify" "stackprotector" ];

  nativeCheckInputs = [ python3 ];

  doCheck = false;

  checkFlags =
    [ "LC_ALL=en_US.UTF-8" ]
    # QT_PLUGIN_PATH needs to be set when executing QT, which is needed when testing Bitcoin's GUI.
    # See also https://github.com/NixOS/nixpkgs/issues/24256
    ++ lib.optional withGui "QT_PLUGIN_PATH=${qtbase}/${qtbase.qtPluginPrefix}";

  enableParallelBuilding = true;

  meta = with lib; {
    description = "Sequentia is a Bitcoin sidechain dedicated to asset tokenization and decentralized exchanges";
    homepage = "https://www.github.com/SequentiaSEQ/SEQ-Core-Elements";
    maintainers = [];
    license = licenses.mit;
    platforms = platforms.unix;
  };
}; in
pkgs

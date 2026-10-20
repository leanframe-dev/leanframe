{
  pkgs,
  lib,
  config,
  inputs,
  ...
}:

let
  nixLibraryPath = lib.makeLibraryPath [
    pkgs.stdenv.cc.cc.lib
    pkgs.zlib
  ];
  pythonEnvClean = ''
    export LD_LIBRARY_PATH="${nixLibraryPath}"
    unset PYTHONPATH _PYTHON_HOST_PLATFORM _PYTHON_SYSCONFIGDATA_NAME
  '';
in
{
  # https://devenv.sh/basics/
  env = {
    GREET = "devenv";
    UV_PYTHON_PREFERENCE = "only-system";
    UV_PYTHON_DOWNLOADS = "never";
  };

  # https://devenv.sh/packages/
  packages = [
    pkgs.git
    inputs.nixpkgs-python.packages.${pkgs.stdenv.system}."3.11"
    inputs.nixpkgs-python.packages.${pkgs.stdenv.system}."3.12"
    inputs.nixpkgs-python.packages.${pkgs.stdenv.system}."3.13"
    inputs.nixpkgs-python.packages.${pkgs.stdenv.system}."3.14"

    pkgs.nox
    pkgs.uv
  ];

  # https://devenv.sh/basics/
  enterShell = ''
    ${pythonEnvClean}
  '';

  # https://devenv.sh/tests/
  enterTest = ''
    ${pythonEnvClean}
    nox
  '';

  # See full reference at https://devenv.sh/reference/options/
}

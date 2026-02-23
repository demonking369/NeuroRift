
let
  nixpkgs = fetchTarball "https://github.com/NixOS/nixpkgs/archive/refs/tags/24.05.tar.gz";
  pkgs = import nixpkgs { system = "x86_64-linux"; };
  dev = import ./.idx/dev.nix { inherit pkgs; };
in
  pkgs.mkShell {
    buildInputs = dev.packages;
  }

{
  description = "Decompiler Explorer";

  inputs.flake-utils.url = "github:numtide/flake-utils";
  inputs.nixpkgs.url = "github:NixOS/nixpkgs/nixpkgs-unstable";

  outputs = {
    self,
    nixpkgs,
    flake-utils,
  }:
    flake-utils.lib.eachDefaultSystem (system: let
      pkgs = nixpkgs.legacyPackages.${system};

      linkedin-api = pkgs.python3Packages.buildPythonPackage rec {
        pname = "pyhidra";
        version = "0.5.2";
        src = pkgs.fetchFromGitHub {
          owner = "tomquirk";
          repo = "linkedin-api";
          rev = "4d69958d1e31f9e5d962ef07712162e2dedaf440";
          sha256 = "sha256-HiMcTSlyeI2VTyPj0qWFH2PfQl95DG2hYfWrtmXI+JU=";
        };
        doCheck = false;
      };
    in {
      devShells.default = pkgs.mkShell {
        packages = with pkgs; [
          (python3.withPackages (ps:
            with ps; [
              requests
              beautifulsoup4
              lxml
              frozendict
              linkedin-api
            ]))
        ];
      };
    });
}

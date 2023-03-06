{
  description = "Flake to manage python workspace";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/master";
    flake-utils.url = "github:numtide/flake-utils";
    mach-nix.url = "github:DavHau/mach-nix?ref=3.5.0";
  };

  outputs = { self, nixpkgs, flake-utils, mach-nix }:
    let
      # Customize starts
      python = "python39";
      pypiDataRev = "27c016151ddb624957f29cbd574624d23741e609";
      pypiDataSha256 = "0ck30dvaaps5s8am24kyq46xc0k3dyz36apy9plwf6v09mjy7qvi";
      devShell = pkgs:
        pkgs.mkShell {
          buildInputs = [
            pkgs.erlang
            (pkgs.${python}.withPackages
              (ps: with ps; [
                pip
                black
                pyflakes
                psycopg2
              ]))
	      pkgs.gdal
	      pkgs.geos
              pkgs.nodePackages.prettier
              pkgs.docker
              pkgs.pyright
          ];
        };
      # Customize ends
    in flake-utils.lib.eachDefaultSystem (system:
      let
        pkgs = nixpkgs.legacyPackages.${system};
        # https://github.com/DavHau/mach-nix/issues/153#issuecomment-717690154
        mach-nix-wrapper = import mach-nix { inherit pkgs python pypiDataRev pypiDataSha256; };
        requirements = builtins.readFile ./requirements.txt;
        pythonShell = mach-nix-wrapper.mkPythonShell { inherit requirements; };
        mergeEnvs = envs:
          pkgs.mkShell (builtins.foldl' (a: v: {
            # runtime
            buildInputs = a.buildInputs ++ v.buildInputs;
            # build time
            nativeBuildInputs = a.nativeBuildInputs ++ v.nativeBuildInputs;
          }) (pkgs.mkShell { }) envs);
      in { devShell = mergeEnvs [ (devShell pkgs) pythonShell ]; });
}

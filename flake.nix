{
  description = "Goal Tracker GTK app in Python";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    flake-utils.url = "github:numtide/flake-utils";
  };

  outputs = { self, nixpkgs, flake-utils }:
    flake-utils.lib.eachDefaultSystem (system:
      let
        pkgs = import nixpkgs { inherit system; };
        python = pkgs.python3;
      in {
        packages.default = python.pkgs.buildPythonApplication {
          pname = "goal-tracker";
          version = "0.1.0";
          format = "other";
          src = ./.;

          nativeBuildInputs = [
            pkgs.wrapGAppsHook
            pkgs.gobject-introspection
          ];

          propagatedBuildInputs = with python.pkgs; [
            pygobject3
          ] ++ [
            pkgs.gtk3
            pkgs.gdk-pixbuf
            pkgs.pango
            pkgs.atk
          ];

          installPhase = ''
            runHook preInstall
            mkdir -p $out/bin
            cp ${./main.py} $out/bin/goal-tracker
            chmod +x $out/bin/goal-tracker
            runHook postInstall
          '';

          meta = with pkgs.lib; {
            description = "GTK-based goal tracker app";
            license = licenses.mit;
            platforms = platforms.linux;
          };
        };

        apps.default = {
          type = "app";
          program = "${self.packages.${system}.default}/bin/goal-tracker";
        };

        devShells.default = pkgs.mkShell {
          buildInputs = [
            python
            python.pkgs.pygobject3
            pkgs.gtk3
            pkgs.gobject-introspection
            pkgs.gdk-pixbuf
            pkgs.pango
            pkgs.atk
          ];
        };
      });
}

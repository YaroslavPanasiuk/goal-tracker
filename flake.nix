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

            mkdir -p $out/share/applications
            cp ${./goal-tracker.desktop} $out/share/applications/

            #mkdir -p $out/share/icons/hicolor/16x$16/apps
            #cp ${./icons/16x16.png} $out/share/icons/hicolor/16x16/apps/goal-tracker.png

            #mkdir -p $out/share/icons/hicolor/24x$24/apps
            #cp ${./icons/24x24.png} $out/share/icons/hicolor/24x24/apps/goal-tracker.png

            #mkdir -p $out/share/icons/hicolor/32x$32/apps
            #cp ${./icons/32x32.png} $out/share/icons/hicolor/32x32/apps/goal-tracker.png

            #mkdir -p $out/share/icons/hicolor/64x$64/apps
            #cp ${./icons/64x64.png} $out/share/icons/hicolor/64x64/apps/goal-tracker.png

            #mkdir -p $out/share/icons/hicolor/128x$128/apps
            #cp ${./icons/128x128.png} $out/share/icons/hicolor/128x128/apps/goal-tracker.png

            #mkdir -p $out/share/icons/hicolor/256x$256/apps
            #cp ${./icons/256x256.png} $out/share/icons/hicolor/256x256/apps/goal-tracker.png

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

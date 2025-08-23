{
  description = "Goal Tracker - Python GTK app";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
  };

  outputs = { self, nixpkgs }:
    let
      system = "x86_64-linux";
      pkgs = import nixpkgs { inherit system; };
      python = pkgs.python3;
    in {
      packages.${system}.default = python.pkgs.buildPythonApplication {
        pname = "goal-tracker";
        version = "0.1.0";
        src = ./.;

        format = "other";
        dontUnpack = true;

        installPhase = ''
          mkdir -p $out/bin
          cp ${./goal-tracker.py} $out/bin/goal-tracker
          chmod +x $out/bin/goal-tracker

          # Install desktop entry
          mkdir -p $out/share/applications
          cat > $out/share/applications/goal-tracker.desktop <<EOF
[Desktop Entry]
Type=Application
Name=Goal Tracker
Exec=goal-tracker
Icon=goal-tracker
Terminal=false
Categories=Utility;GTK;
EOF

          # (Optional) install icon if you have goal-tracker.png/svg
          if [ -f ${./goal-tracker.png} ]; then
            mkdir -p $out/share/icons/hicolor/256x256/apps
            cp ${./goal-tracker.png} $out/share/icons/hicolor/256x256/apps/goal-tracker.png
          fi
        '';

        nativeBuildInputs = [
          pkgs.wrapGAppsHook3
        ];

        propagatedBuildInputs = with python.pkgs; [
          pygobject3
        ] ++ [
          pkgs.gtk3
          pkgs.gobject-introspection
        ];

        meta = with pkgs.lib; {
          description = "GTK-based Goal Tracker";
          license = licenses.mit;
          platforms = platforms.linux;
        };
      };

      apps.${system}.default = {
        type = "app";
        program = "${self.packages.${system}.default}/bin/goal-tracker";
      };

      devShells.${system}.default = pkgs.mkShell {
        buildInputs = [
          python
          python.pkgs.pygobject3
          pkgs.gtk3
          pkgs.gobject-introspection
        ];
      };
    };
}

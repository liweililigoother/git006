{ pkgs ? import <nixpkgs> {} }:
pkgs.mkShell {
  buildInputs = [
    pkgs.python3
    pkgs.python3Packages.flask
  ];
  shellHook = ''
    export FLASK_APP=app.py
    export FLASK_ENV=development
    echo "Flask environment set up. Run 'flask run' to start the server."
  '';
}

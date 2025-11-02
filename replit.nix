{ pkgs }: {
  deps = [
    pkgs.python311
    pkgs.python311Packages.tkinter
    pkgs.python311Packages.pillow
    pkgs.xorg.libX11
    pkgs.xorg.libXext
    pkgs.xorg.libXrender
    pkgs.xorg.libXft
  ];
}

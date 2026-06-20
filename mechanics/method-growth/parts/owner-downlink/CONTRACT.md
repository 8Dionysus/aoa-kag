# Owner Downlink Contract

Allowed payload:

- owner-routed adoption boundary packets;
- adoption dossier and downlink packets;
- owner signal packets that keep `kag_may_force_uptake: false`.

Stop-lines:

- no hidden assistant self-adoption;
- no adoption without owner consent;
- no forced uptake;
- no direct ToS runtime write;
- no source-repo mutation.

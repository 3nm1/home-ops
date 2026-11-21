set quiet
set shell := ['bash', '-euo', 'pipefail', '-c']
set script-interpreter := ['bash', '-euo', 'pipefail']

[private]
default:
    just talos -l

[private]
talos-cd := 'ROOT="' + justfile_directory() + '"; if [ -f "${ROOT}/talenv.yaml" ]; then cd "${ROOT}"; else cd "${ROOT}/talos"; fi'

[doc('Apply Talos config to a node')]
[group('talos')]
apply-node ip mode='auto':
    #!/usr/bin/env bash
    set -euo pipefail
    {{ talos-cd }}
    talhelper gencommand apply --node "{{ ip }}" --extra-flags "--mode={{ mode }}" | bash

[doc('Generate Talos configuration')]
[group('talos')]
generate-config:
    #!/usr/bin/env bash
    set -euo pipefail
    {{ talos-cd }}
    talhelper genconfig

[confirm("This will destroy your cluster and reset all nodes to maintenance mode — continue? [y/N]")]
[doc('Reset all nodes back to maintenance mode (DESTRUCTIVE)')]
[group('talos')]
reset:
    #!/usr/bin/env bash
    set -euo pipefail
    {{ talos-cd }}
    talhelper gencommand reset \
        --extra-flags="--reboot --system-labels-to-wipe STATE --system-labels-to-wipe EPHEMERAL --graceful=false --wait=false" | bash

[confirm("This will reset the specified node to maintenance mode — continue? [y/N]")]
[doc('Reset a single node back to maintenance mode (DESTRUCTIVE)')]
[group('talos')]
reset-node ip:
    #!/usr/bin/env bash
    set -euo pipefail
    {{ talos-cd }}
    talhelper gencommand reset --node "{{ ip }}" \
        --extra-flags="--reboot --system-labels-to-wipe STATE --system-labels-to-wipe EPHEMERAL --graceful=false --wait=false" | bash

[doc('Upgrade Kubernetes')]
[group('talos')]
upgrade-k8s:
    #!/usr/bin/env bash
    set -euo pipefail
    {{ talos-cd }}
    VERSION="$(grep '^kubernetesVersion:' talenv.yaml | awk '{print $2}')"
    talhelper gencommand upgrade-k8s --extra-flags "--to ${VERSION}" | bash

[doc('Upgrade Talos on a single node')]
[group('talos')]
upgrade-node ip:
    #!/usr/bin/env bash
    set -euo pipefail
    {{ talos-cd }}
    talhelper gencommand upgrade --node "{{ ip }}" --extra-flags "--timeout=10m" | bash

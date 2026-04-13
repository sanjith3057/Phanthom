#!/bin/bash
# merge.sh - Executes the SLERP and TIES merges via MergeKit
echo "Executing Phase 3: SLERP Merge"
mergekit-yaml src/mergekit/phantom-slerp.yaml outputs/phantom-slerp --copy-trust-remote-code --cuda
echo "SLERP Merge Built."

echo "Executing Phase 4: TIES+DARE Merge"
mergekit-yaml src/mergekit/phantom-ties-dare.yaml outputs/phantom-ties --copy-trust-remote-code --cuda
echo "TIES Merge Built."

echo "All merges successfully written to outputs/ directory."

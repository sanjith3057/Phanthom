Write-Host "Executing Phase 3: SLERP Merge"
mergekit-yaml src/mergekit/phantom-slerp.yaml outputs/phantom-slerp --copy-trust-remote-code --cuda
Write-Host "SLERP Merge Built."

Write-Host "Executing Phase 4: TIES+DARE Merge"
mergekit-yaml src/mergekit/phantom-ties-dare.yaml outputs/phantom-ties --copy-trust-remote-code --cuda
Write-Host "TIES Merge Built."

Write-Host "All merges successfully written to outputs/ directory."

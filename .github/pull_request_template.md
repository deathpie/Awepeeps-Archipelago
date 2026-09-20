## Validation

- [ ] `python scripts/validate_repo.py` passes.
- [ ] `python -m compileall -q scripts` passes when scripts changed.
- [ ] No ROM content, ROM links, common ROM file types, private secrets, credentials, or generated local output was added.
- [ ] Any new APWorld archive has a trustworthy source or release documented in the season README.
- [ ] Active-season YAMLs use literal player names and match the intended game settings.
- [ ] Archived season history was left unchanged unless this pull request explicitly explains the correction.
- [ ] New session inputs were reviewed with `scripts/scaffold_session.py --dry-run`, and generated artifacts were reviewed with `scripts/publish_session_artifacts.py --dry-run` when applicable.

## Manual review notes

<!-- Mention host settings, local ROM filename requirements, APWorld installation notes, or intentional spoiler files. -->

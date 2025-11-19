# Release Preparation Checklist

This checklist captures the remaining tasks to prepare doctk for public v0.1.0 release.

## Current Status

**MVP Development**: ✅ Complete (749 tests passing)
- All three specs (core-integration, vscode-extension, language-server) are 100% done
- Documentation updated and accurate
- GitHub Pages deployment configured

**Release Status**: 🚧 Pre-Release (distribution not yet decided)

---

## Decision Points

### 1. Distribution Strategy

- [ ] **Decide: Publish to PyPI or keep local-only?**

  **Options:**
  - **A. PyPI + Marketplace** (full public release)
    - Pros: Easy installation (`pip install doctk`), wide distribution
    - Cons: Need to maintain package, handle support
  - **B. Local-only + GitHub Releases** (developer-focused)
    - Pros: Simple, no PyPI maintenance
    - Cons: Manual installation required

  **Action**: Discuss and decide which approach fits project goals

- [ ] **If PyPI: Check name availability**
  - Visit https://pypi.org/project/doctk/ to verify name is available
  - If taken, decide on alternative name (e.g., `python-doctk`, `doc-toolkit`)

- [ ] **If PyPI: Decide on VS Code Marketplace**
  - Marketplace typically expects Python dependency on PyPI
  - Can still distribute via `.vsix` if not publishing to marketplace

---

## Branding & Assets

- [ ] **Design logo/icon**
  - Create icon.png for VS Code extension (128x128px recommended)
  - Consider creating variations for different contexts
  - Tools: Figma, Canva, or AI generation (DALL-E, Midjourney)

- [ ] **Create social media preview image** (optional)
  - For GitHub repository social preview
  - Recommended size: 1280x640px

- [ ] **Update extension branding**
  - Add icon to `extensions/doctk-outliner/icon.png`
  - Update `package.json` with icon path
  - Test appearance in VS Code marketplace preview

---

## Documentation for End Users

- [ ] **Write user-focused installation guide**
  - Separate from developer setup
  - Clear prerequisites (Python 3.12+, VS Code)
  - Step-by-step instructions with screenshots

- [ ] **Create quick start tutorial**
  - 5-minute walkthrough
  - Simple real-world example
  - Video or animated GIFs (optional but recommended)

- [ ] **Document common workflows**
  - REPL usage examples
  - Script file execution patterns
  - VS Code extension usage

- [ ] **Add troubleshooting guide**
  - Common installation issues
  - VS Code extension activation problems
  - LSP server connection issues

---

## Packaging (If Publishing)

### Python Package (PyPI)

- [ ] **Verify package metadata**
  - Check `pyproject.toml` completeness
  - Add classifiers for PyPI
  - Verify dependencies are correct

- [ ] **Test local build**
  - Run `uv build` or `python -m build`
  - Verify dist/ contains .whl and .tar.gz

- [ ] **Test installation from built package**
  - Create fresh virtual environment
  - Install from local .whl
  - Verify CLI works: `doctk --help`

- [ ] **Upload to TestPyPI first**
  - Register at https://test.pypi.org
  - Upload: `twine upload --repository testpypi dist/*`
  - Test install: `pip install --index-url https://test.pypi.org/simple/ doctk`

- [ ] **Upload to PyPI**
  - Only after TestPyPI validation
  - Upload: `twine upload dist/*`
  - Verify at https://pypi.org/project/doctk/

### VS Code Extension (Marketplace)

- [ ] **Set up Azure DevOps account**
  - Required for VS Code marketplace publishing
  - Create organization at https://dev.azure.com

- [ ] **Generate Personal Access Token**
  - Needed for `vsce` publishing
  - Follow: https://code.visualstudio.com/api/working-with-extensions/publishing-extension

- [ ] **Update extension for marketplace**
  - Add publisher name to `package.json`
  - Add icon, categories, keywords
  - Add gallery banner color/theme

- [ ] **Publish to marketplace**
  - Run `vsce publish`
  - Wait for review/approval
  - Monitor marketplace listing

---

## GitHub Release

- [ ] **Write changelog**
  - Summarize all features implemented
  - List breaking changes (if any)
  - Acknowledge contributors

- [ ] **Create GitHub release**
  - Tag: `v0.1.0`
  - Title: "v0.1.0 - Initial Release"
  - Description: Use changelog content
  - Attach: `.vsix` file as release asset

- [ ] **Update documentation links**
  - Ensure installation instructions point to release
  - Update badges if needed

---

## Testing on Clean Machine

- [ ] **Test PyPI installation** (if published)
  - Fresh VM or container
  - `pip install doctk`
  - Run basic commands

- [ ] **Test VS Code extension installation**
  - Fresh VS Code instance
  - Install from `.vsix` or marketplace
  - Verify all features work

- [ ] **Test on Windows** (if supporting)
  - Installation process
  - CLI commands
  - VS Code extension

- [ ] **Test on macOS** (if supporting)
  - Installation process
  - CLI commands
  - VS Code extension

---

## Announcement & Promotion (Optional)

- [ ] **Write announcement post**
  - What is doctk
  - Key features
  - Installation instructions
  - Link to documentation

- [ ] **Share on platforms**
  - Reddit: r/Python, r/programming
  - Hacker News
  - Dev.to blog post
  - Twitter/X
  - LinkedIn

- [ ] **Create demo video** (optional)
  - Screen recording showing key features
  - Upload to YouTube
  - Embed in README

---

## Success Criteria

Before calling v0.1.0 "released", ensure:

- ✅ All MVP features implemented and tested
- ✅ Documentation complete and accurate
- ✅ Installation works on clean machine
- ✅ Distribution method decided and implemented
- ✅ GitHub release created with assets
- ✅ Users can actually install and use the project

---

## Notes

- **Current state**: MVP is complete, but distribution strategy not decided
- **Priority**: Decide PyPI vs local-only first, as it affects all other tasks
- **Timeline**: No rush - take time to get branding and documentation right
- **Philosophy**: "Release when ready" - quality over speed

---

## Future Considerations (Post-Release)

- CI/CD for automated releases
- Automated changelog generation
- Release notes automation
- Marketplace auto-updates
- Version bump automation

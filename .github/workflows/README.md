# About .github/workflows

This project was deployed to the edge with Gitub Actions. Each edge device is its own self-hosted Action Runner that runs the `deploy-to-jetsons.yml` workflow on each git commit.

See [scripts/gh_setup.sh](scripts/gh_setup.sh)

Add the `--do-github` option when running `scripts/system-install.sh`

Github Actions were determined to be a bad fit on the edge. Github will automatically de-register any self-hosted action runners that cannot connect for a short window. The edge devices regularly passed that window.

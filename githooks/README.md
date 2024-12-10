### Adding Git hooks

For adding repository git hooks needs to present at

```bash
git config core.hookspath
```

This setting is currently configured by DevProd scripts and is set to
following global path

```
/usr/local/gitconfig/hooks/
```

### Conundrum

As of today git doesn't allow to configure multiple directories for
having these git hooks. Either git hooks present in

* .git/hooks/<Here> [Local]
* /usr/local/gitconfig/hooks [Global]

can be present for these hooks to be present. Both cannot be applicable simultaneously!

### Suggested Approach

Usually the go forward for this problem is to have a directive in respective
global hooks is to call the local hooks if present and then continue for global hooks

Code from current pre-push script present in global directive
```bash
# By default, a global hook runs *instead* of any local hook, but we also want to
# run any local pre-push hook first, and propagate non-zero exits correctly:
PROJECT_ROOT=$(git rev-parse --show-toplevel)
PROJECT_HOOK=$PROJECT_ROOT/.git/hooks/pre-push
if [ -x "$PROJECT_HOOK" ]; then
  "$PROJECT_HOOK" ${1+"$@"} || exit 1
fi
```

This has to be done for every type of git hook present.


### Approach followed in this repository

You can run the `install-githooks.sh` which copies the hooks present in githooks directory to global one. This command would fail with error code 1, if a hook
is already present in that case someone should use the above suggested approach.
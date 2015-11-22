# Run alias
alias run='npm run'

# Git commit hook
if [ ! -f .git/hooks/pre-commit ]; then
    echo -e "#!/bin/sh\n\n\nnpm run check" > .git/hooks/pre-commit
    chmod +x .git/hooks/pre-commit
fi

# Node env
nvm install 4
nvm use 4
npm update

# Python env
virtualenv venv
source venv/bin/activate
pip install --upgrade -r requirements.txt
pip install --upgrade -r requirements.dev.txt

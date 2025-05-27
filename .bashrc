# .bashrc

# Source global definitions
if [ -f /etc/bashrc ]; then
    . /etc/bashrc
fi

# User specific environment
if ! [[ "$PATH" =~ "$HOME/.local/bin:$HOME/bin:" ]]; then
    PATH="$HOME/.local/bin:$HOME/bin:$PATH"
fi
export PATH

# Uncomment the following line if you don't like systemctl's auto-paging feature:
# export SYSTEMD_PAGER=

# User specific aliases and functions
if [ -d ~/.bashrc.d ]; then
    for rc in ~/.bashrc.d/*; do
        if [ -f "$rc" ]; then
            . "$rc"
        fi
    done
fi
unset rc

# Changes sudo to doas
alias sudo='doas'

# Set up alias 'config' to replace 'git' for config interactions
alias config='/usr/bin/git --git-dir=$HOME/dotfiles/ --work-tree=$HOME'

# Changes how PS1 appears in bash 
#PS1='\[\e[1;32m\]\u\[\e[1;35m\]@\h\[\e[0m\] \w \$ '
#PS1='\u at \h \w \$'
#PS1='\[\e[0m\] \[\e[01;35m\] \w > \[\e[0m\]' 
PS1='\[\e[1;35m\]\u\[\e[36;1m\] \w \[\e[0m\]\$ \[\e[0m\]'

alias nvim='nvim -u ~/.config/nvim/init.vim' 

export EDITOR='nvim'

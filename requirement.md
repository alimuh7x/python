


python3 -m venv myenv
source myenv/bin/activate
python3 -m pip install PyGnuplot

-- check environment --------------------

* Every thing should be path of env

which pip
which python3
which python

--------  put in .bashrc ----------------


export PYTHONDONTWRITEBYTECODE=1
# Auto activate Python virtual environment
if [ -d "$HOME/myenv" ]; then
    source $HOME/myenv/bin/activate
fi

-------------------------------------------

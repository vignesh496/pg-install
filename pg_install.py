import os
import subprocess
import sys

# paths for installation and build
HOME = os.path.expanduser("~")

INSTALLS = f"{HOME}/installs"
POSTGRES_SRC = f"{INSTALLS}/postgres"
LLVM_DIR = f"{INSTALLS}/llvm19"
PG_DEBUG = f"{INSTALLS}/pg-debug"
PG_DATA = f"{INSTALLS}/data"
LLVM_TAR = f"{HOME}/Downloads/LLVM-19.1.1-Linux-X64.tar.xz"
LLVM_URL = "https://github.com/llvm/llvm-project/releases/download/llvmorg-19.1.1/LLVM-19.1.1-Linux-X64.tar.xz"

def run(cmd, cwd=None, env=None):   #function to execute commands
    print(f"\n[RUN] {' '.join(cmd)}")
    subprocess.run(cmd, cwd=cwd, env=env, check=True)

def main():
    os.makedirs(INSTALLS, exist_ok=True)
    if not os.path.exists(POSTGRES_SRC):    # download & install postgresql from source 
        run(["git", "clone", "https://github.com/postgres/postgres.git"], cwd=INSTALLS)
    run(["git", "checkout", "REL_17_STABLE"], cwd=POSTGRES_SRC)

    if not os.path.exists(LLVM_TAR):        # download llvm tarball if not present
        run(["wget", "-O", LLVM_TAR, LLVM_URL])

    if not os.path.exists(LLVM_DIR):        # extract tarball to installs after download
        run(["tar", "-xvf", LLVM_TAR, "-C", INSTALLS])
        run(["mv", f"{INSTALLS}/LLVM-19.1.1-Linux-X64", LLVM_DIR])

    os.makedirs(PG_DEBUG, exist_ok=True)

    env = os.environ.copy()                 # set env. variables for build
    env["CC"] = f"{LLVM_DIR}/bin/clang"
    env["CXX"] = f"{LLVM_DIR}/bin/clang++"
    env["CFLAGS"] = "-O0 -g -DRANDOMIZE_ALLOCATED_MEMORY -fno-omit-frame-pointer"   
    
    run([                                   # configure postgresql, with llvm & debug mode
        f"{POSTGRES_SRC}/configure",
        f"--prefix={PG_DEBUG}",
        "--enable-cassert",
        "--enable-debug",
        "--enable-depend"
    ], cwd=PG_DEBUG, env=env)

    run(["rm", "-rf", "*"])
    run(["make", "-j8"], cwd=PG_DEBUG)      # start build
    run(["make", "install"], cwd=PG_DEBUG)

    os.makedirs(PG_DATA, exist_ok=True)
    pg_version_file = os.path.join(PG_DATA, "PG_VERSION")

    if not os.path.exists(pg_version_file):
        run([f"{PG_DEBUG}/bin/initdb", "-D", PG_DATA])      # create a data directory & initialize
    else:
        print("\n[SKIP] Data directory already initialized.")

    try:
        run([f"{PG_DEBUG}/bin/pg_ctl", "-D", PG_DATA, "-l", "logfile", "start"]) 
    except Exception:
        print("\n[SKIP] PostgreSQL server already started.")

    print("\nPostgreSQL 17 (DEBUG + LLVM 19) installed and running successfully.")

if __name__ == "__main__":
    try:
        main()
    except subprocess.CalledProcessError as e:
        print(f"\nERROR: Command failed with exit code {e.returncode}")
        sys.exit(1)

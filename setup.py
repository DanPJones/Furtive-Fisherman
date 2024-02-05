from cx_Freeze import setup, Executable

# Dependencies are automatically detected, but it might need fine tuning.
build_exe_options = {
    "packages": ["PySimpleGUI", "PIL", "mss", "pywin32", "requests", "jwt"],
    "excludes": [],
    "include_files": []
}

# GUI applications require a different base on Windows (the default is for a
# console application).
base = None    

setup(  name = "FlashClick",
        version = "0.0.1",
        description = "Your application description",
        options = {"build_exe": build_exe_options},
        executables = [Executable("main.py", base=base)])
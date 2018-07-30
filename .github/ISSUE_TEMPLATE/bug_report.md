---
name: Bug report
about: Create a report to help us improve

---

**Describe the bug**

A clear and concise description of what the bug is.

**To Reproduce**

Steps to reproduce the behavior:
1. Go to '...'
2. Click on '....'
3. Scroll down to '....'
4. See error

**Expected behavior**

A clear and concise description of what you expected to happen.

**Screenshots/Screencast**

If applicable, add screenshots to help explain your problem.

OR

Attach a session recording using [asciinema](https://asciinema.org/).
To use it:
```bash
sudo apt install -y asciinema && asciinema rec # start session recording
```
Reproduce the issue:
```bash
pip install -e .[...] # Install command if you encounter issues during install process
```   
OR
```bash
.venv/bin/python -m photobooth # To start photobooth if you encounter issue during usage
```
Stop recording and upload:
```
Ctrl+D # stop recording
y # yes to upload and get URL to paste here
```

**Hardware (please complete the following information)**

 - Device [e.g. Intel Laptop, Raspberry Pi 3B+, Odroid C2]
 - Camera [e.g. Canon EOS 500D]
 - GPIO: [Yes/No]

**Software (please complete the following information)**

 - OS [e.g. Raspbian Stretch]
 - Python version [e.g. 3.5.1]
 
 **Installed packages**
 
 ```
 Run 'pip freeze' in your virtual environment and paste the output here
 ```

**Photobooth log**

Run the application as `.venv/bin/python -m photobooth --debug` and paste the logfile here:

```
Insert the content of photobooth.log here
```

**Additional context**

Add any other context about the problem here.

#!/usr/bin/env python

import os
import os.path
import subprocess
import sys
import threading
import time

import fsevents

src = os.path.abspath('.')
dst = sys.argv[1].rstrip('/')
os.chdir(src)
if not os.path.isdir('.git'):
    print "Paranoia: %s isn't a git repository!" % src
    sys.exit()
if not os.path.isfile('.gitignore'):
    print "Paranoia: %s doesn't have a .gitignore!" % src
    sys.exit()
if ':' not in dst:
    print "Paranoia: %s isn't a remote path!" % dst
    sys.exit()
if src.split('/')[-1] != dst.split('/')[-1]:
    print "Paranoia: %s and %s have different basenames!" % (src, dst)
    sys.exit()
dst = dst.rsplit('/', 1)[0] + '/'

observer = fsevents.Observer()
t = threading.Thread(target=observer.run)
t.daemon = True
t.start()

flag = 0
def callback(event):
    global flag
    if not event.name.startswith(src):
        print "Ignoring", event.name
        return
    gitpath = os.path.abspath('.git')
    if event.name == gitpath or event.name.startswith(gitpath + '/') or event.name.endswith('~'):
        print "Ignoring", event.name
        return
    try:
        output = subprocess.check_output(['git', 'check-ignore', event.name]).strip()
    except subprocess.CalledProcessError as e:
        output = e.output.strip()
    ignored = output.split('\n') if output else ()
    if len(ignored) < 1:  # TODO
        print "Flagging", event.name
        flag = 2

stream = fsevents.Stream(callback, src, file_events=True)
observer.schedule(stream)
while True:
    time.sleep(1)
    if flag == 2:
        flag = 1
        subprocess.check_call('rsync -iru -e ssh --exclude=.git --exclude-from=.gitignore --delete'.split() + [src, dst])
    elif flag == 1:
        flag = 0
        print "Everything up-to-date"

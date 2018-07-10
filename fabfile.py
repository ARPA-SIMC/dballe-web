from __future__ import print_function
from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals
from fabric.api import local, run, sudo, cd, env, hosts, shell_env
from fabric.contrib.files import exists
import git
import re
from six.moves import shlex_quote

env.hosts = ["ventiquattro"]
env.use_ssh_config = True

def cmd(*args):
    return " ".join(shlex_quote(a) for a in args)

@hosts("ventiquattro")
def test_ventiquattro():
    repo = git.Repo()
    remote = repo.remote("ventiquattro")
    push_url = remote.config_reader.get("url")
    remote_dir = re.sub(r"^ssh://[^/]+", "", push_url)

    local(cmd("git", "push", "--force", "ventiquattro", "HEAD"))
    with cd(remote_dir):
        run(cmd("git", "checkout", "-B", "test_ventiquattro", repo.head.commit.hexsha))
        run(cmd("git", "reset", "--hard"))
        run(cmd("git", "clean", "-fx"))
        run(cmd("cmake", "."))
        run(cmd("make"))
        run(cmd("./test-provami"))

def test():
    test_ventiquattro()

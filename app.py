#!/usr/bin/env python
import logging
import tornado.escape
import tornado.ioloop
import tornado.web
import os.path
import uuid

from tornado.concurrent import Future
from tornado import gen
from tornado.options import define, options, parse_command_line
import os

from git import Repo

define("port", default=8888, help="run on the given port", type=int)
define("debug", default=False, help="run in debug mode")
define("root", default=".", help="the project's root path")


def get_root_path():
    return os.path.abspath(os.path.expanduser(options.root))


def get_branches():
    repo = Repo(get_root_path())
    return repo.active_branch.name, [branch.name for branch in repo.branches] 


def get_files(root):
    repo_root = get_root_path()
    ret = [{"path": os.path.relpath(os.path.join(root, name), repo_root),
            "name": name,
            "is_file": os.path.isfile(os.path.join(root, name))}
            for name in os.listdir(root) if not name.startswith(".")]
    parent = os.path.dirname(root)
    rel_parent = os.path.relpath(parent, repo_root)
    if root != os.path.join(repo_root, ""):  # TODO: For some reason the repo_root is missing the last sep
        ret = [{"path": rel_parent, "name": "..", "is_file": False}] + ret
    return ret


class SwitchBranchHandler(tornado.web.RequestHandler):
    def post(self):
        self.write("{'result': 'OK'}")
        branch = self.request.arguments['branch'][0]
        repo = Repo(get_root_path())
        repo.heads[branch].checkout()


class MainHandler(tornado.web.RequestHandler):
    def get(self, path):
        path = os.path.join(get_root_path(), path)
        active_branch, branches = get_branches()
        self.render("index.html", files=get_files(path), selected_branch=active_branch, branches=branches)


class FileHandler(tornado.web.RequestHandler):
    """Handles fetching and updating files that the user should have access to"""
    def get(self, fname):
        self.set_header("Content-Type", 'text/plain; charset=utf-8')
        self.set_header("Content-Security-Policy", "default-src 'none'; style-src 'unsafe-inline'")
        self.set_header("Content-Disposition", "attachment; filename='{}'".format(fname))
        with open(os.path.join(get_root_path(), fname), 'rb') as fs:
            self.write(fs.read())

    def post(self, fname):
        # Save the file content in the current branch if it has the necessary prefix, but create that
        # branch otherwise:
        prefix = "testenv-"

        # TODO! Ensure that the fname is in fact under the expected root folder
        branch = self.request.arguments['branch'][0]
        if not branch.startswith(prefix):
            print "Creating a new branch"
            branch = prefix + branch
            repo = Repo(get_root_path())
            repo.heads["develop"].checkout()
            head = repo.create_head(branch)
            head.checkout()

        content = self.request.arguments['content'][0]
        # TODO: Ensure root path remains as expected (no relative shenanigans)
        path = os.path.join(get_root_path(), fname)
        with open(path, 'w') as fs:
            fs.write(content)

        # TODO: Ensure always branching from the default branch, currently 'develop', but doesn't need to be
        self.write("{'status': 'OK', 'branch': '" + branch + "'}")


def main():
    parse_command_line()
    app = tornado.web.Application(
        [
            (r"/a/file/(.*)", FileHandler),
            (r"/a/switch_branch", SwitchBranchHandler),
            (r"/(.*)", MainHandler),
            ],
        cookie_secret="__TODO:_GENERATE_YOUR_OWN_RANDOM_VALUE_HERE__",
        template_path=os.path.join(os.path.dirname(__file__), "templates"),
        static_path=os.path.join(os.path.dirname(__file__), "static"),
        xsrf_cookies=True,
        debug=options.debug)
    print "Starting the server on port {}...".format(options.port)
    app.listen(options.port)
    tornado.ioloop.IOLoop.current().start()


if __name__ == "__main__":
    main()


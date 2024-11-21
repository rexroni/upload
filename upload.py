#!/usr/bin/env python3

import argparse
import email
import http.server
import os
import subprocess
import sys

def make_page(written):
    return (b"""
        <!DOCTYPE HTML>
        <html lang="en">
            <body>
                <head>
                    <title>Private File Upload</title>
                </head>
                <a class="banner">
                    <header>
                        <h1>Private File Upload</h1>
                    </header>
                </a>
                <div class="containersides">
                <div class="container">
                    <article>
                        <form method="POST" enctype="multipart/form-data"/>
                            Select one or more files to upload: <br/>
                            <input type="file" name="f" multiple/> <br/>
                            <input type="submit" value="upload"/>
                        </form> <br/>
    """
    + b"<br/>".join(b"uploaded file: %s"%w.encode('utf8') for w in written) +
    b"""
                    </article>
                </div>
                </div>
            </body>
        </html>
    """)


class Handler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(make_page([]))

    def do_POST(self):
        body = self.rfile.read(int(self.headers["Content-Length"]))

        content_type = self.headers["Content-Type"]
        m = email.message.Message()
        m['content-type'] = content_type
        boundary = m.get_param('boundary')

        written = []


        # ignore the head and tail after splitting on boundary
        for part in body.split(boundary.encode('utf8'))[1:-1]:
            # drop a '\r\n' on the left and a '\r\n--' on the right
            part = part[2:-4]
            ph, pb = part.split(b'\r\n\r\n', maxsplit=1)
            mm = email.message_from_bytes(ph + b'\r\n\r\n')
            name = mm.get_filename()
            if not name: continue
            dst = "/tmp/uploads/" + name
            written.append(name)
            print("writing to", dst)
            with open(dst, "wb") as f:
                f.write(pb)

        self.send_response(200)
        self.end_headers()
        self.wfile.write(make_page(written))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--fork", action="store_true")
    parser.add_argument("--pid", default="/run/upload/pid", action="store_true")
    parser.add_argument("--fork-pipe", type=int, help=argparse.SUPPRESS)
    parser.add_argument("-b", "--bind", default="127.0.0.1")
    parser.add_argument("-p", "--port", type=int, default=3030)
    parser.add_argument("-s", "--save", default="/tmp/uploads")
    args = parser.parse_args(sys.argv[1:])

    if args.fork_pipe is not None:
        # we are the child of a fork
        notify_pipe = os.fdopen(args.fork_pipe, "wb")
    elif args.fork:
        # create a child process with a pipe to notify the parent when it's ready
        r, w = os.pipe()
        os.set_inheritable(w, True)
        cmd = [sys.executable, *sys.argv, "--fork-pipe", str(w)]
        p = subprocess.Popen(cmd, close_fds=False)
        os.close(w)
        # wait for the child to notify us
        if os.read(r, 4096) != b"k":
            sys.exit(2)
        # write the pid file and exit
        with open(args.pid, "w") as f:
            f.write(str(p.pid))
        sys.exit(0)
    else:
        notify_pipe = None

    os.makedirs(args.save, exist_ok=True)

    s = http.server.HTTPServer((args.bind, args.port), Handler)

    if notify_pipe:
        notify_pipe.write(b"k")
        notify_pipe.close()

    s.serve_forever()

#!/usr/local/bin/python-3.7
import ssl
import urllib.request
import urllib.parse
import http.cookiejar
import json
import argparse
import time

# Insecure SSL context
ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE
cookies = http.cookiejar.CookieJar()


class UnifiController:
    def __init__(self, url, verbose=False):
        self.url = url
        self.verbose = verbose

    def api_request(self, path, data=None):
        if self.verbose:
            print("Request %s/api/%s,data=%s" % (self.url, path, data))
        body = json.dumps(data).encode("ascii") if data else None
        request = urllib.request.Request("%s/api/%s" % (self.url, path), data=body)
        cookies.add_cookie_header(request)
        response = urllib.request.urlopen(request, context=ctx)
        cookies.extract_cookies(response, request)
        return json.loads(response.read())

    def login(self, username, password):
        try:
            login = self.api_request(
                "login",
                {"username": username, "password": password, "sessionTimeout": 600},
            )
        except urllib.error.HTTPError as err:
            print("Erro ao realizar login: %s" % err)

    def call_command_alldevs(self, cmd="restart", opts={}):
        sites = self.api_request("self/sites")
        for site in sites["data"]:
            if site["role"] == "admin":
                devices = self.api_request("s/%s/stat/device" % site["name"])
                for device in devices["data"]:
                    print(
                        "Call %s in device %s IP %s"
                        % (cmd, device["mac"], device["ip"]),
                        end="\n" if self.verbose else ": ",
                    )
                    try:
                        params = {"mac": device["mac"], "cmd": cmd}
                        if opts.get("soft", False):
                            params["reboot_type"] = "soft"
                        self.api_request("s/%s/cmd/devmgr" % site["name"], params)
                        print("ok")
                        time.sleep(120)
                    except urllib.error.HTTPError as e:
                        print("Erro HTTP %s" % e.status)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Reboot all devices in UniFi controller"
    )
    parser.add_argument(
        "-c",
        "--controller",
        default="http://localhost:8443",
        help="UniFi controller URL (default http://localhost:8443)",
    )
    parser.add_argument(
        "-u", "--user", default="admin", help="Admin username (default admin)"
    )
    parser.add_argument(
        "-p",
        "--password",
        default="password",
        help="Admin password (default unifi)",
    )
    parser.add_argument(
        "-t",
        "--timetosleep",
        default=120,
        help="Time to sleep between APs (default: 120 seconds)",
    )
    parser.add_argument("-s", "--soft", help="Do a soft reboot", action="store_true")
    parser.add_argument("-v", help="Verbose output", action="store_true")
    try:
        args = parser.parse_args()
        unifi = UnifiController(args.controller, verbose=args.v)
        unifi.login(args.user, args.password)
        unifi.call_command_alldevs("restart", {"soft": args.soft})
    except argparse.ArgumentError as err:
        # print(err)
        parser.print_help()

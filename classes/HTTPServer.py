#
# Copyright (c) 2020 by Philipp Scheer. All Rights Reserved.
#


# import global packages
from http.server import BaseHTTPRequestHandler, HTTPServer
from jarvis import Logger, Exiter
import classes.API as API
import classes.Permissions as Permissions
import os
import sys
import json
import hashlib
import traceback
import urllib.parse as urlparse


DIRECTORY = os.path.abspath(os.path.dirname(sys.argv[0]))
logger = Logger("http-api")
logger.console_on()


def start_server():
    """
    Starts a JarvisWebServer instance which handles outside API requests
    """
    global logger
    try:
        logger.i("start", "starting http api server")
        server = HTTPServer(('', 2021), JarvisWebServer)
        server.serve_forever()
    except OSError as ose:
        print(traceback.format_exc())
        print("Maybe another Jarvis instance is already running?")
        exit(1)
    except Exception as e:
        raise e


class JarvisWebServer(BaseHTTPRequestHandler):
    """
    The JarvisWebServer handles outside API requests
    """

    def do_OPTIONS(self):
        """
        Handle an OPTIONS request to check which methods are allowed
        """
        self.send_response(200, "ok")
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header("Access-Control-Allow-Headers",
                         "Content-Type, X-Request, X-Requested-With")
        self.send_header('Content-Length', '0')
        self.end_headers()

    def do_POST(self):
        """
        Handle API requests
        """
        # create important variables
        path = self.path.split("?")[0]
        api_function_name = path[1:].replace("-", "_").replace("/", "__")
        arguments = {k: v[0] for k, v in urlparse.parse_qs(
            urlparse.urlparse(self.path).query).items()}
        body = json.loads(self.rfile.read(
            int(self.headers.get('Content-Length'))))
        ip = self.client_address[0]

        logger.i("request", f"{ip} - {self.path}")
        logger.i("body", json.dumps(body))

        # reject master token access (master token is only used by jarvis internal applications)
        if "token" in arguments and arguments["token"] == Permissions.MASTER_TOKEN:
            self._send_auth_invalid()
            logger.c(
                "security", f"rejected {ip} who used master token, requested {path}")

        # check if a special request
        if body is None:
            self._send_auth_invalid()
            return
        if "psk" in body:
            psk = body["psk"]
            hashed_psk = hashlib.sha256(psk.encode('utf-8')).hexdigest()

            if hashed_psk != Permissions.PRE_SHARED_KEY:
                self._send_auth_invalid()
                return
        if "token-key" in body:
            key = body["token-key"]
            hashed_key = hashlib.sha256(key.encode('utf-8')).hexdigest()

            if hashed_key != Permissions.TOKEN_KEY:
                self._send_auth_invalid()
                return
            if api_function_name in Permissions.get_allowed_functions("TOKEN_MASTER"):
                arguments["token"] = Permissions.MASTER_TOKEN

        try:
            # this line is important: reject all app requests to the http api, but accept them in the 
            # backend API class. all apps should request ressources over the MQTT API
            if "token" not in arguments or arguments["token"].startswith("app:"):
                str_result = self._send_auth_invalid()
            else:
                permission_level = API.get_permission_level(arguments["token"])
                if api_function_name not in Permissions.get_allowed_functions(permission_level):
                    str_result = json.dumps(Permissions.SECURITY_VIOLATION)
                    logger.c(
                        "security", f"Rejected {ip} {arguments['token'] if 'token' in arguments else ''} with permission level {permission_level} requested {self.path}")
                else:
                    str_result = json.dumps(
                        {"success": False, "error": "could not find object"})
                    try:
                        api_method = getattr(API, api_function_name)
                        str_result = json.dumps(
                            api_method(ip, arguments, body, logger))
                    except Exception as e:
                        logger.exception("api-method", e)
                        self._send_headers(content_type="application/json")
                        self.wfile.write(json.dumps(
                            Permissions.FAILED_MESSAGE).encode())

            logger.i("response", str_result)

            self._send_headers(content_type="application/json")
            self.wfile.write(str_result.encode())
        except Exception as e:
            self._send_500(e)

    def do_GET(self):
        """
        Show an API documentation
        """
        path = self.path.split("?")[0]
        if path[1:] == "":
            path = "/index.html"
        if os.path.isfile(DIRECTORY + "/apidoc/{}".format(path[1:])):
            self._send_headers()
            self.wfile.write(
                open(DIRECTORY + "/apidoc/{}".format(path[1:]), "rb").read())
        elif path[1:] == "ping":
            self._send_headers(content_type="application/json")
            self.wfile.write("pong".encode())
        else:
            self._send_404()

    def _send_headers(self, code=200, content_type="text/html; charset=utf-8", allow_origin="*"):
        """
        Helper function to send header information
        """
        self.send_response(code)
        self.send_header('Access-Control-Allow-Origin', allow_origin)
        self.send_header('Content-Type', content_type)
        self.end_headers()

    def _send_404(self, error=None):
        """
        Send a Not Found message
        """
        self._send_headers(404)
        self.wfile.write(
            open(DIRECTORY + "/apidoc/not_found.html", "r").read().encode())

        logger.i("response", "404 page")

        if error is not None:
            logger.e("error", str(error))

    def _send_500(self, error=None):
        """
        Send a Internal Server Error message
        """
        self._send_headers(500)
        self.wfile.write(
            open(DIRECTORY + "/apidoc/internal_error.html", "r").read().encode())

        logger.i("response", "500 page")

        if error is not None:
            logger.e("error", str(error))

    def _send_auth_invalid(self):
        """
        Send an Authentication Invalid message
        """
        errmsg = json.dumps(Permissions.SECURITY_VIOLATION)
        self._send_headers(code=403, content_type="application/json")
        self.wfile.write(errmsg.encode())
        logger.i("response", errmsg)
        return errmsg

    def log_message(self, format, *args):
        """
        Disable default module logging
        """
        return


# exiter function
def on_exit():
    """
    If the parent script gets terminated, also shut down this script
    """
    logger.i("shutdown", "shutting down")


Exiter(on_exit)


# helper function
def get_mime_type(filename):
    """
    Return the mime type for a filename
    """
    mimes = {
        ".123"			: "application/vnd.lotus-1-2-3",
        ".3dml"			: "text/vnd.in3d.3dml",
        ".3g2"			: "video/3gpp2",
        ".3gp"			: "video/3gpp",
        ".a"			: "application/octet-stream",
        ".aab"			: "application/x-authorware-bin",
        ".aac"			: "audio/x-aac",
        ".aam"			: "application/x-authorware-map",
        ".aas"			: "application/x-authorware-seg",
        ".abw"			: "application/x-abiword",
        ".acc"			: "application/vnd.americandynamics.acc",
        ".ace"			: "application/x-ace-compressed",
        ".acu"			: "application/vnd.acucobol",
        ".acutc"		: "application/vnd.acucorp",
        ".adp"			: "audio/adpcm",
        ".aep"			: "application/vnd.audiograph",
        ".afm"			: "application/x-font-type1",
        ".afp"			: "application/vnd.ibm.modcap",
        ".ai"			: "application/postscript",
        ".aif"			: "audio/x-aiff",
        ".aifc"			: "audio/x-aiff",
        ".aiff"			: "audio/x-aiff",
        ".air"			: "application/vnd.adobe.air-application-installer-package+zip",
        ".ami"			: "application/vnd.amiga.ami",
        ".apk"			: "application/vnd.android.package-archive",
        ".application"		: "application/x-ms-application",
        ".apr"			: "application/vnd.lotus-approach",
        ".asc"			: "application/pgp-signature",
        ".asf"			: "video/x-ms-asf",
        ".asm"			: "text/x-asm",
        ".aso"			: "application/vnd.accpac.simply.aso",
        ".asx"			: "video/x-ms-asf",
        ".atc"			: "application/vnd.acucorp",
        ".atom"			: "application/atom+xml",
        ".atomcat"		: "application/atomcat+xml",
        ".atomsvc"		: "application/atomsvc+xml",
        ".atx"			: "application/vnd.antix.game-component",
        ".au"			: "audio/basic",
        ".avi"			: "video/x-msvideo",
        ".aw"			: "application/applixware",
        ".azf"			: "application/vnd.airzip.filesecure.azf",
        ".azs"			: "application/vnd.airzip.filesecure.azs",
        ".azw"			: "application/vnd.amazon.ebook",
        ".bat"			: "application/x-msdownload",
        ".bcpio"		: "application/x-bcpio",
        ".bdf"			: "application/x-font-bdf",
        ".bdm"			: "application/vnd.syncml.dm+wbxml",
        ".bh2"			: "application/vnd.fujitsu.oasysprs",
        ".bin"			: "application/octet-stream",
        ".bmi"			: "application/vnd.bmi",
        ".bmp"			: "image/bmp",
        ".book"			: "application/vnd.framemaker",
        ".box"			: "application/vnd.previewsystems.box",
        ".boz"			: "application/x-bzip2",
        ".bpk"			: "application/octet-stream",
        ".btif"			: "image/prs.btif",
        ".bz"			: "application/x-bzip",
        ".bz2"			: "application/x-bzip2",
        ".c"			: "text/x-c",
        ".c4d"			: "application/vnd.clonk.c4group",
        ".c4f"			: "application/vnd.clonk.c4group",
        ".c4g"			: "application/vnd.clonk.c4group",
        ".c4p"			: "application/vnd.clonk.c4group",
        ".c4u"			: "application/vnd.clonk.c4group",
        ".cab"			: "application/vnd.ms-cab-compressed",
        ".car"			: "application/vnd.curl.car",
        ".cat"			: "application/vnd.ms-pki.seccat",
        ".cc"			: "text/x-c",
        ".cct"			: "application/x-director",
        ".ccxml"		: "application/ccxml+xml",
        ".cdbcmsg"		: "application/vnd.contact.cmsg",
        ".cdf"			: "application/x-netcdf",
        ".cdkey"		: "application/vnd.mediastation.cdkey",
        ".cdx"			: "chemical/x-cdx",
        ".cdxml"		: "application/vnd.chemdraw+xml",
        ".cdy"			: "application/vnd.cinderella",
        ".cer"			: "application/pkix-cert",
        ".cgm"			: "image/cgm",
        ".chat"			: "application/x-chat",
        ".chm"			: "application/vnd.ms-htmlhelp",
        ".chrt"			: "application/vnd.kde.kchart",
        ".cif"			: "chemical/x-cif",
        ".cii"			: "application/vnd.anser-web-certificate-issue-initiation",
        ".cil"			: "application/vnd.ms-artgalry",
        ".cla"			: "application/vnd.claymore",
        ".class"		: "application/java-vm",
        ".clkk"			: "application/vnd.crick.clicker.keyboard",
        ".clkp"			: "application/vnd.crick.clicker.palette",
        ".clkt"			: "application/vnd.crick.clicker.template",
        ".clkw"			: "application/vnd.crick.clicker.wordbank",
        ".clkx"			: "application/vnd.crick.clicker",
        ".clp"			: "application/x-msclip",
        ".cmc"			: "application/vnd.cosmocaller",
        ".cmdf"			: "chemical/x-cmdf",
        ".cml"			: "chemical/x-cml",
        ".cmp"			: "application/vnd.yellowriver-custom-menu",
        ".cmx"			: "image/x-cmx",
        ".cod"			: "application/vnd.rim.cod",
        ".com"			: "application/x-msdownload",
        ".conf"			: "text/plain",
        ".cpio"			: "application/x-cpio",
        ".cpp"			: "text/x-c",
        ".cpt"			: "application/mac-compactpro",
        ".crd"			: "application/x-mscardfile",
        ".crl"			: "application/pkix-crl",
        ".crt"			: "application/x-x509-ca-cert",
        ".csh"			: "application/x-csh",
        ".csml"			: "chemical/x-csml",
        ".csp"			: "application/vnd.commonspace",
        ".css"			: "text/css",
        ".cst"			: "application/x-director",
        ".csv"			: "text/csv",
        ".cu"			: "application/cu-seeme",
        ".curl"			: "text/vnd.curl",
        ".cww"			: "application/prs.cww",
        ".cxt"			: "application/x-director",
        ".cxx"			: "text/x-c",
        ".daf"			: "application/vnd.mobius.daf",
        ".dataless"		: "application/vnd.fdsn.seed",
        ".davmount"		: "application/davmount+xml",
        ".dcr"			: "application/x-director",
        ".dcurl"		: "text/vnd.curl.dcurl",
        ".dd2"			: "application/vnd.oma.dd2+xml",
        ".ddd"			: "application/vnd.fujixerox.ddd",
        ".deb"			: "application/x-debian-package",
        ".def"			: "text/plain",
        ".deploy"		: "application/octet-stream",
        ".der"			: "application/x-x509-ca-cert",
        ".dfac"			: "application/vnd.dreamfactory",
        ".dic"			: "text/x-c",
        ".diff"			: "text/plain",
        ".dir"			: "application/x-director",
        ".dis"			: "application/vnd.mobius.dis",
        ".dist"			: "application/octet-stream",
        ".distz"		: "application/octet-stream",
        ".djv"			: "image/vnd.djvu",
        ".djvu"			: "image/vnd.djvu",
        ".dll"			: "application/x-msdownload",
        ".dmg"			: "application/octet-stream",
        ".dms"			: "application/octet-stream",
        ".dna"			: "application/vnd.dna",
        ".doc"			: "application/msword",
        ".docm"			: "application/vnd.ms-word.document.macroenabled.12",
        ".docx"			: "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        ".dot"			: "application/msword",
        ".dotm"			: "application/vnd.ms-word.template.macroenabled.12",
        ".dotx"			: "application/vnd.openxmlformats-officedocument.wordprocessingml.template",
        ".dp"			: "application/vnd.osgi.dp",
        ".dpg"			: "application/vnd.dpgraph",
        ".dsc"			: "text/prs.lines.tag",
        ".dtb"			: "application/x-dtbook+xml",
        ".dtd"			: "application/xml-dtd",
        ".dts"			: "audio/vnd.dts",
        ".dtshd"		: "audio/vnd.dts.hd",
        ".dump"			: "application/octet-stream",
        ".dvi"			: "application/x-dvi",
        ".dwf"			: "model/vnd.dwf",
        ".dwg"			: "image/vnd.dwg",
        ".dxf"			: "image/vnd.dxf",
        ".dxp"			: "application/vnd.spotfire.dxp",
        ".dxr"			: "application/x-director",
        ".ecelp4800"		: "audio/vnd.nuera.ecelp4800",
        ".ecelp7470"		: "audio/vnd.nuera.ecelp7470",
        ".ecelp9600"		: "audio/vnd.nuera.ecelp9600",
        ".ecma"			: "application/ecmascript",
        ".edm"			: "application/vnd.novadigm.edm",
        ".edx"			: "application/vnd.novadigm.edx",
        ".efif"			: "application/vnd.picsel",
        ".ei6"			: "application/vnd.pg.osasli",
        ".elc"			: "application/octet-stream",
        ".eml"			: "message/rfc822",
        ".emma"			: "application/emma+xml",
        ".eol"			: "audio/vnd.digital-winds",
        ".eot"			: "application/vnd.ms-fontobject",
        ".eps"			: "application/postscript",
        ".epub"			: "application/epub+zip",
        ".es3"			: "application/vnd.eszigno3+xml",
        ".esf"			: "application/vnd.epson.esf",
        ".et3"			: "application/vnd.eszigno3+xml",
        ".etx"			: "text/x-setext",
        ".exe"			: "application/x-msdownload",
        ".ext"			: "application/vnd.novadigm.ext",
        ".ez"			: "application/andrew-inset",
        ".ez2"			: "application/vnd.ezpix-album",
        ".ez3"			: "application/vnd.ezpix-package",
        ".f"			: "text/x-fortran",
        ".f4v"			: "video/x-f4v",
        ".f77"			: "text/x-fortran",
        ".f90"			: "text/x-fortran",
        ".fbs"			: "image/vnd.fastbidsheet",
        ".fdf"			: "application/vnd.fdf",
        ".fe_launch"		: "application/vnd.denovo.fcselayout-link",
        ".fg5"			: "application/vnd.fujitsu.oasysgp",
        ".fgd"			: "application/x-director",
        ".fh"			: "image/x-freehand",
        ".fh4"			: "image/x-freehand",
        ".fh5"			: "image/x-freehand",
        ".fh7"			: "image/x-freehand",
        ".fhc"			: "image/x-freehand",
        ".fig"			: "application/x-xfig",
        ".fli"			: "video/x-fli",
        ".flo"			: "application/vnd.micrografx.flo",
        ".flv"			: "video/x-flv",
        ".flw"			: "application/vnd.kde.kivio",
        ".flx"			: "text/vnd.fmi.flexstor",
        ".fly"			: "text/vnd.fly",
        ".fm"			: "application/vnd.framemaker",
        ".fnc"			: "application/vnd.frogans.fnc",
        ".for"			: "text/x-fortran",
        ".fpx"			: "image/vnd.fpx",
        ".frame"		: "application/vnd.framemaker",
        ".fsc"			: "application/vnd.fsc.weblaunch",
        ".fst"			: "image/vnd.fst",
        ".ftc"			: "application/vnd.fluxtime.clip",
        ".fti"			: "application/vnd.anser-web-funds-transfer-initiation",
        ".fvt"			: "video/vnd.fvt",
        ".fzs"			: "application/vnd.fuzzysheet",
        ".g3"			: "image/g3fax",
        ".gac"			: "application/vnd.groove-account",
        ".gdl"			: "model/vnd.gdl",
        ".geo"			: "application/vnd.dynageo",
        ".gex"			: "application/vnd.geometry-explorer",
        ".ggb"			: "application/vnd.geogebra.file",
        ".ggt"			: "application/vnd.geogebra.tool",
        ".ghf"			: "application/vnd.groove-help",
        ".gif"			: "image/gif",
        ".gim"			: "application/vnd.groove-identity-message",
        ".gmx"			: "application/vnd.gmx",
        ".gnumeric"		: "application/x-gnumeric",
        ".gph"			: "application/vnd.flographit",
        ".gqf"			: "application/vnd.grafeq",
        ".gqs"			: "application/vnd.grafeq",
        ".gram"			: "application/srgs",
        ".gre"			: "application/vnd.geometry-explorer",
        ".grv"			: "application/vnd.groove-injector",
        ".grxml"		: "application/srgs+xml",
        ".gsf"			: "application/x-font-ghostscript",
        ".gtar"			: "application/x-gtar",
        ".gtm"			: "application/vnd.groove-tool-message",
        ".gtw"			: "model/vnd.gtw",
        ".gv"			: "text/vnd.graphviz",
        ".gz"			: "application/x-gzip",
        ".h"			: "text/x-c",
        ".h261"			: "video/h261",
        ".h263"			: "video/h263",
        ".h264"			: "video/h264",
        ".hbci"			: "application/vnd.hbci",
        ".hdf"			: "application/x-hdf",
        ".hh"			: "text/x-c",
        ".hlp"			: "application/winhlp",
        ".hpgl"			: "application/vnd.hp-hpgl",
        ".hpid"			: "application/vnd.hp-hpid",
        ".hps"			: "application/vnd.hp-hps",
        ".hqx"			: "application/mac-binhex40",
        ".htke"			: "application/vnd.kenameaapp",
        ".htm"			: "text/html",
        ".html"			: "text/html",
        ".hvd"			: "application/vnd.yamaha.hv-dic",
        ".hvp"			: "application/vnd.yamaha.hv-voice",
        ".hvs"			: "application/vnd.yamaha.hv-script",
        ".icc"			: "application/vnd.iccprofile",
        ".ice"			: "x-conference/x-cooltalk",
        ".icm"			: "application/vnd.iccprofile",
        ".ico"			: "image/x-icon",
        ".ics"			: "text/calendar",
        ".ief"			: "image/ief",
        ".ifb"			: "text/calendar",
        ".ifm"			: "application/vnd.shana.informed.formdata",
        ".iges"			: "model/iges",
        ".igl"			: "application/vnd.igloader",
        ".igs"			: "model/iges",
        ".igx"			: "application/vnd.micrografx.igx",
        ".iif"			: "application/vnd.shana.informed.interchange",
        ".imp"			: "application/vnd.accpac.simply.imp",
        ".ims"			: "application/vnd.ms-ims",
        ".in"			: "text/plain",
        ".ipk"			: "application/vnd.shana.informed.package",
        ".irm"			: "application/vnd.ibm.rights-management",
        ".irp"			: "application/vnd.irepository.package+xml",
        ".iso"			: "application/octet-stream",
        ".itp"			: "application/vnd.shana.informed.formtemplate",
        ".ivp"			: "application/vnd.immervision-ivp",
        ".ivu"			: "application/vnd.immervision-ivu",
        ".jad"			: "text/vnd.sun.j2me.app-descriptor",
        ".jam"			: "application/vnd.jam",
        ".jar"			: "application/java-archive",
        ".java"			: "text/x-java-source",
        ".jisp"			: "application/vnd.jisp",
        ".jlt"			: "application/vnd.hp-jlyt",
        ".jnlp"			: "application/x-java-jnlp-file",
        ".joda"			: "application/vnd.joost.joda-archive",
        ".jpe"			: "image/jpeg",
        ".jpeg"			: "image/jpeg",
        ".jpg"			: "image/jpeg",
        ".jpgm"			: "video/jpm",
        ".jpgv"			: "video/jpeg",
        ".jpm"			: "video/jpm",
        ".js"			: "application/javascript",
        ".json"			: "application/json",
        ".kar"			: "audio/midi",
        ".karbon"		: "application/vnd.kde.karbon",
        ".kfo"			: "application/vnd.kde.kformula",
        ".kia"			: "application/vnd.kidspiration",
        ".kil"			: "application/x-killustrator",
        ".kml"			: "application/vnd.google-earth.kml+xml",
        ".kmz"			: "application/vnd.google-earth.kmz",
        ".kne"			: "application/vnd.kinar",
        ".knp"			: "application/vnd.kinar",
        ".kon"			: "application/vnd.kde.kontour",
        ".kpr"			: "application/vnd.kde.kpresenter",
        ".kpt"			: "application/vnd.kde.kpresenter",
        ".ksh"			: "text/plain",
        ".ksp"			: "application/vnd.kde.kspread",
        ".ktr"			: "application/vnd.kahootz",
        ".ktz"			: "application/vnd.kahootz",
        ".kwd"			: "application/vnd.kde.kword",
        ".kwt"			: "application/vnd.kde.kword",
        ".latex"		: "application/x-latex",
        ".lbd"			: "application/vnd.llamagraphics.life-balance.desktop",
        ".lbe"			: "application/vnd.llamagraphics.life-balance.exchange+xml",
        ".les"			: "application/vnd.hhe.lesson-player",
        ".lha"			: "application/octet-stream",
        ".link66"		: "application/vnd.route66.link66+xml",
        ".list"			: "text/plain",
        ".list3820"		: "application/vnd.ibm.modcap",
        ".listafp"		: "application/vnd.ibm.modcap",
        ".log"			: "text/plain",
        ".lostxml"		: "application/lost+xml",
        ".lrf"			: "application/octet-stream",
        ".lrm"			: "application/vnd.ms-lrm",
        ".ltf"			: "application/vnd.frogans.ltf",
        ".lvp"			: "audio/vnd.lucent.voice",
        ".lwp"			: "application/vnd.lotus-wordpro",
        ".lzh"			: "application/octet-stream",
        ".m13"			: "application/x-msmediaview",
        ".m14"			: "application/x-msmediaview",
        ".m1v"			: "video/mpeg",
        ".m2a"			: "audio/mpeg",
        ".m2v"			: "video/mpeg",
        ".m3a"			: "audio/mpeg",
        ".m3u"			: "audio/x-mpegurl",
        ".m4u"			: "video/vnd.mpegurl",
        ".m4v"			: "video/x-m4v",
        ".ma"			: "application/mathematica",
        ".mag"			: "application/vnd.ecowin.chart",
        ".maker"		: "application/vnd.framemaker",
        ".man"			: "text/troff",
        ".mathml"		: "application/mathml+xml",
        ".mb"			: "application/mathematica",
        ".mbk"			: "application/vnd.mobius.mbk",
        ".mbox"			: "application/mbox",
        ".mc1"			: "application/vnd.medcalcdata",
        ".mcd"			: "application/vnd.mcd",
        ".mcurl"		: "text/vnd.curl.mcurl",
        ".mdb"			: "application/x-msaccess",
        ".mdi"			: "image/vnd.ms-modi",
        ".me"			: "text/troff",
        ".mesh"			: "model/mesh",
        ".mfm"			: "application/vnd.mfmp",
        ".mgz"			: "application/vnd.proteus.magazine",
        ".mht"			: "message/rfc822",
        ".mhtml"		: "message/rfc822",
        ".mid"			: "audio/midi",
        ".midi"			: "audio/midi",
        ".mif"			: "application/vnd.mif",
        ".mime"			: "message/rfc822",
        ".mj2"			: "video/mj2",
        ".mjp2"			: "video/mj2",
        ".mlp"			: "application/vnd.dolby.mlp",
        ".mmd"			: "application/vnd.chipnuts.karaoke-mmd",
        ".mmf"			: "application/vnd.smaf",
        ".mmr"			: "image/vnd.fujixerox.edmics-mmr",
        ".mny"			: "application/x-msmoney",
        ".mobi"			: "application/x-mobipocket-ebook",
        ".mov"			: "video/quicktime",
        ".movie"		: "video/x-sgi-movie",
        ".mp2"			: "audio/mpeg",
        ".mp2a"			: "audio/mpeg",
        ".mp3"			: "audio/mpeg",
        ".mp4"			: "video/mp4",
        ".mp4a"			: "audio/mp4",
        ".mp4s"			: "application/mp4",
        ".mp4v"			: "video/mp4",
        ".mpa"			: "video/mpeg",
        ".mpc"			: "application/vnd.mophun.certificate",
        ".mpe"			: "video/mpeg",
        ".mpeg"			: "video/mpeg",
        ".mpg"			: "video/mpeg",
        ".mpg4"			: "video/mp4",
        ".mpga"			: "audio/mpeg",
        ".mpkg"			: "application/vnd.apple.installer+xml",
        ".mpm"			: "application/vnd.blueice.multipass",
        ".mpn"			: "application/vnd.mophun.application",
        ".mpp"			: "application/vnd.ms-project",
        ".mpt"			: "application/vnd.ms-project",
        ".mpy"			: "application/vnd.ibm.minipay",
        ".mqy"			: "application/vnd.mobius.mqy",
        ".mrc"			: "application/marc",
        ".ms"			: "text/troff",
        ".mscml"		: "application/mediaservercontrol+xml",
        ".mseed"		: "application/vnd.fdsn.mseed",
        ".mseq"			: "application/vnd.mseq",
        ".msf"			: "application/vnd.epson.msf",
        ".msh"			: "model/mesh",
        ".msi"			: "application/x-msdownload",
        ".msl"			: "application/vnd.mobius.msl",
        ".msty"			: "application/vnd.muvee.style",
        ".mts"			: "model/vnd.mts",
        ".mus"			: "application/vnd.musician",
        ".musicxml"		: "application/vnd.recordare.musicxml+xml",
        ".mvb"			: "application/x-msmediaview",
        ".mwf"			: "application/vnd.mfer",
        ".mxf"			: "application/mxf",
        ".mxl"			: "application/vnd.recordare.musicxml",
        ".mxml"			: "application/xv+xml",
        ".mxs"			: "application/vnd.triscape.mxs",
        ".mxu"			: "video/vnd.mpegurl",
        ".n-gage"		: "application/vnd.nokia.n-gage.symbian.install",
        ".nb"			: "application/mathematica",
        ".nc"			: "application/x-netcdf",
        ".ncx"			: "application/x-dtbncx+xml",
        ".ngdat"		: "application/vnd.nokia.n-gage.data",
        ".nlu"			: "application/vnd.neurolanguage.nlu",
        ".nml"			: "application/vnd.enliven",
        ".nnd"			: "application/vnd.noblenet-directory",
        ".nns"			: "application/vnd.noblenet-sealer",
        ".nnw"			: "application/vnd.noblenet-web",
        ".npx"			: "image/vnd.net-fpx",
        ".nsf"			: "application/vnd.lotus-notes",
        ".nws"			: "message/rfc822",
        ".o"			: "application/octet-stream",
        ".oa2"			: "application/vnd.fujitsu.oasys2",
        ".oa3"			: "application/vnd.fujitsu.oasys3",
        ".oas"			: "application/vnd.fujitsu.oasys",
        ".obd"			: "application/x-msbinder",
        ".obj"			: "application/octet-stream",
        ".oda"			: "application/oda",
        ".odb"			: "application/vnd.oasis.opendocument.database",
        ".odc"			: "application/vnd.oasis.opendocument.chart",
        ".odf"			: "application/vnd.oasis.opendocument.formula",
        ".odft"			: "application/vnd.oasis.opendocument.formula-template",
        ".odg"			: "application/vnd.oasis.opendocument.graphics",
        ".odi"			: "application/vnd.oasis.opendocument.image",
        ".odp"			: "application/vnd.oasis.opendocument.presentation",
        ".ods"			: "application/vnd.oasis.opendocument.spreadsheet",
        ".odt"			: "application/vnd.oasis.opendocument.text",
        ".oga"			: "audio/ogg",
        ".ogg"			: "audio/ogg",
        ".ogv"			: "video/ogg",
        ".ogx"			: "application/ogg",
        ".onepkg"		: "application/onenote",
        ".onetmp"		: "application/onenote",
        ".onetoc"		: "application/onenote",
        ".onetoc2"		: "application/onenote",
        ".opf"			: "application/oebps-package+xml",
        ".oprc"			: "application/vnd.palm",
        ".org"			: "application/vnd.lotus-organizer",
        ".osf"			: "application/vnd.yamaha.openscoreformat",
        ".osfpvg"		: "application/vnd.yamaha.openscoreformat.osfpvg+xml",
        ".otc"			: "application/vnd.oasis.opendocument.chart-template",
        ".otf"			: "application/x-font-otf",
        ".otg"			: "application/vnd.oasis.opendocument.graphics-template",
        ".oth"			: "application/vnd.oasis.opendocument.text-web",
        ".oti"			: "application/vnd.oasis.opendocument.image-template",
        ".otm"			: "application/vnd.oasis.opendocument.text-master",
        ".otp"			: "application/vnd.oasis.opendocument.presentation-template",
        ".ots"			: "application/vnd.oasis.opendocument.spreadsheet-template",
        ".ott"			: "application/vnd.oasis.opendocument.text-template",
        ".oxt"			: "application/vnd.openofficeorg.extension",
        ".p"			: "text/x-pascal",
        ".p10"			: "application/pkcs10",
        ".p12"			: "application/x-pkcs12",
        ".p7b"			: "application/x-pkcs7-certificates",
        ".p7c"			: "application/pkcs7-mime",
        ".p7m"			: "application/pkcs7-mime",
        ".p7r"			: "application/x-pkcs7-certreqresp",
        ".p7s"			: "application/pkcs7-signature",
        ".pas"			: "text/x-pascal",
        ".pbd"			: "application/vnd.powerbuilder6",
        ".pbm"			: "image/x-portable-bitmap",
        ".pcf"			: "application/x-font-pcf",
        ".pcl"			: "application/vnd.hp-pcl",
        ".pclxl"		: "application/vnd.hp-pclxl",
        ".pct"			: "image/x-pict",
        ".pcurl"		: "application/vnd.curl.pcurl",
        ".pcx"			: "image/x-pcx",
        ".pdb"			: "application/vnd.palm",
        ".pdf"			: "application/pdf",
        ".pfa"			: "application/x-font-type1",
        ".pfb"			: "application/x-font-type1",
        ".pfm"			: "application/x-font-type1",
        ".pfr"			: "application/font-tdpfr",
        ".pfx"			: "application/x-pkcs12",
        ".pgm"			: "image/x-portable-graymap",
        ".pgn"			: "application/x-chess-pgn",
        ".pgp"			: "application/pgp-encrypted",
        ".pic"			: "image/x-pict",
        ".pkg"			: "application/octet-stream",
        ".pki"			: "application/pkixcmp",
        ".pkipath"		: "application/pkix-pkipath",
        ".pl"			: "text/plain",
        ".plb"			: "application/vnd.3gpp.pic-bw-large",
        ".plc"			: "application/vnd.mobius.plc",
        ".plf"			: "application/vnd.pocketlearn",
        ".pls"			: "application/pls+xml",
        ".pml"			: "application/vnd.ctc-posml",
        ".png"			: "image/png",
        ".pnm"			: "image/x-portable-anymap",
        ".portpkg"		: "application/vnd.macports.portpkg",
        ".pot"			: "application/vnd.ms-powerpoint",
        ".potm"			: "application/vnd.ms-powerpoint.template.macroenabled.12",
        ".potx"			: "application/vnd.openxmlformats-officedocument.presentationml.template",
        ".ppa"			: "application/vnd.ms-powerpoint",
        ".ppam"			: "application/vnd.ms-powerpoint.addin.macroenabled.12",
        ".ppd"			: "application/vnd.cups-ppd",
        ".ppm"			: "image/x-portable-pixmap",
        ".pps"			: "application/vnd.ms-powerpoint",
        ".ppsm"			: "application/vnd.ms-powerpoint.slideshow.macroenabled.12",
        ".ppsx"			: "application/vnd.openxmlformats-officedocument.presentationml.slideshow",
        ".ppt"			: "application/vnd.ms-powerpoint",
        ".pptm"			: "application/vnd.ms-powerpoint.presentation.macroenabled.12",
        ".pptx"			: "application/vnd.openxmlformats-officedocument.presentationml.presentation",
        ".pqa"			: "application/vnd.palm",
        ".prc"			: "application/x-mobipocket-ebook",
        ".pre"			: "application/vnd.lotus-freelance",
        ".prf"			: "application/pics-rules",
        ".ps"			: "application/postscript",
        ".psb"			: "application/vnd.3gpp.pic-bw-small",
        ".psd"			: "image/vnd.adobe.photoshop",
        ".psf"			: "application/x-font-linux-psf",
        ".ptid"			: "application/vnd.pvi.ptid1",
        ".pub"			: "application/x-mspublisher",
        ".pvb"			: "application/vnd.3gpp.pic-bw-var",
        ".pwn"			: "application/vnd.3m.post-it-notes",
        ".pwz"			: "application/vnd.ms-powerpoint",
        ".py"			: "text/x-python",
        ".pya"			: "audio/vnd.ms-playready.media.pya",
        ".pyc"			: "application/x-python-code",
        ".pyo"			: "application/x-python-code",
        ".pyv"			: "video/vnd.ms-playready.media.pyv",
        ".qam"			: "application/vnd.epson.quickanime",
        ".qbo"			: "application/vnd.intu.qbo",
        ".qfx"			: "application/vnd.intu.qfx",
        ".qps"			: "application/vnd.publishare-delta-tree",
        ".qt"			: "video/quicktime",
        ".qwd"			: "application/vnd.quark.quarkxpress",
        ".qwt"			: "application/vnd.quark.quarkxpress",
        ".qxb"			: "application/vnd.quark.quarkxpress",
        ".qxd"			: "application/vnd.quark.quarkxpress",
        ".qxl"			: "application/vnd.quark.quarkxpress",
        ".qxt"			: "application/vnd.quark.quarkxpress",
        ".ra"			: "audio/x-pn-realaudio",
        ".ram"			: "audio/x-pn-realaudio",
        ".rar"			: "application/x-rar-compressed",
        ".ras"			: "image/x-cmu-raster",
        ".rcprofile"		: "application/vnd.ipunplugged.rcprofile",
        ".rdf"			: "application/rdf+xml",
        ".rdz"			: "application/vnd.data-vision.rdz",
        ".rep"			: "application/vnd.businessobjects",
        ".res"			: "application/x-dtbresource+xml",
        ".rgb"			: "image/x-rgb",
        ".rif"			: "application/reginfo+xml",
        ".rl"			: "application/resource-lists+xml",
        ".rlc"			: "image/vnd.fujixerox.edmics-rlc",
        ".rld"			: "application/resource-lists-diff+xml",
        ".rm"			: "application/vnd.rn-realmedia",
        ".rmi"			: "audio/midi",
        ".rmp"			: "audio/x-pn-realaudio-plugin",
        ".rms"			: "application/vnd.jcp.javame.midlet-rms",
        ".rnc"			: "application/relax-ng-compact-syntax",
        ".roff"			: "text/troff",
        ".rpm"			: "application/x-rpm",
        ".rpss"			: "application/vnd.nokia.radio-presets",
        ".rpst"			: "application/vnd.nokia.radio-preset",
        ".rq"			: "application/sparql-query",
        ".rs"			: "application/rls-services+xml",
        ".rsd"			: "application/rsd+xml",
        ".rss"			: "application/rss+xml",
        ".rtf"			: "application/rtf",
        ".rtx"			: "text/richtext",
        ".s"			: "text/x-asm",
        ".saf"			: "application/vnd.yamaha.smaf-audio",
        ".sbml"			: "application/sbml+xml",
        ".sc"			: "application/vnd.ibm.secure-container",
        ".scd"			: "application/x-msschedule",
        ".scm"			: "application/vnd.lotus-screencam",
        ".scq"			: "application/scvp-cv-request",
        ".scs"			: "application/scvp-cv-response",
        ".scurl"		: "text/vnd.curl.scurl",
        ".sda"			: "application/vnd.stardivision.draw",
        ".sdc"			: "application/vnd.stardivision.calc",
        ".sdd"			: "application/vnd.stardivision.impress",
        ".sdkd"			: "application/vnd.solent.sdkm+xml",
        ".sdkm"			: "application/vnd.solent.sdkm+xml",
        ".sdp"			: "application/sdp",
        ".sdw"			: "application/vnd.stardivision.writer",
        ".see"			: "application/vnd.seemail",
        ".seed"			: "application/vnd.fdsn.seed",
        ".sema"			: "application/vnd.sema",
        ".semd"			: "application/vnd.semd",
        ".semf"			: "application/vnd.semf",
        ".ser"			: "application/java-serialized-object",
        ".setpay"		: "application/set-payment-initiation",
        ".setreg"		: "application/set-registration-initiation",
        ".sfd-hdstx"		: "application/vnd.hydrostatix.sof-data",
        ".sfs"			: "application/vnd.spotfire.sfs",
        ".sgl"			: "application/vnd.stardivision.writer-global",
        ".sgm"			: "text/sgml",
        ".sgml"			: "text/sgml",
        ".sh"			: "application/x-sh",
        ".shar"			: "application/x-shar",
        ".shf"			: "application/shf+xml",
        ".si"			: "text/vnd.wap.si",
        ".sic"			: "application/vnd.wap.sic",
        ".sig"			: "application/pgp-signature",
        ".silo"			: "model/mesh",
        ".sis"			: "application/vnd.symbian.install",
        ".sisx"			: "application/vnd.symbian.install",
        ".sit"			: "application/x-stuffit",
        ".sitx"			: "application/x-stuffitx",
        ".skd"			: "application/vnd.koan",
        ".skm"			: "application/vnd.koan",
        ".skp"			: "application/vnd.koan",
        ".skt"			: "application/vnd.koan",
        ".sl"			: "text/vnd.wap.sl",
        ".slc"			: "application/vnd.wap.slc",
        ".sldm"			: "application/vnd.ms-powerpoint.slide.macroenabled.12",
        ".sldx"			: "application/vnd.openxmlformats-officedocument.presentationml.slide",
        ".slt"			: "application/vnd.epson.salt",
        ".smf"			: "application/vnd.stardivision.math",
        ".smi"			: "application/smil+xml",
        ".smil"			: "application/smil+xml",
        ".snd"			: "audio/basic",
        ".snf"			: "application/x-font-snf",
        ".so"			: "application/octet-stream",
        ".spc"			: "application/x-pkcs7-certificates",
        ".spf"			: "application/vnd.yamaha.smaf-phrase",
        ".spl"			: "application/x-futuresplash",
        ".spot"			: "text/vnd.in3d.spot",
        ".spp"			: "application/scvp-vp-response",
        ".spq"			: "application/scvp-vp-request",
        ".spx"			: "audio/ogg",
        ".src"			: "application/x-wais-source",
        ".srx"			: "application/sparql-results+xml",
        ".sse"			: "application/vnd.kodak-descriptor",
        ".ssf"			: "application/vnd.epson.ssf",
        ".ssml"			: "application/ssml+xml",
        ".stc"			: "application/vnd.sun.xml.calc.template",
        ".std"			: "application/vnd.sun.xml.draw.template",
        ".stf"			: "application/vnd.wt.stf",
        ".sti"			: "application/vnd.sun.xml.impress.template",
        ".stk"			: "application/hyperstudio",
        ".stl"			: "application/vnd.ms-pki.stl",
        ".str"			: "application/vnd.pg.format",
        ".stw"			: "application/vnd.sun.xml.writer.template",
        ".sus"			: "application/vnd.sus-calendar",
        ".susp"			: "application/vnd.sus-calendar",
        ".sv4cpio"		: "application/x-sv4cpio",
        ".sv4crc"		: "application/x-sv4crc",
        ".svd"			: "application/vnd.svd",
        ".svg"			: "image/svg+xml",
        ".svgz"			: "image/svg+xml",
        ".swa"			: "application/x-director",
        ".swf"			: "application/x-shockwave-flash",
        ".swi"			: "application/vnd.arastra.swi",
        ".sxc"			: "application/vnd.sun.xml.calc",
        ".sxd"			: "application/vnd.sun.xml.draw",
        ".sxg"			: "application/vnd.sun.xml.writer.global",
        ".sxi"			: "application/vnd.sun.xml.impress",
        ".sxm"			: "application/vnd.sun.xml.math",
        ".sxw"			: "application/vnd.sun.xml.writer",
        ".t"			: "text/troff",
        ".tao"			: "application/vnd.tao.intent-module-archive",
        ".tar"			: "application/x-tar",
        ".tcap"			: "application/vnd.3gpp2.tcap",
        ".tcl"			: "application/x-tcl",
        ".teacher"		: "application/vnd.smart.teacher",
        ".tex"			: "application/x-tex",
        ".texi"			: "application/x-texinfo",
        ".texinfo"		: "application/x-texinfo",
        ".text"			: "text/plain",
        ".tfm"			: "application/x-tex-tfm",
        ".tgz"			: "application/x-gzip",
        ".tif"			: "image/tiff",
        ".tiff"			: "image/tiff",
        ".tmo"			: "application/vnd.tmobile-livetv",
        ".torrent"		: "application/x-bittorrent",
        ".tpl"			: "application/vnd.groove-tool-template",
        ".tpt"			: "application/vnd.trid.tpt",
        ".tr"			: "text/troff",
        ".tra"			: "application/vnd.trueapp",
        ".trm"			: "application/x-msterminal",
        ".tsv"			: "text/tab-separated-values",
        ".ttc"			: "application/x-font-ttf",
        ".ttf"			: "application/x-font-ttf",
        ".twd"			: "application/vnd.simtech-mindmapper",
        ".twds"			: "application/vnd.simtech-mindmapper",
        ".txd"			: "application/vnd.genomatix.tuxedo",
        ".txf"			: "application/vnd.mobius.txf",
        ".txt"			: "text/plain",
        ".u32"			: "application/x-authorware-bin",
        ".udeb"			: "application/x-debian-package",
        ".ufd"			: "application/vnd.ufdl",
        ".ufdl"			: "application/vnd.ufdl",
        ".umj"			: "application/vnd.umajin",
        ".unityweb"		: "application/vnd.unity",
        ".uoml"			: "application/vnd.uoml+xml",
        ".uri"			: "text/uri-list",
        ".uris"			: "text/uri-list",
        ".urls"			: "text/uri-list",
        ".ustar"		: "application/x-ustar",
        ".utz"			: "application/vnd.uiq.theme",
        ".uu"			: "text/x-uuencode",
        ".vcd"			: "application/x-cdlink",
        ".vcf"			: "text/x-vcard",
        ".vcg"			: "application/vnd.groove-vcard",
        ".vcs"			: "text/x-vcalendar",
        ".vcx"			: "application/vnd.vcx",
        ".vis"			: "application/vnd.visionary",
        ".viv"			: "video/vnd.vivo",
        ".vor"			: "application/vnd.stardivision.writer",
        ".vox"			: "application/x-authorware-bin",
        ".vrml"			: "model/vrml",
        ".vsd"			: "application/vnd.visio",
        ".vsf"			: "application/vnd.vsf",
        ".vss"			: "application/vnd.visio",
        ".vst"			: "application/vnd.visio",
        ".vsw"			: "application/vnd.visio",
        ".vtu"			: "model/vnd.vtu",
        ".vxml"			: "application/voicexml+xml",
        ".w3d"			: "application/x-director",
        ".wad"			: "application/x-doom",
        ".wav"			: "audio/x-wav",
        ".wax"			: "audio/x-ms-wax",
        ".wbmp"			: "image/vnd.wap.wbmp",
        ".wbs"			: "application/vnd.criticaltools.wbs+xml",
        ".wbxml"		: "application/vnd.wap.wbxml",
        ".wcm"			: "application/vnd.ms-works",
        ".wdb"			: "application/vnd.ms-works",
        ".wiz"			: "application/msword",
        ".wks"			: "application/vnd.ms-works",
        ".wm"			: "video/x-ms-wm",
        ".wma"			: "audio/x-ms-wma",
        ".wmd"			: "application/x-ms-wmd",
        ".wmf"			: "application/x-msmetafile",
        ".wml"			: "text/vnd.wap.wml",
        ".wmlc"			: "application/vnd.wap.wmlc",
        ".wmls"			: "text/vnd.wap.wmlscript",
        ".wmlsc"		: "application/vnd.wap.wmlscriptc",
        ".wmv"			: "video/x-ms-wmv",
        ".wmx"			: "video/x-ms-wmx",
        ".wmz"			: "application/x-ms-wmz",
        ".wpd"			: "application/vnd.wordperfect",
        ".wpl"			: "application/vnd.ms-wpl",
        ".wps"			: "application/vnd.ms-works",
        ".wqd"			: "application/vnd.wqd",
        ".wri"			: "application/x-mswrite",
        ".wrl"			: "model/vrml",
        ".wsdl"			: "application/wsdl+xml",
        ".wspolicy"		: "application/wspolicy+xml",
        ".wtb"			: "application/vnd.webturbo",
        ".wvx"			: "video/x-ms-wvx",
        ".x32"			: "application/x-authorware-bin",
        ".x3d"			: "application/vnd.hzn-3d-crossword",
        ".xap"			: "application/x-silverlight-app",
        ".xar"			: "application/vnd.xara",
        ".xbap"			: "application/x-ms-xbap",
        ".xbd"			: "application/vnd.fujixerox.docuworks.binder",
        ".xbm"			: "image/x-xbitmap",
        ".xdm"			: "application/vnd.syncml.dm+xml",
        ".xdp"			: "application/vnd.adobe.xdp+xml",
        ".xdw"			: "application/vnd.fujixerox.docuworks",
        ".xenc"			: "application/xenc+xml",
        ".xer"			: "application/patch-ops-error+xml",
        ".xfdf"			: "application/vnd.adobe.xfdf",
        ".xfdl"			: "application/vnd.xfdl",
        ".xht"			: "application/xhtml+xml",
        ".xhtml"		: "application/xhtml+xml",
        ".xhvml"		: "application/xv+xml",
        ".xif"			: "image/vnd.xiff",
        ".xla"			: "application/vnd.ms-excel",
        ".xlam"			: "application/vnd.ms-excel.addin.macroenabled.12",
        ".xlb"			: "application/vnd.ms-excel",
        ".xlc"			: "application/vnd.ms-excel",
        ".xlm"			: "application/vnd.ms-excel",
        ".xls"			: "application/vnd.ms-excel",
        ".xlsb"			: "application/vnd.ms-excel.sheet.binary.macroenabled.12",
        ".xlsm"			: "application/vnd.ms-excel.sheet.macroenabled.12",
        ".xlsx"			: "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        ".xlt"			: "application/vnd.ms-excel",
        ".xltm"			: "application/vnd.ms-excel.template.macroenabled.12",
        ".xltx"			: "application/vnd.openxmlformats-officedocument.spreadsheetml.template",
        ".xlw"			: "application/vnd.ms-excel",
        ".xml"			: "application/xml",
        ".xo"			: "application/vnd.olpc-sugar",
        ".xop"			: "application/xop+xml",
        ".xpdl"			: "application/xml",
        ".xpi"			: "application/x-xpinstall",
        ".xpm"			: "image/x-xpixmap",
        ".xpr"			: "application/vnd.is-xpr",
        ".xps"			: "application/vnd.ms-xpsdocument",
        ".xpw"			: "application/vnd.intercon.formnet",
        ".xpx"			: "application/vnd.intercon.formnet",
        ".xsl"			: "application/xml",
        ".xslt"			: "application/xslt+xml",
        ".xsm"			: "application/vnd.syncml+xml",
        ".xspf"			: "application/xspf+xml",
        ".xul"			: "application/vnd.mozilla.xul+xml",
        ".xvm"			: "application/xv+xml",
        ".xvml"			: "application/xv+xml",
        ".xwd"			: "image/x-xwindowdump",
        ".xyz"			: "chemical/x-xyz",
        ".zaz"			: "application/vnd.zzazz.deck+xml",
        ".zip"			: "application/zip",
        ".zir"			: "application/vnd.zul",
        ".zirz"			: "application/vnd.zul",
        ".zmm"			: "application/vnd.handheld-entertainment+xml"
    }
    return mimes[".{}".format(filename.split(".")[-1])]

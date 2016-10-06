import getpass
import os
import logging
import platform

logger = logging.getLogger("RvTerminal")


class User(object):
    def __init__(self, appname=None):
        self._username = getpass.getuser()
        if appname is None:
            try:
                self.appname = os.path.splitext(os.path.basename(__file__))[0]
            except NameError:
                self.appname = "python"
        else:
            self.appname = appname

    @property
    def appdata(self):

        if platform.system() is 'Linux':
            return os.getenv('HOME')

        if platform.system() in ['Darwin']:
            return os.getenv('HOME')

        else:
            return os.getenv('APPDATA')

    def getPreferenceFile(self):
        preference = os.path.join(self.appdata, self.appname, "%s.pref" % self._username)
        if not os.path.exists(os.path.dirname(preference)):
            os.makedirs(os.path.dirname(preference))
        return preference

    def save(self, text_data, mode="wb"):
        with open(self.getPreferenceFile(), mode) as fh:
            fh.write(text_data)
        logger.debug("Preference file updated at %s" % self.getPreferenceFile())

    def read(self):
        if not os.path.exists(self.getPreferenceFile()):
            text_data = ""
        else:
            with open(self.getPreferenceFile(), "rb") as fh:
                text_data = fh.read()
            logger.debug("Preference file loaded from %s" % self.getPreferenceFile())
        return text_data

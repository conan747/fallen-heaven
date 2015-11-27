__author__ = 'cos'




from fife import fife
from fife.extensions import pychan
from fife.extensions.pychan import widgets
# from fife.extensions.pychan.fife_pychansettings import FifePychanSettings


class InfoDialog(pychan.Window):

    def __init__(self, message='', cancelButton=False, title='Information', callBacks=None):
        super(InfoDialog, self).__init__(name="InfoDialog")
        prototype = pychan.loadXML("gui/dialogs/genericDialog.xml")
        self.addChildren(prototype._cloneChildren("Info"))
        messageLabel = self.findChildByName("InfomessageLabel")
        messageLabel.text = unicode(message)
        self.title = unicode(title)
        if cancelButton:
            buttonBox = self.findChildByName("InfobuttonBox")
            cancelBtn = pychan.Button(parent=self, name="InfocancelButton", text="Cancel")
            buttonBox.addChild(cancelButton)

        if callBacks:
            self.mapEvents(callBacks)
        else:
            self.mapEvents({"InfoOkButton" : self.hide})

        self.adaptLayout()


    def setText(self, text):
        messageLabel = self.findChildByName("InfomessageLabel")
        messageLabel.text = text
        self.adaptLayout()

    def start(self):
        '''
        Simply shows the dialog asynchronously.
        :return:
        '''
        return self.execute({"InfoOkButton" : True})
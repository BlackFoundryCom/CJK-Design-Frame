"""
Copyright 2020 Black Foundry.

This file is part of CJKDesignFrame.

CJKDesignFrame is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

CJKDesignFrame is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with CJKDesignFrame.  If not, see <https://www.gnu.org/licenses/>.
"""

from mojo.events                import addObserver, removeObserver
from AppKit                     import NSImage, NumberFormatter, NSColor
from mojo.extensions            import getExtensionDefault, setExtensionDefault
from lib.UI.toolbarGlyphTools   import ToolbarGlyphTools
from mojo.UI                    import UpdateCurrentGlyphView, CurrentGlyphWindow
from mojo.canvas                import CanvasGroup
from mojo.drawingTools          import *
from vanilla                    import *
from vanilla.dialogs            import putFile, getFile
import json
import os

# toggleCJKDesignFrame = "com.black-foundry.toggleCJKDesignFrame"

def refreshGlyphView(func):
    def wrapper(self, *args, **kwargs):
        func(self, *args, **kwargs)
        UpdateCurrentGlyphView()
    return wrapper

class DesignFrameController:

    base_path = os.path.dirname(__file__)

    def __init__(self):
        self.observers = False
        self.currentGlyph = None
        addObserver(self, "buttonToolBar", "glyphWindowWillShowToolbarItems")
        self.drawer = DesignFrameDrawer(self)
        self.designFrame = HanDesignFrame()
        self.toggleCJKDesignFrame = False
        self.view = ViewCanvas(
            self, 
            posSize = (20, 20, 100, 65),
            delegate = self
            )
        self.view.show(False)
        addObserver(self, "glyphWindowDidOpen", "glyphWindowWillOpen")
        addObserver(self, "glyphWindowWillClose", "glyphWindowWillClose")

    def buttonToolBar(self, info):
        toolbarItems = info['toolbarItems']
        
        label = 'Show CJK Design Frame2'
        identifier = 'CJKDesignFrameButton2'
        filename = 'CJKDesignFrameIcon.pdf'
        callback = self.buttonStartCallback
        index = -2
        
        imagePath = os.path.join(self.base_path, 'resources', filename)
        image = NSImage.alloc().initByReferencingFile_(imagePath)
        
        view = ToolbarGlyphTools(
            (30, 25), 
            [dict(image=image, toolTip=label)], 
            trackingMode="one"
            )
        
        newItem = dict(
            itemIdentifier=identifier,
            label = label,
            callback = callback,
            view = view
            )
        toolbarItems.insert(index, newItem)

    def opaque(self):
        return False

    def acceptsFirstResponder(self):
        return False

    def acceptsMouseMoved(self):
        return True

    def becomeFirstResponder(self):
        return False

    def resignFirstResponder(self):
        return False

    def shouldDrawBackground(self):
        return False

    @property
    def window(self):
        return CurrentGlyphWindow()
    
    @refreshGlyphView
    def buttonStartCallback(self, sender):
        if self.toggleCJKDesignFrame == True:
            try:self.window.removeGlyphEditorSubview(self.view)
            except:pass
            self.toggleCJKDesignFrame = False
            removeObserver(self, "glyphAdditionContextualMenuItems")
            self.toggleObserver(True)
        else:
            if self.window:
                self.window.addGlyphEditorSubview(self.view)
            self.currentGlyph = CurrentGlyph()
            self.setFont()
            
            removeObserver(self, "glyphAdditionContextualMenuItems")
            if not self.currentFont.lib.get('CJKDesignFrameSettings', ''):
                self.currentFont.lib["CJKDesignFrameSettings"] = self.designFrame.get()
                self.openDesignFrameSettings(None)
            addObserver(self, "glyphMenuItems", "glyphAdditionContextualMenuItems")
            self.view.show(True)
            self.toggleCJKDesignFrame = True
            self.toggleObserver()

    def setFont(self):
        self.currentFont = CurrentFont()
        lib = self.currentFont.lib.get('CJKDesignFrameSettings', '')
        self.designFrame.set(lib)

    def addSubView(self):
        if self.window is None: 
            self.toggleObserver(True)
            return
        self.window.addGlyphEditorSubview(self.view)
        self.view.show(True)

    def toggleObserver(self, remove=False):
        if self.observers or remove:
            removeObserver(self, 'currentGlyphChanged')
            removeObserver(self, 'drawPreview')
            removeObserver(self, 'draw')
            removeObserver(self, 'drawInactive')
            # removeObserver(self, 'fontBecameCurrent')
            self.observers = False
        else:
            addObserver(self, 'currentGlyphChanged', 'currentGlyphChanged')
            addObserver(self, 'glyphWindowDraw', 'draw')
            addObserver(self, 'glyphWindowDraw', 'drawPreview')
            addObserver(self, 'glyphWindowDraw', 'drawInactive')
            # addObserver(self, "updateFont", "fontBecameCurrent")
            self.observers = True

    def glyphMenuItems(self, info):
        menuItems = []
        item = ('Design Frame Settings', self.openDesignFrameSettings)
        menuItems.append(item)
        info["additionContextualMenuItems"].extend(menuItems)

    def openDesignFrameSettings(self, sender):
        # addObserver(self, "glyphWindowDraw", "drawInactive")
        DesignFrameSettings(self)

    def glyphWindowDraw(self, info):
        s = info['scale']
        notificationName = info["notificationName"]
        if self.currentGlyph is None: return
        self.drawer.draw(self.currentGlyph, notificationName)

    @refreshGlyphView
    def currentGlyphChanged(self, info): 
        currentGlyph = CurrentGlyph()
        if currentGlyph is None: return
        if self.currentGlyph.name == currentGlyph.name: return
        self.currentGlyph = currentGlyph
        self.addSubView()
        self.toggleObserver(True)
        self.observers = False
        self.toggleObserver()

    @refreshGlyphView
    def glyphWindowDidOpen(self, info):
        if self.window:
            self.window.addGlyphEditorSubview(self.view)

    @refreshGlyphView
    def glyphWindowWillClose(self, info):
        if self.window:
            self.window.removeGlyphEditorSubview(self.view)

    @refreshGlyphView
    def updateFont(self, info):   
        self.buttonStartCallback(None)  

numberFormatter = NumberFormatter()
transparentColor = NSColor.colorWithCalibratedRed_green_blue_alpha_(1, 1, 1, 0)

def buttonAesthetic(element):
    element.getNSButton().setFocusRingType_(1)
    element.getNSButton().setBackgroundColor_(transparentColor)
    element.getNSButton().setBordered_(False)

class DesignFrameSettings:

    def __init__(self, controller):
        self.controller = controller
        self.w = HUDFloatingWindow((280, 375),
            "Design Frame Settings",
            )

        y = 10
        self.w.EM_DimensionTitle = TextBox(
            (10, y, 150, 20),
            "Em dimension x/y (FU)",
            sizeStyle = "small"
            )

        self.w.EM_DimensionXEditText = EditText(
            (140, y, 60, 20),
            int(),
            callback = self.callback,
            formatter = numberFormatter,
            sizeStyle = "small"
            )
        self.w.EM_DimensionXEditText.getNSTextField().setFocusRingType_(1)

        self.w.EM_DimensionYEditText = EditText(
            (210, y, 60, 20),
            int(),
            callback = self.callback,
            formatter = numberFormatter,
            sizeStyle = "small"
            )
        self.w.EM_DimensionYEditText.getNSTextField().setFocusRingType_(1)

        y += 30
        self.w.characterFaceTitle = TextBox(
            (10, y, 150, 20),
            "Character face (em %)",
            sizeStyle = "small"
            )

        self.w.characterFaceEditText = EditText(
            (140, y, 60, 20),
            int(),
            callback = self.callback,
            formatter = numberFormatter,
            sizeStyle = "small"
            )
        self.w.characterFaceEditText.getNSTextField().setFocusRingType_(1)

        y += 30
        self.w.overshootTitle = TextBox(
            (10, y, 150, 20),
            "Overshoot out/in (FU)",
            sizeStyle = "small"
            )

        self.w.overshootOutEditText = EditText(
            (140, y, 60, 20),
            int(),
            callback = self.callback,
            formatter = numberFormatter,
            sizeStyle = "small"
            )
        self.w.overshootOutEditText.getNSTextField().setFocusRingType_(1)

        self.w.overshootInEditText = EditText(
            (210, y, 60, 20),
            int(),
            callback = self.callback,
            formatter = numberFormatter,
            sizeStyle = "small"
            )
        self.w.overshootInEditText.getNSTextField().setFocusRingType_(1)

        y += 30
        self.w.shiftTitle = TextBox(
            (10, y, 150, 20),
            "Shift x/y (FU)",
            sizeStyle = "small"
            )

        self.w.shiftXEditText = EditText(
            (140, y, 60, 20),
            int(),
            callback = self.callback,
            formatter = numberFormatter,
            sizeStyle = "small"
            )
        self.w.shiftXEditText.getNSTextField().setFocusRingType_(1)

        self.w.shiftYEditText = EditText(
            (210, y, 60, 20),
            int(),
            callback = self.callback,
            formatter = numberFormatter,
            sizeStyle = "small"
            )
        self.w.shiftYEditText.getNSTextField().setFocusRingType_(1)

        y += 30
        self.w.segmentedButton = SegmentedButton(
            (10, y, -10, 20),
            [dict(title = "Han"), dict(title = "Hangul")],
            callback = self.segmentedButtonCallback
            )
        self.w.segmentedButton.set(self.controller.designFrame.type == 'hangul')

        y+=30
        self.w.han = Group((0, y, -0, 60))
        self.w.han.show(self.controller.designFrame.type == 'han')
        self.w.hangul = Group((0, y, -0, 60))
        self.w.hangul.show(self.controller.designFrame.type == 'hangul')

        self.w.han.horizontaleLineTitle = TextBox(
            (10, 0, 110, 20),
            "Horizontale Line",
            sizeStyle = "small"
            )

        self.w.han.horizontaleLineSlider = Slider(
            (120, 0, -10, 20),
            minValue = 0,
            maxValue = 50,
            value = 15,
            callback = self.callback,
            sizeStyle = "small"
            )

        self.w.han.verticaleLineTitle = TextBox(
            (10, 30, 110, 20),
            "Verticale Line",
            sizeStyle = "small"
            )

        self.w.han.verticaleLineSlider = Slider(
            (120, 30, -10, 20),
            minValue = 0,
            maxValue = 50,
            value = 15,
            callback = self.callback,
            sizeStyle = "small"
            )

        self.w.hangul.horizontaleLineTitle = TextBox(
            (10, 0, 110, 20),
            "Horizontale Grid",
            sizeStyle = "small"
            )

        self.w.hangul.horizontaleLineSlider = Slider(
            (120, 0, -10, 20),
            minValue = 1,
            maxValue = 20,
            value = 8,
            tickMarkCount = 19,
            stopOnTickMarks = True,
            callback = self.callback,
            sizeStyle = "small"
            )

        self.w.hangul.verticaleLineTitle = TextBox(
            (10, 30, 110, 20),
            "Verticale Grid",
            sizeStyle = "small"
            )

        self.w.hangul.verticaleLineSlider = Slider(
            (120, 30, -10, 20),
            minValue = 1,
            maxValue = 20,
            value = 8,
            tickMarkCount = 19,
            stopOnTickMarks = True,
            callback = self.callback,
            sizeStyle = "small"
            )

        y += 60
        self.w.customsFrameTitle = TextBox(
            (10, y, -10, 20),
            "Customs Frames:",
            sizeStyle = "small"
            )
        slider = SliderListCell(tickMarkCount=26, stopOnTickMarks=True)
        self.w.customsFramesList = List(
            (10, y+20, -10, 80),
            [],
            columnDescriptions = [{"title": "Name", "width" : 75}, 
                                {"title": "Value", "cell": slider}],
            showColumnTitles = False,
            editCallback = self.callback,
            drawFocusRing = False
            )
        self.w.addCustomFrame = Button(
            (10, y+100, 130, 20),
            "+",
            callback = self.addCustomFrameCallback,
            sizeStyle = 'small'
            )
        self.w.removeCustomFrame = Button(
            (140, y+100, 130, 20),
            "-",
            callback = self.removeCustomFrameCallback,
            sizeStyle = 'small'
            )

        self.w.exportButton = SquareButton(
            (10, -30, 130, 20),
            "Export",
            callback = self.exportSettings,
            )
        buttonAesthetic(self.w.exportButton)

        self.w.importButton = SquareButton(
            (140, -30, 130, 20),
            "Import",
            callback = self.importSettings,
            )
        buttonAesthetic(self.w.importButton)

        self.setUI()
        self.w.bind("close", self.close)
        self.w.open()

    def exportSettings(self, sender: Button):
        path = putFile()
        path = path.split(".")[0]+".CJKDesignFrameSettings"
        with open(path, 'w', encoding = "utf-8") as file:
            file.write(json.dumps(self.controller.designFrame.get()))

    @refreshGlyphView
    def importSettings(self, sender: Button):
        path = getFile()
        with open(path[0], 'r', encoding = "utf-8") as file:
            self.controller.designFrame.set(json.load(file))
        self.setUI()

    @refreshGlyphView
    def segmentedButtonCallback(self, sender):
        for i, group in enumerate([self.w.han, self.w.hangul]):
            group.show(i == sender.get())
        self.controller.designFrame = [HanDesignFrame, HangulDesignFrame][sender.get()]()
        self.callback(sender)

    @refreshGlyphView
    def close(self, sender: Window):
        # removeObserver(self.controller, 'drawInactive')
        self.controller.currentFont.lib["CJKDesignFrameSettings"] = self.controller.designFrame.get()

    @refreshGlyphView
    def addCustomFrameCallback(self, sender: Button):
        name = "Frame%i"%len(self.w.customsFramesList.get())
        self.w.customsFramesList.append(dict(Name = name, Value = 0))

    def removeCustomFrameCallback(self, sender: Button):
        sel = self.w.customsFramesList.getSelection()
        if not sel: return
        l = self.w.customsFramesList.get()
        l.pop(sel[0])
        self.w.customsFramesList.set(l)
        self.callback(None)

    @refreshGlyphView
    def callback(self, sender):
        try:
            x = int(self.w.EM_DimensionXEditText.get())
            y = int(self.w.EM_DimensionYEditText.get())
            charface = int(self.w.characterFaceEditText.get())
            overshootIn = int(self.w.overshootInEditText.get())
            overshootOut = int(self.w.overshootOutEditText.get())

            shiftX = int(self.w.shiftXEditText.get())
            shiftY = int(self.w.shiftYEditText.get())

            dftype = ["han", "hangul"][int(self.w.segmentedButton.get())]
            if dftype == 'han':
                horizontaleLine = int(self.w.han.horizontaleLineSlider.get())
                verticalLine = int(self.w.han.verticaleLineSlider.get())
            else:
                horizontaleLine = int(self.w.hangul.horizontaleLineSlider.get())
                verticalLine = int(self.w.hangul.verticaleLineSlider.get())
            customsFrames = self.w.customsFramesList.get()
            customsFrames = [{"Name":e["Name"], "Value":int(e["Value"])} for e in customsFrames]
            lib = {
                "em_Dimension":[x, y],
                "characterFace":charface,
                "overshoot":[overshootOut, overshootIn],
                "shift":[shiftX, shiftY],
                "horizontalLine":horizontaleLine,
                "verticalLine":verticalLine,
                "customsFrames":customsFrames,
                "type": dftype
                }
            self.controller.designFrame.set(lib)
            self.controller.currentFont.lib["CJKDesignFrameSettings"] = self.controller.designFrame.get()
        except: pass

    def setUI(self):
        lib = self.controller.designFrame.get()
        self.w.EM_DimensionXEditText.set(int(lib.get("em_Dimension", list())[0]))
        self.w.EM_DimensionYEditText.set(int(lib.get("em_Dimension", list())[1]))
        self.w.characterFaceEditText.set(int(lib.get("characterFace", int())))
        self.w.overshootInEditText.set(int(lib.get("overshoot", list())[1]))
        self.w.overshootOutEditText.set(int(lib.get("overshoot", list())[0]))
        self.w.shiftXEditText.set(int(lib.get("shift", list())[0]))
        self.w.shiftYEditText.set(int(lib.get("shift", list())[1]))
        if self.controller.designFrame.type == 'han':
            self.w.han.horizontaleLineSlider.set(int(lib.get("horizontalLine", int())))
            self.w.han.verticaleLineSlider.set(int(lib.get("verticalLine", int())))
        else:
            self.w.hangul.horizontaleLineSlider.set(int(lib.get("horizontalLine", int())))
            self.w.hangul.verticaleLineSlider.set(int(lib.get("verticalLine", int())))
        self.w.segmentedButton.set(lib.get("type", "han") != "han")
        self.segmentedButtonCallback(self.w.segmentedButton)
        self.w.customsFramesList.set(lib.get("customsFrames", list()))

class DesignFrame:

    # __slots__ = "em_Dimension", "characterFace", "overshoot", \
    #             "horizontalLine", "verticalLine", "customsFrames"

    def __init__(self):
        self.em_Dimension = [1000, 1000]
        self.characterFace = 90
        self.overshoot = [20, 20]
        self.shift = [0, 0]
        self.customsFrames = []

    def set(self, lib: dict):
        if not lib: return
        for k, v in lib.items():
            setattr(self, k, v)

    def get(self) -> dict:
        return vars(self)

    def __len__(self) -> int:
        return len(list(filter(lambda x: getattr(self, x), vars(self))))

    def __str__(self) -> str:
        str = ""
        for e in vars(self):
            str += f"{e}:{getattr(self, e)}, "
        return str

class HanDesignFrame(DesignFrame):

    def __init__(self):
        super().__init__()
        self.horizontalLine = 15
        self.verticalLine = 15
        self.type = 'han'

class HangulDesignFrame(DesignFrame):

    def __init__(self):
        super().__init__()
        self.horizontalLine = 8
        self.verticalLine = 8
        self.type = 'hangul'


class ViewCanvas(CanvasGroup):

    def __init__(self, controller, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.controller = controller

        y = 5
        self.drawPreview = CheckBox((5, y, -0, 20), 
            "Draw Preview", 
            value = 0, 
            callback = self.drawPreviewCallback,
            sizeStyle = "mini"
            )
        y += 20
        self.secondLines = CheckBox((5, y, -0, 20), 
            "Second Lines", 
            value = 1, 
            callback = self.secondLinesCallback,
            sizeStyle = "mini"
            )
        y += 20
        self.customsFrames = CheckBox((5, y, -0, 20), 
            "Customs Frames", 
            value = 1, 
            callback = self.customsFrameCallback,
            sizeStyle = "mini"
            )

    @refreshGlyphView    
    def drawPreviewCallback(self, sender: CheckBox):
        self.controller.drawer.drawPreview = sender.get()

    @refreshGlyphView    
    def secondLinesCallback(self, sender: CheckBox):
        self.controller.drawer.secondLines = sender.get()

    @refreshGlyphView    
    def customsFrameCallback(self, sender: CheckBox):
        self.controller.drawer.customsFrames = sender.get()

class DesignFrameDrawer:

    def __init__(self, controller):
        self.controller = controller
        self.drawPreview = False
        self.secondLines = True
        self.customsFrames = True

    def _getEmRatioFrame(self, frame: int, w: int, h: int) -> tuple:
        charfaceW = w * frame / 100
        charfaceH = h * frame / 100
        x = (w - charfaceW) * .5
        y = (h - charfaceH) * .5
        return x, y, charfaceW, charfaceH

    def _makeOvershoot(self, 
            glyph: RGlyph, 
            origin_x: int, 
            origin_y: int, 
            width: int, 
            height: int, 
            inside: int, 
            outside: int):
        ox = origin_x - outside
        oy = origin_y - outside
        width += outside
        height += outside
        pen = glyph.getPen()
        pen.moveTo((ox, oy))
        pen.lineTo((ox + width + outside, oy))
        pen.lineTo((ox + width + outside, oy + height + outside))
        pen.lineTo((ox, oy + height + outside))
        pen.closePath()
        ox = origin_x + inside
        oy = origin_y + inside
        width -= outside + inside
        height -= outside + inside
        pen.moveTo((ox, oy))
        pen.lineTo((ox, oy + height - inside))
        pen.lineTo((ox + width - inside, oy + height - inside))
        pen.lineTo((ox + width - inside, oy))
        pen.closePath()
        glyph.round()
        drawGlyph(glyph)

    def _makeHorSecLine(self, 
            glyph: RGlyph, 
            origin_x: int, 
            origin_y: int, 
            width: int, 
            height: int):
        pen = glyph.getPen()
        pen.moveTo((origin_x, origin_y))
        pen.lineTo((origin_x + width, origin_y))
        pen.closePath()
        pen.moveTo((origin_x, height))
        pen.lineTo((origin_x + width, height))
        pen.closePath()
        glyph.round()
        drawGlyph(glyph)

    def _makeVerSecLine(self, 
            glyph: RGlyph, 
            origin_x: int, 
            origin_y: int, 
            width: int, 
            height: int):
        pen = glyph.getPen()
        pen.moveTo((origin_x, origin_y))
        pen.lineTo((origin_x, origin_y + height))
        pen.closePath()
        pen.moveTo((width, origin_y))
        pen.lineTo((width, origin_y + height))
        pen.closePath()
        glyph.round()
        drawGlyph(glyph)

    def _makeSquare(self, 
            glyph: RGlyph, 
            origin_x: int, 
            origin_y: int, 
            width: int, 
            height: int):
        pen = glyph.getPen()
        pen.moveTo((origin_x, origin_y))
        pen.lineTo((origin_x, origin_y + height))
        pen.lineTo((origin_x+width, origin_y + height))
        pen.lineTo((origin_x+width, origin_y))
        pen.closePath()
        glyph.round()
        drawGlyph(glyph)

    def _makeHorGrid(self,
                    glyph: RGlyph, 
                    x: int, 
                    y: int, 
                    w: int,
                    h: int,
                    step: int):
        pen = glyph.getPen()
        dist = y + h / step
        for i in range(step-1):
            pen.moveTo((x, dist))
            pen.lineTo((x+w, dist))
            pen.closePath()
            dist += h / step
        drawGlyph(glyph)

    def _makeVerGrid(self,
                    glyph: RGlyph, 
                    x: int, 
                    y: int, 
                    w: int,
                    h: int,
                    step: int):
        pen = glyph.getPen()
        dist = x + w / step
        for i in range(step-1):
            pen.moveTo((dist, y))
            pen.lineTo((dist, y+h))
            pen.closePath()
            dist += w / step
        drawGlyph(glyph)


    def _findProximity(self, 
            pos: list, 
            point: int, 
            left: int = 0, 
            right: int = 0) -> bool:
        for p in pos:
            if p + left < point < p + right:
                return True
        return False

    def draw(self, 
            glyph = None,
            notificationName: str = "",
            mainFrames: bool = True, 
            customsFrames: bool = True,
            proximityPoints: bool = False, 
            translate_secondLine_X: int = 0, 
            translate_secondLine_Y: int = 0,
            scale: int = 1):

        if notificationName == 'drawPreview' and not self.drawPreview: return
        if not self.controller.designFrame: return
        save()
        fill(None)
    
        stroke(0, 0, 0, 1)
        x, y = 0, 0
        w, h = self.controller.designFrame.em_Dimension
        translateX, translateY = self.controller.designFrame.shift
        translate(translateX,translateY)

        if mainFrames:
            self.controller.main_frame_glyph = RGlyph()
            self._makeSquare(self.controller.main_frame_glyph, x, y, w, h)

            frame = self._getEmRatioFrame(self.controller.designFrame.characterFace, w, h)
            self.controller.frame_glyph = RGlyph()
            self._makeSquare(self.controller.frame_glyph, *frame)
            stroke(None)
            fill(0,.75,1,.3)

            outside, inside = self.controller.designFrame.overshoot
            self.controller.overshoot_glyph = RGlyph()
            self._makeOvershoot(self.controller.overshoot_glyph, *frame, *self.controller.designFrame.overshoot)

            g = glyph
            if proximityPoints and g is not None:
                listXleft = [x - outside, x + charfaceW - inside]
                listXright = [x + inside, x + charfaceW + outside]
                listYbottom = [y - outside + translateY, y + charfaceH - inside + translateY]
                listYtop = [y + inside + translateY, y + charfaceH + outside + translateY]

                for c in g:
                    for p in c.points:
                        px, py = p.x, p.y
                        if p.type == "offcurve": continue
                        if px in [x, charfaceW + x] or py in [y + translateY, y + charfaceH + translateY]:
                            fill(0, 0, 1, .4)
                            oval(px - 10 * scale, py - 10 * scale - translateY, 20 * scale, 20 * scale)
                            continue

                        fill(1, 0, 0, .4)
                        drawOval = 0

                        if self._findProximity(listXleft, px, left = -3, right = 0):
                            drawOval = 1
                        elif self._findProximity(listXright, px, left = 0, right = 3):
                            drawOval = 1
                        elif self._findProximity(listYbottom, py, left = -3, right = 0):
                            drawOval = 1
                        elif self._findProximity(listYtop, py, left = 0, right = 3):
                            drawOval = 1
                        if drawOval:
                            oval(px - 20 * scale, py - 20 * scale - translateY, 40 * scale, 40 * scale)
                            continue 

        if self.secondLines:
            fill(None)
            stroke(.65, 0.16, .39, 1)
            if self.controller.designFrame.type == "han":
                ratio = (h * .5 * (self.controller.designFrame.horizontalLine / 50))
                y = h * .5 - ratio
                height = h * .5 + ratio
                self.controller.horizontal_second_line_glyph = RGlyph()
                self._makeHorSecLine(self.controller.horizontal_second_line_glyph, 0, y + translate_secondLine_Y, w, height + translate_secondLine_Y)

                ratio = (w * .5 * (self.controller.designFrame.verticalLine / 50))
                x = w * .5 - ratio
                width = w * .5 + ratio
                self.controller.vertical_second_line_glyph = RGlyph()
                self._makeVerSecLine(self.controller.vertical_second_line_glyph, x + translate_secondLine_X, 0, width + translate_secondLine_X, h)
            else:
                self.controller.horizontal_gride_glyph = RGlyph()
                self._makeHorGrid(self.controller.horizontal_gride_glyph, *frame, step = int(self.controller.designFrame.horizontalLine))
                self.controller.vertical_gride_glyph = RGlyph()
                self._makeVerGrid(self.controller.vertical_gride_glyph, *frame, step = int(self.controller.designFrame.verticalLine))
        
        if self.customsFrames:
            fill(None)
            stroke(0, 0, 0, 1)

            for frame in self.controller.designFrame.customsFrames:
                if not "Value" in frame: continue
                rect(*self._getEmRatioFrame(frame["Value"], w, h))
        restore()

if __name__ == "__main__":
    DesignFrameController()

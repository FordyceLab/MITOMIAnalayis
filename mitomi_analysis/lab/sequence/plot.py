#!/usr/local/bin/python
#
# 	$Id: plot.py,v 1.21 2008/03/11 02:03:25 peter Exp $	
#
#

import base64
import os
import random
import tempfile
import types
import math

from utils import flatten

from . import genbank
    
from PIL import Image
from PIL import ImageFont
from PIL import ImageDraw


__dummyPlot=ImageDraw.Draw(Image.new('RGB',(100,100),'white'))
pointyness = 5

IS_BELOW = -2
IS_ABOVE = -1


class ImageMapException (Exception):
    pass

def test():
    
    sgb = genbank.Record(file("/sumo/home/kael/ncbi/sars.gb"))
    sp = SequencePlot(len(sgb),figSize=(600,600))
    track3 = ScaleTrack(sp,'',25)
    track1 = FeatureTrack(sp,"GI:"+str(sgb.GI()),25,
                              fillColor="black",textColor="white",
                              showDirections=False)
    track1.addGenBankFeature(list(sgb.features())[0])
    track2 = FeatureTrack(sp,'genes',30)
    for f in sgb.features():
        if f.type=="gene":
            track2.addGenBankFeature(f)
    track2.addFeature('test','test',25000,26000,intron=((25500,25900),))
    track4 = StripChartTrack(sp,"coverage",100,"gray",limits=(None,20))
    trace1 = StripChartTrace(traceColor="blue")
    trace1.loadData("/sumo/home/peter/sample_data.txt")
    track4.loadTrace(trace1)
#    trace2 = StripChartTrace(traceColor="red",vertValue="min")
#    trace2.loadData("/sumo/home/peter/sample_data.txt")
#    track4.loadTrace(trace2)
    sp.render()

    print(sp.imageMap)
    sp.save('test.png',clobber=True)
    sp.render(view=(94,906))
    sp.save('testView.png',clobber=True)
    return sp


def labelXTrim(lblText,widthPx,font):
    """return a substring of lblText which will fit in widthPX 
    pixels when rendered with font. 
    """
    i=len(lblText)
    while (__dummyPlot.textsize(lblText[:i],font=font)[0] > widthPx) and i > 0:
        i-=1
    return lblText[:i]


class SequencePlotInterface:
    """container for graphical representation of sequence data and 
    'tracks' of related data.
    
    Provides the user interface for subclasses that use different 
    graphics subsystems, e.g. PIL, matplotlib, gd, etc.
    
    .tracks = ordered list of tracks
    """
    
    def __init__(self,seqLength,figSize=(600,600), margin=(10,10,10,10),
                 trackWidth=490):
        """Make new Sequence Plot
        figSize=(width,height)
        margin = (top,right,bottom,left), like in CSS
        """
        self.width,self.height=figSize
        self.seqLength=seqLength        
        
        self.trackWidth = trackWidth
        self.marginTop,self.marginRight,self.marginBottom,self.marginLeft = margin
        self.labelMargin = self.marginLeft
        self.bPerPxl = None 
        self.trackLeftOffset = self.width-self.trackWidth-self.marginRight
        self.trackRightOffset = self.width-self.marginRight

        self.tracks=[]
        
        self.__fig_init__()
        
    def __fig_init__(self):
        """Graphics specific subclass provides init code here
        """
        pass

        
    def xPxl(self,xSeq,view=None):
        """Transform base (start,end) tuples in to pixel (start, end) tuples 
        A single pair is fine or xSeq can be an iterator or sequence of 
        (start,end) pairs.  (start, end) tuples may have other values of any type 
        in positions after 0 and 1, these are simply passed through.
        
        view can be (start,end) tuple which defines a view port for
        the figure in seq coordinates, or None in which case the entire sequence 
        is shown. 
        
        If a position falls out side of the view, the translated pixel 
        coordinate returned is 0. if both positions are to the one side of view
        -1 is returned for both pixel coords.
        
        """
        if hasattr(xSeq, 'next') or type(xSeq[0]) in (list, tuple):
            return tuple([self.xPxl(x) for x in xSeq])
 
        if view == None:
            viewSize = self.seqLength
            vLeft=1
            vRight=self.seqLength
        else:
            vLeft,vRight = view
            viewSize =  vRight-vLeft
       
        
        left,right = xSeq[0:2]
        if (left < vLeft and right < vLeft or
            right>vRight and left>vRight):
            leftPx=-1
            rightPx=-1
        else:
            if left<vLeft:
                leftPx = 0
            else:
                leftPx=int(round(float(left-vLeft)/self.bPerPxl))+self.trackLeftOffset
    
            if right>vRight:
                rightPx = 0
            else:
                rightPx=int(round(float(right-vLeft)/self.bPerPxl))+self.trackLeftOffset

        return tuple([leftPx,rightPx] + list(xSeq[2:]))


class SequencePlotGraphicsPIL(SequencePlotInterface):
    """container for graphical representation of sequence data and 
    'tracks' of related data.
    
    SequencePlotPIL uses the Python Imaging Library as the graphics system.
    Other 
    """

    
    def render(self,labelFont='/sumo/home/viroview/cgi-bin/Fonts/helvetica-14.pil',
               view=None):
        """Draw (or redraw), but don't save or return the figure. 
        view can be (start,end) tuple which defines a view port for
        the figure, or None in which case the entire sequence is shown. 
        """
        
        def drawBox(left,right,direction=''):
            if (direction in ('+','3','f') 
                and right >0
                and t.showDirections):
                #show direction - right
                if left<=0:
                    left=self.trackLeftOffset
                startArrow = right-pointyness
                if startArrow < left:
                    startArrow = left
                vertices = [(left,top),(startArrow,top),
                                   (right,top+(bot-top)/2),
                                   (startArrow,bot),(left,bot),
                                   (left,top)]
            elif (direction in ('-','c','rc','r','5') 
                  and left>0
                  and t.showDirections):
                # show direction -  left
                if right <= 0:
                    right=self.rightTrackOffset
                startArrow = left+pointyness
                if startArrow > right:
                    startArrow = right
                vertices = [(right,top),(startArrow,top),
                             (left,top+(bot-top)/2),
                             (startArrow,bot),(right,bot),
                             (right,top)]
            else:
                # don't show direction bc the dir indicator is 
                # outside the view port, or other reasons 
                # (like t.showDirections == False, or "direction" 
                # does not specify a direction
                if left <= 0:
                    left=self.trackLeftOffset
                if right <=0:
                    right = self.trackRightOffset
                vertices = [(left,top),(right,top),
                             (right,bot),(left,bot)]
            self.plot.polygon(vertices,fill=fillColor)
            self.imageMap.addPolygon(self.imageMap.id +'_'+name,vertices,
                                     mouseovertext=name)    
            
        def labelBox(left,right,label):                   
            if left <= 0:
                left = self.trackLeftOffset
            if right <= 0:
                right = self.trackRightOffset
            # feature label
            lblText = labelXTrim(label, right-left,self.labelFont)
            txtWidth,txtHeight = self.plot.textsize(lblText,font=self.labelFont)
            

            fLRcenter=left+(right-left)/2
            # vert/horiz centered
            txtLeft = fLRcenter-txtWidth/2 
            txtTop = tTBcenter-txtHeight/2
            
            self.plot.text((txtLeft,txtTop),lblText,
                           font=self.labelFont,fill=textColor)
 
        def drawLine (left,right,offset=0,fill='black',width=1):
            if left == 0:
                left = self.trackLeftOffset
            if right == 0:
                right = self.trackRightOffset
            self.plot.line(((left,tTBcenter+offset),(right,tTBcenter+offset)),fill,width)
        
        if view == None:
            viewSize = self.seqLength
            vLeft=0
            vRight=self.seqLength
        else:
            vLeft,vRight = view
            viewSize =  vRight-vLeft
        
        self.bPerPxl = (float(viewSize)/float(self.trackWidth))
 
        # set everything to empty
        self.image = Image.new('RGB',(self.width,self.height),'white')
        self.plot = ImageDraw.Draw(self.image)
        self.labelFont = ImageFont.load(labelFont)
        self.imageMap = ImageMap(id=None)
        
        
        
        bot=self.height-self.marginBottom
        for t in self.tracks:
            # track label            
            top = bot - t.height
            tTBcenter=top+(bot-top)/2
            lblText = labelXTrim(t.label,(self.trackLeftOffset-self.labelMargin),
                                 self.labelFont)
            txtWidth,txtHeight = self.plot.textsize(lblText,font=self.labelFont)
            # left justify
            txtLeft = self.trackLeftOffset-self.marginLeft-txtWidth
            # center vertical 
            txtTop = tTBcenter-txtHeight/2
            self.plot.text((txtLeft,txtTop),lblText,font=self.labelFont,fill="black")

            # label done - now track type specific code
            if isinstance(t, FeatureTrack):    
                for f in t.features:
                    start,end,settings = f
                    left,right= self.xPxl((start,end),(vLeft,vRight))
                    # feature is entirely outside of the view port
                    if -1 in (left,right):
                        continue                    
                    #set feature color
                    if 'fillColor' in settings:
                        fillColor = settings['fillColor']
                    else:
                        fillColor = t.fillColor
                    if 'textColor' in settings:
                        textColor = settings['textColor']
                    else:
                        textColor = t.textColor
                    
                    name = settings['name']
                    label = settings['label']
                    direction = settings['direction']

                    if 'intron' in settings:
                        boxes=[]
                        lines=[]
                        biggestBox = (0,0)
                        eStart=left
                        for s,e in settings['intron']:
                            iStart,iEnd =self.xPxl((s,e),(vLeft,vRight))
                            if -1 not in (eStart,iStart):
                                boxes.append((eStart,iStart,direction))
                            lines.append((iStart,iEnd))
                            if eStart==0:
                                l=self.trackLeftOffset
                            else:
                                l=eStart
                            if iStart == 0:
                                r=self.trackRightOffset
                            else:
                                r=iStart
                                
                            boxSize = r-l
                            if boxSize > (biggestBox[1]-biggestBox[0]):
                                biggestBox=(eStart,iStart)
                            eStart=iEnd
                        boxes.append((eStart,right,direction))
                        if eStart==0:
                            l=self.trackLeftOffset
                        else:
                            l=eStart
                        if right == 0:
                            r=self.trackRightOffset
                        else:
                            r=right
                            
                        boxSize = r-l
                        if boxSize > (biggestBox[1]-biggestBox[0]):
                            biggestBox=(eStart,right)
                        
                        
                    else:
                        biggestBox=((left,right))
                        boxes = [(left,right,direction)]
                        lines = []
                        
                    for left,right,direction in boxes:
                        drawBox(left,right,direction)
                    labelBox(biggestBox[0], biggestBox[1], label)
                        
                    #print label,lines
                    for left,right in lines:
                        drawLine(left,right)
                        
            elif isinstance(t, ScaleTrack):
                
                """
                For numTicks and scale, some niceness is implemented based on the length and
                the start and end view coordinates.  It'll end up producing a track with 5 to
                10 tick marks (and a scale that's a nice number (e.g. 50, 100, 200, 500, etc.)
                """
        
                i = 1
                switch = 1

                #prevent an infinite loop
        
                if viewSize < 4:
                    raise ArgumentError(("The chosen view size is too small."))
                    
                #first figure out the scale
                
                while i > 0:
                    if (viewSize/i >= 4) and (viewSize/i < 10):
                        scale = i
                        i = 0
                    elif (switch%3 == 0) or (switch%3 == 1):
                        i*=2
                    else:
                        i=((i/2)*5)
                    switch+=1

                #now figure out the tick marks

                tickMarks = []

                if vLeft % scale != 0:
                    firstNice = scale * ((vLeft / scale) + 1)
                    tickMarks.append(vLeft)
                else:
                    firstNice = vLeft
                    
                j = firstNice

                while j < vRight:
                    tickMarks.append(j)
                    j += scale
                tickMarks.append(vRight)

                #convert tick marks to pixel space

                tickPixels = [self.xPxl((s,s+1),view=(vLeft,vRight))[0] for s in tickMarks]
                
                #draw a line of view length
                
                self.plot.line(((self.trackLeftOffset,(top+tTBcenter)/2),
                                (self.trackRightOffset,(top+tTBcenter)/2)),
                               fill="black",width=1)

                #draw each tick mark

                for tick in tickPixels:
                    self.plot.line(((tick,top),(tick,tTBcenter)),fill="black",width=1)
                    
                #for each of the tick marks, draw a label below it
                #special cases for first and second, penultimate and last labels
                
                for k in range(len(tickMarks)-2):
                    baseNum = str(tickMarks[k])
                    textWidth, textHeight = self.plot.textsize(baseNum,
                                                              font=self.labelFont)
                    textLeft = tickPixels[k] - (textWidth/2)

                    #automatically draw first tick, ensure no overlaps
                    
                    if k == 0:
                        self.plot.text((textLeft,tTBcenter),baseNum,
                                       font=self.labelFont,fill="black")
                    else:
                        if textLeft > tickPixels[k-1]:
                            self.plot.text((textLeft,tTBcenter),baseNum,
                                           font=self.labelFont,fill="black")

                #automatically draw last tick, ensure no overlap with penultimate tick

                penultimate = (len(tickMarks)-2)
                lastWidth = self.plot.textsize(str(tickMarks[-1]),font=self.labelFont)[0]
                lastLeft = tickPixels[-1] - (lastWidth/2)
                penWidth = self.plot.textsize(str(tickMarks[penultimate]),
                                              font=self.labelFont)[0]
                penLeft = tickPixels[penultimate] - (penWidth/2)
                if lastLeft > tickPixels[penultimate]:
                    self.plot.text((penLeft,tTBcenter),str(tickMarks[penultimate]),
                                    font=self.labelFont,fill="black")
                self.plot.text((lastLeft,tTBcenter),str(tickMarks[-1]),
                                font=self.labelFont,fill="black")
                    
            elif isinstance(t, StripChartTrack):

                #first cycle through all the lists of tuples in chartData

                #if there is more than one trace in chartData, turn the
                #fill option off.

                if len(t.chartData) > 1:
                    t.fill = ""

                #get vertical scale set up based on limits

                #limits can be (None, None) which means that it will auto-scale
                #based on maximum and minimum, or it can be (min, None) which
                #means it will enforce min and auto-scale max, or vice-versa for
                #(None, max), or it can be completely user-defined as in (min, max)

                traceValues = []
                for trace in t.chartData:
                    traceValues = traceValues + trace.getValues((vLeft,vRight))
                
                minValue = min(traceValues)
                maxValue = max(traceValues)

                if t.limits[0] == None:
                    yMin = minValue
                else:
                    yMin = t.limits[0]

                if t.limits[1] == None:
                    yMax = maxValue
                else:
                    yMax = t.limits[1]

                #the outer for-loop cycles through each trace individually, first
                #converting (minBase, value) through (maxBase, value) to the form
                #(minPixel, newValue) through (maxPixel, newValue) using xPxl, then
                #uses that dictionary to draw the points (minPixel, pixelValue)
                #through (maxPixel, pixelValue) for each trace
                
                for trace in t.chartData:
                    
                    pixelDict = {}

                    #set up dictionary with bases as keys
                    
                    for base in range(vLeft, vRight):
                        basePixel = self.xPxl((base,base+1),view=(vLeft,vRight))[0]
                        pixelDict[basePixel] = []
                    
                    #add vertical measures for each base

                    i = 0
                    
                    for base, value in trace.traceData:
                        if base < vLeft:
                            i+=1
                            continue
                        if base > vRight:
                            break
                        basePixel = self.xPxl((base,base+1),view=(vLeft,vRight))[0]
                    
                        if basePixel in pixelDict:
                            pixelDict[basePixel].append(trace.traceData[i][1])
                            i+=1
                    
                    #convert the list of values at each pixel into a single
                    #value based on the vertValue option

                    for xPixel in pixelDict:
                        if pixelDict[xPixel] != []:
                            if trace.vertValue == "avg":
                                newValue = sum(pixelDict[xPixel]) / len(pixelDict[xPixel])
                            elif trace.vertValue == "max":
                                newValue = max(pixelDict[xPixel])
                            elif trace.vertValue == "min":
                                newValue = min(pixelDict[xPixel])
                            else:
                                raise ArgumentError("Allowable vertValues are"
                                                  "'max', 'min', or 'avg'; not %s"%vertValues)
                            pixelDict[xPixel] = newValue


                    #convert the vertical values into yPixels

                    for key in list(pixelDict.keys()):
                        v = pixelDict[key]
                        if v != []:
                            pixelValue = t.yPxl((v,v+1),(yMin,yMax))[0]
                            pixelDict[key] = pixelValue

                    #now draw everything

                    #draw halfway line (will be back-most layer)

                    self.plot.line([(self.trackLeftOffset,(bot+top)/2),
                                    (self.trackRightOffset,(bot+top)/2)],
                                    fill="black")
                    
                    #first, if fill is on, fill in the area under and including the trace

                    if t.fill != "":
                        for key in list(pixelDict.keys()):
                            if pixelDict[key] != []:
                                if pixelDict[key] == IS_ABOVE:
                                    self.plot.line(((key,bot),(key,top)),fill=t.fill,width=1)
                                elif pixelDict[key] == IS_BELOW:
                                    pass
                                else:
                                    self.plot.line(((key,bot),(key,bot-pixelDict[key])),
                                                   fill=t.fill,width=1)
                                
                    #now graph the trace, irrespective of having filled

                    xCoords = list(pixelDict.keys())
                    xCoords.sort()
                        
                    for key in xCoords:
                        #only draw a point if the value is in view
                        
                        if (pixelDict[key] != [] and
                            pixelDict[key] != IS_ABOVE and
                            pixelDict[key] != IS_BELOW):
                            self.plot.point((key,bot-pixelDict[key]),
                                            fill=trace.traceColor)

                    #connect dots if necessary

                    if t.connectDots:
                    
                        for i,key in enumerate(xCoords):
                            if i!=len(xCoords)-1:
                                if (pixelDict[key] != [] and
                                    pixelDict[xCoords[i+1]] != []):

                                    if pixelDict[key] == IS_ABOVE:
                                        currHeight = top
                                    elif pixelDict[key] == IS_BELOW:
                                        currHeight = bot
                                    else:
                                        currHeight = bot-pixelDict[key]

                                    if pixelDict[xCoords[i+1]] == IS_ABOVE:
                                        nextHeight = top
                                    elif pixelDict[xCoords[i+1]] == IS_BELOW:
                                        nextHeight = bot
                                    else:
                                        nextHeight = bot-pixelDict[xCoords[i+1]]
                                    self.plot.line(((key,currHeight),
                                                    (xCoords[i+1],nextHeight)),
                                                     fill=trace.traceColor)

                    #draw a box around the whole track
                    #also label max, min, and half
                    
                    self.plot.rectangle([(self.trackLeftOffset,bot),(self.trackRightOffset,top)],
                                        outline="black")
                    
                    self.plot.text((self.trackRightOffset+1,
                                    bot-(txtHeight/2)),"%.2f"%yMin, font=self.labelFont,
                                   fill="black")

                    half = (yMin+yMax)/2

                    self.plot.text((self.trackRightOffset+1,
                                   ((top+bot)/2)-(txtHeight/2)),"%.2f"%half,
                                   font=self.labelFont,fill="black")

                    self.plot.text((self.trackRightOffset+1,
                                    top-(txtHeight/2)),"%.2f"%yMax, font=self.labelFont,
                                   fill="black")

            #move up for next track
            bot = top - t.margin
            
        
    def save(self,filename,clobber=False,format=None):
        if os.access(filename,os.F_OK) and not clobber:
            raise RuntimeError('file "%s" exists' % filename)
        self.image.save(file(filename,'wb'),format=format)
     
    def base64png(self):
        tfd,tfn=tempfile.mkstemp('.png')
        try:
            self.image.save(file(tfn,'wb'),format="PNG")
            b64str = base64.b64encode(file(tfn).read())
        finally:
            os.unlink(tfn)
            
        return b64str
   
        
class SequencePlot(SequencePlotInterface,SequencePlotGraphicsPIL): 
    """
    """
    pass

class ScaleTrack:
    """
    A track to plot at the bottom of all other tracks with mile markers
    and scale bars for the other tracks.
    """

    def __init__ (self,plot,label,height,textColor="black",margin=5):
        self.plot = plot
        self.height = height
        self.label = label
        self.margin = margin
        self.textColor = textColor
        
        self.plot.tracks.append(self)

class StripChartTrack:
    """
    A track to plot at the top of all other tracks with a trace of
    a given measure represented by a vertical value at each base, e.g.
    conservation, hydrophobicity, etc.
    """
    
    def __init__ (self,plot,label,height,fill,limits=(None,None),
                  connectDots=True,textColor="black",margin=15):
        self.plot = plot
        self.height = height
        self.label = label
        self.margin = margin
        self.textColor = textColor
        self.fill = fill
        self.connectDots = connectDots

        #the limits will be the vertical minimum and maximum for the chart

        #a value of "None" at either limit will auto-scale at that or both
        #limits.  if the user wants a %age scale, for example, then the user
        #should set limits = (0,100)
        
        self.limits = limits
        
        #the chartData will be a list of StripChartTraces
        
        self.chartData = []
        self.yPerPxl = None
        
        self.plot.tracks.append(self)
        
    def loadTrace(self,newTrace):
        self.chartData.append(newTrace)

    def yPxl(self,ySeq,yView):
        """
        Totally modded code from xPxl...
        Transform limits (min, max) tuples into pixel (vBottom, vTop) tuples.
        yView will be determined in render and passed in as (min, max)
        It will return 0 for one of the values if one of them is out of view,
        will return (-1, -1) if both values are above view, will return
        (-2, -2) if both values are below view, and will return (-2, -1) if the
        bottom is below view and the top is above view.
        """

        if hasattr(ySeq, 'next') or type(ySeq[0]) in (list, tuple):
            return tuple([self.yPxl(y) for y in ySeq])

        yViewSize = yView[1] - yView[0]
        vBottom = yView[0]
        vTop = yView[1]

        self.yPerPxl = (float(yViewSize)/float(self.height))

        bottom, top = ySeq[0:2]
        if (bottom < vBottom) and (top < vBottom):
            #both below
            botPxl = IS_BELOW
            topPxl = IS_BELOW

        elif (top > vTop) and (bottom > vTop):
            #both above
            botPxl = IS_ABOVE
            topPxl = IS_ABOVE  

        else:
            if bottom < vBottom:
                botPxl = IS_BELOW
            else:
                botPxl = int(round(float(bottom - vBottom)/self.yPerPxl))

            if top > vTop:
                topPxl = IS_ABOVE
            else:
                topPxl = int(round(float(top - vTop)/self.yPerPxl))

        return tuple([botPxl,topPxl] + list(ySeq[2:]))


class StripChartTrace:
    """
    A container for strip chart data.  Each strip chart trace object has traceData
    object which is a list of tuples of the form (baseNum, value), and it has a user
    defined traceColor.
    """


    def __init__ (self,traceColor="black",vertValue="max"):
        self.traceData = []
        self.traceColor = traceColor

        #the vertValue will be the measure by which a vertical value is determined,
        #e.g. the max, the min, or the avg of all potential values at that base
        
        self.vertValue = vertValue
        
    def loadData(self,filePath,logBase=0):
        #method to load in tuples from from file given path
        dataFile = open(filePath, "r")
        for line in dataFile:
            data = line.strip().split()
            base = int(data[0])
            height = float(data[1])
            if logBase != 0 and height != 0:
                height = math.log(height,logBase)
            self.traceData.append((base,height))
        dataFile.close()
            
    def getValues(self,view):
        #quick method to spit out all values (not bases) in view
        traceValues = []
        for pair in self.traceData:
            if (pair[0] >= view[0]) and (pair[0] <= view[1]):
                traceValues.append(pair[1])
        return traceValues
            
class FeatureTrack:
    """
    A track to plot.
    All positions are in sequence coordinates.
    Directions can be '+','f','-','c','rc','r','3','5' or any other string, meaning 
    no direction.  '-','c',rc','r','5' all mean the same thing as do '+','3' and 'f'. 
    
    All other values are unitless.
    properties: 
        features:  
            a list of where positions and 
            other data are saved in a list like:
             [(start1,end1,settings1), 
              (start2,end2,settings)].
        start and end are integers in sequence space and settings is a 
        dictionary with keys name,label,direction and optionally, 
        fillColor, textColor, mouseovertext. 
    """
    
    def __init__ (self,plot,label,height,showTicks=False,margin=5,
                  fillColor='gray',textColor="black",showDirections=True):
        """Make a new track
        plot is the parent plot
        label is show to the side of the track.
        height is the height in pixels
        showTicks is the interval for track tick marks.
 
         Features can be added by appending to self.features or using
         addGenBankFeature.
        
        Values should be set somehow.
        
        """
        self.plot = plot
        self.label=label
        self.height = height
        self.margin=margin
        self.showTicks=showTicks
        self.features=[]
        self.fillColor=fillColor
        self.textColor=textColor
        self.familyTracks=[self]
        self.showDirections=showDirections
    
        self.plot.tracks.append(self)
        
        
    def addGenBankFeature(self,f,name=None,label=None,direction=None,
                          allowOverlap=False,autoAddTracks=True):
        """Add a feature to track's feature list.
        Note that name and label can be feature qualifier
        names and the values of the qualifiers will be used.
        
        if direction is None the direction will be deduced from the 
        feature location.
        """
        defaultDirection = direction
        nameGuessOrder=["product",
                        "gene",
                        "locus_tag",
                        "note",
                        "protein_id",
                        "organism"]
        
        settingsDict = {"allowOverlap":allowOverlap,"autoAddTracks":autoAddTracks}
        
        def processRegion(r):
            if defaultDirection==None:
                if r.complement:
                    direction='-'
                else:
                    direction = '+'
            else:
                direction = defaultDirection
            return [r.start,r.end,direction]

        # set name/label 
        if name != None:
            if name in f.qualifiers:
                name = f.qualifiers[name]
        else:
            for qualGuess in nameGuessOrder:
                if qualGuess in f.qualifiers:
                    name = f.qualifiers[qualGuess]
                    break
            if name == None:
                name = ''
        
        if label == None:
            label = name
        else:
            if label in f.qualifiers:
                label = f.qualifiers[label]
        
        rv = [name,label]
        regions = f.regions()
        if len(regions) == 1:
            self.addFeature(*([name,label] + processRegion(regions[0])),
                            **settingsDict)
        else:
            # calculate introns
#            for r in regions:
#                print r.start
#                print r.end
            start = regions[0].start
            end = regions[-1].end
             
            if defaultDirection==None:
                if regions[0].complement:
                    direction = '-'
                else:
                    direction = '+'
            else:
                direction = defaultDirection
            introns = []
            for i in range(len(regions)-2):
                #print regions[i].end,regions[i+1].start
                if regions[i].end-regions[i+1].start > 1:
                    introns.append((regions[i].end,regions[i+1].start))
            if len(introns)>0:
                settingsDict['intron'] = introns
            
            self.addFeature( name,label,start,end,direction,
                            **settingsDict)
           
        
 
    def addFeature(self,name,label,start,end,direction='',allowOverlap=False,
                   autoAddTracks=True,**args):
        """Check for overlap and add feature to track.
        returns True if the feature is added successfully,
        otherwise False.
        
        Additional kw args are added to the feature's settings dictionary
        """
        args['name']=name 
        args['label']=label 
        args['direction']=direction 
        if allowOverlap:
            self.features.append((start,end,args))
            return True
        else:
            # find an empty track, yo'
            for trk in self.familyTracks:
                if trk.rangeClear(start,end):
                    trk.features.append((start,end,args))
                    return True
            if autoAddTracks:
                trk = self.__class__(self.plot,self.label,self.height,
                                     fillColor=self.fillColor,
                                     textColor=self.textColor)
                self.familyTracks.append(trk)
                trk.features.append((start,end,args))
                return True
            
            return False
        
    def rangeClear(self,start,end):
        """returns True if no feature overlaps this range, otherwise false.
        overlapping end points are not allowed.
        """
        for f in self.features:
            fStart,fEnd = f[:2]
            if fEnd < start:
                continue
            if fStart > end:
                continue
            return False
        return True



class ImageMap:
    """HTML image map
    """
    
    def __init__(self, id=None, **mapTags):
        """New image map.
        Random id is generated as necessary.
        """
        
        if id == None:
            id = str(random.randint(1,900000))
        self.id=id
        self.areaElements = []

        self.moreTags={}
        for k in list(mapTags.keys()):
            if k != "mapTags":
                self.moreTags[k]=mapTags[k]
            else:
                for ky,vlu in list(mapTags[k].items()):
                    self.moreTags[ky]=vlu


    def __str__(self):
        return ('<map id="%s" name="%s" %s>\n%s\n</map>' %
                (self.id,self.id,
                 ' '.join([('%s="%s"' % (x,y)) for x,y, in  list(self.moreTags.items())]),
                "\n".join(self.areaElements)))


    def area(self,id,shape,**kwArgs):
        """return an area tag.
        tag attributes (e.g. COORDS, ALT, SYTLE, HREF, TARGET, etc.) can be specified as kwArgs.
        """

        if id == None:
            id = '_'.join((self.id,shape, str(random.randint(1,900000))))

        for k in list(kwArgs.keys()):
            if k=='more_tags' and type(kwArgs[k]) == dict:
                moreTags=kwArgs[k]
                del kwArgs[k]

                for k in  list(moreTags.keys()):
                    kwArgs[k] = moreTags[k]

        return ('<area id="%s" shape="%s" %s>' %
                (id,shape,
                 ' '.join([('%s="%s"' % (x,y)) for x,y, in  list(kwArgs.items())])))
    

    def addCircle(self,id,center_xy,radius,**kwArgs):
        """Add a CIRCLE area.
        also see 'area'.
        """
        
        if radius < 1:
            radius=1
        
        coords = ",".join([str(int(round(x))) for x in (center_xy[0],center_xy[1],radius)])
        self.areaElements.append(self.area(id,'circle',coords=coords,**kwArgs))
        
    def addPolygon(self,id,vertices,**kwArgs):
        """Add a POLY area.
        also see 'area'.
        """
        coords = ",".join([str(int(round(x))) for x in flatten(vertices)])
        self.areaElements.append(self.area(id,'poly',coords=coords,**kwArgs))

    def addRectangle(self,id,left_x,top_y,right_x,bottom_y,**kwArgs):
        """Add a RECT area.
        also see 'area'.
        """
        coords = ",".join([str(int(round(x))) for x in (left_x,top_y,right_x,bottom_y)])
        self.areaElements.append(self.area(id,'rect',coords=coords,**kwArgs))

    def addDefault(self,id,**kwArgs):
        """Add the DEFUALT area.
        also see 'area'.
        """
        self.areaElements.append(self.area(id,'default',**kwArgs))

    def mapHtml (self):
        """Complete HTML for the MAP tag.
        """
        return str(self)

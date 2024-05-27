import logging
import os
from typing import Annotated, Optional

import vtk
from typing import List

import numpy as np
from __main__ import qt, slicer
import math
import slicer
from slicer.i18n import tr as _
from slicer.i18n import translate
from slicer.ScriptedLoadableModule import *
from slicer.util import VTKObservationMixin
from slicer.parameterNodeWrapper import (
    parameterNodeWrapper,
    WithinRange,
)

from slicer import vtkMRMLScalarVolumeNode


#
# MeasurementWithSpheres
#


class MeasurementWithSpheres(ScriptedLoadableModule):
    """Uses ScriptedLoadableModule base class, available at:
    https://github.com/Slicer/Slicer/blob/main/Base/Python/slicer/ScriptedLoadableModule.py
    """

    def __init__(self, parent):
        ScriptedLoadableModule.__init__(self, parent)
        self.parent.title = _("MeasurementWithSpheres")  # TODO: make this more human readable by adding spaces
        # TODO: set categories (folders where the module shows up in the module selector)
        self.parent.categories = [translate("qSlicerAbstractCoreModule", "Examples")]
        self.parent.dependencies = []  # TODO: add here list of module names that this module requires
        self.parent.contributors = ["Cagatay Alptekin (Non-Nocere)"]  # TODO: replace with "Firstname Lastname (Organization)"
        # TODO: update with short description of the module and a link to online module documentation
        # _() function marks text as translatable to other languages
        self.parent.helpText = _("""
This is an example of scripted loadable module bundled in an extension.
See more information in <a href="https://github.com/cagatayalptekin/MeasurementWithSpheres">module documentation</a>.
""")
        # TODO: replace with organization, grant and thanks
        self.parent.acknowledgementText = _("""
This file was originally developed by Cagatay Alptekin.
""")

        
       
        # Additional initialization step after application startup is complete
 

 
#
# MeasurementWithSpheresParameterNode
#


@parameterNodeWrapper
class MeasurementWithSpheresParameterNode:
    """
    The parameters needed by module.

    inputVolume - The volume to threshold.
    imageThreshold - The value at which to threshold the input volume.
    invertThreshold - If true, will invert the threshold.
    thresholdedVolume - The output volume that will contain the thresholded volume.
    invertedVolume - The output volume that will contain the inverted thresholded volume.
    """
    lineNode = slicer.mrmlScene.AddNewNodeByClass('vtkMRMLMarkupsLineNode', 'Length1')
  
    observerId:int
    lineNode2 =  slicer.mrmlScene.AddNewNodeByClass('vtkMRMLMarkupsLineNode', 'Length2')
    lineNode3 =  slicer.mrmlScene.AddNewNodeByClass('vtkMRMLMarkupsLineNode', 'Length3')
    angleNode = slicer.mrmlScene.AddNewNodeByClass('vtkMRMLMarkupsAngleNode','Angle')
# Get markup node from scene
    markups = slicer.mrmlScene.GetFirstNodeByClass('vtkMRMLMarkupsFiducialNode')
    i=0
    count=1
    spheres = [vtk.vtkSphereSource() for _ in range(4)]
  
    models: List[slicer.vtkMRMLModelNode] = []
    lineLength: Annotated[float, WithinRange(0, 300)] = 50
    center0:float
    radius0:float
    center1:float
    radius1:float
    center2:float
    radius2:float
    center3:float
    radius3:float
    isAngleCreated:bool=False
    




#
# MeasurementWithSpheresWidget
#


class MeasurementWithSpheresWidget(ScriptedLoadableModuleWidget, VTKObservationMixin):
    """Uses ScriptedLoadableModuleWidget base class, available at:
    https://github.com/Slicer/Slicer/blob/main/Base/Python/slicer/ScriptedLoadableModule.py
    """

    def __init__(self, parent=None) -> None:
        """Called when the user opens the module the first time and the widget is initialized."""
        ScriptedLoadableModuleWidget.__init__(self, parent)
        VTKObservationMixin.__init__(self)  # needed for parameter node observation
        self.logic = None
        self._parameterNode = None
        self._parameterNodeGuiTag = None

    def setup(self) -> None:
        """Called when the user opens the module the first time and the widget is initialized."""
        ScriptedLoadableModuleWidget.setup(self)

        # Load widget from .ui file (created by Qt Designer).
        # Additional widgets can be instantiated manually and added to self.layout.
        uiWidget = slicer.util.loadUI(self.resourcePath("UI/MeasurementWithSpheres.ui"))
        self.layout.addWidget(uiWidget)
        self.ui = slicer.util.childWidgetVariables(uiWidget)
        
        
        
       
        # Set scene in MRML widgets. Make sure that in Qt designer the top-level qMRMLWidget's
        # "mrmlSceneChanged(vtkMRMLScene*)" signal in is connected to each MRML widget's.
        # "setMRMLScene(vtkMRMLScene*)" slot.
        uiWidget.setMRMLScene(slicer.mrmlScene)
        
        # Create logic class. Logic implements all computations that should be possible to run
        # in batch mode, without a graphical user interface.
        self.logic = MeasurementWithSpheresLogic()

        # Connections

        # These connections ensure that we update parameter node when scene is closed
        self.addObserver(slicer.mrmlScene, slicer.mrmlScene.StartCloseEvent, self.onSceneStartClose)

        self.addObserver(slicer.mrmlScene, slicer.mrmlScene.EndCloseEvent, self.onSceneEndClose)

        # Buttons
        self.ui.createangle.connect("clicked(bool)", self.createAngle)
        self.ui.changeangleposition.connect("clicked(bool)", self.changeAnglePosition)
        self.ui.generateline.connect("clicked(bool)", self.generateLine)
        self.ui.deleteline.connect("clicked(bool)", self.deleteLine)
        self.ui.resetview.connect("clicked(bool)", self.resetView)
        


        # Make sure parameter node is initialized (needed for module reload)
        self.initializeParameterNode()



    def cleanup(self) -> None:
        """Called when the application closes and the module widget is destroyed."""
        self.removeObservers()

    def enter(self) -> None:
        """Called each time the user opens this module."""
        # Make sure parameter node exists and observed
        self.initializeParameterNode()

    def exit(self) -> None:
        """Called each time the user opens a different module."""
        # Do not react to parameter node changes (GUI will be updated when the user enters into the module)
        if self._parameterNode:
            self._parameterNode.disconnectGui(self._parameterNodeGuiTag)
            self._parameterNodeGuiTag = None
            self.removeObserver(self._parameterNode, vtk.vtkCommand.ModifiedEvent, self._checkCanApply)

    def onSceneStartClose(self, caller, event) -> None:
        """Called just before the scene is closed."""
        # Parameter node will be reset, do not use it anymore
        self.setParameterNode(None)

    def onSceneEndClose(self, caller, event) -> None:
        """Called just after the scene is closed."""
        # If this module is shown while the scene is closed then recreate a new parameter node immediately
        if self.parent.isEntered:
            self.initializeParameterNode()

    def initializeParameterNode(self) -> None:
        """Ensure parameter node exists and observed."""
        # Parameter node stores all user choices in parameter values, node selections, etc.
        # so that when the scene is saved and reloaded, these settings are restored.

        self.setParameterNode(self.logic.getParameterNode())

       

    def setParameterNode(self, inputParameterNode: Optional[MeasurementWithSpheresParameterNode]) -> None:
        """
        Set and observe parameter node.
        Observation is needed because when the parameter node is changed then the GUI must be updated immediately.
        """

        if self._parameterNode:
            self._parameterNode.disconnectGui(self._parameterNodeGuiTag)
            self.removeObserver(self._parameterNode, vtk.vtkCommand.ModifiedEvent, self._checkCanApply)
        self._parameterNode = inputParameterNode
        if self._parameterNode:
            # Note: in the .ui file, a Qt dynamic property called "SlicerParameterName" is set on each
            # ui element that needs connection.
            self._parameterNodeGuiTag = self._parameterNode.connectGui(self.ui)
            self.addObserver(self._parameterNode, vtk.vtkCommand.ModifiedEvent, self._checkCanApply)
            self._checkCanApply()

    def _checkCanApply(self, caller=None, event=None) -> None:


        if self._parameterNode.isAngleCreated:
            self.ui.resetview.toolTip=("Reset View")
            self.ui.resetview.enabled = True
            self.ui.changeangleposition.toolTip = _("Change Angle")
            self.ui.changeangleposition.enabled = True
            self.ui.createangle.toolTip = _("Create Angle")
            self.ui.createangle.enabled = False
            self.ui.deleteline.toolTip = _("Delete Line")
            self.ui.deleteline.enabled = True
            self.ui.generateline.toolTip = _("Generate Line")
            self.ui.generateline.enabled = True


        else:
            self.ui.changeangleposition.toolTip = _("Change Angle")
            self.ui.changeangleposition.enabled = False
            self.ui.createangle.toolTip = _("Create Angle")
            self.ui.createangle.enabled = True
            self.ui.deleteline.toolTip = _("Delete Line")
            self.ui.deleteline.enabled = True
            self.ui.generateline.toolTip = _("Generate Line")
            self.ui.generateline.enabled = True
            self.ui.resetview.toolTip=("Reset View")
            self.ui.resetview.enabled = True
      





        
    def resetView(self)->None:
        slicer.mrmlScene.RemoveNode(self._parameterNode.lineNode)
        slicer.mrmlScene.RemoveNode(self._parameterNode.lineNode2)
        slicer.mrmlScene.RemoveNode(self._parameterNode.lineNode3)
        slicer.mrmlScene.RemoveNode(self._parameterNode.angleNode)
        slicer.mrmlScene.RemoveNode(self._parameterNode.markups)
        

        for itemIndex, model in enumerate(self._parameterNode.models):

            slicer.mrmlScene.RemoveNode(model)
        self._parameterNode.i=0
        self._parameterNode.count=1
        self._parameterNode.isAngleCreated=False
        self._checkCanApply()
        self._parameterNode.spheres = [vtk.vtkSphereSource() for _ in range(4)]
        self._parameterNode.models = []

        self._parameterNode.markups.RemoveObserver(self._parameterNode.observerId)

        slicer.app.processEvents()


        slicer.util.forceRenderAllViews()

        
        
        
        
        

    def deleteLine(self)->None:
        name=self.ui.linetobedeleted.toPlainText()
        self.logic.deleteLine(name)
    def generateLine(self)->None:
        coordinates = self.ui.coordinatesofline.toPlainText().split(',')

 
        x, y, z = map(int, coordinates)
        
       
        self.logic.generateLine(self.ui.lineLengthSliderWidget.value,x,y,z, self.ui.nameofline.toPlainText())

    def changePoints(self,markups,spheres, caller=None, event=None)->None:
       
         
        
        
        self.logic.UpdateModels(self._parameterNode.lineNode,self._parameterNode.lineNode2,self._parameterNode.lineNode3,self._parameterNode.angleNode,self._parameterNode.i,self._parameterNode.count,self._parameterNode.markups,self._parameterNode.spheres)

    def createAngle(self, caller=None, event=None)->None:
        self._parameterNode.modelsLogic = slicer.modules.models.logic()

        for itemIndex, sphere in enumerate(self._parameterNode.spheres):
            sphere.SetPhiResolution(30)
            sphere.SetThetaResolution(30)
            self._parameterNode.model =self._parameterNode.modelsLogic.AddModel(sphere.GetOutputPort())
            self._parameterNode.model.GetDisplayNode().SetVisibility2D(True)


            self._parameterNode.model.GetDisplayNode().SetSliceIntersectionThickness(3)
            self._parameterNode.model.GetDisplayNode().SetColor(1,1-itemIndex*0.3,itemIndex*0.3)
            self._parameterNode.models.append(self._parameterNode.model)
    
            
        self._parameterNode.lineNode = slicer.mrmlScene.AddNewNodeByClass('vtkMRMLMarkupsLineNode','length1')
        self._parameterNode.lineNode2 = slicer.mrmlScene.AddNewNodeByClass('vtkMRMLMarkupsLineNode','length2')
        self._parameterNode.lineNode3 = slicer.mrmlScene.AddNewNodeByClass('vtkMRMLMarkupsLineNode','length3')
        self._parameterNode.angleNode = slicer.mrmlScene.AddNewNodeByClass('vtkMRMLMarkupsAngleNode','Angle')
        self._parameterNode.markups = slicer.mrmlScene.GetFirstNodeByClass('vtkMRMLMarkupsFiducialNode')
        self._parameterNode.i=0
        self._parameterNode.count=1
        center0, radius0 = self.logic.sphereFrom3Points(self._parameterNode.markups,0)
        center1, radius1 = self.logic.sphereFrom3Points(self._parameterNode.markups, 3)
        center2, radius2 = self.logic.sphereFrom3Points(self._parameterNode.markups, 6)
        center3, radius3 = self.logic.sphereFrom3Points(self._parameterNode.markups, 9)
        self._parameterNode.lineNode.AddControlPointWorld(center0)
        self._parameterNode.lineNode.AddControlPointWorld(center1)
        self._parameterNode.lineNode2.AddControlPointWorld(center1)
        self._parameterNode.lineNode2.AddControlPointWorld(center2)
        self._parameterNode.lineNode3.AddControlPointWorld((center0 + center1) / 2)
        self._parameterNode.lineNode3.AddControlPointWorld((center2 + center3) / 2)
        self._parameterNode.angleNode.AddControlPointWorld((center0 + center1) / 2)
        self._parameterNode.angleNode.AddControlPointWorld((center1 + center2) / 2)
        self._parameterNode.isAngleCreated=True
        self._checkCanApply()   

          
            
            
            

        
        self.logic.UpdateModels(self._parameterNode.lineNode,self._parameterNode.lineNode2,self._parameterNode.lineNode3,self._parameterNode.angleNode,self._parameterNode.i,self._parameterNode.count,self._parameterNode.markups,self._parameterNode.spheres)
        self._parameterNode.observerId= self._parameterNode.markups.AddObserver(slicer.vtkMRMLMarkupsNode.PointModifiedEvent, self.changePoints, 2)

    def changeAnglePosition(self)->None:
        self._parameterNode.i, self._parameterNode.count = self.logic.changeAngle(
        self._parameterNode.i,
        self._parameterNode.count,
        self._parameterNode.angleNode,
        self._parameterNode.markups
    )
        
        
          


        
 


class MeasurementWithSpheresLogic(ScriptedLoadableModuleLogic):
    """This class should implement all the actual
    computation done by your module.  The interface
    should be such that other python code can import
    this class and make use of the functionality without
    requiring an instance of the Widget.
    Uses ScriptedLoadableModuleLogic base class, available at:
    https://github.com/Slicer/Slicer/blob/main/Base/Python/slicer/ScriptedLoadableModule.py
    """

    def __init__(self) -> None:
        """Called when the logic class is instantiated. Can be used for initializing member variables."""
        ScriptedLoadableModuleLogic.__init__(self)
        

    def getParameterNode(self):
        return MeasurementWithSpheresParameterNode(super().getParameterNode())
    
    def deleteLine(self,name):
        deletedline = slicer.util.getNode(name)
        deletedline.RemoveAllControlPoints()
    def generateLine(self,lineLength,x,y,z,nameofline):
        lineNode = slicer.mrmlScene.AddNewNodeByClass('vtkMRMLMarkupsLineNode', nameofline)
        lineNode.AddControlPointWorld(x,y,z)
        
        lineNode.AddControlPointWorld(x,y,z+lineLength)
        lineDisplayNode = slicer.util.getNode(lineNode.GetDisplayNodeID())
       
        # Set line color (red in this example)
        lineDisplayNode.SetColor([1, 0, 0])

        # Set line thickness
        lineDisplayNode.SetLineWidth(2)
       

    def sphereFrom3Points(self,markupsNode, startPointIndex):
        """Compute center and radius of 3-point sphere from 3 fiducial points
        source: https://stackoverflow.com/questions/20314306/find-arc-circle-equation-given-three-points-in-space-3d
        """
        A = np.zeros(3)
        B = np.zeros(3)
        C = np.zeros(3)
        if markupsNode is None:
            markupsNode=slicer.mrmlScene.GetFirstNodeByClass('vtkMRMLMarkupsFiducialNode')
        markupsNode.GetNthControlPointPosition(startPointIndex,A)
        markupsNode.GetNthControlPointPosition(startPointIndex+1,B)
        markupsNode.GetNthControlPointPosition(startPointIndex+2,C)
        a = np.linalg.norm(C - B)
        b = np.linalg.norm(C - A)
        c = np.linalg.norm(B - A)
        s = (a + b + c) / 2
        R = a*b*c / 4 / np.sqrt(s * (s - a) * (s - b) * (s - c))
        b1 = a*a * (b*b + c*c - a*a)
        b2 = b*b * (a*a + c*c - b*b)
        b3 = c*c * (a*a + b*b - c*c)
        P = np.column_stack((A, B, C)).dot(np.hstack((b1, b2, b3)))
        P /= b1 + b2 + b3
        return P, R

    def UpdateModels(self,lineNode,lineNode2,lineNode3,angleNode,i,count,markups,spheres):
        """Update the sphere and line models from the fiducial points"""
        
        center0, radius0 = self.sphereFrom3Points(markups,0)
        center1, radius1 = self.sphereFrom3Points(markups, 3)
        center2, radius2 = self.sphereFrom3Points(markups, 6)

        center3, radius3 = self.sphereFrom3Points(markups, 9)

        

        spheres[0].SetCenter(center0)
        spheres[0].SetRadius(radius0)
        spheres[1].SetCenter(center1)
        spheres[1].SetRadius(radius1)
        spheres[2].SetCenter(center2)
        spheres[2].SetRadius(radius2)
        spheres[3].SetCenter(center3)
        spheres[3].SetRadius(radius3)

        


        lineNode.SetNthControlPointPosition(0,center0)
        lineNode.SetNthControlPointPosition(1,center1)

        lineNode2.SetNthControlPointPosition(0,center2)
        lineNode2.SetNthControlPointPosition(1,center3)

        lineNode = slicer.util.getNode(lineNode.GetDisplayNodeID())

        # Set line color (red in this example)
        lineNode.SetColor([1, 0, 0])
        lineNode.SetLineWidth(2)

        lineNode2 = slicer.util.getNode(lineNode2.GetDisplayNodeID())

        # Set line color (red in this example)
        lineNode2.SetColor([1, 0, 0])
        lineNode2.SetLineWidth(2)

 


        
    
     
 
        
        # Calculate the midpoint between the centers of Sphere 1 and Sphere 2
        midpoint_1_2 = (center0 + center1) / 2

        # Calculate the midpoint between the centers of Sphere 3 and Sphere 4
        midpoint_3_4 = (center2 + center3) / 2
        lineNode3.SetNthControlPointPosition(0,midpoint_1_2)
        lineNode3.SetNthControlPointPosition(1,midpoint_3_4)
     
        lineDisplayNode3 = slicer.util.getNode(lineNode3.GetDisplayNodeID())

        # Set line color (red in this example)
        lineDisplayNode3.SetColor([1, 0, 0])

        # Set line thickness
        lineDisplayNode3.SetLineWidth(2)
        
        angleNode.SetNthControlPointPosition(0,midpoint_1_2)
        angleNode.SetNthControlPointPosition(1,midpoint_3_4)
      
        
        

        angleDisplayNode = slicer.util.getNode(angleNode.GetDisplayNodeID())

        # Set line color (red in this example)
        angleDisplayNode.SetColor([1, 0, 0])
        angleDisplayNode.SetLineWidth(2)
        distance_anglepoints = np.linalg.norm(midpoint_3_4 - midpoint_1_2)

         
        print('distance between layers is:',distance_anglepoints)
    
        # Set line thickness
        

        
        slicer.app.processEvents()


        slicer.util.forceRenderAllViews()


    def changeAngle(self,i,count,angleNode,markups):

         
        centertemp=0
     
        if i<4 :
            if i!=0:
                angleNode.RemoveNthControlPoint(2)
            
            center, radius = self.sphereFrom3Points(markups, i*3)
            centertemp=center
            angleNode.AddControlPointWorld(center)
            count=+1
            i+=1
        else:
            i=0
            positionofangle0= angleNode.GetNthControlPointPosition(0)
            positionofangle1= angleNode.GetNthControlPointPosition(1)
            center, radius = self.sphereFrom3Points(markups, 0)
            angleNode.RemoveAllControlPoints()
            angleNode.AddControlPointWorld(positionofangle1)
            angleNode.AddControlPointWorld(positionofangle0)
        return i, count

     

  


#
# MeasurementWithSpheresTest
#








 